import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.bot import (
    BotSession,
    BotSessionStatus,
    Credentials,
    KubernetesPodStatus,
)
from app.models.core import User
from app.tests.utils.utils import random_email, random_lower_string


def get_user_from_token_header(db: Session, headers: dict[str, str]) -> User:
    """Extrai o usuário do banco a partir do token de autenticação."""
    # Obtém o email do usuário a partir do tipo de header fornecido
    if "Authorization" not in headers:
        raise ValueError("Não há token de autorização nos headers")
    
    # Olha para o email do usuário nos testes
    if settings.EMAIL_TEST_USER_SUBSCRIBER in headers.get("Authorization", ""):
        user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER_SUBSCRIBER)).first()
    elif settings.EMAIL_TEST_USER in headers.get("Authorization", ""):
        user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    elif settings.FIRST_SUPERUSER in headers.get("Authorization", ""):
        user = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    else:
        # Tenta encontrar algum usuário válido
        users = db.exec(select(User)).all()
        for user_candidate in users:
            if user_candidate.email in headers.get("Authorization", ""):
                user = user_candidate
                break
        else:
            # Se não encontrar nada, tenta usar o primeiro usuário disponível
            user = db.exec(select(User).limit(1)).first()
    
    if not user:
        raise ValueError("Usuário não encontrado para o token fornecido")
    
    return user


def test_get_all_active_sessions(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting all active bot sessions (admin only)."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, superuser_token_headers)
    
    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,  # Usando o ID do usuário real
        email="test_monitoring@example.com",
        password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)
    
    # Criar algumas sessões
    session1 = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        last_heartbeat_at=datetime.now(timezone.utc) - timedelta(minutes=15)  # Sessão sem heartbeat recente
    )
    db.add(session1)
    
    session2 = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        kubernetes_pod_status=KubernetesPodStatus.FAILED  # Sessão com pod falhado
    )
    db.add(session2)
    db.commit()
    
    r = client.get(
        f"{settings.API_V1_STR}/monitoring/sessions",
        headers=superuser_token_headers,
    )
    
    assert r.status_code == 200, f"Response: {r.text}"
    data = r.json()
    assert "total" in data
    assert "items" in data
    
    # Limpa os dados criados para o teste
    db.delete(session1)
    db.delete(session2)
    db.delete(credentials)
    db.commit()


def test_get_sessions_status_summary(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting sessions status summary (admin only)."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, superuser_token_headers)
    
    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,  # Usando o ID do usuário real
        email="test_monitoring_summary@example.com",
        password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)
    
    # Criar algumas sessões em diferentes estados
    session1 = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc)
    )
    db.add(session1)
    
    session2 = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.FAILED,
        created_at=datetime.now(timezone.utc),
        error_message="Connection error"
    )
    db.add(session2)
    
    session3 = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.COMPLETED,
        created_at=datetime.now(timezone.utc) - timedelta(days=2),
        finished_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db.add(session3)
    db.commit()
    
    r = client.get(
        f"{settings.API_V1_STR}/monitoring/sessions/status",
        headers=superuser_token_headers,
    )
    
    assert r.status_code == 200, f"Response: {r.text}"
    summary = r.json()
    
    assert "total_sessions" in summary
    assert "status_counts" in summary
    assert "recent_sessions" in summary
    assert "error_sessions" in summary
    assert "stalled_sessions" in summary
    assert "zombie_sessions" in summary
    assert "timestamp" in summary
    
    # Limpa os dados criados para o teste
    db.delete(session1)
    db.delete(session2)
    db.delete(session3)
    db.delete(credentials)
    db.commit()


def test_get_kubernetes_pods(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting Kubernetes pods status (admin only)."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, superuser_token_headers)
    
    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,  # Usando o ID do usuário real
        email="test_monitoring_pods@example.com",
        password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)
    
    # Criar algumas sessões com informações de pod
    session1 = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        kubernetes_pod_status=KubernetesPodStatus.RUNNING,
        kubernetes_pod_ip="10.0.0.1"
    )
    db.add(session1)
    
    session2 = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=200,
        status=BotSessionStatus.FAILED,
        created_at=datetime.now(timezone.utc),
        kubernetes_pod_status=KubernetesPodStatus.FAILED
    )
    db.add(session2)
    db.commit()
    
    r = client.get(
        f"{settings.API_V1_STR}/monitoring/kubernetes/pods",
        headers=superuser_token_headers,
    )
    
    assert r.status_code == 200, f"Response: {r.text}"
    pods_data = r.json()
    
    assert "total" in pods_data
    assert "items" in pods_data
    
    # Limpa os dados criados para o teste
    db.delete(session1)
    db.delete(session2)
    db.delete(credentials)
    db.commit()


def test_force_stop_session(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test force stopping a bot session (admin only)."""
    # Obtém o usuário a partir do token
    user = get_user_from_token_header(db, superuser_token_headers)
    
    # Criar credenciais para teste
    credentials = Credentials(
        user_id=user.id,  # Usando o ID do usuário real
        email="test_monitoring_stop@example.com",
        password="testpassword"
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)
    
    # Criar uma sessão para forçar a parada
    session = BotSession(
        user_id=user.id,  # Usando o ID do usuário real
        credentials_id=credentials.id,
        applies_limit=150,
        status=BotSessionStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        kubernetes_pod_status=KubernetesPodStatus.RUNNING
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    r = client.post(
        f"{settings.API_V1_STR}/monitoring/sessions/{session.id}/force-stop",
        headers=superuser_token_headers,
    )
    
    assert r.status_code == 200, f"Response: {r.text}"
    assert r.json() == {"message": "Bot session force stopped successfully"}
    
    # Verificar se o status do pod foi atualizado
    db.refresh(session)
    assert session.kubernetes_pod_status == KubernetesPodStatus.FAILED
    
    # Limpa os dados criados para o teste
    db.delete(session)
    db.delete(credentials)
    db.commit()


def test_force_stop_session_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test force stopping a non-existent bot session."""
    non_existent_id = uuid.uuid4()
    r = client.post(
        f"{settings.API_V1_STR}/monitoring/sessions/{non_existent_id}/force-stop",
        headers=superuser_token_headers,
    )
    
    assert r.status_code == 404, f"Response: {r.text}"
    assert r.json() == {"detail": "Bot session not found or could not be stopped"}


def test_monitoring_endpoints_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test that normal users can't access monitoring endpoints."""
    # Tentar acessar endpoint de sessões ativas
    r = client.get(
        f"{settings.API_V1_STR}/monitoring/sessions",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403, f"Response: {r.text}"
    
    # Tentar acessar endpoint de resumo de status
    r = client.get(
        f"{settings.API_V1_STR}/monitoring/sessions/status",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403, f"Response: {r.text}"
    
    # Tentar acessar endpoint de pods Kubernetes
    r = client.get(
        f"{settings.API_V1_STR}/monitoring/kubernetes/pods",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403, f"Response: {r.text}"
    
    # Tentar forçar parada de sessão
    non_existent_id = uuid.uuid4()
    r = client.post(
        f"{settings.API_V1_STR}/monitoring/sessions/{non_existent_id}/force-stop",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403, f"Response: {r.text}"
