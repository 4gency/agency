from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api import deps
from app.models.bot import BotApply, BotApplyStatus
from app.models.core import ErrorMessage, Message, User
from app.models.preference import generate_config_yaml
from app.models.resume import generate_plain_text_resume_yaml


class BotConfigResponse(BaseModel):
    """Response model for bot configuration"""

    user_config: str
    user_resume: str


class BotApplyCreate(BaseModel):
    """Request model for creating a new apply record"""

    status: BotApplyStatus = BotApplyStatus.SUCCESS
    total_time: int = 0
    job_title: str | None = None
    job_url: str | None = None
    company_name: str | None = None
    failed_reason: str | None = None


router = APIRouter()


@router.post(
    "/apply",
    response_model=Message,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
    },
)
def register_apply(
    *,
    session: deps.SessionDep,
    bot_session: deps.BotSessionDep,
    apply_data: BotApplyCreate,
) -> Any:
    """
    Register a new job application (success or failed) by the bot.
    Requires the bot session's API key for authentication.
    """
    # Create a new apply record
    bot_apply = BotApply(
        bot_session_id=bot_session.id,
        status=apply_data.status,
        total_time=apply_data.total_time,
        job_title=apply_data.job_title,
        job_url=apply_data.job_url,
        company_name=apply_data.company_name,
        failed_reason=apply_data.failed_reason,
    )

    # Add to DB
    session.add(bot_apply)

    # Update bot session statistics
    if bot_apply.status == BotApplyStatus.SUCCESS:
        bot_session.total_success += 1
    else:
        bot_session.total_failed += 1
    bot_session.total_applied += 1

    session.add(bot_session)
    session.commit()

    return {"message": "Application recorded successfully"}


@router.get(
    "/config",
    response_model=BotConfigResponse,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        404: {"model": ErrorMessage, "description": "Configuration not found"},
    },
)
def get_bot_config(
    *,
    session: deps.SessionDep,
    bot_session: deps.BotSessionDep,
) -> Any:
    """
    Get the configuration and resume for the bot in YAML format.
    Requires the bot session's API key for authentication.
    """
    # Get user from bot session
    user_id = bot_session.user_id
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get user configuration
    user_config = user.config
    if not user_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User configuration not found",
        )

    # Get user resume
    plain_text_resume = user.plain_text_resume
    if not plain_text_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User resume not found",
        )

    # Generate YAML strings
    config_yaml = generate_config_yaml(user_config)
    resume_yaml = generate_plain_text_resume_yaml(plain_text_resume)

    return BotConfigResponse(
        user_config=config_yaml,
        user_resume=resume_yaml,
    )
