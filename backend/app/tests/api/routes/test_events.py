import json
import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.bot import BotEvent, BotSession, BotSessionStatus, Credentials


def test_get_session_events(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting events for a bot session."""
    # Criar credenciais para teste
    credentials = Credentials(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        email="test_events@example.com",
        password="testpassword",
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    # Criar alguns eventos para a sessão
    event1 = BotEvent(
        bot_session_id=bot_session.id,
        type="system",
        message="Bot session started",
        severity="info",
        created_at=datetime.now(timezone.utc),
    )
    db.add(event1)

    event2 = BotEvent(
        bot_session_id=bot_session.id,
        type="error",
        message="Connection error",
        severity="error",
        details=json.dumps({"error_code": "E1001"}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(event2)
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/events",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200
    events_data = r.json()
    assert "total" in events_data
    assert "items" in events_data
    assert len(events_data["items"]) >= 2

    # Limpa os dados criados para o teste
    db.delete(event1)
    db.delete(event2)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_session_events_with_filter(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting events for a bot session with type filter."""
    # Criar credenciais para teste
    credentials = Credentials(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        email="test_events_filter@example.com",
        password="testpassword",
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    # Criar alguns eventos para a sessão
    event1 = BotEvent(
        bot_session_id=bot_session.id,
        type="system",
        message="Bot session started",
        severity="info",
        created_at=datetime.now(timezone.utc),
    )
    db.add(event1)

    event2 = BotEvent(
        bot_session_id=bot_session.id,
        type="error",
        message="Connection error",
        severity="error",
        details=json.dumps({"error_code": "E1001"}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(event2)
    db.commit()

    # Filtrar por tipo de evento
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/events?event_type=error",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200
    events_data = r.json()
    assert "total" in events_data
    assert "items" in events_data

    # Deve retornar apenas eventos do tipo error
    for event in events_data["items"]:
        assert event["type"] == "error"

    # Limpa os dados criados para o teste
    db.delete(event1)
    db.delete(event2)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_session_events_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    """Test getting events for a non-existent bot session."""
    non_existent_id = uuid.uuid4()
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{non_existent_id}/events",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 404
    assert r.json() == {"detail": "Bot session not found"}


def test_get_session_events_summary(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting a summary of events for a bot session."""
    # Criar credenciais para teste
    credentials = Credentials(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        email="test_events_summary@example.com",
        password="testpassword",
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Criar uma sessão para o usuário
    bot_session = BotSession(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bot_session)
    db.commit()
    db.refresh(bot_session)

    # Criar vários eventos para a sessão
    for i in range(5):
        event = BotEvent(
            bot_session_id=bot_session.id,
            type="system",
            message=f"System event {i}",
            severity="info",
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)

    for i in range(3):
        event = BotEvent(
            bot_session_id=bot_session.id,
            type="error",
            message=f"Error event {i}",
            severity="error",
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/events/summary",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200
    summary = r.json()
    assert "total_events" in summary
    assert "by_type" in summary
    assert "by_severity" in summary
    assert "latest_events" in summary

    assert summary["by_type"]["system"] == 5
    assert summary["by_type"]["error"] == 3
    assert summary["by_severity"]["info"] == 5
    assert summary["by_severity"]["error"] == 3
    assert len(summary["latest_events"]) <= 10  # Retorna até 10 eventos mais recentes

    # Limpa os dados criados para o teste
    # Primeiro remove eventos
    db.exec(f"DELETE FROM bot_events WHERE bot_session_id = '{bot_session.id}'")
    db.commit()
    # Depois remove a sessão e credenciais
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_session_events_summary_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    """Test getting a summary of events for a non-existent bot session."""
    non_existent_id = uuid.uuid4()
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{non_existent_id}/events/summary",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 404
    assert r.json() == {"detail": "Bot session not found"}
