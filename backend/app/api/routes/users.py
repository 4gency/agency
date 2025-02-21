import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import func, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.integrations.stripe import (
    cancel_subscription_recurring_payment,
    reactivate_subscription,
)
from app.models import crud
from app.models.core import (
    # Item,
    Message,
    Payment,
    PaymentPublic,
    PaymentsPublic,
    Subscription,
    SubscriptionPublic,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import (
    generate_new_account_email,
    send_email,
)

router = APIRouter()


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current one",
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )
    # statement = delete(Item).where(col(Item.owner_id) == current_user.id)
    # session.exec(statement)  # type: ignore
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user == current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )
    # statement = delete(Item).where(col(Item.owner_id) == user_id)
    # session.exec(statement)  # type: ignore
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


@router.get(
    "/me/subscriptions", response_model=list[SubscriptionPublic], tags=["subscriptions"]
)
def get_user_subscriptions(
    user: CurrentUser,
    only_active: bool | None = True,
) -> Any:
    """
    Get user subscription.
    """
    subscriptions: list[Subscription] = user.subscriptions
    if only_active:
        subscriptions = [s for s in subscriptions if s.is_active]
    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No subscriptions found"
        )
    return subscriptions


@router.get(
    "/{user_id}/subscriptions",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[SubscriptionPublic],
    tags=["subscriptions"],
)
def get_user_subscriptions_by_id(
    user_id: uuid.UUID,
    session: SessionDep,
    only_active: bool | None = True,
) -> Any:
    """
    Get user subscription by id.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    subscriptions: list[Subscription] = user.subscriptions
    if only_active:
        subscriptions = [s for s in subscriptions if s.is_active]
    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No subscriptions found"
        )
    return subscriptions


@router.delete(
    "/me/subscriptions/{subscription_id}/cancel",
    response_model=Message,
    tags=["subscriptions"],
)
def cancel_user_subscription(
    user: CurrentUser,
    subscription_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Cancel user subscription (recurring payment).
    """
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    if subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Subscription not found"
        )

    cancel_subscription_recurring_payment(
        session, subscription, cancel_at_period_end=True
    )

    return Message(message="Recurring payment cancelled successfully")


@router.post(
    "/me/subscriptions/{subscription_id}/reactivate",
    response_model=Message,
    tags=["subscriptions"],
)
def reactivate_user_subscription(
    user: CurrentUser,
    subscription_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Reactivate user subscription if still in 'cancel_at_period_end' window.
    """
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    if subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Subscription not found"
        )

    reactivate_subscription(session, subscription)

    return Message(message="Subscription reactivated successfully")


@router.delete(
    "/{user_id}/subscriptions/{subscription_id}/cancel",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    tags=["subscriptions"],
)
def cancel_user_subscription_by_id(
    user_id: uuid.UUID,
    subscription_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Cancel user subscription by id (recurring payment on Stripe).
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    if subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Subscription not found"
        )

    # Se já estiver desativada localmente, não há mais nada a fazer
    if not subscription.is_active:
        return Message(message="Subscription is already inactive")

    cancel_subscription_recurring_payment(
        session, subscription, cancel_at_period_end=True
    )

    return Message(
        message="Recurring payment cancelled successfully (will end at period end)"
    )


@router.post(
    "/{user_id}/subscriptions/{subscription_id}/reactivate",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    tags=["subscriptions"],
)
def reactivate_user_subscription_by_id(
    user_id: uuid.UUID,
    subscription_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Reactivate user subscription by id.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    if subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Subscription not found"
        )

    reactivate_subscription(session, subscription)

    return Message(message="Subscription reactivated successfully")


@router.get("/me/payments", response_model=PaymentsPublic, tags=["payments"])
def read_payments_by_current_user(
    user: CurrentUser, session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve payments for the current user.
    """
    count_statement = (
        select(func.count()).select_from(Payment).where(Payment.user_id == user.id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(Payment).where(Payment.user_id == user.id).offset(skip).limit(limit)
    )
    payments = session.exec(statement).all()
    payments_public = [PaymentPublic.model_validate(p) for p in payments]

    return PaymentsPublic(data=payments_public, count=count)


@router.get(
    "/{user_id}/payments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=PaymentsPublic,
    tags=["payments"],
)
def read_payments_by_user_id(
    user_id: uuid.UUID, session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve payments by user id.
    """
    count_statement = (
        select(func.count()).select_from(Payment).where(Payment.user_id == user_id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(Payment).where(Payment.user_id == user_id).offset(skip).limit(limit)
    )
    payments = session.exec(statement).all()
    payments_public = [PaymentPublic.model_validate(p) for p in payments]

    return PaymentsPublic(data=payments_public, count=count)
