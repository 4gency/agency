from uuid import UUID
from app.integrations import stripe
from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.crud import subscription as crud_subs

router = APIRouter()

@router.post("/stripe/checkout-session")
def get_stripe_checkout_session(
    session: SessionDep,
    subscription_plan_id: UUID,
    user: CurrentUser,
    ):
    """
    Get Stripe checkout session.
    """
    sub_plan = crud_subs.get_subscription_plan_by_id(
        session=session, 
        id=subscription_plan_id
    )
    if not sub_plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    sub, payment = crud_subs.create_sub_payment(
        session=session,
        user=user,
        sub_plan=sub_plan,
        payment_status="pending",
        payment_gateway="stripe",
    )
    
    return stripe.create_checkout_subscription_session(
        session=session,
        subscription_plan=sub_plan,
        user=user,
        payment=payment,
    )