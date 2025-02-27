import logging
from typing import Any, cast
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
    ErrorMessage,
    Message,
)
from app.models.crud import subscription as crud_subs
from app.utils import timestamp_to_datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/stripe/success",
    response_model=Message,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization errors",
            "content": {
                "application/json": {
                    "examples": {
                        "credentials_error": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        },
                        "permissions_error": {
                            "summary": "Not enough permissions",
                            "value": {"detail": "Not enough permissions"},
                        },
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive User",
                            "value": {"detail": "Inactive User"},
                        },
                        "checkout_not_found": {
                            "summary": "Checkout session not found",
                            "value": {"detail": "Checkout session not found"},
                        },
                    }
                }
            },
        },
        500: {"model": ErrorMessage, "description": "Subscription plan not found"},
    },
)
def stripe_success(
    *,
    session: SessionDep,
    session_id: str,
    user: CurrentUser,
) -> Any:
    """
    Stripe success route: usuário retornou do Stripe com session_id.
    """
    checkout = session.exec(
        select(CheckoutSession).where(CheckoutSession.session_id == session_id)
    ).first()

    if not checkout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checkout session not found"
        )

    if checkout.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Checkout session does not belong to the authenticated user",
        )

    stripe_controller.handle_success_callback(session, checkout)

    try:
        stripe_controller.handle_invoice_payment_succeeded_in_checkout_callback(
            session=session, checkout=checkout, user=user, plan=checkout.plan
        )
    except Exception as e:
        logger.error(
            f"Error handling invoice payment succeeded in checkout callback: {e}"
        )

    return {"message": "Success callback processed"}


@router.get(
    "/stripe/checkout-session/{session_id}",
    response_model=CheckoutSessionPublic,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Could not validate credentials",
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive User",
                            "value": {"detail": "Inactive User"},
                        },
                        "checkout_not_found": {
                            "summary": "Checkout session not found",
                            "value": {"detail": "Checkout session not found"},
                        },
                    }
                }
            },
        },
    },
)
def get_stripe_checkout_session_by_id(
    *,
    session: SessionDep,
    session_id: UUID,
    user: CurrentUser,
) -> Any:
    """
    Get Stripe checkout session by ID.
    """
    checkout = session.exec(
        select(CheckoutSession).where(
            CheckoutSession.id == session_id, CheckoutSession.user_id == user.id
        )
    ).first()
    if not checkout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checkout session not found"
        )
    return CheckoutSessionPublic.model_validate(checkout)


@router.get(
    "/stripe/checkout-session",
    response_model=list[CheckoutSessionPublic],
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization errors",
            "content": {
                "application/json": {
                    "examples": {
                        "could_not_validate": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        },
                        "not_enough_permissions": {
                            "summary": "Not enough permissions",
                            "value": {"detail": "Not enough permissions"},
                        },
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive User",
                            "value": {"detail": "Inactive User"},
                        },
                    }
                }
            },
        },
    },
)
def get_stripe_checkout_sessions(
    *,
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: int = 30,
) -> Any:
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


@router.post(
    "/stripe/checkout-session",
    response_model=CheckoutSessionPublic,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Could not validate credentials",
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive User",
                            "value": {"detail": "Inactive User"},
                        },
                        "subscription_plan_not_found": {
                            "summary": "Subscription plan not found",
                            "value": {"detail": "Subscription plan not found"},
                        },
                    }
                }
            },
        },
    },
)
def create_stripe_checkout_session(
    *,
    session: SessionDep,
    subscription_plan_id: UUID,
    user: CurrentUser,
) -> Any:
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
    data = stripe_controller.create_checkout_subscription_session(
        session=session,
        subscription_plan=sub_plan,
        user=user,
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
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization errors",
            "content": {
                "application/json": {
                    "examples": {
                        "could_not_validate": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        },
                        "not_enough_privileges": {
                            "summary": "The user doesn't have enough privileges",
                            "value": {
                                "detail": "The user doesn't have enough privileges"
                            },
                        },
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive User",
                            "value": {"detail": "Inactive User"},
                        },
                        "session_not_found": {
                            "summary": "Checkout session not found",
                            "value": {"detail": "Checkout session not found"},
                        },
                    }
                }
            },
        },
    },
)
def update_stripe_checkout_session(
    *,
    session: SessionDep,
    session_id: UUID,
    checkout_session: CheckoutSessionUpdate,
) -> Any:
    """
    Update Stripe checkout session.
    """
    checkout = session.exec(
        select(CheckoutSession).where(CheckoutSession.id == session_id)
    ).first()
    if not checkout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checkout session not found"
        )
    checkout_data = checkout_session.model_dump(exclude_unset=True)
    checkout.sqlmodel_update(checkout_data)
    session.add(checkout)
    session.commit()
    session.refresh(checkout)
    return CheckoutSessionPublic.model_validate(checkout)


@router.post("/stripe/webhook", response_model=Message)
async def stripe_webhook(
    *,
    request: Request,
    session: SessionDep,
    stripe_signature: str = Header(None),
) -> Any:
    payload = await request.body()
    try:
        event = cast(
            stripe.Event,
            stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
                payload=payload,
                sig_header=stripe_signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            ),
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload or signature: {e}",
        )

    event_type = event.get("type", "")
    handlers = {
        "checkout.session.completed": stripe_controller.handle_checkout_session,
        "checkout.session.async_payment_succeeded": stripe_controller.handle_checkout_session,
        "invoice.paid": stripe_controller.handle_invoice_payment_succeeded,
        "charge.dispute.created": stripe_controller.handle_charge_dispute_created,
        "checkout.session.expired": stripe_controller.handle_checkout_session_expired,
        "checkout.session.async_payment_failed": stripe_controller.handle_checkout_session_async_payment_failed,
    }

    if handler := handlers.get(event_type):
        handler(session, event)
    else:
        print(f"Unhandled event type: {event_type}")

    return {"message": "success"}


@router.post(
    "/stripe/cancel",
    response_model=Message,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization errors",
            "content": {
                "application/json": {
                    "examples": {
                        "could_not_validate": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        },
                        "session_not_belonging": {
                            "summary": "Checkout session does not belong to the authenticated user",
                            "value": {
                                "detail": "Checkout session does not belong to the authenticated user"
                            },
                        },
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive User",
                            "value": {"detail": "Inactive User"},
                        },
                        "session_not_found": {
                            "summary": "Checkout session not found",
                            "value": {"detail": "Checkout session not found"},
                        },
                    }
                }
            },
        },
        500: {
            "model": ErrorMessage,
            "description": "Subscription plan not found, please contact support!",
        },
    },
)
def stripe_cancel(
    *,
    session: SessionDep,
    session_id: str,
    user: CurrentUser,
) -> Any:
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

    if checkout.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Checkout session does not belong to the authenticated user",
        )

    # 3) Chama a função do "stripe_controller" para tratar cancelamento
    stripe_controller.handle_cancel_callback(session, checkout)

    return {"message": "Cancel callback processed"}
