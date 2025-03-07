import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.bot import BotSession, BotSessionStatus, BotStyleChoice, Credentials
from app.tests.utils.user import get_user_from_token_header


def test_create_bot_session(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a bot session as a subscriber."""
    # Primeiro, obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

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
    assert created_session["status"] == BotSessionStatus.STARTING.value

    # Verificar se foi realmente criado no banco de dados
    session_in_db = db.get(BotSession, uuid.UUID(created_session["id"]))
    assert session_in_db is not None
    assert session_in_db.status == BotSessionStatus.STARTING
    assert session_in_db.applies_limit == 100
    assert session_in_db.style == BotStyleChoice.DEFAULT
    assert session_in_db.user_id == user.id
    assert session_in_db.credentials_id == credentials.id


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
    assert session_data["status"] == BotSessionStatus.STOPPING.value

    # Verificar se foi atualizado no banco de dados
    db.refresh(bot_session)
    assert bot_session.status == BotSessionStatus.STOPPING


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
    assert r.json() == {"message": "Bot session deleted successfully"}

    # Verificar se foi excluído do banco de dados
    deleted_session = db.get(BotSession, session_id)
    assert deleted_session is None
