import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import NosqlSessionDep, SessionDep, get_db, get_nosql_db
from app.core.config import settings
from app.models.bot import BotEvent, BotSession
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
    db: SessionDep,
    nosql_db = NosqlSessionDep,
    x_api_key: str | None = Header(None),
) -> BotEvent:
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
        # Preparar dados do webhook, incluindo API key para validação
        webhook_data = event.model_dump()
        webhook_data["api_key"] = x_api_key  # Incluir a API key para validação
        
        # Process the bot event - a validação da API key será feita dentro do método
        result = await bot_service.process_bot_webhook(
            session_id=session_id,
            webhook_data=webhook_data,
        )

        if "event" in result:
            return result["event"]  # Retorna o evento criado
        else:
            # Fallback para compatibilidade
            created_event = BotEvent(
                bot_session_id=session_id,
                type=event.event_type,
                severity="info",
                message=f"Event {event.event_type} received",
                details=str(event.data),
                source="webhook",
            )
            await bot_service.create_bot_event(created_event)
            return created_event

    except HTTPException as e:
        logger.error(f"Erro ao processar evento do bot: {e.status_code}: {e.detail}")
        # Propagar a exceção HTTP original
        raise e
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
        401: {"description": "Não autorizado"},
        500: {"description": "Erro interno"},
    },
)
async def update_bot_statuses(
    *,
    background_tasks: BackgroundTasks,
    db: SessionDep,
    nosql_db = NosqlSessionDep,
    x_api_key: str | None = Header(None),
) -> Dict[str, Any]:
    """
    Endpoint para atualizar o status de todas as sessões de bot ativas.
    Este endpoint pode ser chamado periodicamente por um cron job para
    manter a sincronização entre o estado do Kubernetes e o banco de dados.
    """
    # Verificar API key
    if not x_api_key or x_api_key != settings.BOT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida ou não fornecida",
        )
        
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
