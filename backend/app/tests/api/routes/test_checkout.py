import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.core import (
    CheckoutSession,
    SubscriptionMetric,
    SubscriptionPlan,
    User,  # Ensure you can import your User model here
)


class DummyUser:
    id: str


dummy_user = DummyUser()
dummy_user.id = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(autouse=True)
def override_current_user(client: TestClient, db: Session) -> Any:
    """
    Override current user with a user record that actually exists in the DB, so that
    foreign key constraints pass and the checkout session belongs to the authenticated user.
    """
    from app.api.deps import get_current_active_superuser, get_current_user

    # Check if our dummy user is already in the DB; if not, create it.
    existing = db.exec(select(User).where(User.id == dummy_user.id)).first()
    if not existing:
        new_user = User(
            id=dummy_user.id,
            email="dummy.user@test.com",
            hashed_password="fakepassword",
            is_superuser=True,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    # Now override the dependency to return that actual DB user.
    def _dummy_user_dep() -> Any:
        return db.exec(select(User).where(User.id == dummy_user.id)).first()

    client.app.dependency_overrides[get_current_user] = _dummy_user_dep  # type: ignore
    client.app.dependency_overrides[get_current_active_superuser] = _dummy_user_dep  # type: ignore
    yield
    client.app.dependency_overrides.clear()  # type: ignore


def create_dummy_subscription_plan(db: Session, plan_id: uuid.UUID) -> SubscriptionPlan:
    plan = SubscriptionPlan(
        id=plan_id,
        name="Dummy Plan",
        price=20.0,
        has_badge=False,
        badge="",
        has_discount=False,
        price_without_discount=20.0,
        currency="USD",
        description="Dummy plan description",
        is_active=True,
        metric_type=SubscriptionMetric.MONTH,
        metric_value=1,
        stripe_product_id=None,
        stripe_price_id=None,
    )
    db.add(plan)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(plan)
    return plan


def create_dummy_checkout_session(
    db: Session, session_id: str, plan_id: uuid.UUID, user_id: str
) -> CheckoutSession:
    checkout = CheckoutSession(
        session_id=session_id,
        session_url="http://example.com/checkout",
        user_id=user_id,
        subscription_plan_id=plan_id,
        status="open",
        payment_status="pending",
        expires_at=datetime.now(timezone.utc),
    )
    db.add(checkout)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(checkout)
    return checkout


@pytest.fixture
def checkout_base_url() -> str:
    return f"{settings.API_V1_STR}/checkout/stripe"


# ------------------------------------------------------------------------------
# Tests for Checkout Routes


def test_stripe_success(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test the Stripe success callback endpoint.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    dummy_session_id = "dummy-session-id"
    # Create a checkout session with the dummy user.
    create_dummy_checkout_session(db, dummy_session_id, plan_id, dummy_user.id)

    with patch(
        "app.integrations.stripe.handle_success_callback"
    ) as mock_handle_success:
        response = client.post(
            f"{checkout_base_url}/success",
            params={"session_id": dummy_session_id},
            headers=superuser_token_headers,
        )
        # Should be 200 if the authenticated user (dummy_user) matches checkout.user_id.
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert (
            data["message"] == "Success callback processed"
        ), "Unexpected success message"
        mock_handle_success.assert_called_once()


def test_get_stripe_checkout_session_by_id(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test retrieving a checkout session by its ID.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "dummy-session-id", plan_id, dummy_user.id
    )
    session_id = checkout.id
    response = client.get(
        f"{checkout_base_url}/checkout-session/{session_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, f"Response: {response.text}"
    data: dict[str, Any] = response.json()
    assert data["id"] == str(session_id), "Mismatch in checkout session ID"
    assert data["session_id"] == checkout.session_id, "Mismatch in session_id field"


def test_get_stripe_checkout_sessions(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test retrieving multiple checkout sessions.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    for i in range(3):
        create_dummy_checkout_session(db, f"session-{i}", plan_id, dummy_user.id)
    response = client.get(
        f"{checkout_base_url}/checkout-session",
        headers=superuser_token_headers,
        params={"skip": 0, "limit": 10},
    )
    assert response.status_code == 200, f"Response: {response.text}"
    sessions = response.json()
    assert isinstance(sessions, list), "Response should be a list"
    assert len(sessions) >= 3, "Expected at least 3 checkout sessions"


def test_create_stripe_checkout_session(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test creating a new Stripe checkout session.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    fake_stripe_data: dict[str, Any] = {
        "id": "cs_test_123",
        "url": "http://stripe.com/checkout",
        "status": "open",
        "payment_status": "pending",
        "expires_at": 9999999999,
    }
    with patch(
        "app.integrations.stripe.create_checkout_subscription_session",
        return_value=fake_stripe_data,
    ) as mock_create_session:
        response = client.post(
            f"{checkout_base_url}/checkout-session",
            headers=superuser_token_headers,
            params={"subscription_plan_id": str(plan_id)},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert (
            data["session_id"] == fake_stripe_data["id"]
        ), "Stripe session ID mismatch"
        assert (
            data["session_url"] == fake_stripe_data["url"]
        ), "Stripe session URL mismatch"
        mock_create_session.assert_called_once()


def test_update_stripe_checkout_session(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test updating an existing Stripe checkout session.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "session-to-update", plan_id, dummy_user.id
    )
    session_id = checkout.id
    update_payload: dict[str, Any] = {"status": "completed"}
    response = client.patch(
        f"{checkout_base_url}/checkout-session/{session_id}",
        headers=superuser_token_headers,
        json=update_payload,
    )
    assert response.status_code == 200, f"Response: {response.text}"
    # Instead of relying solely on the JSON response (which might not include 'status'),
    # refresh the object from the DB and assert its status.
    db.refresh(checkout)
    assert checkout.status == "completed", "Checkout session status was not updated"


def test_stripe_webhook(
    client: TestClient,
    checkout_base_url: str,
) -> None:
    """
    Test processing a Stripe webhook.
    """
    fake_payload: bytes = b'{"id": "evt_test", "type": "checkout.session.completed"}'
    fake_signature: str = "test-signature"
    fake_event: dict[str, Any] = {"type": "checkout.session.completed"}
    with patch(
        "stripe.Webhook.construct_event", return_value=fake_event
    ) as mock_construct, patch(
        "app.integrations.stripe.handle_checkout_session"
    ) as mock_handle_checkout:
        response = client.post(
            f"{checkout_base_url}/webhook",
            data=fake_payload,  # type: ignore
            headers={"stripe-signature": fake_signature},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert data["message"] == "success", "Webhook did not return success"
        mock_construct.assert_called_once()
        mock_handle_checkout.assert_called_once()


def test_stripe_cancel(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test the Stripe cancel callback endpoint.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "cancel-session", plan_id, dummy_user.id
    )
    with patch("app.integrations.stripe.handle_cancel_callback") as mock_handle_cancel:
        response = client.post(
            f"{checkout_base_url}/cancel",
            headers=superuser_token_headers,
            params={"session_id": checkout.session_id},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert data["message"] == "Cancel callback processed", "Cancel message mismatch"
        mock_handle_cancel.assert_called_once()


def test_update_subscription_payment(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test the update_subscription_payment function.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "update-subscription-payment", plan_id, dummy_user.id
    )
    with patch("app.integrations.stripe.update_subscription_payment") as mock_update:
        response = client.post(
            f"{checkout_base_url}/update-subscription-payment",
            headers=superuser_token_headers,
            params={"session_id": checkout.session_id},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert data["message"] == "Subscription payment updated", "Update message mismatch"
        mock_update.assert_called_once()


def test_handle_invoice_payment_succeeded(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test the handle_invoice_payment_succeeded function.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "handle-invoice-payment-succeeded", plan_id, dummy_user.id
    )
    with patch("app.integrations.stripe.handle_invoice_payment_succeeded") as mock_handle:
        response = client.post(
            f"{checkout_base_url}/handle-invoice-payment-succeeded",
            headers=superuser_token_headers,
            params={"session_id": checkout.session_id},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert data["message"] == "Invoice payment succeeded", "Handle message mismatch"
        mock_handle.assert_called_once()


def test_handle_checkout_session_expired(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test the handle_checkout_session_expired function.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "handle-checkout-session-expired", plan_id, dummy_user.id
    )
    with patch("app.integrations.stripe.handle_checkout_session_expired") as mock_handle:
        response = client.post(
            f"{checkout_base_url}/handle-checkout-session-expired",
            headers=superuser_token_headers,
            params={"session_id": checkout.session_id},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert data["message"] == "Checkout session expired", "Handle message mismatch"
        mock_handle.assert_called_once()


def test_handle_checkout_session_async_payment_failed(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test the handle_checkout_session_async_payment_failed function.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "handle-checkout-session-async-payment-failed", plan_id, dummy_user.id
    )
    with patch("app.integrations.stripe.handle_checkout_session_async_payment_failed") as mock_handle:
        response = client.post(
            f"{checkout_base_url}/handle-checkout-session-async-payment-failed",
            headers=superuser_token_headers,
            params={"session_id": checkout.session_id},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert data["message"] == "Checkout session async payment failed", "Handle message mismatch"
        mock_handle.assert_called_once()


def test_handle_charge_dispute_created(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    checkout_base_url: str,
) -> None:
    """
    Test the handle_charge_dispute_created function.
    """
    plan_id = uuid.uuid4()
    _ = create_dummy_subscription_plan(db, plan_id)
    checkout = create_dummy_checkout_session(
        db, "handle-charge-dispute-created", plan_id, dummy_user.id
    )
    with patch("app.integrations.stripe.handle_charge_dispute_created") as mock_handle:
        response = client.post(
            f"{checkout_base_url}/handle-charge-dispute-created",
            headers=superuser_token_headers,
            params={"session_id": checkout.session_id},
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data: dict[str, Any] = response.json()
        assert data["message"] == "Charge dispute created", "Handle message mismatch"
        mock_handle.assert_called_once()
