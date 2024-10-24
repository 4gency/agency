import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import SessionDep, get_current_active_superuser
from app.crud import subscription as crud_subscription
from app.models.core import (
    Message,
    SubscriptionPlanCreate,
    SubscriptionPlanPublic,
    SubscriptionPlansPublic,
    SubscriptionPlanUpdate,
)

router = APIRouter()


@router.get("/plans", response_model=SubscriptionPlansPublic)
def read_subscription_plans(
    session: SessionDep,
) -> Any:
    """
    Retrieve subscription plans (public endpoint).
    """
    subscription_plans = crud_subscription.get_subscription_plans(
        session=session,
    )
    count = crud_subscription.get_total_subscription_plans_count(session=session)
    subscription_plans_public = [
        SubscriptionPlanPublic.model_validate(sp) for sp in subscription_plans
    ]
    return SubscriptionPlansPublic(plans=subscription_plans_public, count=count)


@router.get("/plans/{id}", response_model=SubscriptionPlanPublic)
def read_subscription_plan(
    *,
    session: SessionDep,
    id: uuid.UUID,
) -> Any:
    """
    Get subscription plan by ID (public endpoint).
    """
    subscription_plan = crud_subscription.get_subscription_plan_by_id(
        session=session, id=id
    )
    if not subscription_plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    return subscription_plan


@router.post(
    "/plans",
    response_model=SubscriptionPlanPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def create_subscription_plan(
    *,
    session: SessionDep,
    subscription_plan_in: SubscriptionPlanCreate,
) -> Any:
    """
    Create new subscription plan (superuser only).
    """
    subscription_plan = crud_subscription.create_subscription_plan(
        session=session, subscription_plan_create=subscription_plan_in
    )
    # TODO: Add webhook to create subscription plan in Stripe
    return subscription_plan


@router.put(
    "/plans/{id}",
    response_model=SubscriptionPlanPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def update_subscription_plan(
    *,
    session: SessionDep,
    id: uuid.UUID,
    subscription_plan_in: SubscriptionPlanUpdate,
) -> Any:
    """
    Update a subscription plan (superuser only).
    """
    subscription_plan = crud_subscription.get_subscription_plan_by_id(
        session=session, id=id
    )
    if not subscription_plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    updated_subscription_plan = crud_subscription.update_subscription_plan(
        session=session,
        db_subscription_plan=subscription_plan,
        subscription_plan_in=subscription_plan_in,
    )
    return updated_subscription_plan


@router.delete("/plans/{id}", dependencies=[Depends(get_current_active_superuser)])
def delete_subscription_plan(
    *,
    session: SessionDep,
    id: uuid.UUID,
) -> Message:
    """
    Delete a subscription plan (superuser only).
    """
    subscription_plan = crud_subscription.get_subscription_plan_by_id(
        session=session, id=id
    )
    if not subscription_plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    crud_subscription.delete_subscription_plan(
        session=session, db_subscription_plan=subscription_plan
    )
    return Message(message="Subscription plan deleted successfully")
