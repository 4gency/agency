import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_db, get_nosql_db
from app.models.bot import BotEvent
from app.services.bot import get_bot_service

logger = logging.getLogger(__name__)

router = APIRouter()


class BotEventRequest(BaseModel):
    """Modelo de dados para eventos enviados pelo bot."""

    event_type: str
    data: dict[str, Any]


@router.post(
    "/bot/{session_id}",
    response_model=BotEvent,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Requisição inválida"},
        401: {"description": "Não autorizado"},
        404: {"description": "Sessão não encontrada"},
    },
)
async def handle_bot_event(
    *,
    session_id: UUID,
    event: BotEventRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    nosql_db=Depends(get_nosql_db),
    x_api_key: str | None = Header(None),
):
    """
    Recebe eventos do bot em execução. Esta rota é chamada diretamente pelo
    bot para informar sobre seu estado, progresso, e qualquer notificação ou
    ação requerida do usuário.

    A autenticação é feita via API key única para cada sessão de bot.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key não fornecida",
        )

    # Get bot service
    bot_service = await get_bot_service(db, nosql_db)

    try:
        # Get the bot session to verify API key
        bot_session = bot_service.get_bot_session(session_id)

        if not bot_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sessão {session_id} não encontrada",
            )

        if bot_session.api_key != x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key inválida",
            )

        # Process the bot event
        created_event = bot_service.handle_bot_event(
            session_id=session_id,
            event_type=event.event_type,
            data=event.data,
            background_tasks=background_tasks,
        )

        return created_event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Erro ao processar evento do bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar evento",
        )


@router.post(
    "/status-update",
    status_code=status.HTTP_200_OK,
    responses={
        500: {"description": "Erro interno"},
    },
)
async def update_bot_statuses(
    *,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    nosql_db=Depends(get_nosql_db),
):
    """
    Endpoint para atualizar o status de todas as sessões de bot ativas.
    Este endpoint pode ser chamado periodicamente por um cron job para
    manter a sincronização entre o estado do Kubernetes e o banco de dados.
    """
    try:
        bot_service = await get_bot_service(db, nosql_db)
        updated_count = await bot_service.update_pod_status(background_tasks)

        return {"updated_count": updated_count, "status": "success"}

    except Exception as e:
        logger.exception(f"Erro ao atualizar status dos bots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar status dos bots",
        )
