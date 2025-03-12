from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api import deps
from app.models.bot import (
    BotApplyStatus,
    BotSessionStatus,
    UserActionType,
)
from app.models.core import ErrorMessage, Message, User
from app.models.preference import generate_config_yaml
from app.models.resume import generate_plain_text_resume_yaml
from app.services.action import UserActionService
from app.services.apply import ApplyService
from app.services.event import EventService


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


class BotEventCreate(BaseModel):
    """Request model for creating a new event record"""

    type: str
    message: str
    severity: str = "info"
    details: dict[str, Any] | None = None


class BotUserActionCreate(BaseModel):
    """Request model for creating a new user action request"""

    action_type: UserActionType
    description: str
    input_field: str | None = None


class UserActionResponse(BaseModel):
    """Response model for user action creation"""

    id: str
    message: str
    action_type: UserActionType
    description: str
    input_field: str | None = None
    requested_at: str


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
    apply_service = ApplyService(session)

    bot_apply = apply_service.create_apply(
        session_id=bot_session.id,
        total_time=apply_data.total_time,
        job_title=apply_data.job_title,
        job_url=apply_data.job_url,
        company_name=apply_data.company_name,
        failed_reason=apply_data.failed_reason,
        status=apply_data.status,
    )

    if not bot_apply:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create apply record",
        )

    return {"message": "Application recorded successfully"}


@router.post(
    "/events",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
    },
)
def create_event(
    *,
    session: deps.SessionDep,
    bot_session: deps.BotSessionDep,
    event_data: BotEventCreate,
) -> Any:
    """
    Create a new event for the bot session.
    Requires the bot session's API key for authentication.

    Special events with type matching BotSessionStatus values
    (e.g., "running", "paused", "stopping", "completed", "failed", "waiting")
    will update the bot session status accordingly.
    """
    # Create the event service
    event_service = EventService(session)

    # Create a new event
    event = event_service.add_event(
        session_id=bot_session.id,
        event_type=event_data.type,
        message=event_data.message,
        severity=event_data.severity,
        details=event_data.details,
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event",
        )

    # Check if the event type should update the session status
    status_updated = False

    # Special handling for 'waiting' event type that maps to WAITING_INPUT
    if event_data.type.lower() == "waiting":
        old_status = bot_session.status
        new_status = BotSessionStatus.WAITING_INPUT
        status_updated = True
    else:
        try:
            # Try to convert event type to BotSessionStatus enum
            status_value = event_data.type.upper()
            if hasattr(BotSessionStatus, status_value):
                # Get the new status enum value
                new_status = BotSessionStatus[status_value]
                old_status = bot_session.status
                status_updated = True
            else:
                status_updated = False
        except (KeyError, ValueError, AttributeError):
            # Not a valid status event - will just log the event without status change
            status_updated = False

    # Update session status if needed
    if status_updated:
        # Update the session status without validating current status
        bot_session.status = new_status

        # Add status-specific handling
        if new_status == BotSessionStatus.RUNNING:
            if old_status == BotSessionStatus.STARTING:
                bot_session.started_at = event.created_at
            elif old_status == BotSessionStatus.PAUSED:
                bot_session.resumed_at = event.created_at
        elif new_status == BotSessionStatus.PAUSED:
            bot_session.paused_at = event.created_at
        elif new_status == BotSessionStatus.COMPLETED:
            bot_session.finished_at = event.created_at
        elif new_status == BotSessionStatus.FAILED:
            bot_session.finished_at = event.created_at
            if event_data.message:
                bot_session.error_message = event_data.message

        # Update last status message
        bot_session.last_status_message = event_data.message

        # Save the session changes
        session.add(bot_session)
        session.commit()

    return {
        "id": str(event.id),
        "message": "Event created successfully",
        "type": event.type,
        "severity": event.severity,
        "created_at": event.created_at.isoformat(),
        "status_updated": status_updated,
    }


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


@router.post(
    "/user-actions",
    response_model=UserActionResponse,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        500: {"model": ErrorMessage, "description": "Failed to create user action"},
    },
)
def request_user_action(
    *,
    session: deps.SessionDep,
    bot_session: deps.BotSessionDep,
    action_data: BotUserActionCreate,
) -> Any:
    """
    Request an action from the user, such as providing 2FA code or solving a CAPTCHA.
    Requires the bot session's API key for authentication.
    """
    # Create the user action service
    action_service = UserActionService(session)

    # Create a new user action request
    user_action = action_service.create_user_action(
        session_id=bot_session.id,
        action_type=action_data.action_type,
        description=action_data.description,
        input_field=action_data.input_field,
    )

    if not user_action:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user action request",
        )

    # Add an event for this action request
    event_service = EventService(session)
    event_service.add_event(
        session_id=bot_session.id,
        event_type="user_action",
        message=f"User action requested: {action_data.description}",
        severity="info",
        details={
            "action_type": action_data.action_type.value,
            "action_id": str(user_action.id),
        },
    )

    return UserActionResponse(
        id=str(user_action.id),
        message="User action requested successfully",
        action_type=user_action.action_type,
        description=user_action.description,
        input_field=user_action.input_field,
        requested_at=user_action.requested_at.isoformat(),
    )
