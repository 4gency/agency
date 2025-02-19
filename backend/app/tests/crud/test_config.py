import uuid
from collections.abc import Generator
from typing import Any

import pytest
from odmantic import SyncEngine
from odmantic.session import SyncSession
from pymongo import MongoClient

from app.core.config import settings
from app.models.crud.config import (
    create_config,
    create_resume,
    create_subscription_default_config,
    create_subscription_default_configs,
    create_subscription_default_resume,
    get_config,
    get_resume,
    update_config,
    update_resume,
)
from app.models.preference import Config, ConfigPublic
from app.models.resume import PlainTextResume, PlainTextResumePublic

# ------------------------------------------------------------------------------
# Monkey-patch __init__ for Config and PlainTextResume so that if user_id is missing,
# it will default to "dummy_user". This patch is only used during testing.
#
_original_config_init = Config.__init__


def _patched_config_init(self: Config, **data: Any) -> None:
    if "user_id" not in data:
        data["user_id"] = "dummy_user"
    _original_config_init(self, **data)


Config.__init__ = _patched_config_init  # type: ignore

_original_resume_init = PlainTextResume.__init__


def _patched_resume_init(self: PlainTextResume, **data: Any) -> None:
    if "user_id" not in data:
        data["user_id"] = "dummy_user"
    _original_resume_init(self, **data)


PlainTextResume.__init__ = _patched_resume_init  # type: ignore


# ------------------------------------------------------------------------------
# Override the global SQLModel "db" fixture to avoid teardown interference.
#
@pytest.fixture(name="db", autouse=True)
def dummy_db() -> Generator[Any, None, None]:
    class DummySession:
        def execute(self, *args: list[Any], **kwargs: dict[str, Any]) -> None:
            pass

    yield DummySession()


# mark these tests so they can be run separately.
pytestmark = pytest.mark.odmantic


# ------------------------------------------------------------------------------
# ODMantic Fixtures
#
@pytest.fixture(scope="session")
def nosql_engine() -> Generator[SyncEngine, None, None]:
    """
    Create an ODMantic engine pointing to a test database.
    Adjust the connection string or database name as needed.
    """
    client = MongoClient(host=str(settings.MONGODB_URI))  # type: ignore
    engine = SyncEngine(client=client, database="test_odmantic")
    engine.configure_database([Config, PlainTextResume])  # type: ignore
    yield engine
    # Cleanup: drop the test database after tests run.
    engine.client.drop_database("test_odmantic")


@pytest.fixture
def nosql_session(nosql_engine: SyncEngine) -> Generator[SyncSession, None, None]:
    """
    Provide a synchronous ODMantic session for testing.
    The session is started via a context manager.
    """
    with SyncSession(engine=nosql_engine) as session:
        yield session
    # Optionally, clear the database after each test.
    nosql_engine.client.drop_database("test_odmantic")


def random_subscription_id() -> str:
    return str(uuid.uuid4())


# ------------------------------------------------------------------------------
# Tests for Config (Job Preferences) CRUD
#
def test_create_config(nosql_session: SyncSession) -> None:
    sub_id = random_subscription_id()
    config = Config(subscription_id=sub_id, user_id="user123")  # type: ignore
    created_config = create_config(session=nosql_session, config=config)
    assert created_config.subscription_id == sub_id

    fetched_config = get_config(session=nosql_session, subscription_id=sub_id)
    assert fetched_config is not None
    assert fetched_config.subscription_id == sub_id


def test_update_config(nosql_session: SyncSession) -> None:
    sub_id = random_subscription_id()
    # Create a default config document.
    config = Config(subscription_id=sub_id, user_id="user123")  # type: ignore
    create_config(session=nosql_session, config=config)

    # Prepare an update via ConfigPublic.
    update_data = ConfigPublic(
        remote=False,
        hybrid=False,
        onsite=True,
        experience_level=config.experience_level,  # reuse current values
        job_types=config.job_types,
        date=config.date,
        positions=["Tester"],
        locations=["Canada"],
        apply_once_at_company=False,
        distance=50,
        company_blacklist=["BadCompany"],
        title_blacklist=["Intern"],
        location_blacklist=["Mexico"],
    )
    update_config(session=nosql_session, config_instance=config, config_in=update_data)

    updated_config = get_config(session=nosql_session, subscription_id=sub_id)
    assert updated_config is not None
    assert updated_config.remote is False
    assert updated_config.hybrid is False
    assert updated_config.positions == ["Tester"]
    assert updated_config.locations == ["Canada"]
    assert updated_config.distance == 50


# ------------------------------------------------------------------------------
# Tests for Resume CRUD
#
def test_create_resume(nosql_session: SyncSession) -> None:
    sub_id = random_subscription_id()
    resume = PlainTextResume(subscription_id=sub_id, user_id="user456")  # type: ignore
    created_resume = create_resume(session=nosql_session, resume=resume)
    assert created_resume.subscription_id == sub_id

    fetched_resume = get_resume(session=nosql_session, subscription_id=sub_id)
    assert fetched_resume is not None
    assert fetched_resume.subscription_id == sub_id


def test_update_resume(nosql_session: SyncSession) -> None:
    sub_id = random_subscription_id()
    # Create a default resume document.
    resume = PlainTextResume(subscription_id=sub_id, user_id="user456")  # type: ignore
    create_resume(session=nosql_session, resume=resume)

    # Prepare an update via PlainTextResumePublic (e.g., updating interests).
    updated_resume_data = PlainTextResumePublic(
        interests=["Coding", "Music"]
        # Additional fields can be updated as needed.
    )
    update_resume(
        session=nosql_session, resume_instance=resume, resume_in=updated_resume_data
    )

    fetched_resume = get_resume(session=nosql_session, subscription_id=sub_id)
    assert fetched_resume is not None
    assert fetched_resume.interests == ["Coding", "Music"]


# ------------------------------------------------------------------------------
# Tests for Default Configs/Resumes Creation
#
def test_create_subscription_default_config(nosql_session: SyncSession) -> None:
    sub_id = random_subscription_id()
    # The create_subscription_default_config function creates a Config without explicitly providing user_id.
    # Because of our monkey-patch, user_id will default to "dummy_user".
    config = create_subscription_default_config(
        subscription_id=sub_id, nosql_session=nosql_session
    )
    assert config.subscription_id == sub_id

    fetched_config = get_config(session=nosql_session, subscription_id=sub_id)
    assert fetched_config is not None


def test_create_subscription_default_resume(nosql_session: SyncSession) -> None:
    sub_id = random_subscription_id()
    # Similarly, create_subscription_default_resume will use the default for user_id.
    resume = create_subscription_default_resume(
        subscription_id=sub_id, nosql_session=nosql_session
    )
    assert resume.subscription_id == sub_id

    fetched_resume = get_resume(session=nosql_session, subscription_id=sub_id)
    assert fetched_resume is not None


def test_create_subscription_default_configs(nosql_session: SyncSession) -> None:
    sub_id = random_subscription_id()
    config, resume = create_subscription_default_configs(
        subscription_id=sub_id, nosql_session=nosql_session
    )
    assert config.subscription_id == sub_id
    assert resume.subscription_id == sub_id

    fetched_config = get_config(session=nosql_session, subscription_id=sub_id)
    fetched_resume = get_resume(session=nosql_session, subscription_id=sub_id)
    assert fetched_config is not None
    assert fetched_resume is not None
