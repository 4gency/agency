import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.routes.webhooks import router
from app.tests.utils.bot import create_test_bot_session


@pytest.fixture
def mock_bot_service():
    """Create a mock bot service."""
    with patch("app.api.routes.webhooks.get_bot_service") as mock_get_service:
        service = MagicMock()
        service.handle_bot_event = AsyncMock(return_value=True)
        service.update_bot_status = AsyncMock(return_value=True)
        mock_get_service.return_value = service
        yield service


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/webhooks")
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_bot_session(db: Session):
    """Create a sample bot session for testing."""
    return create_test_bot_session(db)


class TestWebhooks:
    """Tests for the webhook API routes."""

    def test_bot_event_webhook_unauthorized(self, client):
        """Test that the bot event webhook requires an API key."""
        # Act
        response = client.post(
            f"/api/v1/webhooks/bot/{uuid.uuid4()}",
            json={"event_type": "status_update", "status": "running"},
        )

        # Assert
        assert response.status_code == 401
        assert "API key is missing" in response.json()["detail"]

    def test_bot_event_webhook_invalid_session(self, client, mock_bot_service):
        """Test that the bot event webhook validates the session ID."""
        # Arrange
        mock_bot_service.handle_bot_event.side_effect = Exception("Session not found")

        # Act
        response = client.post(
            f"/api/v1/webhooks/bot/{uuid.uuid4()}",
            json={"event_type": "status_update", "status": "running"},
            headers={"X-API-Key": "test-api-key"},
        )

        # Assert
        assert response.status_code == 404
        assert "Bot session not found" in response.json()["detail"]

    def test_bot_event_webhook_success(
        self, client, mock_bot_service, sample_bot_session
    ):
        """Test successful bot event webhook."""
        # Arrange
        event_data = {
            "event_type": "status_update",
            "status": "running",
            "message": "Bot is running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Act
        response = client.post(
            f"/api/v1/webhooks/bot/{sample_bot_session.id}",
            json=event_data,
            headers={"X-API-Key": "test-api-key"},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"success": True}
        mock_bot_service.handle_bot_event.assert_called_once_with(
            session_id=mock_bot_service.handle_bot_event.call_args[1]["session_id"],
            event_data=event_data,
        )

    def test_status_update_webhook_unauthorized(self, client):
        """Test that the status update webhook requires an API key."""
        # Act
        response = client.post("/api/v1/webhooks/status-update", json={})

        # Assert
        assert response.status_code == 401
        assert "API key is missing" in response.json()["detail"]

    def test_status_update_webhook_success(self, client, mock_bot_service):
        """Test successful status update webhook."""
        # Act
        response = client.post(
            "/api/v1/webhooks/status-update",
            json={},
            headers={"X-API-Key": "test-api-key"},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"success": True}
        mock_bot_service.update_bot_status.assert_called_once()

    def test_status_update_webhook_error(self, client, mock_bot_service):
        """Test error handling in status update webhook."""
        # Arrange
        mock_bot_service.update_bot_status.side_effect = Exception("Test error")

        # Act
        response = client.post(
            "/api/v1/webhooks/status-update",
            json={},
            headers={"X-API-Key": "test-api-key"},
        )

        # Assert
        assert response.status_code == 500
        assert "Error updating bot statuses" in response.json()["detail"]
