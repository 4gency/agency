import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

# A sample payload for creating a subscription plan.
subscription_plan_payload = {
    "name": "Test Plan",
    "price": 10.0,
    "has_badge": False,
    "badge_text": "",
    "button_text": "Subscribe",
    "button_enabled": True,
    "has_discount": False,
    "price_without_discount": 0.0,
    "currency": "USD",
    "description": "A test subscription plan",
    "is_active": True,
    "metric_type": "month",  # if using an enum, providing the string value is acceptable
    "metric_value": 1,
    "benefits": [],
}


# Fixture for the base URL of subscription plan routes.
@pytest.fixture
def base_url() -> str:
    return f"{settings.API_V1_STR}/subscription-plans"


def test_read_subscription_plans(
    client: TestClient, superuser_token_headers: dict[str, str], base_url: str
) -> None:
    # Create two subscription plans first.
    for _ in range(2):
        resp = client.post(
            f"{base_url}",
            headers=superuser_token_headers,
            json=subscription_plan_payload,
        )
        # Expect 200 OK on creation.
        assert resp.status_code == 200, f"Create response: {resp.text}"

    # Now, retrieve the list of plans.
    resp = client.get(f"{base_url}", headers=superuser_token_headers)
    assert resp.status_code == 200, f"List response: {resp.text}"
    data = resp.json()
    # The response should have a "plans" key.
    assert "plans" in data
    # At least two active plans should be returned.
    assert len(data["plans"]) >= 2
    for plan in data["plans"]:
        assert "id" in plan
        assert "name" in plan
        assert "description" in plan


def test_read_subscription_plan(
    client: TestClient, superuser_token_headers: dict[str, str], base_url: str
) -> None:
    # Create a subscription plan.
    create_resp = client.post(
        f"{base_url}",
        headers=superuser_token_headers,
        json=subscription_plan_payload,
    )
    assert create_resp.status_code == 200, f"Create response: {create_resp.text}"
    created_plan = create_resp.json()
    plan_id = created_plan["id"]

    # Retrieve the plan by its ID.
    get_resp = client.get(f"{base_url}/{plan_id}", headers=superuser_token_headers)
    assert get_resp.status_code == 200, f"Get response: {get_resp.text}"
    plan = get_resp.json()
    assert plan["id"] == plan_id
    assert plan["name"] == subscription_plan_payload["name"]

    # Test the not-found scenario.
    random_id = str(uuid.uuid4())
    not_found_resp = client.get(
        f"{base_url}/{random_id}", headers=superuser_token_headers
    )
    assert (
        not_found_resp.status_code == 404
    ), f"Not-found response: {not_found_resp.text}"
    assert not_found_resp.json()["detail"] == "Subscription plan not found"


def test_create_subscription_plan(
    client: TestClient, superuser_token_headers: dict[str, str], base_url: str
) -> None:
    # Patch out Stripe integration calls.
    with patch(
        "app.integrations.stripe.integration_enabled", return_value=True
    ) as mock_enabled, patch(
        "app.integrations.stripe.create_subscription_plan"
    ) as mock_create:
        resp = client.post(
            f"{base_url}",
            headers=superuser_token_headers,
            json=subscription_plan_payload,
        )
        assert resp.status_code == 200, f"Create response: {resp.text}"
        plan = resp.json()
        assert plan["name"] == subscription_plan_payload["name"]
        mock_enabled.assert_called_once()
        mock_create.assert_called_once()
        # Optionally, verify that the stripe call was made with the created plan.
        args, kwargs = mock_create.call_args
        assert "subscription_plan" in kwargs


def test_update_subscription_plan(
    client: TestClient, superuser_token_headers: dict[str, str], base_url: str
) -> None:
    # First, create a subscription plan.
    create_resp = client.post(
        f"{base_url}",
        headers=superuser_token_headers,
        json=subscription_plan_payload,
    )
    assert create_resp.status_code == 200, f"Create response: {create_resp.text}"
    plan = create_resp.json()
    plan_id = plan["id"]

    update_payload = {
        "name": "Updated Plan",
        "price": 20.0,
        "description": "Updated description",
    }
    with patch(
        "app.integrations.stripe.integration_enabled", return_value=True
    ) as mock_enabled, patch(
        "app.integrations.stripe.update_subscription_plan"
    ) as mock_update:
        update_resp = client.put(
            f"{base_url}/{plan_id}",
            headers=superuser_token_headers,
            json=update_payload,
        )
        assert update_resp.status_code == 200, f"Update response: {update_resp.text}"
        msg = update_resp.json()
        assert msg["message"] == "Subscription plan updated successfully"
        mock_enabled.assert_called_once()
        mock_update.assert_called_once()


def test_delete_subscription_plan(
    client: TestClient, superuser_token_headers: dict[str, str], base_url: str
) -> None:
    # Create a subscription plan first.
    create_resp = client.post(
        f"{base_url}",
        headers=superuser_token_headers,
        json=subscription_plan_payload,
    )
    assert create_resp.status_code == 200, f"Create response: {create_resp.text}"
    plan = create_resp.json()
    plan_id = plan["id"]

    with patch(
        "app.integrations.stripe.integration_enabled", return_value=True
    ) as mock_enabled, patch(
        "app.integrations.stripe.deactivate_subscription_plan"
    ) as mock_deactivate:
        delete_resp = client.delete(
            f"{base_url}/{plan_id}",
            headers=superuser_token_headers,
        )
        assert delete_resp.status_code == 200, f"Delete response: {delete_resp.text}"
        msg = delete_resp.json()
        assert msg["message"] == "Subscription plan deleted successfully"
        mock_enabled.assert_called_once()
        mock_deactivate.assert_called_once()
