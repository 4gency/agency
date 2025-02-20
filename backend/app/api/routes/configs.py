import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import NosqlSessionDep, SessionDep, get_current_user
from app.models.core import ErrorMessage
from app.models.crud import config as config_crud
from app.models.crud import subscription as subscription_crud
from app.models.preference import ConfigPublic
from app.models.resume import PlainTextResumePublic

router = APIRouter()


@router.get(
    "/{subscription_id}/job-preferences",
    dependencies=[Depends(get_current_user)],
    response_model=ConfigPublic,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization error",
            "content": {
                "application/json": {
                    "examples": {
                        "could_not_validate": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        }
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
                        },
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive user",
                            "value": {"detail": "Inactive user"},
                        },
                    }
                }
            },
        },
    },
)
def get_config(
    *,
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
    session: SessionDep,
) -> Any:
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    config = config_crud.get_config(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not config:
        config = config_crud.create_subscription_default_config(
            subscription_id=str(subscription_id),
            user_id=str(subscription.user_id),
            nosql_session=nosql_session,
        )

    return ConfigPublic(**config.model_dump())


@router.get(
    "/{subscription_id}/resume",
    dependencies=[Depends(get_current_user)],
    response_model=PlainTextResumePublic,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization error",
            "content": {
                "application/json": {
                    "examples": {
                        "could_not_validate": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        }
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
                        },
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive user",
                            "value": {"detail": "Inactive user"},
                        },
                    }
                }
            },
        },
    },
)
def get_plain_text_resume(
    *,
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
    session: SessionDep,
) -> Any:
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    resume = config_crud.get_resume(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not resume:
        resume = config_crud.create_subscription_default_resume(
            subscription_id=str(subscription_id),
            user_id=str(subscription.user_id),
            nosql_session=nosql_session,
        )

    return PlainTextResumePublic(**resume.model_dump())


@router.patch(
    "/{subscription_id}/job-preferences",
    dependencies=[Depends(get_current_user)],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization error",
            "content": {
                "application/json": {
                    "examples": {
                        "could_not_validate": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        }
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
                        },
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive user",
                            "value": {"detail": "Inactive user"},
                        },
                    }
                }
            },
        },
    },
)
def update_config(
    *,
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
    config_in: ConfigPublic,
    session: SessionDep,
) -> Any:
    """
    Update config.
    """
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    config = config_crud.get_config(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not config:
        config = config_crud.create_subscription_default_config(
            subscription_id=str(subscription_id),
            user_id=str(subscription.user_id),
            nosql_session=nosql_session,
        )

    config_crud.update_config(
        session=nosql_session,
        config_instance=config,
        config_in=config_in,
    )


@router.patch(
    "/{subscription_id}/resume",
    dependencies=[Depends(get_current_user)],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        403: {
            "model": ErrorMessage,
            "description": "Authorization error",
            "content": {
                "application/json": {
                    "examples": {
                        "could_not_validate": {
                            "summary": "Could not validate credentials",
                            "value": {"detail": "Could not validate credentials"},
                        }
                    }
                }
            },
        },
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
                        },
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User not found"},
                        },
                        "inactive_user": {
                            "summary": "Inactive user",
                            "value": {"detail": "Inactive user"},
                        },
                    }
                }
            },
        },
    },
)
def update_plain_text_resume(
    *,
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
    resume_in: PlainTextResumePublic,
    session: SessionDep,
) -> Any:
    """
    Update plain text resume.
    """
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    resume = config_crud.get_resume(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not resume:
        resume = config_crud.create_subscription_default_resume(
            subscription_id=str(subscription_id),
            user_id=str(subscription.user_id),
            nosql_session=nosql_session,
        )

    config_crud.update_resume(
        session=nosql_session,
        resume_instance=resume,
        resume_in=resume_in,
    )
