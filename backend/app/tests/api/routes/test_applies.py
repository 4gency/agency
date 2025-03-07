import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.bot import (
    BotApply,
    BotApplyStatus,
    BotSession,
    BotSessionStatus,
    Credentials,
)
from app.tests.utils.user import get_user_from_token_header


def test_get_session_applies(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting applies for a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_applies@example.com", password="testpassword"
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

    # Criar algumas aplicações para a sessão
    apply1 = BotApply(
        bot_session_id=bot_session.id,
        status=BotApplyStatus.SUCCESS,
        job_title="Software Developer",
        company_name="TechCorp",
        job_url="https://example.com/job1",
        total_time=45,
        created_at=datetime.now(timezone.utc),
    )
    db.add(apply1)

    apply2 = BotApply(
        bot_session_id=bot_session.id,
        status=BotApplyStatus.FAILED,
        job_title="Senior Developer",
        company_name="MegaTech",
        job_url="https://example.com/job2",
        total_time=30,
        failed_reason="Form validation error",
        created_at=datetime.now(timezone.utc),
    )
    db.add(apply2)
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/applies",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    applies_data = r.json()
    assert "total" in applies_data
    assert "items" in applies_data
    assert len(applies_data["items"]) == 2
    assert applies_data["total"] == 2

    # Limpa os dados criados para o teste
    db.delete(apply1)
    db.delete(apply2)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_session_applies_with_filter(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting applies for a bot session with status filter."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,
        email="test_applies_filter@example.com",
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

    # Criar algumas aplicações para a sessão
    apply1 = BotApply(
        bot_session_id=bot_session.id,
        status=BotApplyStatus.SUCCESS,
        job_title="Software Developer",
        company_name="TechCorp",
        job_url="https://example.com/job1",
        total_time=45,
        created_at=datetime.now(timezone.utc),
    )
    db.add(apply1)

    apply2 = BotApply(
        bot_session_id=bot_session.id,
        status=BotApplyStatus.FAILED,
        job_title="Senior Developer",
        company_name="MegaTech",
        job_url="https://example.com/job2",
        total_time=30,
        failed_reason="Form validation error",
        created_at=datetime.now(timezone.utc),
    )
    db.add(apply2)
    db.commit()

    # Filtrar por status de aplicação (FAILED)
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/applies?status=failed",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    applies_data = r.json()
    assert "total" in applies_data
    assert "items" in applies_data

    # Imprimir dados para debug
    print(f"Response data: {applies_data}")
    print(f"Items count: {len(applies_data['items'])}")
    for i, apply in enumerate(applies_data["items"]):
        print(f"Item {i}: {apply['status']} - {apply['job_title']}")

    # Deve haver pelo menos um item na resposta
    assert len(applies_data["items"]) > 0, "Nenhum item retornado"

    # Verificar que pelo menos um item com status 'failed' está na resposta
    failed_items = [
        a for a in applies_data["items"] if a["status"] == BotApplyStatus.FAILED.value
    ]
    assert len(failed_items) > 0, "Nenhum item com status 'failed' encontrado"

    # Limpa os dados criados para o teste
    db.delete(apply1)
    db.delete(apply2)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_session_applies_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    """Test getting applies for a non-existent bot session."""
    non_existent_id = uuid.uuid4()
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{non_existent_id}/applies",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 404, f"Response: {r.text}"
    assert r.json() == {"detail": "Bot session not found"}


def test_get_apply_details(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting details of a specific apply."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id, email="test_apply_details@example.com", password="testpassword"
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

    # Criar uma aplicação para a sessão
    apply = BotApply(
        bot_session_id=bot_session.id,
        status=BotApplyStatus.SUCCESS,
        job_title="Software Developer",
        company_name="TechCorp",
        job_url="https://example.com/job1",
        total_time=45,
        created_at=datetime.now(timezone.utc),
    )
    db.add(apply)
    db.commit()
    db.refresh(apply)

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/applies/{apply.id}",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    apply_data = r.json()
    assert apply_data["id"] == apply.id
    assert apply_data["job_title"] == "Software Developer"
    assert apply_data["company_name"] == "TechCorp"

    # Limpa os dados criados para o teste
    db.delete(apply)
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_apply_details_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting details of a non-existent apply."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,
        email="test_apply_notfound@example.com",
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

    # ID inexistente
    non_existent_id = 99999

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/applies/{non_existent_id}",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 404, f"Response: {r.text}"
    assert r.json() == {"detail": "Application not found"}

    # Limpa os dados criados para o teste
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_applies_summary(
    client: TestClient, normal_subscriber_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting a summary of applies for a bot session."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, normal_subscriber_token_headers, client)

    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,
        email="test_applies_summary@example.com",
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

    # Criar várias aplicações para a sessão
    # 5 aplicações bem-sucedidas
    success_applies = []
    for i in range(5):
        apply = BotApply(
            bot_session_id=bot_session.id,
            status=BotApplyStatus.SUCCESS,
            job_title=f"Job {i}",
            company_name="TechCorp",
            job_url=f"https://example.com/job{i}",
            total_time=30,
            created_at=datetime.now(timezone.utc),
        )
        db.add(apply)
        success_applies.append(apply)

    # 3 aplicações com falha
    failed_applies = []
    for i in range(3):
        apply = BotApply(
            bot_session_id=bot_session.id,
            status=BotApplyStatus.FAILED,
            job_title=f"Failed Job {i}",
            company_name="MegaTech",
            job_url=f"https://example.com/failedjob{i}",
            total_time=20,
            failed_reason="Error applying",
            created_at=datetime.now(timezone.utc),
        )
        db.add(apply)
        failed_applies.append(apply)
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{bot_session.id}/applies/summary",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 200, f"Response: {r.text}"
    summary = r.json()
    assert "total_applies" in summary
    assert "by_status" in summary
    assert "by_company" in summary
    assert "total_time_seconds" in summary
    assert "latest_applies" in summary

    # Imprimir o conteúdo do summary para depuração
    print(f"Summary content: {summary}")
    print(f"Status counts: {summary['by_status']}")
    print(f"Success count: {summary['by_status'].get('success', 'not found')}")

    assert summary["by_status"]["success"] == 5
    assert summary["by_status"]["failed"] == 3
    assert summary["by_company"]["TechCorp"] == 5
    assert summary["by_company"]["MegaTech"] == 3
    assert summary["total_time_seconds"] == (5 * 30) + (3 * 20)  # 5 * 30s + 3 * 20s
    assert (
        len(summary["latest_applies"]) <= 10
    )  # Retorna até 10 aplicações mais recentes

    # Limpa os dados criados para o teste
    # Primeiro remove aplicações
    for apply in success_applies + failed_applies:
        db.delete(apply)
    db.commit()

    # Depois remove a sessão e credenciais
    db.delete(bot_session)
    db.delete(credentials)
    db.commit()


def test_get_applies_summary_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    """Test getting a summary of applies for a non-existent bot session."""
    non_existent_id = uuid.uuid4()
    r = client.get(
        f"{settings.API_V1_STR}/bots/sessions/{non_existent_id}/applies/summary",
        headers=normal_subscriber_token_headers,
    )

    assert r.status_code == 404, f"Response: {r.text}"
    assert r.json() == {"detail": "Bot session not found"}
