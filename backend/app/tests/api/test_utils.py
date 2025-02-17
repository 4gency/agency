import uuid
from datetime import datetime, timedelta, timezone

from app.api.utils import update_user_active_subscriptions
from app.models.core import Subscription, SubscriptionMetric, User

class DummySession:
    def __init__(self):
        self.commits = 0
        self.added = []
        self.refreshed = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        self.refreshed.append(obj)


def test_update_user_active_subscriptions_deactivates_expired_and_applies_subscriptions():
    now = datetime.now(timezone.utc)

    expired_subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=1),  # End date in the past
        is_active=True,
        metric_type=SubscriptionMetric.DAY,
        metric_status=5,
        stripe_subscription_id=None,
    )
    active_subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=10),  # End date in the future
        is_active=True,
        metric_type=SubscriptionMetric.DAY,
        metric_status=5,
        stripe_subscription_id=None,
    )

    applies_subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=10),  # end_date is irrelevant for APPLIES
        is_active=True,
        metric_type=SubscriptionMetric.APPLIES,
        metric_status=0,  # No credits left
        stripe_subscription_id=None,
    )

    inactive_subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=1),
        is_active=False,
        metric_type=SubscriptionMetric.DAY,
        metric_status=5,
        stripe_subscription_id=None,
    )

    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        hashed_password="hashedpassword",
        subscriptions=[
            expired_subscription,
            active_subscription,
            applies_subscription,
            inactive_subscription,
        ],
    )

    dummy_session = DummySession()

    update_user_active_subscriptions(dummy_session, user)

    assert expired_subscription.is_active is False
    assert applies_subscription.is_active is False

    assert active_subscription.is_active is True
    assert inactive_subscription.is_active is False

    assert dummy_session.commits == 2

    assert expired_subscription in dummy_session.added
    assert applies_subscription in dummy_session.added
    assert dummy_session.refreshed.count(user) == 2


def test_update_user_active_subscriptions_no_deactivation():
    now = datetime.now(timezone.utc)

    active_subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=10),  # Future end date
        is_active=True,
        metric_type=SubscriptionMetric.DAY,
        metric_status=5,
        stripe_subscription_id=None,
    )

    user = User(
        id=uuid.uuid4(),
        email="user2@example.com",
        hashed_password="hashedpassword",
        subscriptions=[active_subscription],
    )

    dummy_session = DummySession()

    update_user_active_subscriptions(dummy_session, user)

    assert active_subscription.is_active is True

    assert dummy_session.commits == 0
    assert len(dummy_session.added) == 0
    assert len(dummy_session.refreshed) == 0
