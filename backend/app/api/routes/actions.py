from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel

from app.api.deps import CurrentUser, SessionDep
from app.models.bot import UserActionType
from app.models.core import ErrorMessage, Message
from app.services.action import UserActionService


class ActionResponse(SQLModel):
    """Modelo para resposta de ação do usuário"""

    user_input: str


class UserActionPublic(SQLModel):
    """Modelo para exibição pública de uma ação do usuário"""

    id: UUID
    bot_session_id: UUID
    type: UserActionType
    message: str
    details: dict[str, Any] | None = None
    completed: bool
    user_input: str | None = None
    created_at: str
    completed_at: str | None = None

    class Config:
        from_attributes = True


class UserActionsResponse(SQLModel):
    """Modelo para resposta de listagem de ações"""

    total: int
    items: list[UserActionPublic]


router = APIRouter()


@router.get(
    "/sessions/{session_id}/actions",
    response_model=UserActionsResponse,
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

    return {
        "total": total,
        "items": [UserActionPublic.model_validate(a) for a in actions],
    }


@router.post(
    "/sessions/{session_id}/actions/{action_id}/complete",
    response_model=Message,
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
