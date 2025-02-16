from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.config import settings
from app.integrations import stripe as stripe_controller
from app.models.core import (
    CheckoutSession,
    CheckoutSessionPublic,
    CheckoutSessionUpdate,
    SubscriptionPlan,
)
from app.models.crud import subscription as crud_subs
from app.utils import timestamp_to_datetime

router = APIRouter()


@router.post("/stripe/success")
def stripe_success(
    session: SessionDep,
    session_id: str,
    user: CurrentUser,
):
    """
    Stripe success route: usuário retornou do Stripe com session_id.
    """
    checkout = session.exec(
        select(CheckoutSession).where(CheckoutSession.session_id == session_id)
    ).first()

    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    plan: SubscriptionPlan | None = crud_subs.get_subscription_plan_by_id(
        session=session, id=checkout.subscription_plan_id
    )

    if not plan:
        raise HTTPException(
            status_code=500,
            detail="Subscription plan not found, please contact support!",
        )

    if checkout.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Checkout session does not belong to the authenticated user"
        )

    stripe_controller.handle_success_callback(session, checkout, plan, user)

    return {"message": "Success callback processed"}


@router.get(
    "/stripe/checkout-session/{session_id}", response_model=CheckoutSessionPublic
)
def get_stripe_checkout_session_by_id(
    session: SessionDep,
    session_id: UUID,
    user: CurrentUser,
):
    """
    Get Stripe checkout session by ID.
    """
    checkout = session.exec(
        select(CheckoutSession).where(
            CheckoutSession.id == session_id, CheckoutSession.user_id == user.id
        )
    ).first()
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout session not found")
    return CheckoutSessionPublic.model_validate(checkout)


@router.get("/stripe/checkout-session", response_model=list[CheckoutSessionPublic])
def get_stripe_checkout_sessions(
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: int = 30,
):
    """
    Get Stripe checkout sessions.
    """
    checkout_sessions = session.exec(
        select(CheckoutSession)
        .where(CheckoutSession.user_id == user.id)
        .offset(skip)
        .limit(limit)
    ).all()

    return [
        CheckoutSessionPublic.model_validate(checkout) for checkout in checkout_sessions
    ]


@router.post("/stripe/checkout-session", response_model=CheckoutSessionPublic)
def create_stripe_checkout_session(
    session: SessionDep,
    subscription_plan_id: UUID,
    user: CurrentUser,
) -> CheckoutSession:
    """
    Create Stripe checkout session.
    """
    sub_plan = crud_subs.get_subscription_plan_by_id(
        session=session, id=subscription_plan_id
    )
    if not sub_plan or not sub_plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found"
        )
    sub, payment = crud_subs.create_sub_payment(
        session=session,
        user=user,
        sub_plan=sub_plan,
        payment_status="pending",
        payment_gateway="stripe",
    )
    data = stripe_controller.create_checkout_subscription_session(
        session=session,
        subscription_plan=sub_plan,
        user=user,
        payment=payment,
    )

    checkout = CheckoutSession(
        payment_gateway="stripe",
        session_id=data["id"],
        session_url=data["url"],
        user_id=user.id,
        subscription_plan_id=subscription_plan_id,
        status=data["status"],
        payment_status=data["payment_status"],
        expires_at=timestamp_to_datetime(data["expires_at"]),
    )

    session.add(checkout)
    session.commit()

    return checkout


@router.patch(
    "/stripe/checkout-session/{session_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=CheckoutSessionPublic,
)
def update_stripe_checkout_session(
    session: SessionDep, session_id: UUID, checkout_session: CheckoutSessionUpdate
):
    """
    Update Stripe checkout session.
    """
    checkout = session.exec(
        select(CheckoutSession).where(CheckoutSession.id == session_id)
    ).first()
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout session not found")
    checkout_data = checkout_session.model_dump(exclude_unset=True)
    checkout.sqlmodel_update(checkout_data)
    session.add(checkout)
    session.commit()
    session.refresh(checkout)
    return CheckoutSessionPublic.model_validate(checkout)


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    session: SessionDep,
    stripe_signature: str = Header(None),
):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    except stripe.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    event_type = event.get("type", "")
    if event_type == "checkout.session.completed":
        stripe_controller.handle_checkout_session(session, event)
    else:
        print(f"Unhandled event type: {event_type}")

    return {"status": "success"}


@router.post("/stripe/cancel")
def stripe_cancel(
    session: SessionDep,
    session_id: str,
    user: CurrentUser,
):
    """
    Stripe cancel route: usuário retornou do Stripe pela URL de cancelamento.
    """
    # 1) Busca a checkout session local via "session_id" do Stripe
    checkout = session.exec(
        select(CheckoutSession).where(CheckoutSession.session_id == session_id)
    ).first()

    if not checkout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checkout session not found"
        )

    # 2) Busca o subscription_plan
    plan = crud_subs.get_subscription_plan_by_id(
        session=session, id=checkout.subscription_plan_id
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription plan not found, please contact support!",
        )

    # 3) Chama a função do "stripe_controller" para tratar cancelamento
    stripe_controller.handle_cancel_callback(session, checkout, plan, user)

    return {"message": "Cancel callback processed"}
