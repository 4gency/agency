import uuid
from datetime import datetime, timezone

from sqlmodel import Session

from app.models.bot import (
    BotConfig,
    BotSession,
    BotSessionStatus,
    LinkedInCredentials,
)
from app.tests.utils.subscription import create_test_subscription


def create_test_linkedin_credentials(
    db: Session,
    subscription_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> LinkedInCredentials:
    """Create test LinkedIn credentials for testing.

    Creates a subscription if not provided.
    """
    if not subscription_id or not user_id:
        subscription = create_test_subscription(db)
        subscription_id = subscription.id
        user_id = subscription.user_id

    credentials = LinkedInCredentials(
        id=uuid.uuid4(),
        subscription_id=subscription_id,
        user_id=user_id,
        email="test@example.com",
        password="encrypted_password",
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)
    return credentials


def create_test_bot_config(
    db: Session,
    subscription_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> BotConfig:
    """Create a test bot configuration for testing.

    Creates a subscription if not provided.
    """
    if not subscription_id or not user_id:
        subscription = create_test_subscription(db)
        subscription_id = subscription.id
        user_id = subscription.user_id

    # Generate random keys for required fields
    config_key = f"config-{uuid.uuid4()}.yaml"
    resume_key = f"resume-{uuid.uuid4()}.yaml"

    config = BotConfig(
        id=uuid.uuid4(),
        user_id=user_id,
        subscription_id=subscription_id,
        name="Test Config",
        config_yaml_key=config_key,
        resume_yaml_key=resume_key,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def create_test_bot_session(
    db: Session,
    bot_config_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> BotSession:
    """Create a test bot session for testing.

    Creates a bot config and subscription if not provided.
    """
    if not bot_config_id or not subscription_id or not user_id:
        bot_config = create_test_bot_config(db)
        bot_config_id = bot_config.id
        subscription_id = bot_config.subscription_id
        user_id = bot_config.user_id

    now = datetime.now(timezone.utc)
    session = BotSession(
        id=uuid.uuid4(),
        subscription_id=subscription_id,
        bot_config_id=bot_config_id,
        status=BotSessionStatus.RUNNING,
        kubernetes_pod_name="test-pod",
        kubernetes_pod_ip="10.0.0.1",
        applies_limit=10,
        created_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
