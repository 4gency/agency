import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.bot import (
    BotApply,
    BotApplyStatus,
    BotEvent,
    BotSession,
    BotSessionStatus,
    BotUserAction,
    Credentials,
    UserActionType,
)
from app.models.core import User
from app.models.preference import Config
from app.models.resume import PlainTextResume
from app.tests.utils.user import get_user_from_token_header


@pytest.fixture
def config_data() -> dict[str, Any]:
    """Fixture for complete Config data"""
    return {
        "remote": True,
        "experience_level": {
            "intership": True,
            "entry": True,
            "associate": True,
            "mid_senior_level": True,
            "director": True,
            "executive": True,
        },
        "job_types": {
            "full_time": True,
            "contract": True,
            "part_time": True,
            "temporary": True,
            "internship": True,
            "other": True,
            "volunteer": True,
        },
        "date": {"all_time": True, "month": False, "week": False, "hours": False},
        "positions": ["Backend Developer", "Python Developer"],
        "locations": ["United States", "Remote"],
        "apply_once_at_company": True,
        "distance": 100,
        "company_blacklist": ["BadCompany Inc"],
        "title_blacklist": ["Sales"],
        "location_blacklist": ["Antarctica"],
        "llm_model_type": "openai",
        "llm_model": "gpt-4o-mini",
    }


@pytest.fixture
def valid_resume_data() -> dict[str, Any]:
    """Fixture for valid PlainTextResume data"""
    return {
        "personal_information": {
            "name": "John",
            "surname": "Doe",
            "date_of_birth": "1990-01-01",
            "country": "USA",
            "city": "New York",
            "address": "123 Main St",
            "zip_code": "10001",
            "phone_prefix": "+1",
            "phone": "555-123-4567",
            "email": "john.doe@example.com",
            "github": "https://github.com/johndoe",
            "linkedin": "https://linkedin.com/in/johndoe",
        },
        "education_details": [
            {
                "education_level": "Bachelor's Degree",
                "institution": "University of New York",
                "field_of_study": "Computer Science",
                "final_evaluation_grade": "A",
                "start_date": "2010",
                "year_of_completion": "2014",
                "exam": ["GRE", "TOEFL"],
            }
        ],
        "experience_details": [
            {
                "position": "Software Engineer",
                "company": "Tech Solutions Inc.",
                "employment_period": "2014-2020",
                "location": "New York",
                "industry": "Technology",
                "key_responsibilities": [
                    "Developed web applications",
                    "Maintained legacy code",
                ],
                "skills_acquired": ["Python", "JavaScript", "SQL"],
            }
        ],
        "projects": [
            {
                "name": "Personal Website",
                "description": "Created a portfolio website to showcase projects",
                "link": "https://johndoe.dev",
            }
        ],
        "achievements": [
            {
                "name": "Employee of the Year",
                "description": "Awarded for outstanding contribution to the team",
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Developer",
                "description": "Associate level certification for AWS development",
            }
        ],
        "languages": [
            {"language": "English", "proficiency": "Native"},
            {"language": "Spanish", "proficiency": "Intermediate"},
        ],
        "interests": ["Coding", "Music", "Hiking"],
        "availability": {"notice_period": "2 weeks"},
        "salary_expectations": {"salary_range_usd": "80000-100000"},
        "self_identification": {
            "gender": "Male",
            "pronouns": "He/Him",
            "veteran": False,
            "disability": False,
            "ethnicity": "White",
        },
        "legal_authorization": {
            "us_work_authorization": True,
            "requires_visa_sponsorship": False,
        },
        "work_preferences": {
            "remote_work": True,
            "in_person_work": True,
            "open_to_relocation": True,
        },
    }


@pytest.fixture
def bot_session_with_api_key(
    client: TestClient,
    normal_subscriber_token_headers: dict[str, str],
    db: Session,
    config_data: dict[str, Any],
    valid_resume_data: dict[str, Any],
) -> Generator[tuple[BotSession, str], Any, None]:
    """Fixture to create a bot session with API key for testing webhook endpoints."""
    # Get user from token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Create test credentials
    credentials = Credentials(
        user_id=user.id, email="test_bot_webhook@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Create a session for user
    api_key = f"test_key_{uuid.uuid4().hex[:8]}"
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        api_key=api_key,
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    # Create or update user configuration using the config_data fixture
    if user.config:
        # Update existing config
        for key, value in config_data.items():
            setattr(user.config, key, value)
        db.add(user.config)
    else:
        # Create new config
        config = Config(user_id=user.id, **config_data)
        db.add(config)

    db.commit()

    # Create or update user resume using the valid_resume_data fixture
    if user.plain_text_resume:
        # Update existing resume
        for key, value in valid_resume_data.items():
            setattr(user.plain_text_resume, key, value)
        db.add(user.plain_text_resume)
    else:
        # Create new resume
        resume = PlainTextResume(user_id=user.id, **valid_resume_data)
        db.add(resume)

    db.commit()
    db.refresh(user)

    yield bot_session, api_key

    # Clean up
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_register_apply_success(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test registering a successful application through the bot webhook."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a successful application
    apply_data = {
        "status": BotApplyStatus.SUCCESS.value,
        "total_time": 60,
        "job_title": "Senior Python Developer",
        "job_url": "https://example.com/job123",
        "company_name": "Example Corp",
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/apply",
        headers={"api-key": api_key},
        json=apply_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    assert response.json()["message"] == "Application recorded successfully"

    # Verify the application was created and session stats were updated
    bot_applies = db.exec(
        select(BotApply).where(BotApply.bot_session_id == bot_session.id)
    ).all()

    assert len(bot_applies) == 1
    assert bot_applies[0].status == BotApplyStatus.SUCCESS
    assert bot_applies[0].job_title == "Senior Python Developer"
    assert bot_applies[0].company_name == "Example Corp"

    # Refresh bot session and check stats
    db.refresh(bot_session)
    assert bot_session.total_applied == 1
    assert bot_session.total_success == 1
    assert bot_session.total_failed == 0

    # Clean up the created apply
    db.delete(bot_applies[0])
    db.commit()


def test_register_apply_failed(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test registering a failed application through the bot webhook."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a failed application
    apply_data = {
        "status": BotApplyStatus.FAILED.value,
        "total_time": 30,
        "job_title": "DevOps Engineer",
        "job_url": "https://example.com/job456",
        "company_name": "Another Company",
        "failed_reason": "Application form error",
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/apply",
        headers={"api-key": api_key},
        json=apply_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    assert response.json()["message"] == "Application recorded successfully"

    # Verify the application was created and session stats were updated
    bot_applies = db.exec(
        select(BotApply).where(BotApply.bot_session_id == bot_session.id)
    ).all()

    assert len(bot_applies) == 1
    assert bot_applies[0].status == BotApplyStatus.FAILED
    assert bot_applies[0].job_title == "DevOps Engineer"
    assert bot_applies[0].company_name == "Another Company"
    assert bot_applies[0].failed_reason == "Application form error"

    # Refresh bot session and check stats
    db.refresh(bot_session)
    assert bot_session.total_applied == 1
    assert bot_session.total_success == 0
    assert bot_session.total_failed == 1

    # Clean up the created apply
    db.delete(bot_applies[0])
    db.commit()


def test_register_apply_invalid_api_key(client: TestClient) -> None:
    """Test registering an application with an invalid API key."""
    # Prepare request data
    apply_data = {
        "status": BotApplyStatus.SUCCESS.value,
        "job_title": "Python Developer",
    }

    # Make request with invalid API key
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/apply",
        headers={"api-key": "invalid_key"},
        json=apply_data,
    )

    # Check response
    assert response.status_code == 401
    assert "Invalid API Key" in response.text


def test_get_bot_config(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test getting bot configuration through the webhook."""
    bot_session, api_key = bot_session_with_api_key

    # Get user from bot session
    user = db.get(User, bot_session.user_id)
    assert user is not None
    assert user.config is not None
    assert user.plain_text_resume is not None

    # Make request with API key in header
    response = client.get(
        f"{settings.API_V1_STR}/bot-webhook/config",
        headers={"api-key": api_key},
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()

    # Verify YAML configuration
    assert "user_config" in data
    assert "user_resume" in data

    # Check for key elements in the config YAML
    for key_phrase in ["remote:", "experienceLevel:", "jobTypes:", "positions:"]:
        assert key_phrase in data["user_config"]

    # Check for key elements in the resume YAML
    for key_phrase in [
        "personal_information:",
        "education_details:",
        "experience_details:",
    ]:
        assert key_phrase in data["user_resume"]


def test_get_bot_config_invalid_api_key(client: TestClient) -> None:
    """Test getting bot configuration with an invalid API key."""
    # Make request with invalid API key
    response = client.get(
        f"{settings.API_V1_STR}/bot-webhook/config",
        headers={"api-key": "invalid_key"},
    )

    # Check response
    assert response.status_code == 401
    assert "Invalid API Key" in response.text


def test_get_bot_config_missing_config(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting bot configuration when the user has no config."""
    # Get user from token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Create credentials and bot session without user config
    credentials = Credentials(
        user_id=user.id, email="no_config_test@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Delete user config if exists
    if user.config:
        db.delete(user.config)
        db.commit()
        db.refresh(user)

    # Create a bot session with API key
    api_key = f"no_config_key_{uuid.uuid4().hex[:8]}"
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        api_key=api_key,
    )
    db.add(bot_session)
    db.commit()

    # Make request with API key in header
    response = client.get(
        f"{settings.API_V1_STR}/bot-webhook/config",
        headers={"api-key": api_key},
    )

    # Check response - should fail because config is missing
    assert response.status_code == 404
    assert "User configuration not found" in response.text

    # Clean up
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_create_event_success(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test creating a regular event that doesn't change the session status."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for an event
    event_data = {
        "type": "log",
        "message": "Test event message",
        "severity": "info",
        "details": {
            "source": "test_bot",
            "action": "test_action",
            "additional_info": "This is a test event",
        },
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": api_key},
        json=event_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["message"] == "Event created successfully"
    assert data["type"] == "log"
    assert data["severity"] == "info"
    assert data["status_updated"] is False
    assert "id" in data
    assert "created_at" in data

    # Verify the event was created in the database
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()

    assert len(events) == 1
    assert events[0].type == "log"
    assert events[0].message == "Test event message"
    assert events[0].severity == "info"

    # Verify the session status did not change
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.RUNNING  # Still in the initial state

    # Clean up the created event
    db.delete(events[0])
    db.commit()


def test_create_event_status_running(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test creating an event that changes session status to RUNNING."""
    bot_session, api_key = bot_session_with_api_key

    # Set the session to STARTING first
    bot_session.status = BotSessionStatus.STARTING
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    # Prepare request data for a status change event
    event_data = {
        "type": "running",  # This will trigger status change
        "message": "Bot is now running",
        "severity": "info",
        "details": {"source": "test_bot", "previous_status": "starting"},
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": api_key},
        json=event_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["status_updated"] is True

    # Verify the event was created and session status was updated
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.RUNNING
    assert bot_session.started_at is not None
    assert bot_session.last_status_message == "Bot is now running"

    # Verify event was created
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()

    # Should only have the original event now
    assert len(events) == 1
    assert events[0].type == "running"

    # Clean up events before cleaning up the session
    for event in events:
        db.delete(event)
    db.commit()


def test_create_event_status_paused(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test creating an event that changes session status to PAUSED."""
    bot_session, api_key = bot_session_with_api_key

    # Ensure session is in RUNNING state
    bot_session.status = BotSessionStatus.RUNNING
    db.add(bot_session)
    db.commit()

    # Prepare request data for a status change event
    event_data = {
        "type": "paused",  # This will trigger status change
        "message": "Bot has been paused",
        "severity": "info",
        "details": {"source": "test_bot", "reason": "user requested pause"},
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": api_key},
        json=event_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["status_updated"] is True

    # Verify the event was created and session status was updated
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.PAUSED
    assert bot_session.paused_at is not None
    assert bot_session.last_status_message == "Bot has been paused"

    # Clean up all events
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in events:
        db.delete(event)
    db.commit()


def test_create_event_status_completed(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test creating an event that changes session status to COMPLETED."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a status change event
    event_data = {
        "type": "completed",  # This will trigger status change
        "message": "Bot has completed all tasks",
        "severity": "info",
        "details": {"source": "test_bot", "total_applies": 42, "success_rate": "85%"},
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": api_key},
        json=event_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["status_updated"] is True

    # Verify the event was created and session status was updated
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.COMPLETED
    assert bot_session.finished_at is not None
    assert bot_session.last_status_message == "Bot has completed all tasks"

    # Clean up all events
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in events:
        db.delete(event)
    db.commit()


def test_create_event_status_failed(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test creating an event that changes session status to FAILED."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a status change event
    event_data = {
        "type": "failed",  # This will trigger status change
        "message": "Bot has failed due to authentication error",
        "severity": "error",
        "details": {
            "source": "test_bot",
            "error_code": "AUTH_FAILED",
            "error_details": "LinkedIn rejected the login attempt",
        },
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": api_key},
        json=event_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["status_updated"] is True

    # Verify the event was created and session status was updated
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.FAILED
    assert bot_session.finished_at is not None
    assert bot_session.error_message == "Bot has failed due to authentication error"

    # Clean up all events
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in events:
        db.delete(event)
    db.commit()


def test_create_event_status_waiting(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test creating an event that changes session status to WAITING_INPUT."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a status change event
    event_data = {
        "type": "waiting",  # This will trigger status change to WAITING_INPUT
        "message": "Bot is waiting for user action",
        "severity": "info",
        "details": {"source": "test_bot", "wait_reason": "authentication challenge"},
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": api_key},
        json=event_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["status_updated"] is True

    # Verify the event was created and session status was updated
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.WAITING_INPUT
    assert bot_session.last_status_message == "Bot is waiting for user action"

    # Clean up the created event
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in events:
        db.delete(event)
    db.commit()


def test_create_custom_bot_events(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test creating custom bot events that don't change status."""
    bot_session, api_key = bot_session_with_api_key

    # Set a known status
    bot_session.status = BotSessionStatus.RUNNING
    db.add(bot_session)
    db.commit()

    # List of custom events to test
    custom_events = [
        {
            "type": "logged_in",
            "message": "Successfully logged in to LinkedIn",
            "severity": "info",
        },
        {
            "type": "search_started",
            "message": "Started searching for jobs",
            "severity": "info",
        },
        {
            "type": "job_found",
            "message": "Found job: Software Developer at Example Corp",
            "severity": "info",
            "details": {"job_id": "12345", "company": "Example Corp"},
        },
        {
            "type": "apply_started",
            "message": "Starting application process",
            "severity": "info",
        },
        {
            "type": "error",
            "message": "Error during job search",
            "severity": "error",
            "details": {"error": "Network timeout"},
        },
    ]

    # First, clean up any existing events
    existing_events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in existing_events:
        db.delete(event)
    db.commit()

    for event_data in custom_events:
        # Make request with API key in header
        response = client.post(
            f"{settings.API_V1_STR}/bot-webhook/events",
            headers={"api-key": api_key},
            json=event_data,
        )

        # Check response
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        assert data["status_updated"] is False
        assert data["type"] == event_data["type"]  # type: ignore
        assert data["severity"] == event_data["severity"]  # type: ignore

    # Verify the events were created
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()

    assert len(events) == len(custom_events)

    # Verify the session status did not change
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.RUNNING

    # Clean up all the created events
    for event in events:
        db.delete(event)
    db.commit()


def test_bot_cannot_resume_paused_session(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test resuming a paused session with a running event."""
    bot_session, api_key = bot_session_with_api_key

    # Set session to PAUSED first
    bot_session.status = BotSessionStatus.PAUSED
    bot_session.paused_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.add(bot_session)
    db.commit()

    # Prepare request data for a status change event
    event_data = {
        "type": "running",  # This will trigger status change from PAUSED to RUNNING
        "message": "Bot resumed operation",
        "severity": "info",
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": api_key},
        json=event_data,
    )

    # Check response
    assert response.status_code == 400, f"Response: {response.text}"

    # Verify the event was created and session status was updated
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.PAUSED
    assert bot_session.resumed_at is None

    # Clean up the created event
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in events:
        db.delete(event)
    db.commit()


def test_request_user_action_2fa(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test requesting a 2FA code action from the user through the bot webhook."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a 2FA action
    action_data = {
        "action_type": UserActionType.PROVIDE_2FA.value,
        "description": "Please provide the 2FA code from your authenticator app",
        "input_field": "2fa_code",
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/user-actions",
        headers={"api-key": api_key},
        json=action_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["message"] == "User action requested successfully"
    assert data["action_type"] == UserActionType.PROVIDE_2FA.value
    assert (
        data["description"] == "Please provide the 2FA code from your authenticator app"
    )
    assert data["input_field"] == "2fa_code"
    assert "id" in data
    assert "requested_at" in data

    # Verify the action was created in the database
    actions = db.exec(
        select(BotUserAction).where(BotUserAction.bot_session_id == bot_session.id)
    ).all()

    assert len(actions) == 1
    assert actions[0].action_type == UserActionType.PROVIDE_2FA
    assert (
        actions[0].description
        == "Please provide the 2FA code from your authenticator app"
    )
    assert actions[0].input_field == "2fa_code"
    assert actions[0].is_completed is False

    # Verify that the bot session status was updated to WAITING_INPUT
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.WAITING_INPUT

    # Verify that an event was created for this action
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()

    assert len(events) > 0
    assert any(event.type == "user_action" for event in events)

    # Clean up the created action and events
    for action in actions:
        db.delete(action)
    for event in events:
        db.delete(event)
    db.commit()


def test_request_user_action_captcha(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test requesting a CAPTCHA solving action from the user through the bot webhook."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a CAPTCHA action
    action_data = {
        "action_type": UserActionType.SOLVE_CAPTCHA.value,
        "description": "Please solve the CAPTCHA to continue",
        "input_field": "captcha_solution",
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/user-actions",
        headers={"api-key": api_key},
        json=action_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["action_type"] == UserActionType.SOLVE_CAPTCHA.value

    # Verify the action was created in the database
    actions = db.exec(
        select(BotUserAction).where(BotUserAction.bot_session_id == bot_session.id)
    ).all()

    assert len(actions) == 1
    assert actions[0].action_type == UserActionType.SOLVE_CAPTCHA

    # Clean up the created action
    db.delete(actions[0])

    # Also clean up any events created
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in events:
        db.delete(event)

    db.commit()


def test_request_user_action_question(
    client: TestClient, bot_session_with_api_key: tuple[BotSession, str], db: Session
) -> None:
    """Test requesting a custom question action from the user through the bot webhook."""
    bot_session, api_key = bot_session_with_api_key

    # Prepare request data for a custom question action
    action_data = {
        "action_type": UserActionType.ANSWER_QUESTION.value,
        "description": "Do you want to apply for jobs requiring relocation?",
        "input_field": "relocation_answer",
    }

    # Make request with API key in header
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/user-actions",
        headers={"api-key": api_key},
        json=action_data,
    )

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"

    # Verify the action was created in the database
    actions = db.exec(
        select(BotUserAction).where(BotUserAction.bot_session_id == bot_session.id)
    ).all()

    assert len(actions) == 1
    assert actions[0].action_type == UserActionType.ANSWER_QUESTION
    assert (
        actions[0].description == "Do you want to apply for jobs requiring relocation?"
    )

    # Clean up the created action and any events
    db.delete(actions[0])
    events = db.exec(
        select(BotEvent).where(BotEvent.bot_session_id == bot_session.id)
    ).all()
    for event in events:
        db.delete(event)
    db.commit()


def test_request_user_action_invalid_api_key(client: TestClient) -> None:
    """Test requesting a user action with an invalid API key."""
    # Prepare request data
    action_data = {
        "action_type": UserActionType.PROVIDE_2FA.value,
        "description": "Please provide the 2FA code",
    }

    # Make request with invalid API key
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/user-actions",
        headers={"api-key": "invalid_key"},
        json=action_data,
    )

    # Check response
    assert response.status_code == 401
    assert "Invalid API Key" in response.text


def test_create_event_invalid_api_key(client: TestClient) -> None:
    """Test creating an event with an invalid API key."""
    # Prepare request data
    event_data = {
        "type": "log",
        "message": "Test message",
    }

    # Make request with invalid API key
    response = client.post(
        f"{settings.API_V1_STR}/bot-webhook/events",
        headers={"api-key": "invalid_key"},
        json=event_data,
    )

    # Check response
    assert response.status_code == 401
    assert "Invalid API Key" in response.text
