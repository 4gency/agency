import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlmodel import Session, select

from app.models.bot import (
    BotSession,
    BotSessionStatus,
    KubernetesPodStatus,
)
from app.services.bot import get_bot_service
from app.tests.utils.bot import (
    create_test_bot_config,
    create_test_bot_session,
    create_test_linkedin_credentials,
)


@pytest.fixture
def mock_kubernetes_manager():
    """Mock for the Kubernetes manager."""
    with patch("app.services.bot.get_kubernetes_manager") as mock:
        kubernetes_manager = MagicMock()
        kubernetes_manager.deploy_bot_pod = AsyncMock(
            return_value=("pod-name", "pod-ip")
        )
        kubernetes_manager.delete_pod = AsyncMock(return_value=True)
        kubernetes_manager.send_command_to_pod = AsyncMock(return_value=True)
        kubernetes_manager.get_pod_status = AsyncMock(
            return_value=KubernetesPodStatus.RUNNING
        )
        mock.return_value = kubernetes_manager
        yield kubernetes_manager


@pytest.fixture
def mock_nosql_db():
    """Create a mock NoSQL database session."""
    return MagicMock()


@pytest.fixture
async def mock_bot_service(db: Session, mock_kubernetes_manager, mock_nosql_db):
    """Create a mock bot service with dependencies."""
    # Create a real service instance first
    service = await get_bot_service(db, mock_nosql_db)

    # Then patch its private methods with mocks
    with patch.object(
        service, "_get_config_yaml", AsyncMock(return_value="config: test")
    ), patch.object(
        service, "_get_resume_yaml", AsyncMock(return_value="resume: test")
    ), patch.object(
        service, "_get_active_subscription_id", AsyncMock(return_value=uuid.uuid4())
    ), patch.object(service, "_update_session_metrics", AsyncMock()), patch.object(
        service, "_record_bot_event", AsyncMock()
    ):
        yield service


@pytest.fixture
def sample_bot_config(db: Session):
    """Create a sample bot configuration for testing."""
    return create_test_bot_config(db)


@pytest.fixture
def sample_linkedin_credentials(db: Session, sample_bot_config):
    """Create sample LinkedIn credentials for testing."""
    return create_test_linkedin_credentials(
        db,
        subscription_id=sample_bot_config.subscription_id,
        user_id=sample_bot_config.user_id,
    )


@pytest.fixture
def sample_bot_session(db: Session, sample_bot_config):
    """Create a sample bot session for testing."""
    # Update the status to STARTING for some tests that need this state
    session = create_test_bot_session(
        db,
        bot_config_id=sample_bot_config.id,
        subscription_id=sample_bot_config.subscription_id,
        user_id=sample_bot_config.user_id,
    )

    # Update status to STARTING for specific tests
    session.status = BotSessionStatus.STARTING
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestBotService:
    """Tests for the BotService class."""

    async def test_start_bot_session(
        self, mock_bot_service, sample_bot_config, sample_linkedin_credentials, db
    ):
        """Test starting a bot session."""
        background_tasks = BackgroundTasks()

        # Act
        session = await mock_bot_service.start_bot_session(
            user_id=sample_bot_config.user_id,
            subscription_id=sample_bot_config.subscription_id,
            bot_config_id=sample_bot_config.id,
            background_tasks=background_tasks,
        )

        # Assert
        assert session is not None
        assert session.user_id == sample_bot_config.user_id
        assert session.subscription_id == sample_bot_config.subscription_id
        assert session.bot_config_id == sample_bot_config.id
        assert session.status == BotSessionStatus.STARTING

        # Verify the session was saved to the database
        db_session = db.exec(
            select(BotSession).where(BotSession.id == session.id)
        ).first()
        assert db_session is not None
        assert db_session.status == BotSessionStatus.STARTING

    async def test_stop_bot_session(self, mock_bot_service, sample_bot_session, db):
        """Test stopping a bot session."""
        # Act
        result = await mock_bot_service.stop_bot_session(
            session_id=sample_bot_session.id, user_id=sample_bot_session.user_id
        )

        # Assert
        assert result is True

        # Verify the session status was updated
        db_session = db.exec(
            select(BotSession).where(BotSession.id == sample_bot_session.id)
        ).first()
        assert db_session is not None
        assert db_session.status == BotSessionStatus.STOPPING

    async def test_pause_bot_session(self, mock_bot_service, sample_bot_session, db):
        """Test pausing a bot session."""
        # Update session to RUNNING status
        sample_bot_session.status = BotSessionStatus.RUNNING
        db.add(sample_bot_session)
        db.commit()

        # Act
        result = await mock_bot_service.pause_bot_session(
            session_id=sample_bot_session.id, user_id=sample_bot_session.user_id
        )

        # Assert
        assert result is True

        # Verify the session status was updated
        db_session = db.exec(
            select(BotSession).where(BotSession.id == sample_bot_session.id)
        ).first()
        assert db_session is not None
        assert db_session.status == BotSessionStatus.PAUSED

    async def test_resume_bot_session(self, mock_bot_service, sample_bot_session, db):
        """Test resuming a bot session."""
        # Update session to PAUSED status
        sample_bot_session.status = BotSessionStatus.PAUSED
        db.add(sample_bot_session)
        db.commit()

        # Act
        result = await mock_bot_service.resume_bot_session(
            session_id=sample_bot_session.id, user_id=sample_bot_session.user_id
        )

        # Assert
        assert result is True

        # Verify the session status was updated
        db_session = db.exec(
            select(BotSession).where(BotSession.id == sample_bot_session.id)
        ).first()
        assert db_session is not None
        assert db_session.status == BotSessionStatus.RUNNING

    async def test_get_bot_session(self, mock_bot_service, sample_bot_session):
        """Test getting a bot session."""
        # Act
        session = await mock_bot_service.get_bot_session(
            session_id=sample_bot_session.id, user_id=sample_bot_session.user_id
        )

        # Assert
        assert session is not None
        assert session.id == sample_bot_session.id
        assert session.user_id == sample_bot_session.user_id
        assert session.status == sample_bot_session.status

    async def test_get_bot_session_not_found(self, mock_bot_service):
        """Test getting a non-existent bot session."""
        # Act/Assert
        with pytest.raises(HTTPException) as excinfo:
            await mock_bot_service.get_bot_session(
                session_id=uuid.uuid4(), user_id=uuid.uuid4()
            )

        assert excinfo.value.status_code == 404
        assert "Bot session not found" in excinfo.value.detail

    async def test_list_bot_sessions(self, mock_bot_service, sample_bot_session):
        """Test listing bot sessions for a user."""
        # Act
        sessions = await mock_bot_service.list_bot_sessions(
            user_id=sample_bot_session.user_id
        )

        # Assert
        assert len(sessions) >= 1
        assert any(session.id == sample_bot_session.id for session in sessions)

    async def test_handle_bot_event(self, mock_bot_service, sample_bot_session, db):
        """Test handling a bot event."""
        # Arrange
        event_data = {
            "event_type": "status_update",
            "status": "running",
            "message": "Bot is running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Act
        result = await mock_bot_service.handle_bot_event(
            session_id=sample_bot_session.id, event_data=event_data
        )

        # Assert
        assert result is True

        # Verify event was recorded
        mock_bot_service._record_bot_event.assert_called_once()
