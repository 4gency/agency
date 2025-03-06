from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.models.core import ErrorMessage
from app.services.event import EventService


class EventPublic(BaseModel):
    """Modelo para exibição pública de um evento"""

    id: UUID
    bot_session_id: UUID
    type: str
    message: str
    severity: str = "info"
    details: dict[str, Any] | None = None
    created_at: str

    class Config:
        from_attributes = True


class EventsResponse(BaseModel):
    """Modelo para resposta de listagem de eventos"""

    total: int
    items: list[EventPublic]


class EventSummary(BaseModel):
    """Modelo para resumo de eventos"""

    total_events: int
    by_type: dict[str, int]
    by_severity: dict[str, int]
    latest_events: list[EventPublic]


router = APIRouter()


@router.get(
    "/sessions/{session_id}/events",
    response_model=EventsResponse,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def get_session_events(
    *,
    session: SessionDep,
    user: CurrentUser,
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    event_type: list[str] | None = None,
) -> Any:
    """
    Get all events for a specific bot session.
    """
    event_service = EventService(session)

    try:
        events, total = event_service.get_session_events(
            session_id=session_id,
            user=user,
            skip=skip,
            limit=limit,
            event_type=event_type,
        )
    except HTTPException as e:
        raise e

    return {"total": total, "items": [EventPublic.model_validate(e) for e in events]}


@router.get(
    "/sessions/{session_id}/events/summary",
    response_model=EventSummary,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def get_session_events_summary(
    *, session: SessionDep, user: CurrentUser, session_id: UUID
) -> Any:
    """
    Get a summary of events for a specific bot session.
    """
    event_service = EventService(session)

    # Como não há um método específico para resumo, vamos obter todos os eventos
    # e criar um resumo básico
    try:
        events, total = event_service.get_session_events(
            session_id=session_id,
            user=user,
            limit=1000,  # Obter um número maior para o resumo
        )
    except HTTPException as e:
        raise e

    # Criar um resumo básico dos eventos
    event_types: dict[str, int] = {}
    severities: dict[str, int] = {}

    for event in events:
        # Contar por tipo
        event_type = event.type
        if event_type in event_types:
            event_types[event_type] += 1
        else:
            event_types[event_type] = 1

        # Contar por severidade
        severity = event.severity
        if severity in severities:
            severities[severity] += 1
        else:
            severities[severity] = 1

    return {
        "total_events": total,
        "by_type": event_types,
        "by_severity": severities,
        "latest_events": [EventPublic.model_validate(e) for e in events],
    }
