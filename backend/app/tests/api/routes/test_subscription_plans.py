import uuid
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

# A sample payload for creating a subscription plan.
subscription_plan_payload: dict[str, Any] = {
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


@pytest.fixture
def base_url() -> str:
    """Returns the base URL for subscription plan routes."""
    return f"{settings.API_V1_STR}/subscription-plans"


def test_read_subscription_plans(
    client: TestClient, superuser_token_headers: dict[str, str], base_url: str
) -> None:
    # Create two subscription plans.
    for _ in range(2):
        response = client.post(
            f"{base_url}",
            headers=superuser_token_headers,
            json=subscription_plan_payload,
        )
        assert response.status_code == 200, f"Create response: {response.text}"

    # Retrieve the list of subscription plans.
    response = client.get(f"{base_url}", headers=superuser_token_headers)
    assert response.status_code == 200, f"List response: {response.text}"
    data: dict[str, Any] = response.json()
    assert "plans" in data, "Response must include 'plans' key"
    # Expect at least two active plans.
    assert len(data["plans"]) >= 2, "Expected at least 2 plans in response"
    for plan in data["plans"]:
        assert "id" in plan, "Plan should contain an 'id'"
        assert "name" in plan, "Plan should contain a 'name'"
        assert "description" in plan, "Plan should contain a 'description'"


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
    created_plan: dict[str, Any] = create_resp.json()
    plan_id: str = created_plan["id"]

    # Retrieve the created plan by its ID.
    get_resp = client.get(f"{base_url}/{plan_id}", headers=superuser_token_headers)
    assert get_resp.status_code == 200, f"Get response: {get_resp.text}"
    plan: dict[str, Any] = get_resp.json()
    assert (
        plan["id"] == plan_id
    ), "The retrieved plan's ID does not match the created plan"
    assert plan["name"] == subscription_plan_payload["name"]

    # Test not-found: use a random UUID.
    random_id: str = str(uuid.uuid4())
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
        plan: dict[str, Any] = resp.json()
        assert plan["name"] == subscription_plan_payload["name"], "Plan name mismatch"
        mock_enabled.assert_called_once()
        mock_create.assert_called_once()
        # Optionally, check that the Stripe call received the created plan.
        args, kwargs = mock_create.call_args
        assert (
            "subscription_plan" in kwargs
        ), "Stripe call missing 'subscription_plan' argument"


def test_update_subscription_plan(
    client: TestClient, superuser_token_headers: dict[str, str], base_url: str
) -> None:
    # Create a subscription plan first.
    create_resp = client.post(
        f"{base_url}",
        headers=superuser_token_headers,
        json=subscription_plan_payload,
    )
    assert create_resp.status_code == 200, f"Create response: {create_resp.text}"
    plan: dict[str, Any] = create_resp.json()
    plan_id: str = plan["id"]

    update_payload: dict[str, Any] = {
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
        msg: dict[str, Any] = update_resp.json()
        assert (
            msg["message"] == "Subscription plan updated successfully"
        ), "Update message mismatch"
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
    plan: dict[str, Any] = create_resp.json()
    plan_id: str = plan["id"]

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
        msg: dict[str, Any] = delete_resp.json()
        assert (
            msg["message"] == "Subscription plan deleted successfully"
        ), "Delete message mismatch"
        mock_enabled.assert_called_once()
        mock_deactivate.assert_called_once()
