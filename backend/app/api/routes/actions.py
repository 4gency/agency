from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.models.core import ErrorMessage
from app.services.action import UserActionService


class ActionResponse(BaseModel):
    user_input: str


router = APIRouter()


@router.get(
    "/sessions/{session_id}/actions",
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def get_session_actions(
    *,
    session: SessionDep,
    user: CurrentUser,
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    include_completed: bool = False,
) -> Any:
    """
    Get all actions for a specific bot session.
    """
    action_service = UserActionService(session)

    try:
        actions, total = action_service.get_session_actions(
            session_id=session_id,
            user=user,
            skip=skip,
            limit=limit,
            include_completed=include_completed,
        )
    except HTTPException as e:
        raise e

    return {"total": total, "items": actions}


@router.post(
    "/sessions/{session_id}/actions/{action_id}/complete",
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Action not found"},
    },
)
def complete_action(
    *,
    session: SessionDep,
    user: CurrentUser,
    session_id: UUID,
    action_id: UUID,
    response: ActionResponse,
) -> Any:
    """
    Complete a user action with the provided response.
    """
    action_service = UserActionService(session)

    try:
        result = action_service.complete_action(
            action_id=action_id,
            session_id=session_id,
            user=user,
            user_input=response.user_input,
        )
    except HTTPException as e:
        raise e

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found or could not be completed",
        )

    return {"message": "Action completed successfully"}
