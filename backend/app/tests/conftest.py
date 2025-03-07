from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.main import app
from app.tests.utils.user import (
    authentication_subscriber_token_from_email,
    authentication_token_from_email,
)
from app.tests.utils.utils import get_superuser_token_headers


@contextmanager
def get_test_db() -> Generator[Session, None, None]:
    """Fornece uma sessão isolada de teste que faz rollback ao final"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Fixture que fornece sessão de BD isolada para cada teste"""
    with get_test_db() as session:
        yield session


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient que usa a sessão de DB de teste"""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    # Aplica o override na aplicação
    from app.api.deps import get_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Remove o override após o teste
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(scope="function")
def normal_subscriber_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_subscriber_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER_SUBSCRIBER, db=db
    )
