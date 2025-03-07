import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.bot import Credentials
from app.tests.utils.utils import random_email, random_lower_string


def test_get_user_credentials(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test getting all credentials for the current user."""
    r = client.get(
        f"{settings.API_V1_STR}/credentials/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_create_credentials(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating new credentials."""
    email = random_email()
    password = random_lower_string()

    data = {"email": email, "password": password}

    r = client.post(
        f"{settings.API_V1_STR}/credentials/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    created_credentials = r.json()
    assert "id" in created_credentials
    assert created_credentials["email"] != email  # Deve retornar a versão ofuscada

    # Verifique se foi criado no banco de dados
    cred_id = uuid.UUID(created_credentials["id"])
    credentials_in_db = db.get(Credentials, cred_id)
    assert credentials_in_db is not None
    assert credentials_in_db.email == email

    # Limpa as credenciais criadas para o teste
    db.delete(credentials_in_db)
    db.commit()


def test_update_credentials(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating credentials."""
    # Criar credenciais para atualizar
    credentials = Credentials(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        email="update_test@example.com",
        password="original_password",
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    # Novos dados
    new_email = random_email()
    new_password = random_lower_string()

    data = {"email": new_email, "password": new_password}

    r = client.put(
        f"{settings.API_V1_STR}/credentials/{credentials.id}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    updated_credentials = r.json()
    assert updated_credentials["id"] == str(credentials.id)

    # Verifique se foi atualizado no banco de dados
    db.refresh(credentials)
    assert credentials.email == new_email

    # Limpa as credenciais criadas para o teste
    db.delete(credentials)
    db.commit()


def test_update_credentials_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test updating non-existent credentials."""
    non_existent_id = uuid.uuid4()

    data = {"email": random_email(), "password": random_lower_string()}

    r = client.put(
        f"{settings.API_V1_STR}/credentials/{non_existent_id}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 404
    assert r.json() == {"detail": "Credentials not found"}


def test_delete_credentials(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting credentials."""
    # Criar credenciais para excluir
    credentials = Credentials(
        user_id=uuid.uuid4(),  # Será substituído pelo ID real do usuário
        email="delete_test@example.com",
        password="delete_password",
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    credentials_id = credentials.id

    r = client.delete(
        f"{settings.API_V1_STR}/credentials/{credentials_id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert r.json() == {"message": "Credentials deleted successfully"}

    # Verifique se foi excluído do banco de dados
    deleted_credentials = db.get(Credentials, credentials_id)
    assert deleted_credentials is None


def test_delete_credentials_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test deleting non-existent credentials."""
    non_existent_id = uuid.uuid4()

    r = client.delete(
        f"{settings.API_V1_STR}/credentials/{non_existent_id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404
    assert r.json() == {"detail": "Credentials not found"}
