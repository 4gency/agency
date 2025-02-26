import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
import stripe
from sqlmodel import Session, SQLModel, create_engine, select

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
    update_subscription_plan,
    update_subscription_payment,
    handle_invoice_payment_succeeded,
    handle_checkout_session_expired,
    handle_checkout_session_async_payment_failed,
    handle_charge_dispute_created,
)
from app.models.core import (
    CheckoutSession,
    Payment,
    Subscription,
    SubscriptionMetric,
    SubscriptionPlan,
    User,
)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Provides a fresh in-memory SQLite session for each test.
    """
    # Use in-memory SQLite. echo=False to avoid verbose SQL logs.
    engine = create_engine("sqlite://", echo=False)
    # Create tables for all SQLModel-derived models
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Optional: drop tables after each test
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="session", autouse=True)
def set_stripe_api_key() -> None:
    # Just set a dummy key to avoid Stripe complaining
    stripe.api_key = "sk_test_dummy"


@pytest.fixture(autouse=True)
def mock_stripe_calls(mocker: Any) -> None:
    """
    Auto-used fixture to mock out all Stripe calls for every test,
    so we never hit the real Stripe API with the dummy key.
    """
    # Product
    mock_product_create = MagicMock()
    mock_product_create.id = "prod_mock_id"
    mocker.patch("stripe.Product.create", return_value=mock_product_create)

    mock_product_modify = MagicMock()
    mock_product_modify.id = "prod_modified_id"
    mocker.patch("stripe.Product.modify", return_value=mock_product_modify)

    # Price
    mock_price_create = MagicMock()
    mock_price_create.id = "price_mock_id"
    mocker.patch("stripe.Price.create", return_value=mock_price_create)

    mock_price_retrieve = MagicMock()
    mock_price_retrieve.id = "retrieved_price_id"
    mock_price_retrieve.unit_amount = 10000
    mock_price_retrieve.currency = "usd"
    mock_price_retrieve.recurring = {"interval": "month", "interval_count": 1}
    mocker.patch("stripe.Price.retrieve", return_value=mock_price_retrieve)

    # Customer
    mock_customer_create = MagicMock()
    mock_customer_create.id = "cust_mock_id"
    mocker.patch("stripe.Customer.create", return_value=mock_customer_create)

    # Subscription
    mock_subscription_retrieve = MagicMock()
    mock_subscription_retrieve.status = "active"
    mock_subscription_retrieve.current_period_start = 1234567890
    mock_subscription_retrieve.current_period_end = 1234567890
    mock_subscription_retrieve.latest_invoice = "inv_mock_id"
    mock_subscription_retrieve.cancel_at_period_end = False
    mock_subscription_retrieve.delete.return_value = {"ended_at": 1234567890}
    mocker.patch(
        "stripe.Subscription.retrieve", return_value=mock_subscription_retrieve
    )
    mocker.patch("stripe.Subscription.delete", return_value={"ended_at": 1234567890})
    mocker.patch("stripe.Subscription.modify", return_value=mock_subscription_retrieve)

    # Invoice
    mock_invoice_retrieve = MagicMock()
    mock_invoice_retrieve.status = "paid"
    mock_invoice_retrieve.created = 1234567890
    mock_invoice_retrieve.amount_paid = 999
    mock_invoice_retrieve.currency = "usd"
    mock_invoice_retrieve.payment_intent = "pi_mock_id"
    mocker.patch("stripe.Invoice.retrieve", return_value=mock_invoice_retrieve)

    # Checkout Session
    mock_session_create = MagicMock()
    mock_session_create.id = "sess_mock_id"
    mock_session_create.payment_status = "unpaid"
    mocker.patch("stripe.checkout.Session.create", return_value=mock_session_create)
    mocker.patch("stripe.checkout.Session.retrieve", return_value=mock_session_create)


def test_create_subscription_plan_invalid_currency(db: Any) -> None:
    plan = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Test Plan",
        price=9.99,
        currency="INVALID",  # invalid currency
        description="A test plan",
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
    )
    # The function should raise BadRequest before committing
    with pytest.raises(BadRequest) as exc:
        create_subscription_plan(db, plan)
    assert "Invalid currency" in str(exc.value)


def test_create_subscription_plan_success(db: Any) -> None:
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
    _, _ = create_subscription_plan(db, plan)
    # After creation, plan should have updated Stripe fields
    db.refresh(plan)
    assert plan.stripe_product_id == "prod_mock_id"
    assert plan.stripe_price_id == "price_mock_id"


def test_update_subscription_plan_creates_if_none(db: Any, mocker: Any) -> None:
    """
    If the plan doesn't have stripe_product_id/stripe_price_id,
    update_subscription_plan calls create_subscription_plan.
    """
    create_plan_mock = mocker.patch(
        "app.integrations.stripe.create_subscription_plan",
        side_effect=lambda sess, pl: (pl, "price_obj_mock"),
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
    db.add(pl)
    db.commit()

    update_subscription_plan(db, pl)
    create_plan_mock.assert_called_once()


def test_update_subscription_plan_invalid_metric(db: Any) -> None:
    """
    Negative or zero metric_value should raise BadRequest.
    """
    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Invalid Plan",
        price=10.0,
        currency="USD",
        metric_type=SubscriptionMetric.MONTH,
        metric_value=-1,  # invalid
        stripe_product_id="prod_id",
        stripe_price_id="price_id",
    )
    db.add(pl)
    db.commit()

    with pytest.raises(BadRequest) as e:
        update_subscription_plan(db, pl)
    assert "Invalid metric value" in str(e.value)


def test_update_subscription_plan_update_price(db: Any, mocker: Any) -> None:
    """
    If the price or interval changes, create a new Price in Stripe.
    """
    old_price_mock = mocker.MagicMock()
    old_price_mock.unit_amount = 10000  # 100.00 USD
    old_price_mock.currency = "usd"
    old_price_mock.recurring = {"interval": "month", "interval_count": 1}
    mocker.patch("stripe.Price.retrieve", return_value=old_price_mock)

    new_price_mock = mocker.MagicMock()
    new_price_mock.id = "new_price_id"
    mocker.patch("stripe.Price.create", return_value=new_price_mock)

    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Updated Plan",
        price=50.0,  # was 100.00, now 50.00 => unit_amount=5000
        currency="USD",
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
        stripe_product_id="existing_prod_id",
        stripe_price_id="existing_price_id",
        is_active=True,
    )
    db.add(pl)
    db.commit()

    update_subscription_plan(db, pl)
    db.refresh(pl)
    assert pl.stripe_price_id == "new_price_id"


def test_deactivate_subscription_plan_success(db: Any) -> None:
    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Deactivating Plan",
        price=10.0,
        currency="USD",
        stripe_product_id="existing_prod_id",
        stripe_price_id="existing_price_id",
    )
    db.add(pl)
    db.commit()

    deactivate_subscription_plan(db, pl)
    # Ensure stripe.Product.modify was called
    stripe.Product.modify.assert_called_once_with("existing_prod_id", active=False)  # type: ignore


def test_deactivate_subscription_plan_not_found(db: Any) -> None:
    """
    If the plan has no stripe_product_id, raises NotFound.
    """
    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Plan Without Product ID",
        price=10.0,
        currency="USD",
        stripe_product_id=None,
    )
    db.add(pl)
    db.commit()

    with pytest.raises(NotFound):
        deactivate_subscription_plan(db, pl)


def test_ensure_stripe_customer_already_exists(db: Any) -> None:
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="abc123",
        stripe_customer_id="existing_customer_id",
    )
    db.add(user)
    db.commit()

    result = ensure_stripe_customer(db, user)
    assert result == "existing_customer_id"
    # No change needed in DB, so no new commit is strictly necessary.


def test_ensure_stripe_customer_new(db: Any, mocker: Any) -> None:
    cust_mock = mocker.MagicMock()
    cust_mock.id = "cust_mock_id"
    mocker.patch("stripe.Customer.create", return_value=cust_mock)

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="abc123",
    )
    db.add(user)
    db.commit()

    result = ensure_stripe_customer(db, user)
    assert result == "cust_mock_id"

    db.refresh(user)
    assert user.stripe_customer_id == "cust_mock_id"


def test_create_checkout_subscription_session_missing_price(db: Any) -> None:
    """
    If subscription_plan has no stripe_price_id, it should be created/updated in Stripe.
    """
    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Plan Missing Price",
        price=10.0,
        currency="USD",
        stripe_product_id="some_prod_id",
        stripe_price_id=None,
    )
    user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="abc")
    db.add(pl)
    db.add(user)
    db.commit()

    session_resp = create_checkout_subscription_session(db, pl, user)
    db.refresh(pl)
    assert pl.stripe_price_id == "price_mock_id"
    assert session_resp.id == "sess_mock_id"


def test_create_checkout_subscription_session_success(db: Any, mocker: Any) -> None:
    mocker.patch(
        "app.integrations.stripe.ensure_stripe_customer", return_value="cust_mock_id"
    )

    pl = SubscriptionPlan(
        id=uuid.uuid4(),
        name="Checkout Plan",
        price=10.0,
        currency="USD",
        stripe_product_id="prod_id",
        stripe_price_id="price_id",
    )
    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        hashed_password="xyz",
        stripe_customer_id=None,
    )
    db.add(pl)
    db.add(user)
    db.commit()

    cs = create_checkout_subscription_session(db, pl, user)
    stripe.checkout.Session.create.assert_called_once()  # type: ignore
    assert cs.id == "sess_mock_id"


def test_cancel_subscription_no_stripe_id(db: Any) -> None:
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
    db.add(s)
    db.commit()

    with pytest.raises(NotFound):
        cancel_subscription(db, s)


def test_cancel_subscription_success(db: Any) -> None:
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
    db.add(s)
    db.commit()

    cancel_subscription(db, s)
    # Reload from DB
    s_db = db.get(Subscription, s.id)
    assert s_db.is_active is False


def test_cancel_subscription_recurring_payment_no_id(db: Any) -> None:
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
    db.add(s)
    db.commit()

    with pytest.raises(NotFound):
        cancel_subscription_recurring_payment(db, s, True)


def test_cancel_subscription_recurring_payment_already_canceled(
    db: Any, mocker: Any
) -> None:
    sub_mock = mocker.MagicMock()
    sub_mock.status = "canceled"
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_mock)

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
    db.add(s)
    db.commit()

    with pytest.raises(BadRequest) as e:
        cancel_subscription_recurring_payment(db, s, True)
    assert "already fully canceled" in str(e.value)


def test_cancel_subscription_recurring_payment_cancel_at_period_end_true(
    db: Any, mocker: Any
) -> None:
    sub_retrieve_mock = mocker.MagicMock()
    sub_retrieve_mock.status = "active"
    sub_retrieve_mock.cancel_at_period_end = False
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_retrieve_mock)

    sub_modify_mock = mocker.MagicMock()
    sub_modify_mock.status = "active"
    sub_modify_mock.cancel_at_period_end = True
    mocker.patch("stripe.Subscription.modify", return_value=sub_modify_mock)

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
    db.add(s)
    db.commit()

    cancel_subscription_recurring_payment(db, s, True)
    s_db = db.get(Subscription, s.id)
    # Should still be active, but canceled at period end
    assert s_db.is_active is True


def test_cancel_subscription_recurring_payment_cancel_at_period_end_false(
    db: Any, mocker: Any
) -> None:
    sub_retrieve_mock = mocker.MagicMock()
    sub_retrieve_mock.status = "active"
    sub_retrieve_mock.ended_at = None
    sub_retrieve_mock.cancel_at_period_end = True
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_retrieve_mock)

    sub_modify_mock = mocker.MagicMock()
    sub_modify_mock.ended_at = 1234567890
    sub_modify_mock.status = "canceled"
    mocker.patch("stripe.Subscription.modify", return_value=sub_modify_mock)

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
    db.add(s)
    db.commit()

    cancel_subscription_recurring_payment(db, s, False)
    s_db = db.get(Subscription, s.id)
    assert s_db.is_active is False
    # If your logic sets end_date to ended_at:
    assert int(s_db.end_date.timestamp()) == 1234567890


def test_reactivate_subscription_canceled(db: Any, mocker: Any) -> None:
    sub_mock = mocker.MagicMock()
    sub_mock.status = "canceled"
    sub_mock.cancel_at_period_end = False
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_mock)

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
    db.add(s)
    db.commit()

    with pytest.raises(BadRequest) as exc:
        reactivate_subscription(db, s)
    assert "Need a new subscription" in str(exc.value)


def test_reactivate_subscription_success(db: Any, mocker: Any) -> None:
    sub_mock = mocker.MagicMock()
    sub_mock.status = "active"
    sub_mock.cancel_at_period_end = True
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_mock)

    modify_mock = mocker.MagicMock()
    modify_mock.status = "active"
    modify_mock.cancel_at_period_end = False
    mocker.patch("stripe.Subscription.modify", return_value=modify_mock)

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
    db.add(s)
    db.commit()

    reactivate_subscription(db, s)
    s_db = db.get(Subscription, s.id)
    assert s_db.is_active is True


def test_update_subscription_payment(db: Any, mocker: Any) -> None:
    sub_mock = mocker.MagicMock()
    sub_mock.status = "active"
    sub_mock.current_period_start = 1234567890
    sub_mock.current_period_end = 1234567890
    sub_mock.latest_invoice = "inv_mock_id"
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_mock)

    inv_mock = mocker.MagicMock()
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
    db.add(s)
    db.add(p)
    db.commit()

    update_subscription_payment(db, s, p, sub_mock)
    s_db = db.get(Subscription, s.id)
    p_db = db.get(Payment, p.id)
    assert s_db.is_active is True
    assert p_db.payment_status == "paid"
    assert p_db.transaction_id == "pi_mock_id"


def test_handle_invoice_payment_succeeded(db: Any, mocker: Any) -> None:
    user = User(
        email=f"test{uuid.uuid4().hex}@example.com",
        hashed_password="abc123",
        is_active=True,
        stripe_customer_id="cust_mock_id",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    plan = SubscriptionPlan(
        name="Test Plan",
        price=10.0,
        currency="USD",
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
        stripe_product_id="prod_mock_id",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    evt = {
        "data": {
            "object": {
                "id": "inv_mock_id",
                "subscription": "sub_mock_id",
                "customer": user.stripe_customer_id,
            }
        }
    }

    sub_mock = mocker.MagicMock()
    sub_mock.id = "sub_mock_id"
    sub_mock.status = "active"
    sub_mock.current_period_start = 1234567890
    sub_mock.current_period_end = 1234567890
    sub_mock.latest_invoice = "inv_mock_id"
    mocker.patch("stripe.Subscription.retrieve", return_value=sub_mock)

    inv_mock = mocker.MagicMock()
    inv_mock.status = "paid"
    inv_mock.created = 1234567890
    inv_mock.amount_paid = 10000
    inv_mock.currency = "usd"
    inv_mock.payment_intent = "pi_mock_id"
    mocker.patch("stripe.Invoice.retrieve", return_value=inv_mock)

    handle_invoice_payment_succeeded(db, evt)  # type: ignore

    subs = db.exec(select(Subscription)).all()
    pays = db.exec(select(Payment)).all()
    assert len(subs) == 1
    assert len(pays) == 1
    assert subs[0].is_active is True
    assert pays[0].payment_status == "paid"


def test_handle_checkout_session_expired(db: Any, mocker: Any) -> None:
    user = User(
        email=f"test{uuid.uuid4().hex}@example.com",
        hashed_password="abc123",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    plan = SubscriptionPlan(
        name="Test Plan",
        price=10.0,
        currency="USD",
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    session_id = f"sess_mock_id_{uuid.uuid4().hex}"

    evt = {
        "data": {
            "object": {
                "id": session_id,
                "payment_status": "unpaid",
                "metadata": {
                    "plan_id": str(plan.id),
                    "user_id": str(user.id),
                },
            }
        }
    }

    ck = CheckoutSession(
        session_id=session_id,
        status="open",
        payment_status="unpaid",
        user_id=user.id,
        subscription_plan_id=plan.id,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        updated_at=datetime.now(timezone.utc),
        session_url="https://example.com/checkout/sess_mock_id",
    )
    db.add(ck)
    db.commit()
    db.refresh(ck)

    handle_checkout_session_expired(db, evt)  # type: ignore
    db.refresh(ck)
    assert ck.status == "expired"
    assert ck.payment_status == "unpaid"


def test_handle_checkout_session_async_payment_failed(db: Any, mocker: Any) -> None:
    user = User(
        email=f"test{uuid.uuid4().hex}@example.com",
        hashed_password="abc123",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    plan = SubscriptionPlan(
        name="Test Plan",
        price=10.0,
        currency="USD",
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    session_id = f"sess_mock_id_{uuid.uuid4().hex}"

    evt = {
        "data": {
            "object": {
                "id": session_id,
                "payment_status": "unpaid",
                "metadata": {
                    "plan_id": str(plan.id),
                    "user_id": str(user.id),
                },
            }
        }
    }

    ck = CheckoutSession(
        session_id=session_id,
        status="open",
        payment_status="unpaid",
        user_id=user.id,
        subscription_plan_id=plan.id,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        updated_at=datetime.now(timezone.utc),
        session_url="https://example.com/checkout/sess_mock_id",
    )
    db.add(ck)
    db.commit()
    db.refresh(ck)

    handle_checkout_session_async_payment_failed(db, evt)  # type: ignore
    db.refresh(ck)
    assert ck.status == "failed"
    assert ck.payment_status == "unpaid"


def test_handle_charge_dispute_created(db: Any, mocker: Any) -> None:
    user = User(
        email=f"test{uuid.uuid4().hex}@example.com",
        hashed_password="abc123",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    plan = SubscriptionPlan(
        name="Test Plan",
        price=10.0,
        currency="USD",
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    s = Subscription(
        id=uuid.uuid4(),
        user_id=user.id,
        subscription_plan_id=plan.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
        stripe_subscription_id="sub_mock_id",
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    p = Payment(
        id=uuid.uuid4(),
        subscription_id=s.id,
        user_id=user.id,
        amount=9.99,
        currency="USD",
        payment_date=datetime.now(timezone.utc),
        payment_status="paid",
        transaction_id="trx123",
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    evt = {
        "data": {
            "object": {
                "id": "evt_mock_id",
                "payment_intent": p.transaction_id,
            }
        }
    }

    handle_charge_dispute_created(db, evt)  # type: ignore

    db.refresh(s)
    db.refresh(user)
    assert s.is_active is False
    assert user.is_active is False
