from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.models.core import ErrorMessage
from app.models.crud import config as config_crud
from app.models.preference import ConfigPublic
from app.models.resume import PlainTextResumePublic

router = APIRouter()


@router.get(
    "/job-preferences",
    response_model=ConfigPublic,
    responses={
        401: {
            "model": ErrorMessage,
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
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
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
    session: SessionDep,
    user: CurrentUser,
) -> Any:
    config = config_crud.get_config(
        session=session,
        user_id=user.id,
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        )

    return ConfigPublic(**config.model_dump())


@router.get(
    "/resume",
    response_model=PlainTextResumePublic,
    responses={
        401: {
            "model": ErrorMessage,
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
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
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
    session: SessionDep,
    user: CurrentUser,
) -> Any:
    resume = config_crud.get_resume(
        session=session,
        user_id=user.id,
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
        )

    return PlainTextResumePublic(**resume.model_dump())


@router.patch(
    "/job-preferences",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"schema": {}}},
        },
        401: {
            "model": ErrorMessage,
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
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
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
    config_in: ConfigPublic,
    session: SessionDep,
    user: CurrentUser,
) -> Any:
    config = config_crud.get_config(
        session=session,
        user_id=user.id,
    )

    if not config:
        config = config_crud.create_user_default_config(
            user_id=user.id,
            session=session,
        )

    config_crud.update_config(
        session=session,
        config_instance=config,
        config_in=config_in,
    )

    return {"status": "Config updated"}


@router.patch(
    "/resume",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"schema": {}}},
        },
        401: {
            "model": ErrorMessage,
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
        404: {
            "model": ErrorMessage,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "examples": {
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
def update_plain_text_resume(
    *,
    resume_in: PlainTextResumePublic,
    session: SessionDep,
    user: CurrentUser,
) -> Any:
    resume = config_crud.get_resume(
        session=session,
        user_id=user.id,
    )

    if not resume:
        resume = config_crud.create_user_default_resume(
            user_id=user.id,
            session=session,
        )

    config_crud.update_resume(
        session=session,
        resume_instance=resume,
        resume_in=resume_in,
    )

    return {"status": "Resume updated"}
