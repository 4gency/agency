import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Path,
    Query,
    status,
)

from app.api.deps import CurrentSubscriber, NosqlSessionDep, SessionDep
from app.models.bot import (
    BotApplyDetailPublic,
    BotApplyPublic,
    BotConfigurationCreate,
    BotConfigurationPublic,
    BotEventPublic,
    BotNotificationPublic,
    BotSessionCreate,
    BotSessionDetailPublic,
    BotSessionPublic,
    BotUserActionPublic,
    BotUserActionUpdate,
    LinkedInCredentialsCreate,
    LinkedInCredentialsPublic,
)
from app.models.core import ErrorMessage
from app.models.crud import subscription as subscription_crud
from app.services.bot import get_bot_service
from app.services.config import BotConfigService

# Aliases para serviços
BotConfigurationService = BotConfigService


# Function alias
async def convert_config_to_yaml(nosql_session, subscription_id):
    """Wrapper para o método convert_config_to_yaml do BotConfigService."""
    service = BotConfigService(None, nosql_session)
    return await service.convert_config_to_yaml(subscription_id)


# Router principal para bots
router = APIRouter()

# ======================================================================
# Sessões do Bot
# ======================================================================


@router.post(
    "/sessions/",
    response_model=BotSessionPublic,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        400: {"model": ErrorMessage, "description": "Erro de validação"},
        404: {"model": ErrorMessage, "description": "Configuração não encontrada"},
    },
)
async def create_bot_session(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    session_in: BotSessionCreate,
) -> Any:
    """
    Cria uma nova sessão de bot com base nas configurações existentes.
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        # Verificar se existe configuração e currículo
        config_yaml, resume_yaml = await convert_config_to_yaml(
            nosql_session, session_in.subscription_id
        )

        # Criar sessão com os YAMLs já convertidos
        bot_session = await bot_service.create_bot_session(
            user_id=current_user.id,
            bot_config_id=session_in.bot_config_id,
            applies_limit=session_in.applies_limit,
            time_limit=session_in.time_limit,
        )

        return bot_session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/sessions/",
    response_model=list[BotSessionPublic],
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
    },
)
async def read_bot_sessions(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    skip: int = 0,
    limit: int = 100,
    status: list[str] | None = Query(
        None, description="Filtrar por status (STARTING, RUNNING, PAUSED, etc.)"
    ),
    order_by: str = Query("created_at", description="Campo para ordenação"),
    order_dir: str = Query("desc", description="Direção da ordenação (asc, desc)"),
) -> Any:
    """
    Recupera todas as sessões de bot do usuário.

    * Requer que o usuário seja assinante
    * Retorna uma lista de sessões de bot
    * Pode ser filtrada por status
    """
    bot_service = await get_bot_service(session, nosql_session)

    sessions, _ = await bot_service.get_bot_sessions(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status,
        order_by=order_by,
        order_dir=order_dir,
    )
    return sessions


@router.get(
    "/sessions/{session_id}",
    response_model=BotSessionDetailPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
    },
)
async def read_bot_session(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    session_id: UUID = Path(..., description="ID da sessão"),
) -> Any:
    """
    Recupera uma sessão de bot específica.

    * Requer que o usuário seja assinante
    * Retorna detalhes da sessão de bot
    """
    bot_service = await get_bot_service(session, nosql_session)

    bot_session = await bot_service.get_bot_session(
        session_id=session_id, user_id=current_user.id
    )
    return bot_session


@router.get(
    "/sessions/{session_id}/status",
    response_model=dict,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
    },
)
async def get_bot_session_status(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
) -> Any:
    """
    Recupera o status atual de uma sessão de bot.

    * Requer que o usuário seja assinante
    * Retorna informações detalhadas sobre o status atual do bot e do pod Kubernetes
    * Inclui métricas de execução atualizadas
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        status_info = await bot_service.get_bot_session_status(
            session_id=session_id, user_id=current_user.id
        )
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error getting bot session status: {str(e)}",
        )


@router.get(
    "/sessions/{session_id}/logs",
    response_model=str,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
        500: {"model": ErrorMessage, "description": "Erro ao obter logs"},
    },
)
async def get_bot_session_logs(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
    tail_lines: int = Query(
        100, description="Número de linhas a retornar do final do log"
    ),
) -> Any:
    """
    Recupera os logs de uma sessão de bot.

    * Requer que o usuário seja assinante
    * Retorna os logs do pod Kubernetes
    * Permite especificar o número de linhas a serem retornadas do final do log
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        logs = await bot_service.get_bot_session_logs(
            session_id=session_id, user_id=current_user.id, tail_lines=tail_lines
        )
        return logs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting bot session logs: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/start",
    response_model=BotSessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
        400: {"model": ErrorMessage, "description": "Sessão já em execução"},
        500: {"model": ErrorMessage, "description": "Erro ao iniciar a sessão"},
    },
)
async def start_bot_session(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    background_tasks: BackgroundTasks,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
) -> Any:
    """
    Inicia uma sessão de bot.

    * Requer que o usuário seja assinante
    * Cria o pod Kubernetes para a sessão
    * Inicia a execução do bot
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        bot_session = await bot_service.start_bot_session(
            bot_session_id=session_id,
            user_id=current_user.id,
            background_tasks=background_tasks,
        )
        return bot_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting bot session: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/stop",
    response_model=BotSessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
        400: {"model": ErrorMessage, "description": "Sessão já parada"},
        500: {"model": ErrorMessage, "description": "Erro ao parar a sessão"},
    },
)
async def stop_bot_session(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    background_tasks: BackgroundTasks,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
) -> Any:
    """
    Para uma sessão de bot.

    * Requer que o usuário seja assinante
    * Para a execução do bot
    * Remove o pod Kubernetes
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        bot_session = await bot_service.stop_bot_session(
            bot_session_id=session_id,
            user_id=current_user.id,
            background_tasks=background_tasks,
        )
        return bot_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping bot session: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/pause",
    response_model=BotSessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
        400: {"model": ErrorMessage, "description": "Sessão não está em execução"},
        500: {"model": ErrorMessage, "description": "Erro ao pausar a sessão"},
    },
)
async def pause_bot_session(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    background_tasks: BackgroundTasks,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
) -> Any:
    """
    Pausa uma sessão de bot.

    * Requer que o usuário seja assinante
    * Pausa a execução do bot
    * Mantém o pod Kubernetes ativo
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        bot_session = await bot_service.pause_bot_session(
            bot_session_id=session_id,
            user_id=current_user.id,
            background_tasks=background_tasks,
        )
        return bot_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pausing bot session: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/resume",
    response_model=BotSessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
        400: {"model": ErrorMessage, "description": "Sessão não está pausada"},
        500: {"model": ErrorMessage, "description": "Erro ao retomar a sessão"},
    },
)
async def resume_bot_session(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    background_tasks: BackgroundTasks,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
) -> Any:
    """
    Retoma uma sessão de bot pausada.

    * Requer que o usuário seja assinante
    * Retoma a execução de uma sessão pausada
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        bot_session = await bot_service.resume_bot_session(
            bot_session_id=session_id,
            user_id=current_user.id,
            background_tasks=background_tasks,
        )
        return bot_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resuming bot session: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/restart",
    response_model=BotSessionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
        500: {"model": ErrorMessage, "description": "Erro ao reiniciar a sessão"},
    },
)
async def restart_bot_session(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    background_tasks: BackgroundTasks,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
) -> Any:
    """
    Reinicia uma sessão de bot.

    * Requer que o usuário seja assinante
    * Para e reinicia a execução do bot
    * Recria o pod Kubernetes
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        bot_session = await bot_service.restart_bot_session(
            bot_session_id=session_id,
            user_id=current_user.id,
            background_tasks=background_tasks,
        )
        return bot_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting bot session: {str(e)}",
        )


# ======================================================================
# Aplicações do Bot
# ======================================================================


@router.get(
    "/sessions/{session_id}/applies",
    response_model=list[BotApplyPublic],
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
    },
)
async def read_bot_session_applies(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
    skip: int = 0,
    limit: int = 100,
    status: list[str] | None = Query(
        None, description="Filtrar por status (SUCCESS, FAILED, etc.)"
    ),
    order_by: str = Query("created_at", description="Campo para ordenação"),
    order_dir: str = Query("desc", description="Direção da ordenação (asc, desc)"),
) -> Any:
    """
    Recupera todas as aplicações de uma sessão de bot.

    * Requer que o usuário seja assinante
    * Retorna uma lista de aplicações para vagas
    * Pode ser filtrada por status
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        applies, _ = await bot_service.get_bot_session_applies(
            bot_session_id=session_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status,
            order_by=order_by,
            order_dir=order_dir,
        )
        return applies
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error getting bot applications: {str(e)}",
        )


@router.get(
    "/applies/{apply_id}",
    response_model=BotApplyDetailPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Aplicação não encontrada"},
    },
)
async def read_bot_apply(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    apply_id: int = Path(..., description="ID da aplicação"),
) -> Any:
    """
    Recupera os detalhes de uma aplicação específica.

    * Requer que o usuário seja assinante
    * Retorna os detalhes completos da aplicação, incluindo etapas
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        apply = await bot_service.get_bot_apply(
            apply_id=apply_id, user_id=current_user.id
        )
        return apply
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot application not found",
        )


# ======================================================================
# Eventos do Bot
# ======================================================================


@router.get(
    "/sessions/{session_id}/events",
    response_model=list[BotEventPublic],
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Sessão não encontrada"},
    },
)
async def read_bot_session_events(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    session_id: uuid.UUID = Path(..., description="ID da sessão do bot"),
    skip: int = 0,
    limit: int = 100,
    event_type: list[str] | None = Query(
        None, description="Filtrar por tipo de evento"
    ),
    severity: list[str] | None = Query(None, description="Filtrar por severidade"),
    since: datetime | None = Query(
        None, description="Filtrar eventos a partir desta data"
    ),
    order_by: str = Query("created_at", description="Campo para ordenação"),
    order_dir: str = Query("desc", description="Direção da ordenação (asc, desc)"),
) -> Any:
    """
    Recupera todos os eventos de uma sessão de bot.

    * Requer que o usuário seja assinante
    * Retorna uma lista de eventos
    * Pode ser filtrada por tipo, severidade e data
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        events, _ = await bot_service.get_bot_session_events(
            bot_session_id=session_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            event_type=event_type,
            severity=severity,
            since=since,
            order_by=order_by,
            order_dir=order_dir,
        )
        return events
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error getting bot events: {str(e)}",
        )


# ======================================================================
# Ações do Usuário
# ======================================================================


@router.get(
    "/user-actions/",
    response_model=list[BotUserActionPublic],
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
    },
)
async def read_user_actions(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    skip: int = 0,
    limit: int = 100,
    completed: bool | None = Query(None, description="Filtrar por status de conclusão"),
    action_type: list[str] | None = Query(None, description="Filtrar por tipo de ação"),
    order_by: str = Query("requested_at", description="Campo para ordenação"),
    order_dir: str = Query("desc", description="Direção da ordenação (asc, desc)"),
) -> Any:
    """
    Recupera todas as ações pendentes do usuário.

    * Requer que o usuário seja assinante
    * Retorna uma lista de ações que requerem intervenção do usuário
    * Pode ser filtrada por status e tipo
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        actions, _ = await bot_service.get_user_actions(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            completed=completed,
            action_type=action_type,
            order_by=order_by,
            order_dir=order_dir,
        )
        return actions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user actions: {str(e)}",
        )


@router.get(
    "/user-actions/{action_id}",
    response_model=BotUserActionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Ação não encontrada"},
    },
)
async def read_user_action(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    action_id: uuid.UUID = Path(..., description="ID da ação do usuário"),
) -> Any:
    """
    Recupera os detalhes de uma ação específica.

    * Requer que o usuário seja assinante
    * Retorna os detalhes completos da ação
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        action = await bot_service.get_user_action(
            action_id=action_id, user_id=current_user.id
        )
        return action
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User action not found",
        )


@router.post(
    "/user-actions/{action_id}/complete",
    response_model=BotUserActionPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Ação não encontrada"},
        400: {"model": ErrorMessage, "description": "Ação já concluída ou expirada"},
    },
)
async def complete_user_action(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    action_id: uuid.UUID = Path(..., description="ID da ação do usuário"),
    action_update: BotUserActionUpdate,
) -> Any:
    """
    Completa uma ação do usuário.

    * Requer que o usuário seja assinante
    * Envia a entrada do usuário para completar a ação (2FA, CAPTCHA, etc.)
    * A sessão do bot será retomada após a conclusão
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        action = await bot_service.complete_user_action(
            action_id=action_id,
            user_id=current_user.id,
            user_input=action_update.user_input,
        )
        return action
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error completing user action: {str(e)}",
        )


# ======================================================================
# Notificações
# ======================================================================


@router.get(
    "/notifications/",
    response_model=list[BotNotificationPublic],
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
    },
)
async def read_notifications(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    skip: int = 0,
    limit: int = 100,
    read: bool | None = Query(None, description="Filtrar por status de leitura"),
    priority: list[str] | None = Query(None, description="Filtrar por prioridade"),
    requires_action: bool | None = Query(
        None, description="Filtrar por necessidade de ação"
    ),
    order_by: str = Query("created_at", description="Campo para ordenação"),
    order_dir: str = Query("desc", description="Direção da ordenação (asc, desc)"),
) -> Any:
    """
    Recupera todas as notificações do usuário.

    * Requer que o usuário seja assinante
    * Retorna uma lista de notificações
    * Pode ser filtrada por status, prioridade e necessidade de ação
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        notifications, _ = await bot_service.get_user_notifications(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            read=read,
            priority=priority,
            requires_action=requires_action,
            order_by=order_by,
            order_dir=order_dir,
        )
        return notifications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting notifications: {str(e)}",
        )


@router.get(
    "/notifications/{notification_id}",
    response_model=BotNotificationPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Notificação não encontrada"},
    },
)
async def read_notification(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    notification_id: uuid.UUID = Path(..., description="ID da notificação"),
) -> Any:
    """
    Recupera os detalhes de uma notificação específica.

    * Requer que o usuário seja assinante
    * Retorna os detalhes completos da notificação
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        notification = await bot_service.get_user_notification(
            notification_id=notification_id, user_id=current_user.id
        )
        return notification
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )


@router.post(
    "/notifications/{notification_id}/mark-as-read",
    response_model=BotNotificationPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Notificação não encontrada"},
    },
)
async def mark_notification_as_read(
    *,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    notification_id: uuid.UUID = Path(..., description="ID da notificação"),
) -> Any:
    """
    Marca uma notificação como lida.

    * Requer que o usuário seja assinante
    * Atualiza o status da notificação para "lida"
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        notification = await bot_service.mark_notification_as_read(
            notification_id=notification_id, user_id=current_user.id
        )
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error marking notification as read: {str(e)}",
        )


@router.post(
    "/subscriptions/{subscription_id}/linkedin-credentials",
    response_model=LinkedInCredentialsPublic,
    status_code=status.HTTP_201_CREATED,
)
async def save_linkedin_credentials(
    *,
    subscription_id: UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    credentials: LinkedInCredentialsCreate,
) -> Any:
    """
    Salva as credenciais do LinkedIn para uso pelo bot.

    * As credenciais são armazenadas de forma segura
    * São necessárias para que o bot faça login no LinkedIn
    """
    # Verificar se a assinatura pertence ao usuário
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    # Criar/atualizar credenciais
    bot_config_service = BotConfigurationService(session)
    creds = await bot_config_service.create_linkedin_credentials(
        subscription_id=subscription_id,
        user_id=current_user.id,
        credentials=credentials,
    )

    return LinkedInCredentialsPublic(
        email=creds.email, subscription_id=creds.subscription_id
    )


@router.get(
    "/subscriptions/{subscription_id}/linkedin-credentials",
    response_model=LinkedInCredentialsPublic,
)
async def get_linkedin_credentials(
    *,
    subscription_id: uuid.UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
) -> Any:
    """
    Recupera as credenciais do LinkedIn configuradas.

    * Por segurança, a senha não é retornada
    """
    # Verificar se a assinatura pertence ao usuário
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    # Obter credenciais
    bot_config_service = BotConfigurationService(session)
    creds = await bot_config_service.get_linkedin_credentials(subscription_id)

    if not creds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LinkedIn credentials not found",
        )

    return LinkedInCredentialsPublic(
        email=creds.email, subscription_id=creds.subscription_id
    )


@router.post(
    "/subscriptions/{subscription_id}/bot-configuration",
    response_model=BotConfigurationPublic,
)
async def save_bot_configuration(
    *,
    subscription_id: uuid.UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    configuration: BotConfigurationCreate,
) -> Any:
    """
    Salva configurações específicas do bot.

    * Estilo visual dos documentos
    * User Agent personalizado (opcional)
    """
    # Verificar se a assinatura pertence ao usuário
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    # Criar/atualizar configuração
    bot_config_service = BotConfigurationService(session)
    config = await bot_config_service.create_bot_configuration(
        subscription_id=subscription_id, user_id=current_user.id, config=configuration
    )

    return BotConfigurationPublic(
        id=config.id,
        subscription_id=config.subscription_id,
        style_choice=config.style_choice,
        user_agent=config.user_agent,
    )


@router.get(
    "/subscriptions/{subscription_id}/bot-configuration",
    response_model=BotConfigurationPublic,
)
async def get_bot_configuration(
    *,
    subscription_id: uuid.UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
) -> Any:
    """
    Recupera as configurações do bot.
    """
    # Verificar se a assinatura pertence ao usuário
    subscription = subscription_crud.get_subscription_by_id(
        session=session, id=subscription_id
    )

    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    # Obter configuração
    bot_config_service = BotConfigurationService(session)
    config = await bot_config_service.get_bot_configuration(subscription_id)

    if not config:
        # Criar configuração padrão
        config = await bot_config_service.create_bot_configuration(
            subscription_id=subscription_id,
            user_id=current_user.id,
            config=BotConfigurationCreate(),
        )

    return BotConfigurationPublic(
        id=config.id,
        subscription_id=config.subscription_id,
        style_choice=config.style_choice,
        user_agent=config.user_agent,
    )


@router.post(
    "/subscriptions/{subscription_id}/linkedin-credentials",
    response_model=LinkedInCredentialsPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_or_update_linkedin_credentials(
    *,
    subscription_id: UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    credentials: LinkedInCredentialsCreate,
) -> Any:
    """
    Cria ou atualiza as credenciais do LinkedIn para uma assinatura.

    * Requer que o usuário seja assinante
    * Retorna as credenciais criadas ou atualizadas
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        # Criar ou atualizar credenciais
        linkedin_credentials = await bot_service.create_or_update_linkedin_credentials(
            user_id=current_user.id,
            subscription_id=subscription_id,
            credentials=credentials,
        )
        return linkedin_credentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/subscriptions/{subscription_id}/linkedin-credentials",
    response_model=LinkedInCredentialsPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Credenciais não encontradas"},
    },
)
async def get_linkedin_credentials(
    *,
    subscription_id: UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
) -> Any:
    """
    Recupera as credenciais do LinkedIn para uma assinatura.

    * Requer que o usuário seja assinante
    * Retorna as credenciais do LinkedIn ou 404 se não existirem
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        # Obter credenciais
        linkedin_credentials = await bot_service.get_linkedin_credentials(
            subscription_id=subscription_id
        )
        if not linkedin_credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LinkedIn credentials not found",
            )
        return linkedin_credentials
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/subscriptions/{subscription_id}/bot-configuration",
    response_model=BotConfigurationPublic,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        400: {"model": ErrorMessage, "description": "Erro de validação"},
    },
)
async def create_or_update_bot_configuration(
    *,
    subscription_id: UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
    configuration: BotConfigurationCreate,
) -> Any:
    """
    Cria ou atualiza a configuração do bot para uma assinatura.

    * Requer que o usuário seja assinante
    * Retorna a configuração criada ou atualizada
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        # Criar ou atualizar configuração
        bot_configuration = await bot_service.create_or_update_bot_configuration(
            user_id=current_user.id,
            subscription_id=subscription_id,
            config=configuration,
        )
        return bot_configuration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/subscriptions/{subscription_id}/bot-configuration",
    response_model=BotConfigurationPublic,
    responses={
        401: {"model": ErrorMessage, "description": "Não autenticado"},
        403: {"model": ErrorMessage, "description": "Não é assinante"},
        404: {"model": ErrorMessage, "description": "Configuração não encontrada"},
    },
)
async def get_bot_configuration(
    *,
    subscription_id: UUID,
    session: SessionDep,
    nosql_session: NosqlSessionDep,
    current_user: CurrentSubscriber,
) -> Any:
    """
    Recupera a configuração do bot para uma assinatura.

    * Requer que o usuário seja assinante
    * Retorna a configuração do bot ou 404 se não existir
    """
    bot_service = await get_bot_service(session, nosql_session)

    try:
        # Obter configuração
        bot_configuration = await bot_service.get_bot_configuration(
            subscription_id=subscription_id
        )
        if not bot_configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found",
            )
        return bot_configuration
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
