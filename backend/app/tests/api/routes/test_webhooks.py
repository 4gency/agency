import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.routes.webhooks import router
from app.tests.utils.bot import create_test_bot_session


@pytest.fixture
def mock_bot_service():
    """Create a mock bot service."""
    with patch("app.api.routes.webhooks.get_bot_service") as mock_get_service:
        service = MagicMock()
        service.get_bot_session = AsyncMock()
        service.process_bot_webhook = AsyncMock()
        service.update_pod_status = AsyncMock()
        service.handle_bot_event = AsyncMock()
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
    session = create_test_bot_session(db)
    # Definir uma API key para o teste
    session.api_key = "test-api-key"
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestWebhooks:
    """Tests for the webhook API routes."""

    def test_bot_event_webhook_unauthorized(self, client):
        """Test that the bot event webhook requires an API key."""
        # Act
        response = client.post(
            f"/api/v1/webhooks/bot/{uuid.uuid4()}",
            json={"event_type": "status_update", "data": {"status": "running"}},
        )

        # Assert
        assert response.status_code == 401
        assert "API key não fornecida" in response.json()["detail"]

    def test_bot_event_webhook_invalid_session(self, client, mock_bot_service):
        """Test that the bot event webhook validates the session ID."""
        # Arrange
        # Configurar o mock para lançar uma exceção HTTP 404
        mock_bot_service.process_bot_webhook.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )

        # Act
        response = client.post(
            f"/api/v1/webhooks/bot/{uuid.uuid4()}",
            json={"event_type": "status_update", "data": {"status": "running"}},
            headers={"X-API-Key": "test-api-key"},
        )

        # Assert
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"]

    def test_bot_event_webhook_success(
        self, client, mock_bot_service, sample_bot_session
    ):
        """Test successful bot event webhook."""
        # Arrange
        event_data = {
            "event_type": "status_update",
            "data": {
                "status": "running",
                "message": "Bot is running",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
        
        mock_bot_service.get_bot_session.return_value = sample_bot_session
        
        # Configure o mock para retornar um evento real como o serviço faria
        event = {
            "status": "success", 
            "event_type": "status_update",
            "event": {
                "id": str(uuid.uuid4()),
                "bot_session_id": str(sample_bot_session.id),
                "type": "status_update",
                "severity": "info",
                "message": "Event status_update received"
            }
        }
        mock_bot_service.process_bot_webhook.return_value = event

        # Act
        response = client.post(
            f"/api/v1/webhooks/bot/{sample_bot_session.id}",
            json=event_data,
            headers={"X-API-Key": "test-api-key"},
        )

        # Assert
        assert response.status_code == 201
        assert "id" in response.json()
        mock_bot_service.process_bot_webhook.assert_called_once()

    def test_status_update_webhook_unauthorized(self, client):
        """Test that the status update webhook requires an API key."""
        # Act
        response = client.post(
            "/api/v1/webhooks/status-update",
            json={},
            headers={},  # Sem API key
        )

        # Assert
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]

    def test_status_update_webhook_success(self, client, mock_bot_service):
        """Test successful status update webhook."""
        # Configure mock
        mock_bot_service.update_pod_status.return_value = 5

        # Patch settings para aceitar nossa API key de teste
        with patch("app.api.routes.webhooks.settings") as mock_settings:
            mock_settings.BOT_API_KEY = "test-api-key"
            
            # Act
            response = client.post(
                "/api/v1/webhooks/status-update",
                json={},
                headers={"X-API-Key": "test-api-key"},
            )

            # Assert
            assert response.status_code == 200
            assert response.json()["updated_count"] >= 0
            mock_bot_service.update_pod_status.assert_called_once()

    def test_status_update_webhook_error(self, client, mock_bot_service):
        """Test error handling in status update webhook."""
        # Arrange
        mock_bot_service.update_pod_status.side_effect = Exception("Test error")

        # Patch settings para aceitar nossa API key de teste
        with patch("app.api.routes.webhooks.settings") as mock_settings:
            mock_settings.BOT_API_KEY = "test-api-key"
            
            # Act
            response = client.post(
                "/api/v1/webhooks/status-update",
                json={},
                headers={"X-API-Key": "test-api-key"},
            )

            # Assert
            assert response.status_code == 500
            assert "Erro" in response.json()["detail"]
