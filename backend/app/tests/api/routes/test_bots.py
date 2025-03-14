import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.bot import BotSession, BotSessionStatus, BotStyleChoice, Credentials
from app.models.preference import Config
from app.models.resume import PlainTextResume
from app.tests.utils.user import get_user_from_token_header


def test_create_bot_session(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a bot session as a subscriber."""
    # Primeiro, obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Create job preferences and resume settings
    job_preferences = Config(user_id=user.id)
    db.add(job_preferences)
    db.commit()
    db.refresh(job_preferences)

    resume_settings = PlainTextResume(
        user_id=user.id,
        personal_information={
            "name": "John",
            "surname": "Doe",
            "date_of_birth": "1990-01-01",
            "country": "United States",
            "city": "New York",
            "address": "123 Main St",
            "zip_code": "10001",
            "phone_prefix": "+1",
            "phone": "1234567890",
            "email": "john.doe@example.com",
            "github": "https://github.com/john_doe",
            "linkedin": "https://linkedin.com/in/john_doe",
        },
        education_details=[
            {
                "education_level": "Bachelor's Degree",
                "institution": "University of Example",
                "field_of_study": "Computer Science",
                "final_evaluation_grade": "A",
                "start_date": "2018",
                "year_of_completion": "2022",
                "exam": ["Test1", "Test2"],
            }
        ],
        experience_details=[
            {
                "position": "Software Engineer",
                "company": "Example Corp",
                "employment_period": "2020 - 2022",
                "location": "New York",
                "industry": "Technology",
                "key_responsibilities": ["Developed features", "Fixed bugs"],
                "skills_acquired": ["Python", "Django", "React"],
            }
        ],
        projects=[
            {
                "name": "Test Project",
                "description": "A test project",
                "link": "www.example.com",
            }
        ],
        achievements=[{"name": "Achievement", "description": "Test achievement"}],
        certifications=[{"name": "Certification", "description": "Test certification"}],
        languages=[{"language": "English", "proficiency": "Native"}],
        interests=["Reading", "Swimming"],
        availability={"notice_period": "2 weeks"},
        salary_expectations={"salary_range_usd": "70000 - 90000"},
        self_identification={
            "gender": "Prefer not to say",
            "pronouns": "They/Them",
            "veteran": False,
            "disability": False,
            "ethnicity": "Prefer not to say",
        },
        legal_authorization={
            "eu_work_authorization": True,
            "us_work_authorization": True,
            "requires_us_visa": False,
            "requires_us_sponsorship": False,
            "requires_eu_visa": False,
            "legally_allowed_to_work_in_eu": True,
            "legally_allowed_to_work_in_us": True,
            "requires_eu_sponsorship": False,
            "canada_work_authorization": False,
            "requires_canada_visa": False,
            "legally_allowed_to_work_in_canada": False,
            "requires_canada_sponsorship": False,
            "uk_work_authorization": False,
            "requires_uk_visa": False,
            "legally_allowed_to_work_in_uk": False,
            "requires_uk_sponsorship": False,
        },
        work_preferences={
            "remote_work": True,
            "in_person_work": False,
            "open_to_relocation": True,
            "willing_to_complete_assessments": True,
            "willing_to_undergo_drug_tests": True,
            "willing_to_undergo_background_checks": True,
        },
    )
    db.add(resume_settings)
    db.commit()
    db.refresh(resume_settings)

    # Cria uma credencial para o usuário correto
    credentials = Credentials(
        user_id=user.id, email="test_cred@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    data = {
        "credentials_id": str(credentials.id),
        "applies_limit": 100,
        "style": BotStyleChoice.DEFAULT.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions",
        headers=normal_subscriber_token_headers,
        json=data,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    created_session = r.json()
    assert created_session["credentials_id"] == str(credentials.id)
    assert created_session["applies_limit"] == 100
    assert created_session["status"] == BotSessionStatus.RUNNING.value
    assert created_session["style"] == BotStyleChoice.DEFAULT.value

    # Verificar se foi realmente criado no banco de dados
    session_in_db = db.get(BotSession, uuid.UUID(created_session["id"]))
    assert session_in_db is not None
    assert session_in_db.status == BotSessionStatus.RUNNING
    assert session_in_db.applies_limit == 100
    assert session_in_db.style == BotStyleChoice.DEFAULT
    assert session_in_db.user_id == user.id
    assert session_in_db.credentials_id == credentials.id


def test_create_bot_session_without_job_preferences_and_resume_settings(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a bot session without job preferences and resume settings."""
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    credentials = Credentials(
        user_id=user.id, email="test_cred2@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    data = {
        "credentials_id": str(credentials.id),
        "applies_limit": 100,
        "style": BotStyleChoice.DEFAULT.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions",
        headers=normal_subscriber_token_headers,
        json=data,
    )

    assert r.status_code == 406, f"Response: {r.text}"
    assert r.json() == {
        "detail": "You cannot create a session without creating job preferences and resume settings first."
    }


def test_create_bot_session_without_job_preferences(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a bot session without job preferences."""
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    resume_settings = PlainTextResume(
        user_id=user.id,
        personal_information={
            "name": "John",
            "surname": "Doe",
            "date_of_birth": "1990-01-01",
            "country": "United States",
            "city": "New York",
            "address": "123 Main St",
            "zip_code": "10001",
            "phone_prefix": "+1",
            "phone": "1234567890",
            "email": "john.doe@example.com",
            "github": "https://github.com/john_doe",
            "linkedin": "https://linkedin.com/in/john_doe",
        },
        education_details=[
            {
                "education_level": "Bachelor's Degree",
                "institution": "University of Example",
                "field_of_study": "Computer Science",
                "final_evaluation_grade": "A",
                "start_date": "2018",
                "year_of_completion": "2022",
                "exam": ["Test1", "Test2"],
            }
        ],
        experience_details=[
            {
                "position": "Software Engineer",
                "company": "Example Corp",
                "employment_period": "2020 - 2022",
                "location": "New York",
                "industry": "Technology",
                "key_responsibilities": ["Developed features", "Fixed bugs"],
                "skills_acquired": ["Python", "Django", "React"],
            }
        ],
        projects=[
            {
                "name": "Test Project",
                "description": "A test project",
                "link": "www.example.com",
            }
        ],
        achievements=[{"name": "Achievement", "description": "Test achievement"}],
        certifications=[{"name": "Certification", "description": "Test certification"}],
        languages=[{"language": "English", "proficiency": "Native"}],
        interests=["Reading", "Swimming"],
        availability={"notice_period": "2 weeks"},
        salary_expectations={"salary_range_usd": "70000 - 90000"},
        self_identification={
            "gender": "Prefer not to say",
            "pronouns": "They/Them",
            "veteran": False,
            "disability": False,
            "ethnicity": "Prefer not to say",
        },
        legal_authorization={
            "eu_work_authorization": True,
            "us_work_authorization": True,
            "requires_us_visa": False,
            "requires_us_sponsorship": False,
            "requires_eu_visa": False,
            "legally_allowed_to_work_in_eu": True,
            "legally_allowed_to_work_in_us": True,
            "requires_eu_sponsorship": False,
            "canada_work_authorization": False,
            "requires_canada_visa": False,
            "legally_allowed_to_work_in_canada": False,
            "requires_canada_sponsorship": False,
            "uk_work_authorization": False,
            "requires_uk_visa": False,
            "legally_allowed_to_work_in_uk": False,
            "requires_uk_sponsorship": False,
        },
        work_preferences={
            "remote_work": True,
            "in_person_work": False,
            "open_to_relocation": True,
            "willing_to_complete_assessments": True,
            "willing_to_undergo_drug_tests": True,
            "willing_to_undergo_background_checks": True,
        },
    )
    db.add(resume_settings)
    db.commit()
    db.refresh(resume_settings)

    credentials = Credentials(
        user_id=user.id, email="test_cred3@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    data = {
        "credentials_id": str(credentials.id),
        "applies_limit": 100,
        "style": BotStyleChoice.DEFAULT.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions",
        headers=normal_subscriber_token_headers,
        json=data,
    )

    assert r.status_code == 406, f"Response: {r.text}"
    assert r.json() == {
        "detail": "You cannot create a session without creating job preferences first."
    }

    # Limpa as credenciais criadas para o teste
    db.delete(credentials)
    db.commit()


def test_create_bot_session_without_resume_settings(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a bot session without resume settings."""
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    job_preferences = Config(user_id=user.id)
    db.add(job_preferences)
    db.commit()
    db.refresh(job_preferences)

    credentials = Credentials(
        user_id=user.id, email="test_cred4@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    data = {
        "credentials_id": str(credentials.id),
        "applies_limit": 100,
        "style": BotStyleChoice.DEFAULT.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions",
        headers=normal_subscriber_token_headers,
        json=data,
    )

    assert r.status_code == 406, f"Response: {r.text}"
    assert r.json() == {
        "detail": "You cannot create a session without creating resume settings first."
    }

    # Limpa as credenciais criadas para o teste
    db.delete(credentials)
    db.commit()


def test_create_bot_session_not_subscriber(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that non-subscribers can't create a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_user_token_headers, client)

    # Cria uma credencial para o usuário correto
    credentials = Credentials(
        user_id=user.id, email="test_cred2@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    data = {
        "credentials_id": str(credentials.id),
        "applies_limit": 100,
        "style": BotStyleChoice.DEFAULT.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 403, f"Response: {r.text}"
    assert r.json() == {"detail": "The user is not a subscriber"}

    # Limpa as credenciais criadas para o teste
    db.delete(credentials)
    db.commit()


def test_get_bot_sessions(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting all bot sessions for the current user."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_cred3@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    sessions = r.json()
    assert "total" in sessions
    assert "items" in sessions

    # Limpa os dados criados para o teste
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_bot_session_by_id(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting a specific bot session by ID."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_cred4@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    session_data = r.json()
    assert session_data["id"] == str(bot_session.id)
    assert session_data["status"] == BotSessionStatus.RUNNING.value

    # Limpa os dados criados para o teste
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_bot_session_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    """Test getting a non-existent bot session."""
    non_existent_id = uuid.uuid4()
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{non_existent_id}",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 404, f"Response: {r.text}"
    assert r.json() == {"detail": "Bot session not found"}


def test_start_bot_session(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test starting a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_cred5@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.STARTING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/start",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    session_data = r.json()
    assert session_data["id"] == str(bot_session.id)
    assert session_data["status"] == BotSessionStatus.RUNNING.value

    # Verificar se foi atualizado no banco de dados
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.RUNNING


def test_stop_bot_session(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test stopping a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_cred6@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/stop",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    session_data = r.json()
    assert session_data["id"] == str(bot_session.id)
    assert session_data["status"] == BotSessionStatus.COMPLETED.value

    # Verificar se foi atualizado no banco de dados
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.COMPLETED


def test_pause_bot_session(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test pausing a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_cred7@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/pause",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    session_data = r.json()
    assert session_data["id"] == str(bot_session.id)
    assert session_data["status"] == BotSessionStatus.PAUSED.value

    # Verificar se foi atualizado no banco de dados
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.PAUSED


def test_resume_bot_session(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test resuming a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_cred8@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.PAUSED,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/resume",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    session_data = r.json()
    assert session_data["id"] == str(bot_session.id)
    assert session_data["status"] == BotSessionStatus.RUNNING.value

    # Verificar se foi atualizado no banco de dados
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.RUNNING


def test_delete_bot_session(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_cred9@example.com", password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=user.id,
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.STOPPED,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    session_id = bot_session.id

    r = client.delete(
        f"{settings.API_V1_STR}/bots/sessions/{session_id}",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    assert r.json() == {"message": "Session deleted successfully"}

    # Verificar se foi excluído do banco de dados
    deleted_session = db.get(BotSession, session_id)
    assert deleted_session is not None
    assert deleted_session.is_deleted
