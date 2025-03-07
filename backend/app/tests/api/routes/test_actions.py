import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.bot import (
    BotSession,
    BotSessionStatus,
    BotUserAction,
    Credentials,
    UserActionType,
)
from app.tests.utils.user import get_user_from_token_header


def test_get_session_actions(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting actions for a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_actions@example.com", password="testpassword"
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

    # Criar algumas ações para a sessão
    action1 = BotUserAction(
        bot_session_id=bot_session.id,
        action_type=UserActionType.PROVIDE_2FA,
        description="Please provide 2FA code",
        is_completed=False,
        requested_at=datetime.now(timezone.utc),
    )
    db.add(action1)

    action2 = BotUserAction(
        bot_session_id=bot_session.id,
        action_type=UserActionType.SOLVE_CAPTCHA,
        description="Please solve CAPTCHA",
        is_completed=True,
        user_input="solved",
        requested_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(action2)
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/actions?include_completed=true",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    actions_data = r.json()
    assert "total" in actions_data
    assert "items" in actions_data
    assert len(actions_data["items"]) >= 2

    # Limpa os dados criados para o teste
    db.delete(action1)
    db.delete(action2)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_session_actions_with_filter(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting actions for a bot session with filters."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,
        email="test_actions_filter@example.com",
        password="testpassword",
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

    # Criar algumas ações para a sessão
    action1 = BotUserAction(
        bot_session_id=bot_session.id,
        action_type=UserActionType.PROVIDE_2FA,
        description="Please provide 2FA code",
        is_completed=False,
        requested_at=datetime.now(timezone.utc),
    )
    db.add(action1)

    action2 = BotUserAction(
        bot_session_id=bot_session.id,
        action_type=UserActionType.SOLVE_CAPTCHA,
        description="Please solve CAPTCHA",
        is_completed=True,
        user_input="solved",
        requested_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(action2)
    db.commit()

    # Filtrar para incluir apenas ações completas
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/actions?include_completed=true",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    actions_data = r.json()
    assert "total" in actions_data
    assert "items" in actions_data

    # Limpa os dados criados para o teste
    db.delete(action1)
    db.delete(action2)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_session_actions_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    """Test getting actions for a non-existent bot session."""
    non_existent_id = uuid.uuid4()
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{non_existent_id}/actions",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 404, f"Response: {r.text}"
    assert r.json() == {"detail": "Bot session not found"}


def test_complete_action(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test completing a user action."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,
        email="test_complete_action@example.com",
        password="testpassword",
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

    # Criar uma ação para completar
    action = BotUserAction(
        bot_session_id=bot_session.id,
        action_type=UserActionType.PROVIDE_2FA,
        description="Please provide 2FA code",
        is_completed=False,
        requested_at=datetime.now(timezone.utc),
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    data = {
        "user_input": "123456"  # Código 2FA de exemplo
    }

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/actions/{action.id}/complete",
        headers=normal_subscriber_token_headers,
        json=data,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    assert r.json() == {"message": "Action completed successfully"}

    # Verificar se a ação foi atualizada no banco de dados
    db.refresh(action)
    assert action.is_completed is True
    assert action.user_input == "123456"
    assert action.completed_at is not None

    # Limpa os dados criados para o teste
    db.delete(action)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_complete_action_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test completing a non-existent action."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,
        email="test_complete_not_found@example.com",
        password="testpassword",
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

    non_existent_id = uuid.uuid4()
    data = {"user_input": "123456"}

    r = client.post(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/actions/{non_existent_id}/complete",
        headers=normal_subscriber_token_headers,
        json=data,
    )

    assert r.status_code == 404, f"Response: {r.text}"
    assert r.json() == {"detail": "User action not found"}

    # Limpa os dados criados para o teste
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()
