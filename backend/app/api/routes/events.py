from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models.core import ErrorMessage
from app.services.event import EventService

router = APIRouter()


@router.get(
    "/sessions/{session_id}/events",
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

    return {"total": total, "items": events}


@router.get(
    "/sessions/{session_id}/events/summary",
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
    event_types = {}
    severities = {}

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
        "latest_events": events[:10],  # Últimos 10 eventos
    }
