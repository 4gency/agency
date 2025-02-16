import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, NosqlSessionDep
from app.models.crud import config as config_crud
from app.models.preference import ConfigPublic
from app.models.resume import PlainTextResumePublic

router = APIRouter()


@router.get("/{subscription_id}/job-preferences", response_model=ConfigPublic)
def get_config(
    current_user: CurrentUser,  # noqa
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
) -> Any:
    config = config_crud.get_config(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Config not found"
        )

    return ConfigPublic(**config.model_dump())


@router.get("/{subscription_id}/resume", response_model=PlainTextResumePublic)
def get_plain_text_resume(
    current_user: CurrentUser,  # noqa
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
) -> Any:
    resume = config_crud.get_resume(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Resume not found"
        )

    return PlainTextResumePublic(**resume.model_dump())


@router.patch("/{subscription_id}/job-preferences", status_code=status.HTTP_200_OK)
def update_config(
    *,
    current_user: CurrentUser,  # noqa
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
    config_in: ConfigPublic,
) -> Any:
    """
    Update config.
    """
    config = config_crud.get_config(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Config not found"
        )

    if config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this config",
        )

    config_crud.update_config(
        session=nosql_session,
        config_instance=config,
        config_in=config_in,
    )


@router.patch(
    "/{subscription_id}/resume", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
)
def update_plain_text_resume(
    *,
    current_user: CurrentUser,  # noqa
    subscription_id: uuid.UUID,
    nosql_session: NosqlSessionDep,
    resume_in: PlainTextResumePublic,
) -> Any:
    """
    Update plain text resume.
    """
    resume = config_crud.get_resume(
        session=nosql_session,
        subscription_id=str(subscription_id),
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Resume not found"
        )

    if resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this resume",
        )

    config_crud.update_resume(
        session=nosql_session,
        resume_instance=resume,
        resume_in=resume_in,
    )
