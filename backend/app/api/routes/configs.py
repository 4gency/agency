import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, NosqlSessionDep, SessionDep
from app.models.core import ErrorMessage
from app.models.crud import config as config_crud
from app.models.crud import subscription as subscription_crud
from app.models.preference import ConfigPublic
from app.models.resume import PlainTextResumePublic

router = APIRouter()


@router.get(
    "/{subscription_id}/job-preferences",
    response_model=ConfigPublic,
    responses={
        401: {
            "model": "ErrorMessage",
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Not authenticated",
                            "value": {"detail": "Not authenticated"},
                        }
                    }
                }
            },
        },
        403: {
            "model": "ErrorMessage",
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authorized": {
                            "summary": "Not authorized",
                            "value": {"detail": "Not authorized to access this subscription"},
                        }
                    }
                }
            },
        },
        404: {
            "model": "ErrorMessage",
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
                        },
                        "config_not_found": {
                            "summary": "Config not found",
                            "value": {"detail": "Config not found"},
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
    user: CurrentUser,
) -> Any:
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    if subscription.user_id != user.id and not user.is_superuser:
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
    response_model=PlainTextResumePublic,
    responses={
        401: {
            "model": "ErrorMessage",
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Not authenticated",
                            "value": {"detail": "Not authenticated"},
                        }
                    }
                }
            },
        },
        403: {
            "model": "ErrorMessage",
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authorized": {
                            "summary": "Not authorized",
                            "value": {"detail": "Not authorized to access this subscription"},
                        }
                    }
                }
            },
        },
        404: {
            "model": "ErrorMessage",
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
                        },
                        "resume_not_found": {
                            "summary": "Resume not found",
                            "value": {"detail": "Resume not found"},
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
    user: CurrentUser,
) -> Any:
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    if subscription.user_id != user.id and not user.is_superuser:
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
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"schema": {}}},
        },
        401: {
            "model": "ErrorMessage",
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Not authenticated",
                            "value": {"detail": "Not authenticated"},
                        }
                    }
                }
            },
        },
        403: {
            "model": "ErrorMessage",
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authorized": {
                            "summary": "Not authorized",
                            "value": {"detail": "Not authorized to access this subscription"},
                        }
                    }
                }
            },
        },
        404: {
            "model": "ErrorMessage",
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
                        },
                        "config_not_found": {
                            "summary": "Config not found",
                            "value": {"detail": "Config not found"},
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
    user: CurrentUser,
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

    if subscription.user_id != user.id and not user.is_superuser:
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
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        500: {
            "description": "Successful Response",
            "content": {"application/json": {"schema": {}}},
        },
        401: {
            "model": "ErrorMessage",
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Not authenticated",
                            "value": {"detail": "Not authenticated"},
                        }
                    }
                }
            },
        },
        403: {
            "model": "ErrorMessage",
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authorized": {
                            "summary": "Not authorized",
                            "value": {"detail": "Not authorized to access this subscription"},
                        }
                    }
                }
            },
        },
        404: {
            "model": "ErrorMessage",
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
                        "subscription_not_found": {
                            "summary": "Subscription not found",
                            "value": {"detail": "Subscription not found"},
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
    user: CurrentUser,
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

    if subscription.user_id != user.id and not user.is_superuser:
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
