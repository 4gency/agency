from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel

from app.api.deps import (
    CurrentSubscriber,
    CurrentUser,
    SessionDep,
)
from app.models.bot import BotSessionStatus, BotStyleChoice, UserDashboardStats
from app.models.core import ErrorMessage, Message
from app.services.bot import BotService
from app.services.monitoring import MonitoringService


# Modelos para as rotas
class SessionCreate(SQLModel):
    """Modelo para criação de uma sessão de bot"""

    credentials_id: UUID
    applies_limit: int = 200
    style: BotStyleChoice = BotStyleChoice.DEFAULT


class SessionPublic(SQLModel):
    id: UUID

    # Configs
    credentials_id: UUID
    applies_limit: int = 200
    style: BotStyleChoice = BotStyleChoice.DEFAULT

    # Métricas básicas
    status: BotSessionStatus
    total_applied: int
    total_success: int
    total_failed: int

    api_key: str  # TODO: REMOVE THIS FIELD FOR PRODUCTION

    # Controle de tempo
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    resumed_at: datetime | None = None
    paused_at: datetime | None = None
    total_paused_time: int
    last_heartbeat_at: datetime | None = None


class SessionsResponse(SQLModel):
    """Modelo para resposta de listagem de sessões"""

    total: int
    items: list[SessionPublic]


router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionPublic,
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
        403: {
            "model": ErrorMessage,
            "description": "Permission error",
            "content": {
                "application/json": {
                    "examples": {
                        "not_subscriber": {
                            "summary": "User is not a subscriber",
                            "value": {"detail": "The user is not a subscriber"},
                        }
                    }
                }
            },
        },
        406: {
            "model": ErrorMessage,
            "description": "Not acceptable",
            "content": {
                "application/json": {
                    "examples": {
                        "not_job_preferences": {
                            "summary": "User has not created job preferences",
                            "value": {
                                "detail": "The user has not created job preferences"
                            },
                        },
                        "not_resume_settings": {
                            "summary": "User has not created resume settings",
                            "value": {
                                "detail": "The user has not created resume settings"
                            },
                        },
                        "not_job_preferences_and_resume_settings": {
                            "summary": "User has not created job preferences and resume settings",
                            "value": {
                                "detail": "The user has not created job preferences and resume settings"
                            },
                        },
                    }
                }
            },
        },
    },
)
def create_bot_session(
    *, session: SessionDep, user: CurrentSubscriber, bot_session_in: SessionCreate
) -> Any:
    """
    Create a new bot session.
    """
    # Check if user has created job preferences and resume settings first
    if not user.config and not user.plain_text_resume:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="You cannot create a session without creating job preferences and resume settings first.",
        )
    elif not user.config:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="You cannot create a session without creating job preferences first.",
        )
    elif not user.plain_text_resume:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="You cannot create a session without creating resume settings first.",
        )

    bot_service = BotService(session)
    bot_session = bot_service.create_bot_session(
        user_id=user.id,
        credentials_id=bot_session_in.credentials_id,
        applies_limit=bot_session_in.applies_limit,
        style=bot_session_in.style,
    )

    return SessionPublic.model_validate(bot_session)


@router.get(
    "/sessions",
    response_model=SessionsResponse,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
    },
)
def get_bot_sessions(
    *,
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all bot sessions for the current user.
    """
    bot_service = BotService(session)
    sessions, total = bot_service.get_user_sessions(
        user=user, skip=skip, limit=limit, show_deleted=False
    )

    return {
        "total": total,
        "items": [SessionPublic.model_validate(s) for s in sessions],
    }


@router.get(
    "/sessions/{session_id}",
    response_model=SessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def get_bot_session(*, session: SessionDep, user: CurrentUser, session_id: UUID) -> Any:
    """
    Get a specific bot session.
    """
    bot_service = BotService(session)

    try:
        bot_session = bot_service.get_bot_session(
            session_id=session_id, user=user, show_deleted=False
        )
    except HTTPException as e:
        raise e

    return SessionPublic.model_validate(bot_session)


@router.post(
    "/sessions/{session_id}/start",
    response_model=SessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def start_bot_session(
    *, session: SessionDep, user: CurrentSubscriber, session_id: UUID
) -> Any:
    """
    Start a bot session.
    """
    bot_service = BotService(session)

    try:
        bot_session = bot_service.start_bot_session(session_id=session_id, user=user)
    except HTTPException as e:
        raise e

    return SessionPublic.model_validate(bot_session)


@router.post(
    "/sessions/{session_id}/stop",
    response_model=SessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def stop_bot_session(
    *, session: SessionDep, user: CurrentUser, session_id: UUID
) -> Any:
    """
    Stop a bot session.
    """
    bot_service = BotService(session)

    try:
        bot_session = bot_service.stop_bot_session(session_id=session_id, user=user)
    except HTTPException as e:
        raise e

    return SessionPublic.model_validate(bot_session)


@router.post(
    "/sessions/{session_id}/pause",
    response_model=SessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def pause_bot_session(
    *, session: SessionDep, user: CurrentUser, session_id: UUID
) -> Any:
    """
    Pause a bot session.
    """
    bot_service = BotService(session)

    try:
        bot_session = bot_service.pause_bot_session(session_id=session_id, user=user)
    except HTTPException as e:
        raise e

    return SessionPublic.model_validate(bot_session)


@router.post(
    "/sessions/{session_id}/resume",
    response_model=SessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def resume_bot_session(
    *, session: SessionDep, user: CurrentUser, session_id: UUID
) -> Any:
    """
    Resume a paused bot session.
    """
    bot_service = BotService(session)

    try:
        bot_session = bot_service.resume_bot_session(session_id=session_id, user=user)
    except HTTPException as e:
        raise e

    return SessionPublic.model_validate(bot_session)


@router.delete(
    "/sessions/{session_id}",
    response_model=Message,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def delete_bot_session(
    *, session: SessionDep, user: CurrentUser, session_id: UUID
) -> Any:
    """
    Delete a bot session.
    """
    bot_service = BotService(session)

    try:
        result = bot_service.delete_bot_session(session_id=session_id, user=user)
    except HTTPException as e:
        raise e

    return {
        "message": "Session deleted successfully"
        if result
        else "Failed to delete session"
    }


@router.get(
    "/dashboard/stats",
    response_model=UserDashboardStats,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
    },
)
def get_user_dashboard_stats(*, session: SessionDep, user: CurrentUser) -> Any:
    """
    Get user dashboard statistics.

    Returns aggregated statistics across all user's bot sessions, including:
    - Total applications
    - Successful applications
    - Success rate
    - Failed applications
    - Failure rate
    - Pending applications
    """
    monitoring_service = MonitoringService(session)
    stats = monitoring_service.get_user_dashboard_stats(user_id=user.id)

    return UserDashboardStats(**stats)
