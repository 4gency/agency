import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.routes.bot import router
from app.models.bot import (
    BotConfig,
)
from app.services.bot import BotService
from app.tests.utils.bot import create_test_bot_config, create_test_bot_session
from app.tests.utils.user import create_random_user


@pytest.fixture
def mock_bot_service():
    """Mock the bot service."""
    with patch("app.api.routes.bot.get_bot_service") as mock_get_service:
        service = MagicMock(spec=BotService)

        # Mock methods
        service.create_bot_config = AsyncMock()
        service.get_bot_config = AsyncMock()
        service.update_bot_config = AsyncMock()
        service.delete_bot_config = AsyncMock(return_value=True)
        service.list_bot_configs = AsyncMock(return_value=[])

        service.start_bot_session = AsyncMock()
        service.stop_bot_session = AsyncMock(return_value=True)
        service.pause_bot_session = AsyncMock(return_value=True)
        service.resume_bot_session = AsyncMock(return_value=True)
        service.get_bot_session = AsyncMock()
        service.list_bot_sessions = AsyncMock(return_value=[])

        service.create_linkedin_credentials = AsyncMock()
        service.get_linkedin_credentials = AsyncMock()
        service.update_linkedin_credentials = AsyncMock()

        mock_get_service.return_value = service
        yield service


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/bot")
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
def user_token_headers(client: TestClient):
    """Get token headers for a normal user."""
    # This would normally come from the conftest.py
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_user(db: Session):
    """Create a sample user for testing."""
    return create_random_user(db)


@pytest.fixture
def sample_bot_config(db: Session):
    """Create a sample bot configuration for testing."""
    return create_test_bot_config(db)


@pytest.fixture
def sample_bot_session(db: Session, sample_bot_config):
    """Create a sample bot session for testing."""
    return create_test_bot_session(
        db,
        bot_config_id=sample_bot_config.id,
        subscription_id=sample_bot_config.subscription_id,
        user_id=sample_bot_config.user_id,
    )


class TestBotRoutes:
    """Tests for the bot API routes."""

    def test_create_bot_config(
        self, client, user_token_headers, mock_bot_service, sample_user
    ):
        """Test creating a bot configuration."""
        # Arrange
        config_data = {
            "name": "Test Config",
            "job_search_query": "Software Engineer",
            "location": "Remote",
            "default_applies_limit": 10,
        }

        # Mock the service response
        mock_bot_service.create_bot_config.return_value = BotConfig(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            subscription_id=uuid.uuid4(),
            **config_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        response = client.post(
            "/api/v1/bot/configs/", json=config_data, headers=user_token_headers
        )

        # Assert
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["name"] == config_data["name"]
        mock_bot_service.create_bot_config.assert_called_once()

    def test_get_bot_config(
        self, client, user_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test getting a bot configuration."""
        # Arrange
        config_id = sample_bot_config.id
        mock_bot_service.get_bot_config.return_value = sample_bot_config

        # Act
        response = client.get(
            f"/api/v1/bot/configs/{config_id}", headers=user_token_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == str(config_id)
        mock_bot_service.get_bot_config.assert_called_once_with(
            config_id=mock_bot_service.get_bot_config.call_args[1]["config_id"],
            user_id=mock_bot_service.get_bot_config.call_args[1]["user_id"],
        )

    def test_update_bot_config(
        self, client, user_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test updating a bot configuration."""
        # Arrange
        config_id = sample_bot_config.id
        update_data = {
            "name": "Updated Config",
            "job_search_query": "Python Developer",
            "location": "New York",
        }

        # Mock the service response
        updated_config = sample_bot_config.copy(deep=True)
        updated_config.name = update_data["name"]
        updated_config.job_search_query = update_data["job_search_query"]
        updated_config.location = update_data["location"]
        mock_bot_service.update_bot_config.return_value = updated_config

        # Act
        response = client.patch(
            f"/api/v1/bot/configs/{config_id}",
            json=update_data,
            headers=user_token_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == update_data["name"]
        assert response.json()["job_search_query"] == update_data["job_search_query"]
        mock_bot_service.update_bot_config.assert_called_once()

    def test_delete_bot_config(
        self, client, user_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test deleting a bot configuration."""
        # Arrange
        config_id = sample_bot_config.id

        # Act
        response = client.delete(
            f"/api/v1/bot/configs/{config_id}", headers=user_token_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_bot_service.delete_bot_config.assert_called_once_with(
            config_id=mock_bot_service.delete_bot_config.call_args[1]["config_id"],
            user_id=mock_bot_service.delete_bot_config.call_args[1]["user_id"],
        )

    def test_list_bot_configs(
        self, client, user_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test listing bot configurations."""
        # Arrange
        mock_bot_service.list_bot_configs.return_value = [sample_bot_config]

        # Act
        response = client.get("/api/v1/bot/configs/", headers=user_token_headers)

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == str(sample_bot_config.id)
        mock_bot_service.list_bot_configs.assert_called_once()

    def test_start_bot_session(
        self,
        client,
        user_token_headers,
        mock_bot_service,
        sample_bot_config,
        sample_bot_session,
    ):
        """Test starting a bot session."""
        # Arrange
        session_data = {"bot_config_id": str(sample_bot_config.id), "applies_limit": 10}
        mock_bot_service.start_bot_session.return_value = sample_bot_session

        # Act
        response = client.post(
            "/api/v1/bot/sessions/", json=session_data, headers=user_token_headers
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == str(sample_bot_session.id)
        assert response.json()["status"] == sample_bot_session.status.value
        mock_bot_service.start_bot_session.assert_called_once()

    def test_stop_bot_session(
        self, client, user_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test stopping a bot session."""
        # Arrange
        session_id = sample_bot_session.id

        # Act
        response = client.post(
            f"/api/v1/bot/sessions/{session_id}/stop", headers=user_token_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_bot_service.stop_bot_session.assert_called_once_with(
            session_id=mock_bot_service.stop_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.stop_bot_session.call_args[1]["user_id"],
        )

    def test_pause_bot_session(
        self, client, user_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test pausing a bot session."""
        # Arrange
        session_id = sample_bot_session.id

        # Act
        response = client.post(
            f"/api/v1/bot/sessions/{session_id}/pause", headers=user_token_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_bot_service.pause_bot_session.assert_called_once_with(
            session_id=mock_bot_service.pause_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.pause_bot_session.call_args[1]["user_id"],
        )

    def test_resume_bot_session(
        self, client, user_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test resuming a bot session."""
        # Arrange
        session_id = sample_bot_session.id

        # Act
        response = client.post(
            f"/api/v1/bot/sessions/{session_id}/resume", headers=user_token_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_bot_service.resume_bot_session.assert_called_once_with(
            session_id=mock_bot_service.resume_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.resume_bot_session.call_args[1]["user_id"],
        )

    def test_get_bot_session(
        self, client, user_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test getting a bot session."""
        # Arrange
        session_id = sample_bot_session.id
        mock_bot_service.get_bot_session.return_value = sample_bot_session

        # Act
        response = client.get(
            f"/api/v1/bot/sessions/{session_id}", headers=user_token_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == str(session_id)
        mock_bot_service.get_bot_session.assert_called_once_with(
            session_id=mock_bot_service.get_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.get_bot_session.call_args[1]["user_id"],
        )

    def test_list_bot_sessions(
        self, client, user_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test listing bot sessions."""
        # Arrange
        mock_bot_service.list_bot_sessions.return_value = [sample_bot_session]

        # Act
        response = client.get("/api/v1/bot/sessions/", headers=user_token_headers)

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == str(sample_bot_session.id)
        mock_bot_service.list_bot_sessions.assert_called_once()
