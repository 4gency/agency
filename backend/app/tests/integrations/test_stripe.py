import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
import stripe

from app.integrations.stripe import (
    BadRequest,
    NotFound,
    cancel_subscription,
    cancel_subscription_recurring_payment,
    create_checkout_subscription_session,
    create_subscription_plan,
    deactivate_subscription_plan,
    ensure_stripe_customer,
    handle_cancel_callback,
    handle_checkout_session,
    handle_success_callback,
    reactivate_subscription,
    update_subscription_payment,
    update_subscription_plan,
)
from app.models.core import (
    CheckoutSession,
    Payment,
    Subscription,
    SubscriptionMetric,
    SubscriptionPlan,
    User,
)


@pytest.fixture(scope="session", autouse=True)
def set_stripe_api_key() -> None:
    stripe.api_key = "sk_test_dummy"


@pytest.fixture(autouse=True)
def mock_integration_enabled(mocker: Any) -> None:
    mocker.patch("app.integrations.stripe.integration_enabled", return_value=True)


@pytest.fixture
def dummy_session() -> Any:
    class DummySession:
        def __init__(self) -> None:
            self.added: list[Any] = []
            self.commits: int = 0
            self.refreshed: list[Any] = []
            self.data: dict[Any, Any] = {}

        def add_all(self, objs: Any) -> None:
            self.added.extend(objs)

        def add(self, obj: Any) -> None:
            self.added.append(obj)

        def commit(self) -> None:
            self.commits += 1

        def refresh(self, obj: Any) -> None:
            self.refreshed.append(obj)

        def exec(self, statement: Any) -> MagicMock:
            return MagicMock(first=lambda: None)

        def get(self, model: Any, primary_key: Any) -> Any:
            return self.data.get((model, primary_key), None)

        def flush(self) -> None:
            pass

        def rollback(self) -> None:
            pass

    return DummySession()


@pytest.fixture
def mock_stripe_core_calls(mocker: Any) -> None:
    product_mock = MagicMock()
    product_mock.id = "prod_mock_id"
    mocker.patch("stripe.Product.create", return_value=product_mock)

    price_mock = MagicMock()
    price_mock.id = "price_mock_id"
    mocker.patch("stripe.Price.create", return_value=price_mock)

    pm = MagicMock()
    pm.id = "prod_mock_modified_id"
    mocker.patch("stripe.Product.modify", return_value=pm)

    pr = MagicMock()
    pr.unit_amount = 10000
    pr.currency = "usd"
    pr.recurring = {"interval": "month", "interval_count": 1}
    mocker.patch("stripe.Price.retrieve", return_value=pr)

    sm = MagicMock()
    sm.id = "sess_mock_id"
    mocker.patch("stripe.checkout.Session.create", return_value=sm)


@pytest.fixture(autouse=True)
def mock_all_stripe_calls(mocker: Any) -> None:
    pm = MagicMock(id="prod_mock_id")
    mocker.patch("stripe.Product.create", return_value=pm)
    mocker.patch("stripe.Product.modify", return_value=pm)

    pr = MagicMock(id="price_mock_id")
    mocker.patch("stripe.Price.create", return_value=pr)
    mocker.patch("stripe.Price.retrieve", return_value=pr)

    sub = MagicMock()
    sub.status = "active"
    sub.current_period_start = 1234567890
    sub.current_period_end = 1234567890
    sub.latest_invoice = "inv_mock_id"
    sub.delete.return_value = {"ended_at": 1234567890}
    mocker.patch("stripe.Subscription.retrieve", return_value=sub)
    mocker.patch("stripe.Subscription.delete", return_value={"ended_at": 1234567890})
    mocker.patch("stripe.Subscription.modify", return_value=sub)

    cm = MagicMock(id="cust_mock_id")
    mocker.patch("stripe.Customer.create", return_value=cm)

    inv = MagicMock()
    inv.status = "paid"
    inv.created = 1234567890
    inv.amount_paid = 999
    inv.currency = "usd"
    inv.payment_intent = "pi_mock_id"
    mocker.patch("stripe.Invoice.retrieve", return_value=inv)

    ch = MagicMock()
    ch.id = "sess_mock_id"
    ch.payment_status = "unpaid"

    def checkout_get_side_effect(key: Any, default: Any = None) -> Any:
        if key == "subscription":
            return "sub_mock_id"
        elif key == "metadata":
            return {}
        return default

    ch.get.side_effect = checkout_get_side_effect
    mocker.patch("stripe.checkout.Session.create", return_value=ch)
    mocker.patch("stripe.checkout.Session.retrieve", return_value=ch)


def test_create_subscription_plan_invalid_currency(dummy_session: Any) -> None:
    plan = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Test Plan",
        price=9.99,
        currency="invalid",
        description="A test plan",
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
    )
    with pytest.raises(BadRequest) as exc:
        create_subscription_plan(dummy_session, plan)
    assert "Invalid currency" in str(exc.value)


def test_create_subscription_plan_success(dummy_session: Any) -> None:
    plan = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Test Plan",
        price=9.99,
        currency="USD",
        description="A test plan",
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
    )
    p, pr = create_subscription_plan(dummy_session, plan)
    assert plan.stripe_product_id == "prod_mock_id"
    assert plan.stripe_price_id == "price_mock_id"
    assert dummy_session.commits == 1


def test_ensure_stripe_customer_already_exists(dummy_session: Any) -> None:
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="abc123",
        stripe_customer_id="existing_customer_id",
    )
    dummy_session.data[(User, user.id)] = user
    r = ensure_stripe_customer(dummy_session, user)
    assert r == "existing_customer_id"
    assert dummy_session.commits == 0


def test_ensure_stripe_customer_new(dummy_session: Any, mocker: Any) -> None:
    c = MagicMock()
    c.id = "cust_mock_id"
    mocker.patch("stripe.Customer.create", return_value=c)

    user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="abc123")
    dummy_session.data[(User, user.id)] = user

    r = ensure_stripe_customer(dummy_session, user)
    assert r == "cust_mock_id"
    assert user.stripe_customer_id == "cust_mock_id"
    assert dummy_session.commits == 1


def test_update_subscription_payment_no_stripe_id(dummy_session: Any) -> None:
    sub = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id=None,
    )
    pay = Payment(
        id=uuid.uuid4(),
        subscription_id=sub.id,
        user_id=sub.user_id,
        amount=9.99,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="pending",
        transaction_id="trx123",
    )
    dummy_session.data[(Subscription, sub.id)] = sub
    dummy_session.data[(Payment, pay.id)] = pay
    with pytest.raises(NotFound) as exc:
        update_subscription_payment(dummy_session, sub, pay)
    assert "does not have a Stripe Subscription ID" in str(exc.value)


def test_update_subscription_payment_success(dummy_session: Any, mocker: Any) -> None:
    sub_mock = MagicMock()
    sub_mock.status = "active"
    sub_mock.current_period_start = 1234567890
    sub_mock.current_period_end = 1234567890
    sub_mock.latest_invoice = "inv_mock_id"
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_mock)

    inv_mock = MagicMock()
    inv_mock.status = "paid"
    inv_mock.created = 1234567890
    inv_mock.amount_paid = 10000
    inv_mock.currency = "usd"
    inv_mock.payment_intent = "pi_mock_id"
    mocker.patch("stripe.Invoice.retrieve", return_value=inv_mock)

    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=False,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    p = Payment(
        id=uuid.uuid4(),
        subscription_id=s.id,
        user_id=s.user_id,
        amount=9.99,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="pending",
        transaction_id="trx123",
    )
    dummy_session.data[(Subscription, s.id)] = s
    dummy_session.data[(Payment, p.id)] = p

    update_subscription_payment(dummy_session, s, p)
    assert s.is_active is True
    assert p.payment_status == "paid"
    assert p.transaction_id == "pi_mock_id"
    assert dummy_session.commits == 1


def test_cancel_subscription_no_stripe_id(dummy_session: Any) -> None:
    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id=None,
    )
    dummy_session.data[(Subscription, s.id)] = s
    with pytest.raises(NotFound):
        cancel_subscription(dummy_session, s)


def test_cancel_subscription_success(dummy_session: Any, mocker: Any) -> None:
    mr = MagicMock()
    mr.status = "active"
    mr.ended_at = None
    mr.delete.return_value = {"ended_at": 1234567890}
    mocker.patch("stripe.Subscription.retrieve", return_value=mr)

    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    dummy_session.data[(Subscription, s.id)] = s
    cancel_subscription(dummy_session, s)
    mr.delete.assert_called_once()
    assert s.is_active is False
    assert dummy_session.commits == 1


def test_handle_checkout_session_paid(dummy_session: Any, mocker: Any) -> None:
    sm = MagicMock()
    sm.status = "active"
    sm.current_period_start = 1234567890
    sm.current_period_end = 1234567890
    sm.latest_invoice = None
    mocker.patch("stripe.Subscription.retrieve", return_value=sm)

    evt = {
        "data": {
            "object": {
                "id": "sess_mock_id",
                "payment_status": "paid",
                "subscription": "sub_mock_id",
                "metadata": {
                    "payment_id": str(uuid.uuid4()),
                    "subscription_id": str(uuid.uuid4()),
                },
            }
        }
    }
    sub_id = uuid.UUID(evt["data"]["object"]["metadata"]["subscription_id"])  # type: ignore
    pay_id = uuid.UUID(evt["data"]["object"]["metadata"]["payment_id"])  # type: ignore
    s = Subscription(
        id=sub_id,
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=False,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id=None,
    )
    p = Payment(
        id=pay_id,
        subscription_id=s.id,
        user_id=s.user_id,
        amount=9.99,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="pending",
        transaction_id="trx_mock_id",
    )
    dummy_session.data[(Subscription, s.id)] = s
    dummy_session.data[(Payment, p.id)] = p

    handle_checkout_session(dummy_session, evt)
    assert s.is_active is True
    assert p.payment_status == "paid"
    assert dummy_session.commits == 1


def test_handle_checkout_session_unpaid(dummy_session: Any) -> None:
    evt = {
        "data": {
            "object": {
                "id": "sess_mock_id",
                "payment_status": "unpaid",
                "metadata": {
                    "payment_id": str(uuid.uuid4()),
                },
            }
        }
    }
    pay_id = uuid.UUID(evt["data"]["object"]["metadata"]["payment_id"])  # type: ignore
    p = Payment(
        id=pay_id,
        subscription_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        amount=9.99,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="pending",
        transaction_id="trx_mock_id",
    )
    dummy_session.data[(Payment, p.id)] = p
    handle_checkout_session(dummy_session, evt)
    assert p.payment_status == "canceled"
    assert dummy_session.commits == 1


def test_reactivate_subscription_canceled(dummy_session: Any, mocker: Any) -> None:
    sub_m = MagicMock()
    sub_m.status = "canceled"
    sub_m.cancel_at_period_end = False
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_m)

    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=False,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    dummy_session.data[(Subscription, s.id)] = s
    with pytest.raises(BadRequest) as exc:
        reactivate_subscription(dummy_session, s)
    assert "Need a new subscription" in str(exc.value)
    assert dummy_session.commits == 0


def test_reactivate_subscription_success(dummy_session: Any, mocker: Any) -> None:
    sub_m = MagicMock()
    sub_m.status = "active"
    sub_m.cancel_at_period_end = True
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_m)

    mm = MagicMock()
    mm.status = "active"
    mm.cancel_at_period_end = False
    mocker.patch("stripe.Subscription.modify", return_value=mm)

    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=False,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    dummy_session.data[(Subscription, s.id)] = s
    reactivate_subscription(dummy_session, s)
    assert s.is_active is True
    assert dummy_session.commits == 1


def test_update_subscription_plan_creates_if_none(
    dummy_session: Any, mocker: Any
) -> None:
    def create_plan_side_effect(session: Any, plan: Any) -> Any:
        assert plan
        session.commits += 1
        return (MagicMock(), MagicMock())

    mc = mocker.patch(
        "app.integrations.stripe.create_subscription_plan",
        side_effect=create_plan_side_effect,
    )

    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="New Subscription Plan",
        price=9.99,
        currency="USD",
        description="A new subscription plan for testing",
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
        stripe_product_id=None,
        stripe_price_id=None,
    )
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    update_subscription_plan(dummy_session, pl)
    mc.assert_called_once()
    assert dummy_session.commits == 1


def test_update_subscription_plan_update_price(dummy_session: Any, mocker: Any) -> None:
    pm = MagicMock()
    pm.id = "existing_prod_id"
    mocker.patch("stripe.Product.modify", return_value=pm)

    op = MagicMock()
    op.unit_amount = 10000
    op.recurring = {"interval": "month", "interval_count": 1}
    mocker.patch("stripe.Price.retrieve", return_value=op)

    np = MagicMock()
    np.id = "new_price_id"
    mocker.patch("stripe.Price.create", return_value=np)

    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Updated Plan",
        price=50.0,
        currency="USD",
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
        stripe_product_id="existing_prod_id",
        stripe_price_id="existing_price_id",
        is_active=True,
    )
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    update_subscription_plan(dummy_session, pl)
    assert pl.stripe_price_id == "new_price_id"
    assert dummy_session.commits == 1


def test_update_subscription_plan_invalid_metric(dummy_session: Any) -> None:
    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Invalid Plan",
        price=10.0,
        currency="USD",
        metric_type=SubscriptionMetric("month"),
        metric_value=-1,
        stripe_product_id="prod_id",
        stripe_price_id="price_id",
    )
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    with pytest.raises(BadRequest) as e:
        update_subscription_plan(dummy_session, pl)
    assert "Invalid metric value" in str(e.value)


def test_deactivate_subscription_plan_success(dummy_session: Any, mocker: Any) -> None:
    pm = MagicMock()
    pm.id = "prod_mock_deactivated"
    mocker.patch("stripe.Product.modify", return_value=pm)

    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Deactivating Plan",
        price=10.0,
        currency="USD",
        stripe_product_id="existing_prod_id",
        stripe_price_id="existing_price_id",
    )
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    deactivate_subscription_plan(dummy_session, pl)
    stripe.Product.modify.assert_called_once_with("existing_prod_id", active=False)  # type: ignore


def test_deactivate_subscription_plan_not_found(dummy_session: Any) -> None:
    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Plan Without Product ID",
        price=10.0,
        currency="USD",
        stripe_product_id=None,
    )
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    with pytest.raises(NotFound):
        deactivate_subscription_plan(dummy_session, pl)


def test_create_checkout_subscription_session_missing_price(dummy_session: Any) -> None:
    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Plan Missing Price",
        price=10.0,
        currency="USD",
        stripe_product_id="some_prod_id",
        stripe_price_id=None,
    )
    u = User(id=uuid.uuid4(), email="test@example.com", hashed_password="abc")
    pay = Payment(
        id=uuid.uuid4(),
        subscription_id=uuid.uuid4(),
        user_id=u.id,
        amount=10.0,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="pending",
        transaction_id="txn_123",
    )
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    dummy_session.data[(User, u.id)] = u
    dummy_session.data[(Payment, pay.id)] = pay
    create_checkout_subscription_session(dummy_session, pl, u, pay)
    # now price should be created
    assert pl.stripe_price_id is not None
    assert dummy_session.commits == 2


def test_create_checkout_subscription_session_success(
    dummy_session: Any, mocker: Any
) -> None:
    me = mocker.patch(
        "app.integrations.stripe.ensure_stripe_customer", return_value="cust_mock_id"
    )
    sess_m = MagicMock()
    sess_m.id = "sess_mock_id"
    mocker.patch("stripe.checkout.Session.create", return_value=sess_m)

    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Checkout Plan",
        price=10.0,
        currency="USD",
        stripe_product_id="prod_id",
        stripe_price_id="price_id",
    )
    u = User(
        id=uuid.uuid4(),
        email="user@example.com",
        hashed_password="xyz",
        stripe_customer_id=None,
    )
    pay = Payment(
        id=uuid.uuid4(),
        subscription_id=uuid.uuid4(),
        user_id=u.id,
        amount=10.0,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="pending",
        transaction_id="txn_ABC",
    )
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    dummy_session.data[(User, u.id)] = u
    dummy_session.data[(Payment, pay.id)] = pay
    cs = create_checkout_subscription_session(dummy_session, pl, u, pay)
    me.assert_called_once_with(dummy_session, u)
    stripe.checkout.Session.create.assert_called_once()  # type: ignore
    assert cs.id == "sess_mock_id"


def test_cancel_subscription_recurring_payment_no_id(dummy_session: Any) -> None:
    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id=None,
    )
    dummy_session.data[(Subscription, s.id)] = s
    with pytest.raises(NotFound):
        cancel_subscription_recurring_payment(dummy_session, s, True)


def test_cancel_subscription_recurring_payment_already_canceled(
    dummy_session: Any, mocker: Any
) -> None:
    sm = MagicMock()
    sm.status = "canceled"
    mocker.patch("stripe.Subscription.retrieve", return_value=sm)
    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    dummy_session.data[(Subscription, s.id)] = s
    with pytest.raises(BadRequest) as e:
        cancel_subscription_recurring_payment(dummy_session, s, True)
    assert "already fully canceled" in str(e.value)


def test_cancel_subscription_recurring_payment_cancel_at_period_end_true(
    dummy_session: Any, mocker: Any
) -> None:
    sr = MagicMock()
    sr.status = "active"
    sr.cancel_at_period_end = False
    mocker.patch("stripe.Subscription.retrieve", return_value=sr)

    sm = MagicMock()
    sm.status = "active"
    sm.cancel_at_period_end = True
    mocker.patch("stripe.Subscription.modify", return_value=sm)

    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    dummy_session.data[(Subscription, s.id)] = s
    cancel_subscription_recurring_payment(dummy_session, s, True)
    mocker.patch("stripe.Subscription.retrieve", return_value=sr)
    mocker.patch("stripe.Subscription.modify", return_value=sm)
    assert s.is_active is True
    assert dummy_session.commits == 1


def test_cancel_subscription_recurring_payment_cancel_at_period_end_false(
    dummy_session: Any, mocker: Any
) -> None:
    sr = MagicMock()
    sr.status = "active"
    sr.ended_at = None
    sr.cancel_at_period_end = True
    mocker.patch("stripe.Subscription.retrieve", return_value=sr)

    sm = MagicMock()
    sm.ended_at = 1234567890
    sm.status = "canceled"
    mocker.patch("stripe.Subscription.modify", return_value=sm)

    s = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    dummy_session.data[(Subscription, s.id)] = s
    cancel_subscription_recurring_payment(dummy_session, s, False)
    assert s.is_active is False
    assert s.end_date.timestamp() == 1234567890
    assert dummy_session.commits == 1


def test_handle_success_callback_not_paid(dummy_session: Any, mocker: Any) -> None:
    c = CheckoutSession(
        id=uuid.uuid4(),
        session_id="sess_123",
        status="open",
        payment_status="unpaid",
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        updated_at=datetime.now(timezone.utc),
        session_url="https://example.com/checkout/sess_123",
    )
    pl = SubscriptionPlan(id=uuid.uuid4(), name="Test Plan", price=10.0, currency="USD")
    u = User(id=uuid.uuid4(), email="user@example.com", hashed_password="abc")

    sm = MagicMock()
    sm.payment_status = "unpaid"
    mocker.patch("stripe.checkout.Session.retrieve", return_value=sm)

    dummy_session.data[(CheckoutSession, c.id)] = c
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    dummy_session.data[(User, u.id)] = u

    from app.integrations.stripe import BadRequest, handle_success_callback

    with pytest.raises(BadRequest) as e:
        handle_success_callback(dummy_session, c, pl, u)
    assert "not 'paid'" in str(e.value)


def test_handle_success_callback_paid(dummy_session: Any, mocker: Any) -> None:
    sm = MagicMock()
    sm.payment_status = "paid"

    def sess_mock_get_side_effect(k: Any, d: Any = None) -> Any:
        if k == "subscription":
            return "sub_mock_id"
        elif k == "metadata":
            return {
                "payment_id": str(uuid.uuid4()),
                "subscription_id": str(uuid.uuid4()),
            }
        return d

    sm.get.side_effect = sess_mock_get_side_effect
    mocker.patch("stripe.checkout.Session.retrieve", return_value=sm)

    c = CheckoutSession(
        id=uuid.uuid4(),
        session_id="sess_123",
        status="open",
        payment_status="unpaid",
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        updated_at=datetime.now(timezone.utc),
        session_url="https://example.com/checkout/sess_123",
    )
    pl = SubscriptionPlan(id=uuid.uuid4(), name="Paid Plan", price=10.0, currency="USD")
    u = User(id=uuid.uuid4(), email="user@example.com", hashed_password="abc")
    dummy_session.data[(CheckoutSession, c.id)] = c
    dummy_session.data[(SubscriptionPlan, pl.id)] = pl
    dummy_session.data[(User, u.id)] = u

    r = handle_success_callback(dummy_session, c, pl, u)
    assert "Success callback processed" in r["message"]
    assert dummy_session.commits == 2


def test_handle_cancel_callback_already_processed(dummy_session: Any) -> None:
    c = CheckoutSession(
        id=uuid.uuid4(),
        session_id="sess_123",
        status="complete",
        payment_status="paid",
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        updated_at=datetime.now(timezone.utc),
        session_url="https://example.com/checkout/sess_123",
    )
    dummy_session.data[(CheckoutSession, c.id)] = c
    r = handle_cancel_callback(dummy_session, c)
    assert "Already processed" in r["message"]
    assert dummy_session.commits == 0


def test_handle_cancel_callback_not_paid(dummy_session: Any, mocker: Any) -> None:
    c = CheckoutSession(
        id=uuid.uuid4(),
        session_id="sess_456",
        status="open",
        payment_status="unpaid",
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        updated_at=datetime.now(timezone.utc),
        session_url="https://example.com/checkout/sess_456",
    )
    p = Payment(
        id=uuid.uuid4(),
        user_id=c.user_id,
        subscription_id=uuid.uuid4(),
        amount=9.99,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="pending",
        transaction_id=str(c.session_id),
    )
    dummy_session.data[(CheckoutSession, c.id)] = c
    dummy_session.data[(Payment, p.id)] = p

    sm = MagicMock()
    sm.payment_status = "unpaid"

    def sess_mock_get_side_effect(k: Any, d: Any = None) -> Any:
        if k == "metadata":
            return {"payment_id": str(p.id)}
        return d

    sm.get.side_effect = sess_mock_get_side_effect
    mocker.patch("stripe.checkout.Session.retrieve", return_value=sm)

    r = handle_cancel_callback(dummy_session, c)
    assert "Cancel callback processed" in r["message"]
    assert p.payment_status == "canceled"
    assert dummy_session.commits == 2
