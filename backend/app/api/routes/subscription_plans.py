import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import OptionalCurrentUser, SessionDep, get_current_active_superuser
from app.integrations import stripe
from app.models.core import (
    Message,
    SubscriptionPlanCreate,
    SubscriptionPlanPublic,
    SubscriptionPlansPublic,
    SubscriptionPlanUpdate,
    ErrorMessage,
)
from app.models.crud import subscription as crud_subs

router = APIRouter()


@router.get("/", response_model=SubscriptionPlansPublic)
def read_subscription_plans(
    *, session: SessionDep, only_active: bool = True, user: OptionalCurrentUser
) -> Any:
    """
    Retrieve subscription plans (public endpoint).
    """

    # 1) Retrieve subscription plans
    subscription_plans = crud_subs.get_subscription_plans(session=session)

    # 2) Optionally filter to only active plans
    if only_active:
        subscription_plans = [plan for plan in subscription_plans if plan.is_active]

    # 3) Convert each plan to its public schema
    public_plans = [
        SubscriptionPlanPublic.model_validate(plan) for plan in subscription_plans
    ]

    # 4) If the user is a subscriber, attach badges or add any plans not already in the list
    if user and user.is_subscriber:
        active_subscriptions = user.get_active_subscriptions()

        for active_sub in active_subscriptions:
            # Find if this plan is already in our public list
            matched_plan = next(
                (p for p in public_plans if p.id == active_sub.subscription_plan_id),
                None,
            )
            if matched_plan:
                matched_plan.has_badge = True
                matched_plan.badge_text = "Your Plan"
                matched_plan.button_text = "Current Plan"
                matched_plan.button_enabled = False
            else:
                # Create a new public plan entry
                plan_public = SubscriptionPlanPublic.model_validate(
                    active_sub.subscription_plan
                )
                plan_public.has_badge = True
                plan_public.badge_text = "Your Plan"
                plan_public.button_text = "Current Plan"
                plan_public.button_enabled = False
                plan_public.is_active = True
                public_plans.append(plan_public)

    # 5) Sort the *final* list of subscription plans by price
    public_plans.sort(key=lambda plan: plan.price)

    # 6) Return the collection of public subscription plans
    return SubscriptionPlansPublic(plans=public_plans)


@router.get("/{id}", response_model=SubscriptionPlanPublic, responses={
    404: {
        "model": "ErrorMessage",
        "description": "Subscription plan not found",
        "content": {
            "application/json": {
                "examples": {
                    "plan_not_found": {
                        "summary": "Subscription plan not found",
                        "value": {"detail": "Subscription plan not found"},
                    }
                }
            }
        },
    },
})
def read_subscription_plan(
    *,
    session: SessionDep,
    id: uuid.UUID,
) -> Any:
    """
    Get subscription plan by ID (public endpoint).
    """
    subscription_plan = crud_subs.get_subscription_plan_by_id(session=session, id=id)
    if not subscription_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found"
        )
    return subscription_plan


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=SubscriptionPlanPublic,
    responses={
        400: {
            "model": "ErrorMessage",
            "description": "Validation error",
            "content": {
                "application/json": {
                    "examples": {
                        "validation_error": {
                            "summary": "Validation error",
                            "value": {"detail": "Validation error message"},
                        }
                    }
                }
            },
        },
        401: {
            "model": "ErrorMessage",
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Not authenticated",
                            "value": {"detail": "Not authenticated"},
                        }
                    }
                }
            },
        },
        403: {
            "model": "ErrorMessage",
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_superuser": {
                            "summary": "The user doesn't have enough privileges",
                            "value": {"detail": "The user doesn't have enough privileges"},
                        }
                    }
                }
            },
        },
    },
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
    "/{id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    responses={
        401: {
            "model": "ErrorMessage",
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Not authenticated",
                            "value": {"detail": "Not authenticated"},
                        }
                    }
                }
            },
        },
        403: {
            "model": "ErrorMessage",
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_superuser": {
                            "summary": "The user doesn't have enough privileges",
                            "value": {"detail": "The user doesn't have enough privileges"},
                        }
                    }
                }
            },
        },
        404: {
            "model": "ErrorMessage",
            "description": "Subscription plan not found",
            "content": {
                "application/json": {
                    "examples": {
                        "plan_not_found": {
                            "summary": "Subscription plan not found",
                            "value": {"detail": "Subscription plan not found"},
                        }
                    }
                }
            },
        },
    },
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
    subscription_plan = crud_subs.get_subscription_plan_by_id(session=session, id=id)
    if not subscription_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found"
        )
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


@router.delete(
    "/{id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    responses={
        401: {
            "model": "ErrorMessage",
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Not authenticated",
                            "value": {"detail": "Not authenticated"},
                        }
                    }
                }
            },
        },
        403: {
            "model": "ErrorMessage",
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_superuser": {
                            "summary": "The user doesn't have enough privileges",
                            "value": {"detail": "The user doesn't have enough privileges"},
                        }
                    }
                }
            },
        },
        404: {
            "model": "ErrorMessage",
            "description": "Subscription plan not found",
            "content": {
                "application/json": {
                    "examples": {
                        "plan_not_found": {
                            "summary": "Subscription plan not found",
                            "value": {"detail": "Subscription plan not found"},
                        }
                    }
                }
            },
        },
    },
)
def delete_subscription_plan(
    *,
    session: SessionDep,
    id: uuid.UUID,
) -> Message:
    """
    Delete a subscription plan (superuser only).
    """
    subscription_plan = crud_subs.get_subscription_plan_by_id(session=session, id=id)
    if not subscription_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found"
        )

    crud_subs.deactivate_subscription_plan(
        session=session, db_subscription_plan=subscription_plan
    )

    if stripe.integration_enabled():
        try:
            stripe.deactivate_subscription_plan(
                session=session,
                subscription_plan=subscription_plan,
            )
        except stripe.NotFound:
            pass  # Subscription plan not found in Stripe
    return Message(message="Subscription plan deleted successfully")
