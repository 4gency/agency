from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models.core import (
    CheckoutSession,
    Payment,
    Subscription,
    SubscriptionPlan,
    SubscriptionPlanBenefit,
    User,
)
from app.tests.utils.user import (
    authentication_subscriber_token_from_email,
    authentication_token_from_email,
)
from app.tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(Payment)
        session.execute(statement)
        statement = delete(Subscription)
        session.execute(statement)
        statement = delete(CheckoutSession)
        session.execute(statement)
        statement = delete(SubscriptionPlanBenefit)
        session.execute(statement)
        statement = delete(SubscriptionPlan)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(scope="module")
def normal_subscriber_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_subscriber_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER_SUBSCRIBER, db=db
    )
