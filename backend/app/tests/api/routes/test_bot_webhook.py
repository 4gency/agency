import uuid
from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.bot import (
    BotApply,
    BotApplyStatus,
    BotSession,
    BotSessionStatus,
    Credentials,
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
