from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import Field, SQLModel

from app.api.deps import CurrentUser, SessionDep
from app.models.bot import BotApplyStatus
from app.models.core import ErrorMessage
from app.services.apply import ApplyService


class ApplyPublic(SQLModel):
    """Modelo para exibição pública de uma aplicação de emprego"""

    id: UUID
    bot_session_id: UUID
    status: BotApplyStatus = BotApplyStatus.SUCCESS
    total_time: int = Field(default=0, description="Total time in seconds")

    # Informações da vaga
    job_title: str | None = None
    job_url: str | None = None
    company_name: str | None = None

    class Config:
        from_attributes = True


class AppliesResponse(SQLModel):
    """Modelo para resposta de listagem de aplicações"""

    total: int
    items: list[ApplyPublic]


class ApplySummary(SQLModel):
    """Modelo para resumo de aplicações"""

    total_applies: int
    by_status: dict[str, int]
    by_company: dict[str, int]
    total_time_seconds: int
    latest_applies: list[ApplyPublic]


router = APIRouter()


@router.get(
    "/sessions/{session_id}/applies",
    response_model=AppliesResponse,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def get_session_applies(
    *,
    session: SessionDep,
    user: CurrentUser,
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: list[str] | None = None,
) -> Any:
    """
    Get all job applications for a specific bot session.
    """
    apply_service = ApplyService(session)

    try:
        applies, total = apply_service.get_session_applies(
            session_id=session_id, user=user, skip=skip, limit=limit, status=status
        )
    except HTTPException as e:
        raise e

    return {"total": total, "items": [ApplyPublic.model_validate(a) for a in applies]}


@router.get(
    "/sessions/{session_id}/applies/{apply_id}",
    response_model=ApplyPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Application not found"},
    },
)
def get_apply_details(
    *, session: SessionDep, user: CurrentUser, session_id: UUID, apply_id: int
) -> Any:
    """
    Get details of a specific job application.
    """
    apply_service = ApplyService(session)

    try:
        apply = apply_service.get_apply_by_id(
            apply_id=apply_id, session_id=session_id, user=user
        )
    except HTTPException as e:
        raise e

    return ApplyPublic.model_validate(apply)


@router.get(
    "/sessions/{session_id}/applies/summary",
    response_model=ApplySummary,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def get_applies_summary(
    *, session: SessionDep, user: CurrentUser, session_id: UUID
) -> Any:
    """
    Get a summary of job applications for a specific bot session.
    """
    apply_service = ApplyService(session)

    try:
        # Como não há um método específico para resumo, vamos obter todos os applies
        # e criar um resumo básico
        applies, total = apply_service.get_session_applies(
            session_id=session_id,
            user=user,
            limit=1000,  # Obter um número maior para o resumo
        )
    except HTTPException as e:
        raise e

    # Criar um resumo básico dos applies
    status_counts: dict[str, int] = {}
    companies: dict[str, int] = {}
    total_time = 0

    for apply in applies:
        # Contar por status
        status_str = (
            apply.status.value if hasattr(apply.status, "value") else str(apply.status)
        )
        if status_str in status_counts:
            status_counts[status_str] += 1
        else:
            status_counts[status_str] = 1

        # Contar por empresa
        if apply.company_name:
            if apply.company_name in companies:
                companies[apply.company_name] += 1
            else:
                companies[apply.company_name] = 1

        # Somar tempo total
        total_time += apply.total_time if apply.total_time else 0

    return {
        "total_applies": total,
        "by_status": status_counts,
        "by_company": companies,
        "total_time_seconds": total_time,
        "latest_applies": [ApplyPublic.model_validate(a) for a in applies],
    }
