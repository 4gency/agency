from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, NosqlSessionDep
from app.crud import config as config_crud
from app.models.preference import ConfigPublic
from app.models.resume import PlainTextResumePublic

router = APIRouter()


@router.get("/job-preferences", response_model=ConfigPublic)
def get_config(current_user: CurrentUser, nosql_session: NosqlSessionDep):
    config = config_crud.get_config(
        session=nosql_session,
        user_id=str(current_user.id),
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Config not found")

    return ConfigPublic(**config.model_dump())


@router.get("/resume", response_model=PlainTextResumePublic)
def get_plain_text_resume(current_user: CurrentUser, nosql_session: NosqlSessionDep):
    resume = config_crud.get_resume(
        session=nosql_session,
        user_id=str(current_user.id),
    )

    if not resume:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Resume not found")

    return PlainTextResumePublic(**resume.model_dump())


@router.patch("/job-preferences", status_code=status.HTTP_200_OK)
def update_config(
    *,
    current_user: CurrentUser,
    nosql_session: NosqlSessionDep,
    config_in: ConfigPublic,
) -> Any:
    """
    Update config.
    """
    config = config_crud.get_config(
        session=nosql_session,
        user_id=str(current_user.id),
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Config not found")

    update_dict = config_in.model_dump(exclude_unset=True)
    config_crud.update_config(
        session=nosql_session,
        config_instance=config,
        new_config_data=update_dict,
    )


@router.patch("/resume", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
def update_plain_text_resume(
    *,
    current_user: CurrentUser,
    nosql_session: NosqlSessionDep,
    resume_in: PlainTextResumePublic,
) -> Any:
    """
    Update plain text resume.
    """
    resume = config_crud.get_resume(
        session=nosql_session,
        user_id=str(current_user.id),
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Resume not found"
        )

    update_dict = resume_in.model_dump(exclude_unset=True)
    config_crud.update_resume(
        session=nosql_session,
        resume_instance=resume,
        new_resume_data=update_dict,
    )
