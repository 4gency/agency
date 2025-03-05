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
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_user
    ):
        """Test creating a bot configuration."""
        # Arrange
        config_data = {
            "name": "Test Config",
            "description": "Test bot configuration",
            "default_applies_limit": 10,
        }
        
        # Criar um subscription_id para o teste
        subscription_id = uuid.uuid4()

        # Mock the service response
        mock_bot_service.create_bot_config.return_value = BotConfig(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            subscription_id=subscription_id,
            name=config_data["name"],
            description=config_data.get("description"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            # Campos obrigatórios
            config_yaml_key="test-config.yaml",
            resume_yaml_key="test-resume.yaml",
            cloud_provider="https://br-se1.magaluobjects.com",
            kubernetes_namespace="bot-jobs",
            kubernetes_resources_cpu="500m",
            kubernetes_resources_memory="1Gi",
            kubernetes_limits_cpu="1000m",
            kubernetes_limits_memory="2Gi",
            config_bucket="configs",
            resume_bucket="resumes",
            config_version=1,
            resume_version=1,
            config_yaml_created_at=datetime.now(timezone.utc),
            resume_yaml_created_at=datetime.now(timezone.utc),
        )

        # Act
        response = client.post(
            f"/api/v1/bot/configs/?subscription_id={subscription_id}", 
            json=config_data, 
            headers=normal_subscriber_token_headers
        )

        # Assert
        assert "id" in response.json()
        assert response.status_code == 201, f"Response: {response.text}"
        assert response.json()["name"] == config_data["name"]
        mock_bot_service.create_bot_config.assert_called_once()

    def test_get_bot_config(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test getting a bot configuration."""
        # Arrange
        config_id = sample_bot_config.id
        mock_bot_service.get_bot_config.return_value = sample_bot_config

        # Act
        response = client.get(
            f"/api/v1/bot/configs/{config_id}", headers=normal_subscriber_token_headers
        )

        # Assert
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["id"] == str(config_id)
        mock_bot_service.get_bot_config.assert_called_once_with(
            config_id=mock_bot_service.get_bot_config.call_args[1]["config_id"],
            user_id=mock_bot_service.get_bot_config.call_args[1]["user_id"],
        )

    def test_update_bot_config(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test updating a bot configuration."""
        # Arrange
        config_id = sample_bot_config.id
        update_data = {
            "name": "Updated Config",
            "description": "Updated description"
        }

        # Mock the service response - criando um novo objeto em vez de modificar o existente
        mock_bot_service.update_bot_config.return_value = BotConfig(
            id=config_id,
            user_id=sample_bot_config.user_id,
            subscription_id=sample_bot_config.subscription_id,
            name=update_data["name"],
            description=update_data["description"],
            created_at=sample_bot_config.created_at,
            updated_at=datetime.now(timezone.utc),
            # Incluindo outros campos obrigatórios
            config_yaml_key="test-config.yaml",
            resume_yaml_key="test-resume.yaml",
            cloud_provider=sample_bot_config.cloud_provider,
            kubernetes_namespace=sample_bot_config.kubernetes_namespace,
            kubernetes_resources_cpu=sample_bot_config.kubernetes_resources_cpu,
            kubernetes_resources_memory=sample_bot_config.kubernetes_resources_memory,
            kubernetes_limits_cpu=sample_bot_config.kubernetes_limits_cpu,
            kubernetes_limits_memory=sample_bot_config.kubernetes_limits_memory,
            config_bucket=sample_bot_config.config_bucket,
            resume_bucket=sample_bot_config.resume_bucket,
            config_version=sample_bot_config.config_version,
            resume_version=sample_bot_config.resume_version,
            config_yaml_created_at=sample_bot_config.config_yaml_created_at,
            resume_yaml_created_at=sample_bot_config.resume_yaml_created_at,
        )

        # Act
        response = client.patch(
            f"/api/v1/bot/configs/{config_id}",
            json=update_data,
            headers=normal_subscriber_token_headers,
        )

        # Assert
        assert "name" in response.json()
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["name"] == update_data["name"]
        assert response.json()["description"] == update_data["description"]
        mock_bot_service.update_bot_config.assert_called_once()

    def test_delete_bot_config(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test deleting a bot configuration."""
        # Arrange
        config_id = sample_bot_config.id

        # Act
        response = client.delete(
            f"/api/v1/bot/configs/{config_id}", headers=normal_subscriber_token_headers
        )

        # Assert
        assert "success" in response.json()
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["success"] is True
        mock_bot_service.delete_bot_config.assert_called_once_with(
            config_id=mock_bot_service.delete_bot_config.call_args[1]["config_id"],
            user_id=mock_bot_service.delete_bot_config.call_args[1]["user_id"],
        )

    def test_list_bot_configs(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_config
    ):
        """Test listing bot configurations."""
        # Arrange
        mock_bot_service.list_bot_configs.return_value = [sample_bot_config]

        # Act
        response = client.get("/api/v1/bot/configs/", headers=normal_subscriber_token_headers)

        # Assert
        assert response.status_code == 200, f"Response: {response.text}"
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == str(sample_bot_config.id)
        mock_bot_service.list_bot_configs.assert_called_once()

    def test_start_bot_session(
        self,
        client,
        normal_subscriber_token_headers,
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
            "/api/v1/bot/sessions/", json=session_data, headers=normal_subscriber_token_headers
        )

        # Assert
        assert "id" in response.json()
        assert response.status_code == 201, f"Response: {response.text}"
        assert response.json()["id"] == str(sample_bot_session.id)
        assert response.json()["status"] == sample_bot_session.status.value
        mock_bot_service.start_bot_session.assert_called_once()

    def test_stop_bot_session(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test stopping a bot session."""
        # Arrange
        session_id = sample_bot_session.id

        # Act
        response = client.post(
            f"/api/v1/bot/sessions/{session_id}/stop", headers=normal_subscriber_token_headers
        )

        # Assert
        assert "success" in response.json()
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["success"] is True
        mock_bot_service.stop_bot_session.assert_called_once_with(
            session_id=mock_bot_service.stop_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.stop_bot_session.call_args[1]["user_id"],
        )

    def test_pause_bot_session(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test pausing a bot session."""
        # Arrange
        session_id = sample_bot_session.id

        # Act
        response = client.post(
            f"/api/v1/bot/sessions/{session_id}/pause", headers=normal_subscriber_token_headers
        )

        # Assert
        assert "success" in response.json()
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["success"] is True
        mock_bot_service.pause_bot_session.assert_called_once_with(
            session_id=mock_bot_service.pause_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.pause_bot_session.call_args[1]["user_id"],
        )

    def test_resume_bot_session(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test resuming a bot session."""
        # Arrange
        session_id = sample_bot_session.id

        # Act
        response = client.post(
            f"/api/v1/bot/sessions/{session_id}/resume", headers=normal_subscriber_token_headers
        )

        # Assert
        assert "success" in response.json()
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["success"] is True
        mock_bot_service.resume_bot_session.assert_called_once_with(
            session_id=mock_bot_service.resume_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.resume_bot_session.call_args[1]["user_id"],
        )

    def test_get_bot_session(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test getting a bot session."""
        # Arrange
        session_id = sample_bot_session.id
        mock_bot_service.get_bot_session.return_value = sample_bot_session

        # Act
        response = client.get(
            f"/api/v1/bot/sessions/{session_id}", headers=normal_subscriber_token_headers
        )

        # Assert
        assert "id" in response.json()
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["id"] == str(session_id)
        mock_bot_service.get_bot_session.assert_called_once_with(
            session_id=mock_bot_service.get_bot_session.call_args[1]["session_id"],
            user_id=mock_bot_service.get_bot_session.call_args[1]["user_id"],
        )

    def test_list_bot_sessions(
        self, client, normal_subscriber_token_headers, mock_bot_service, sample_bot_session
    ):
        """Test listing bot sessions."""
        # Arrange
        mock_bot_service.list_bot_sessions.return_value = [sample_bot_session]

        # Act
        response = client.get("/api/v1/bot/sessions/", headers=normal_subscriber_token_headers)

        # Assert
        assert response.status_code == 200, f"Response: {response.text}"
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == str(sample_bot_session.id)
        mock_bot_service.list_bot_sessions.assert_called_once()
