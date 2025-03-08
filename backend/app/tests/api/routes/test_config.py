import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.core import (
    SubscriptionCreate,
    SubscriptionMetric,
    SubscriptionPlan,
    SubscriptionPlanCreate,
    User,
)
from app.models.crud import subscription as subscription_crud
from app.models.preference import ConfigPublic
from app.models.resume import PlainTextResumePublic
from app.tests.utils.user import (
    authentication_subscriber_token_from_email,
    create_random_user,
)

PREFERENCES_PREFIX = f"{settings.API_V1_STR}/configs"


@pytest.fixture
def normal_user(db: Session) -> User:
    user = create_random_user(db)
    user.is_subscriber = True
    db.commit()
    return user


@pytest.fixture
def subscription_plan(db: Session) -> SubscriptionPlan:
    plan = SubscriptionPlanCreate(name="Test Plan", price=99.99)
    return subscription_crud.create_subscription_plan(
        session=db, subscription_plan_create=plan
    )


@pytest.fixture
def subscription_in(
    normal_user: User, subscription_plan: SubscriptionPlan
) -> SubscriptionCreate:
    return SubscriptionCreate(
        user_id=normal_user.id,
        subscription_plan_id=subscription_plan.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
        metric_type=SubscriptionMetric.MONTH,
        metric_status=1,
    )


def test_get_job_preferences_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    url = f"{PREFERENCES_PREFIX}/job-preferences"
    response = client.get(url, headers=normal_subscriber_token_headers)
    assert response.status_code == 200
    data = response.json()
    for field in ConfigPublic.model_fields:
        assert field in data


def test_get_job_preferences_creates_default_if_missing(
    client: TestClient,
    db: Session,
    subscription_in: SubscriptionCreate,
) -> None:
    subscription = subscription_crud.create_subscription(
        session=db, subscription_create=subscription_in
    )
    headers = authentication_subscriber_token_from_email(
        client=client, email=subscription.user.email, db=db
    )
    url = f"{PREFERENCES_PREFIX}/job-preferences"
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    data = response.json()
    for field in ConfigPublic.model_fields:
        assert field in data


def test_update_job_preferences_creates_default_if_missing(
    client: TestClient,
    db: Session,
    subscription_in: SubscriptionCreate,
) -> None:
    subscription = subscription_crud.create_subscription(
        session=db, subscription_create=subscription_in
    )
    headers = authentication_subscriber_token_from_email(
        client=client, email=subscription.user.email, db=db
    )
    url = f"{PREFERENCES_PREFIX}/job-preferences"
    update_data = {
        "remote": False,
        "hybrid": True,
        "onsite": False,
        "positions": ["DevOps", "Tester"],
        "locations": ["Canada"],
    }
    response = client.patch(url, headers=headers, json=update_data)
    assert response.status_code == 202

    get_response = client.get(url, headers=headers)
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["positions"] == ["DevOps", "Tester"]
    assert data["locations"] == ["Canada"]


def test_update_job_preferences_existing_config(
    client: TestClient,
    db: Session,
    subscription_in: SubscriptionCreate,
) -> None:
    subscription = subscription_crud.create_subscription(
        session=db, subscription_create=subscription_in
    )
    headers = authentication_subscriber_token_from_email(
        client=client, email=subscription.user.email, db=db
    )
    get_url = f"{PREFERENCES_PREFIX}/job-preferences"
    client.get(get_url, headers=headers)

    patch_url = f"{PREFERENCES_PREFIX}/job-preferences"
    update_data = {
        "remote": True,
        "hybrid": False,
        "onsite": True,
        "positions": ["QA"],
        "company_blacklist": ["AcmeInc"],
    }
    response = client.patch(patch_url, headers=headers, json=update_data)
    assert response.status_code == 202

    get_response = client.get(get_url, headers=headers)
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["remote"] is True
    assert data["hybrid"] is False
    assert data["onsite"] is True
    assert data["positions"] == ["QA"]
    assert data["company_blacklist"] == ["AcmeInc"]


def test_get_resume_not_found(
    client: TestClient, normal_subscriber_token_headers: dict[str, str]
) -> None:
    url = f"{PREFERENCES_PREFIX}/resume"
    response = client.get(url, headers=normal_subscriber_token_headers)
    assert response.status_code == 200
    data = response.json()
    for field in PlainTextResumePublic.model_fields:
        assert field in data


def test_get_resume_creates_default_if_missing(
    client: TestClient,
    db: Session,
    subscription_in: SubscriptionCreate,
) -> None:
    subscription = subscription_crud.create_subscription(
        session=db, subscription_create=subscription_in
    )
    headers = authentication_subscriber_token_from_email(
        client=client, email=subscription.user.email, db=db
    )
    url = f"{PREFERENCES_PREFIX}/resume"
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    data = response.json()
    for field in PlainTextResumePublic.model_fields:
        assert field in data


def test_update_resume_creates_default_if_missing(
    client: TestClient,
    db: Session,
    subscription_in: SubscriptionCreate,
) -> None:
    subscription = subscription_crud.create_subscription(
        session=db, subscription_create=subscription_in
    )
    headers = authentication_subscriber_token_from_email(
        client=client, email=subscription.user.email, db=db
    )
    url = f"{PREFERENCES_PREFIX}/resume"
    update_data = {"interests": ["Music", "Traveling"]}
    response = client.patch(url, headers=headers, json=update_data)
    assert response.status_code == 202

    get_response = client.get(url, headers=headers)
    assert get_response.status_code == 200
    data = get_response.json()
    for field in update_data:
        assert data[field] == update_data[field]


def test_update_resume_existing_document(
    client: TestClient,
    db: Session,
    subscription_in: SubscriptionCreate,
) -> None:
    subscription = subscription_crud.create_subscription(
        session=db, subscription_create=subscription_in
    )
    headers = authentication_subscriber_token_from_email(
        client=client, email=subscription.user.email, db=db
    )
    get_url = f"{PREFERENCES_PREFIX}/resume"
    client.get(get_url, headers=headers)

    patch_url = f"{PREFERENCES_PREFIX}/resume"
    update_data = {
        "interests": ["Chess", "AI"],
    }
    response = client.patch(patch_url, headers=headers, json=update_data)
    assert response.status_code == 202

    get_response = client.get(get_url, headers=headers)
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["interests"] == ["Chess", "AI"]
