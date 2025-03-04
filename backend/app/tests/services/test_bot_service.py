import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlmodel import Session, select

from app.models.bot import (
    BotConfig,
    BotSession,
    BotSessionStatus,
    KubernetesPodStatus,
    LinkedInCredentials,
)
from app.services.bot import get_bot_service


@pytest.fixture
def mock_kubernetes_manager():
    """Mock for the Kubernetes manager."""
    with patch("app.services.bot_service_extensions.get_kubernetes_manager") as mock:
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
async def mock_bot_service(db: Session, _mock_kubernetes_manager, mock_nosql_db):
    """Create a mock bot service with dependencies."""
    service = await get_bot_service(db, mock_nosql_db)
    service._get_config_yaml = AsyncMock(return_value="config: test")
    service._get_resume_yaml = AsyncMock(return_value="resume: test")
    service._get_active_subscription_id = AsyncMock(return_value=uuid.uuid4())
    service._update_session_metrics = AsyncMock()
    service._record_bot_event = AsyncMock()
    return service


@pytest.fixture
def sample_bot_config(db: Session):
    """Create a sample bot configuration for testing."""
    user_id = uuid.uuid4()
    subscription_id = uuid.uuid4()

    config = BotConfig(
        id=uuid.uuid4(),
        user_id=user_id,
        subscription_id=subscription_id,
        name="Test Config",
        job_search_query="Software Engineer",
        location="Remote",
        default_applies_limit=10,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@pytest.fixture
def sample_linkedin_credentials(db: Session, sample_bot_config):
    """Create sample LinkedIn credentials for testing."""
    credentials = LinkedInCredentials(
        id=uuid.uuid4(),
        subscription_id=sample_bot_config.subscription_id,
        username="test@example.com",
        password="encrypted_password",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(credentials)
    db.commit()
    db.refresh(credentials)
    return credentials


@pytest.fixture
def sample_bot_session(db: Session, sample_bot_config, _sample_linkedin_credentials):
    """Create a sample bot session for testing."""
    session = BotSession(
        id=uuid.uuid4(),
        user_id=sample_bot_config.user_id,
        subscription_id=sample_bot_config.subscription_id,
        bot_config_id=sample_bot_config.id,
        status=BotSessionStatus.STARTING,
        pod_name="test-pod",
        pod_ip="10.0.0.1",
        applies_limit=10,
        applies_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

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

        # Verify the event was recorded
        mock_bot_service._record_bot_event.assert_called_once()

        # Verify the session status was updated
        db_session = db.exec(
            select(BotSession).where(BotSession.id == sample_bot_session.id)
        ).first()
        assert db_session is not None
        assert db_session.status == BotSessionStatus.RUNNING
