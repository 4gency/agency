import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, get_current_active_superuser
from app.models.crud import subscription as crud_subs
from app.models.core import (
    Message,
    Subscription,
    SubscriptionPublic,
    SubscriptionPlanCreate,
    SubscriptionPlanPublic,
    SubscriptionPlansPublic,
    SubscriptionPlanUpdate,
)
from app.integrations import stripe

router = APIRouter()

@router.get("/plans", response_model=SubscriptionPlansPublic)
def read_subscription_plans(
    *,
    session: SessionDep,
    only_active: bool = True,
) -> Any:
    """
    Retrieve subscription plans (public endpoint).
    """
    sps_public: list[SubscriptionPlanPublic] = []
    subscription_plans = crud_subs.get_subscription_plans(session=session,)
    
    # Serialize subscription plans
    for sp in subscription_plans:
        if only_active and not sp.is_active:
            continue
        sp_temp = SubscriptionPlanPublic.model_validate(sp)
        sps_public.append(sp_temp)

    return SubscriptionPlansPublic(plans=sps_public)


@router.get("/plans/{id}", response_model=SubscriptionPlanPublic)
def read_subscription_plan(
    *,
    session: SessionDep,
    id: uuid.UUID,
) -> Any:
    """
    Get subscription plan by ID (public endpoint).
    """
    subscription_plan = crud_subs.get_subscription_plan_by_id(
        session=session, id=id
    )
    if not subscription_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
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
    subscription_plan = crud_subs.create_subscription_plan(
        session=session, subscription_plan_create=subscription_plan_in
    )
    if stripe.integration_enabled():
        stripe.create_subscription_plan(
            session=session,
            subscription_plan=subscription_plan,
        )
    return subscription_plan


@router.put(
    "/plans/{id}",
    response_model=Message,
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
    subscription_plan = crud_subs.get_subscription_plan_by_id(
        session=session, id=id
    )
    if not subscription_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
    subscription_plan_data = subscription_plan_in.model_dump(exclude_unset=True)
    subscription_plan.sqlmodel_update(subscription_plan_data)
    if stripe.integration_enabled():
        stripe.update_subscription_plan(
            session=session,
            subscription_plan=subscription_plan,
        )
    session.add(subscription_plan)
    session.commit()
    session.refresh(subscription_plan)
    return Message(message="Subscription plan updated successfully")


@router.delete("/plans/{id}", dependencies=[Depends(get_current_active_superuser)], response_model=Message)
def delete_subscription_plan(
    *,
    session: SessionDep,
    id: uuid.UUID,
) -> Message:
    """
    Delete a subscription plan (superuser only).
    """
    subscription_plan = crud_subs.get_subscription_plan_by_id(
        session=session, id=id
    )
    if not subscription_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
    
    crud_subs.deactivate_subscription_plan(
        session=session,
        db_subscription_plan=subscription_plan
    )
    
    if stripe.integration_enabled():
        stripe.deactivate_subscription_plan(
            session=session,
            subscription_plan=subscription_plan,
        )
    return Message(message="Subscription plan deleted successfully")
