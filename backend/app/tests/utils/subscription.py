import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from app.models.core import (
    PaymentRecurrenceStatus,
    Subscription,
    SubscriptionMetric,
    SubscriptionPlan,
)
from app.tests.utils.user import create_random_user


def create_test_subscription_plan(db: Session) -> SubscriptionPlan:
    """Create a test subscription plan for testing."""
    plan = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Test Plan",
        price=9.99,
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
        currency="USD",
        description="Test subscription plan for automated tests",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def create_test_subscription(
    db: Session, user_id: uuid.UUID | None = None, plan_id: uuid.UUID | None = None
) -> Subscription:
    """Create a test subscription for testing.

    Creates a user and plan if not provided.
    """
    if not user_id:
        user = create_random_user(db)
        user_id = user.id

    if not plan_id:
        plan = create_test_subscription_plan(db)
        plan_id = plan.id

    now = datetime.now(timezone.utc)
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=user_id,
        subscription_plan_id=plan_id,
        start_date=now,
        end_date=now + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        payment_recurrence_status=PaymentRecurrenceStatus.ACTIVE,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription
