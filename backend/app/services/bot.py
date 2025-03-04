import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import yaml
from fastapi import BackgroundTasks, Depends, HTTPException, status
from odmantic.session import SyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlmodel import Session

from app.api.deps import get_db, get_nosql_db
from app.integrations.kubernetes import get_kubernetes_service
from app.models.bot import (
    BotApply,
    BotApplyStatus,
    BotCommand,
    BotCommandType,
    BotConfig,
    BotConfigCreate,
    BotConfigUpdate,
    BotConfiguration,
    BotConfigurationCreate,
    BotEvent,
    BotNotification,
    BotNotificationPriority,
    BotNotificationStatus,
    BotSession,
    BotSessionStatus,
    BotUserAction,
    KubernetesPodStatus,
    LinkedInCredentials,
    LinkedInCredentialsCreate,
    UserActionType,
)
from app.models.core import Subscription, SubscriptionMetric
from app.models.crud import config as config_crud

logger = logging.getLogger(__name__)


class BotService:
    """
    Serviço para gerenciar bots de aplicação em vagas.

    Este serviço coordena todas as operações relacionadas com:
    - Configurações de bot (SQL)
    - Credenciais de LinkedIn (SQL)
    - Sessões de bot (SQL)
    - Job preferences (MongoDB)
    - Currículos (MongoDB)
    """

    def __init__(self, db: AsyncSession, nosql_db: SyncSession):
        """
        Inicializa o serviço com sessões para ambos os bancos de dados.

        Args:
            db: Sessão do PostgreSQL (SQLAlchemy/SQLModel)
            nosql_db: Sessão do MongoDB (odmantic)
        """
        self.db = db
        self.nosql_db = nosql_db

    # ======================================================
    # GERENCIAMENTO DE CREDENCIAIS DO LINKEDIN
    # ======================================================

    async def get_linkedin_credentials(
        self, subscription_id: UUID
    ) -> LinkedInCredentials | None:
        """
        Obtém as credenciais do LinkedIn para uma assinatura.

        Args:
            subscription_id: ID da assinatura

        Returns:
            Credenciais do LinkedIn ou None se não encontradas
        """
        result = await self.db.execute(
            select(LinkedInCredentials).where(
                LinkedInCredentials.subscription_id == subscription_id
            )
        )
        return result.scalars().first()

    async def create_or_update_linkedin_credentials(
        self,
        user_id: UUID,
        subscription_id: UUID,
        credentials: LinkedInCredentialsCreate,
    ) -> LinkedInCredentials:
        """
        Cria ou atualiza as credenciais do LinkedIn para uma assinatura.

        Args:
            user_id: ID do usuário
            subscription_id: ID da assinatura
            credentials: Dados das credenciais

        Returns:
            Credenciais criadas ou atualizadas

        Raises:
            HTTPException: Se a assinatura não existir ou não pertencer ao usuário
        """
        # Verificar se a assinatura existe e pertence ao usuário
        subscription = await self._get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
            )

        if subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this subscription",
            )

        # Verificar se já existem credenciais
        existing = await self.get_linkedin_credentials(subscription_id)

        if existing:
            # Atualizar credenciais existentes
            existing.email = credentials.email
            existing.password = credentials.password  # Em produção, usar criptografia
            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Criar novas credenciais
        new_credentials = LinkedInCredentials(
            subscription_id=subscription_id,
            user_id=user_id,
            email=credentials.email,
            password=credentials.password,  # Em produção, usar criptografia
        )

        self.db.add(new_credentials)
        await self.db.commit()
        await self.db.refresh(new_credentials)

        return new_credentials

    # ======================================================
    # GERENCIAMENTO DE CONFIGURAÇÕES DO BOT
    # ======================================================

    async def get_bot_configuration(
        self, subscription_id: UUID
    ) -> BotConfiguration | None:
        """
        Obtém a configuração do bot para uma assinatura.

        Args:
            subscription_id: ID da assinatura

        Returns:
            Configuração do bot ou None se não encontrada
        """
        result = await self.db.execute(
            select(BotConfiguration).where(
                BotConfiguration.subscription_id == subscription_id
            )
        )
        return result.scalars().first()

    async def create_or_update_bot_configuration(
        self, user_id: UUID, subscription_id: UUID, config: BotConfigurationCreate
    ) -> BotConfiguration:
        """
        Cria ou atualiza a configuração do bot para uma assinatura.

        Args:
            user_id: ID do usuário
            subscription_id: ID da assinatura
            config: Dados da configuração

        Returns:
            Configuração criada ou atualizada

        Raises:
            HTTPException: Se a assinatura não existir ou não pertencer ao usuário
        """
        # Verificar se a assinatura existe e pertence ao usuário
        subscription = await self._get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
            )

        if subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this subscription",
            )

        # Verificar se já existe configuração
        existing = await self.get_bot_configuration(subscription_id)

        if existing:
            # Atualizar configuração existente
            existing.style_choice = config.style_choice
            if config.user_agent:
                existing.user_agent = config.user_agent
            if config.sec_ch_ua:
                existing.sec_ch_ua = config.sec_ch_ua
            if config.sec_ch_ua_platform:
                existing.sec_ch_ua_platform = config.sec_ch_ua_platform

            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Criar nova configuração
        new_config = BotConfiguration(
            subscription_id=subscription_id,
            user_id=user_id,
            style_choice=config.style_choice,
            user_agent=config.user_agent
            or BotConfiguration.__annotations__["user_agent"].default,
            sec_ch_ua=config.sec_ch_ua
            or BotConfiguration.__annotations__["sec_ch_ua"].default,
            sec_ch_ua_platform=config.sec_ch_ua_platform
            or BotConfiguration.__annotations__["sec_ch_ua_platform"].default,
        )

        self.db.add(new_config)
        await self.db.commit()
        await self.db.refresh(new_config)

        return new_config

    async def create_bot_config(
        self, user_id: UUID, config_data: BotConfigCreate
    ) -> BotConfig:
        """
        Cria uma nova configuração de bot.

        Args:
            user_id: ID do usuário
            config_data: Dados da configuração

        Returns:
            Configuração criada
        """
        # Criar nova configuração
        new_config = BotConfig(
            user_id=user_id,
            name=config_data.name,
            description=config_data.description,
            max_applies_per_session=config_data.max_applies_per_session,
            max_applies_per_day=config_data.max_applies_per_day,
            allow_dynamic_updates=config_data.allow_dynamic_updates,
            auto_restart_on_failure=config_data.auto_restart_on_failure,
            max_auto_restarts=config_data.max_auto_restarts,
            notify_on_success=config_data.notify_on_success,
            notify_on_failure=config_data.notify_on_failure,
            notify_on_action_required=config_data.notify_on_action_required,
            # Campos que precisam ser definidos mas serão atualizados posteriormente
            config_yaml_key=f"config_{user_id}_{datetime.now(timezone.utc).isoformat()}.yaml",
            resume_yaml_key=f"resume_{user_id}_{datetime.now(timezone.utc).isoformat()}.yaml",
        )

        self.db.add(new_config)
        await self.db.commit()
        await self.db.refresh(new_config)

        return new_config

    async def update_bot_config(
        self, config_id: UUID, user_id: UUID, config_data: BotConfigUpdate
    ) -> BotConfig:
        """
        Atualiza uma configuração de bot existente.

        Args:
            config_id: ID da configuração
            user_id: ID do usuário
            config_data: Dados atualizados

        Returns:
            Configuração atualizada

        Raises:
            HTTPException: Se a configuração não existir ou não pertencer ao usuário
        """
        # Obter configuração
        config = await self._get_bot_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found",
            )

        if config.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this configuration",
            )

        # Atualizar campos
        update_data = config_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        config.updated_at = datetime.now(timezone.utc)

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        return config

    async def delete_bot_config(self, config_id: UUID, user_id: UUID) -> bool:
        """
        Remove uma configuração de bot.

        Args:
            config_id: ID da configuração
            user_id: ID do usuário

        Returns:
            True se removida com sucesso

        Raises:
            HTTPException: Se a configuração não existir, não pertencer ao usuário ou estiver em uso
        """
        # Obter configuração
        config = await self._get_bot_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found",
            )

        if config.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this configuration",
            )

        # Verificar se há sessões ativas usando esta configuração
        active_sessions_count = await self._count_active_sessions_with_config(config_id)
        if active_sessions_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete configuration in use by {active_sessions_count} active sessions",
            )

        # Remover configuração
        await self.db.delete(config)
        await self.db.commit()

        return True

    async def get_user_bot_configs(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[BotConfig]:
        """
        Obtém todas as configurações de bot de um usuário.

        Args:
            user_id: ID do usuário
            skip: Número de registros a pular
            limit: Limite de registros a retornar

        Returns:
            Lista de configurações
        """
        result = await self.db.execute(
            select(BotConfig)
            .where(BotConfig.user_id == user_id)
            .order_by(BotConfig.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()

    async def get_bot_config(self, config_id: UUID, user_id: UUID) -> BotConfig:
        """
        Obtém uma configuração de bot específica.

        Args:
            config_id: ID da configuração
            user_id: ID do usuário

        Returns:
            Configuração de bot

        Raises:
            HTTPException: Se a configuração não existir ou não pertencer ao usuário
        """
        config = await self._get_bot_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found",
            )

        if config.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this configuration",
            )

        return config

    # ======================================================
    # CONVERSÃO DE CONFIGURAÇÕES PARA YAML
    # ======================================================

    async def generate_config_yamls(self, subscription_id: UUID) -> tuple[str, str]:
        """
        Gera os YAMLs de configuração e currículo a partir dos modelos MongoDB.

        Args:
            subscription_id: ID da assinatura

        Returns:
            Tuple[config_yaml, resume_yaml]

        Raises:
            ValueError: Se não encontrar configuração ou currículo
        """
        # Obter configuração do MongoDB
        job_config = config_crud.get_config(
            session=self.nosql_db, subscription_id=str(subscription_id)
        )

        if not job_config:
            raise ValueError(
                f"Job configuration not found for subscription {subscription_id}"
            )

        # Obter currículo do MongoDB
        resume = config_crud.get_resume(
            session=self.nosql_db, subscription_id=str(subscription_id)
        )

        if not resume:
            raise ValueError(f"Resume not found for subscription {subscription_id}")

        # Converter para dicionários, excluindo campos que não devem ir para o YAML
        job_config_dict = job_config.model_dump(exclude={"subscription_id", "user_id"})
        resume_dict = resume.model_dump(exclude={"subscription_id", "user_id"})

        # Converter para YAML
        config_yaml = yaml.dump(job_config_dict, default_flow_style=False)
        resume_yaml = yaml.dump(resume_dict, default_flow_style=False)

        return config_yaml, resume_yaml

    # ======================================================
    # GERENCIAMENTO DE SESSÕES
    # ======================================================

    async def create_bot_session(
        self,
        user_id: UUID,
        subscription_id: UUID,
        bot_config_id: UUID,
        applies_limit: int | None = None,
        time_limit: int | None = None,
    ) -> BotSession:
        """
        Cria uma nova sessão de bot.

        Args:
            user_id: ID do usuário
            subscription_id: ID da assinatura
            bot_config_id: ID da configuração do bot
            applies_limit: Limite de aplicações (opcional)
            time_limit: Limite de tempo em segundos (opcional)

        Returns:
            Sessão de bot criada

        Raises:
            HTTPException: Se ocorrer algum erro durante a criação
        """
        try:
            # Verificar assinatura
            subscription = await self._get_subscription(subscription_id)
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subscription not found",
                )

            if subscription.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to use this subscription",
                )

            # Verificar se a assinatura está ativa
            if not subscription.is_active or subscription.need_to_deactivate():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subscription is not active or has expired",
                )

            # Verificar configuração do bot
            bot_config = await self._get_bot_config(bot_config_id)
            if not bot_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot configuration not found",
                )

            if bot_config.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to use this bot configuration",
                )

            # Verificar dependências

            # 1. Verificar credenciais LinkedIn
            linkedin_creds = await self.get_linkedin_credentials(subscription_id)
            if not linkedin_creds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LinkedIn credentials not configured. Please configure them first.",
                )

            # 2. Verificar configuração específica do bot
            bot_specific_config = await self.get_bot_configuration(subscription_id)
            if not bot_specific_config:
                # Criar configuração padrão
                bot_specific_config = await self.create_or_update_bot_configuration(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    config=BotConfigurationCreate(),
                )

            # 3. Gerar YAMLs das configurações
            try:
                config_yaml, resume_yaml = await self.generate_config_yamls(
                    subscription_id
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )

            # Verificar limites de aplicações para métricas tipo APPLIES
            if subscription.metric_type == SubscriptionMetric.APPLIES:
                max_allowed = subscription.metric_status
                requested = applies_limit or bot_config.max_applies_per_session

                if requested > max_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Applies limit exceeds available credits. Available: {max_allowed}, Requested: {requested}",
                    )

            # Criar a sessão de bot
            session_limit = applies_limit or bot_config.max_applies_per_session

            bot_session = BotSession(
                subscription_id=subscription_id,
                bot_config_id=bot_config_id,
                status=BotSessionStatus.STARTING,
                applies_limit=session_limit,
                time_limit=time_limit,
                config_version=bot_config.config_version,
                resume_version=bot_config.resume_version,
                config_yaml=config_yaml,
                resume_yaml=resume_yaml,
                linkedin_credentials_valid=True,
                config_valid=True,
                resume_valid=True,
            )

            # Adicionar evento inicial
            bot_session.add_event(
                event_type="system",
                message="Bot session created",
                severity="info",
                source="bot-service",
            )

            self.db.add(bot_session)
            await self.db.commit()
            await self.db.refresh(bot_session)

            return bot_session

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating bot session: {str(e)}",
            )

    async def start_bot_session(
        self,
        bot_session_id: UUID,
        user_id: UUID,
        background_tasks: BackgroundTasks | None = None,
    ) -> BotSession:
        """
        Inicia uma sessão de bot.

        Args:
            bot_session_id: ID da sessão
            user_id: ID do usuário
            background_tasks: Tarefas em segundo plano (opcional)

        Returns:
            Sessão de bot atualizada

        Raises:
            HTTPException: Se ocorrer algum erro durante a inicialização
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(bot_session_id)
            if not bot_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot session not found",
                )

            # Verificar permissão
            if not await self._check_user_permission(
                user_id, bot_session.subscription_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to manage this session",
                )

            # Verificar estado atual
            if bot_session.status in [
                BotSessionStatus.RUNNING,
                BotSessionStatus.STARTING,
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session is already running or starting",
                )

            # Criar comando START
            command = BotCommand(
                bot_session_id=bot_session_id,
                command_type=BotCommandType.START,
                sent_by_user_id=user_id,
                source="api",
            )

            self.db.add(command)
            await self.db.commit()
            await self.db.refresh(command)

            # Executa em segundo plano ou sincronicamente
            if background_tasks:
                background_tasks.add_task(self._execute_command_async, command.id)

                # Atualiza o status imediatamente para feedback do usuário
                bot_session.status = BotSessionStatus.STARTING
                bot_session.add_event(
                    event_type="command",
                    message="START command sent",
                    severity="info",
                    source="bot-service",
                )

                await self.db.commit()
                await self.db.refresh(bot_session)

                return bot_session
            else:
                # Execução síncrona
                k8s_service = await get_kubernetes_service(self.db)
                success, message = await k8s_service.execute_bot_command(command)

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to start bot session: {message}",
                    )

                await self.db.refresh(bot_session)
                return bot_session

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error starting bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error starting bot session: {str(e)}",
            )

    async def stop_bot_session(
        self,
        bot_session_id: UUID,
        user_id: UUID,
        background_tasks: BackgroundTasks | None = None,
    ) -> BotSession:
        """
        Para uma sessão de bot.

        Args:
            bot_session_id: ID da sessão
            user_id: ID do usuário
            background_tasks: Tarefas em segundo plano (opcional)

        Returns:
            Sessão de bot atualizada

        Raises:
            HTTPException: Se ocorrer algum erro durante a parada
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(bot_session_id)
            if not bot_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot session not found",
                )

            # Verificar permissão
            if not await self._check_user_permission(
                user_id, bot_session.subscription_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to manage this session",
                )

            # Verificar estado atual
            if bot_session.status in [
                BotSessionStatus.STOPPED,
                BotSessionStatus.COMPLETED,
                BotSessionStatus.FAILED,
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Session is already in final state: {bot_session.status.value}",
                )

            # Criar comando STOP
            command = BotCommand(
                bot_session_id=bot_session_id,
                command_type=BotCommandType.STOP,
                sent_by_user_id=user_id,
                source="api",
            )

            self.db.add(command)
            await self.db.commit()
            await self.db.refresh(command)

            # Executa em segundo plano ou sincronicamente
            if background_tasks:
                background_tasks.add_task(self._execute_command_async, command.id)

                # Atualiza o status imediatamente para feedback do usuário
                bot_session.status = BotSessionStatus.STOPPING
                bot_session.add_event(
                    event_type="command",
                    message="STOP command sent",
                    severity="info",
                    source="bot-service",
                )

                await self.db.commit()
                await self.db.refresh(bot_session)

                return bot_session
            else:
                # Execução síncrona
                k8s_service = await get_kubernetes_service(self.db)
                success, message = await k8s_service.execute_bot_command(command)

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to stop bot session: {message}",
                    )

                await self.db.refresh(bot_session)
                return bot_session

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error stopping bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error stopping bot session: {str(e)}",
            )

    async def pause_bot_session(
        self,
        bot_session_id: UUID,
        user_id: UUID,
        background_tasks: BackgroundTasks | None = None,
    ) -> BotSession:
        """
        Pausa uma sessão de bot.

        Args:
            bot_session_id: ID da sessão
            user_id: ID do usuário
            background_tasks: Tarefas em segundo plano (opcional)

        Returns:
            Sessão de bot atualizada

        Raises:
            HTTPException: Se ocorrer algum erro durante a pausa
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(bot_session_id)
            if not bot_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot session not found",
                )

            # Verificar permissão
            if not await self._check_user_permission(
                user_id, bot_session.subscription_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to manage this session",
                )

            # Verificar estado atual
            if bot_session.status != BotSessionStatus.RUNNING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Session is not running (current status: {bot_session.status.value})",
                )

            # Criar comando PAUSE
            command = BotCommand(
                bot_session_id=bot_session_id,
                command_type=BotCommandType.PAUSE,
                sent_by_user_id=user_id,
                source="api",
            )

            self.db.add(command)
            await self.db.commit()
            await self.db.refresh(command)

            # Executa em segundo plano ou sincronicamente
            if background_tasks:
                background_tasks.add_task(self._execute_command_async, command.id)

                # Atualiza o status imediatamente para feedback do usuário
                bot_session.status = BotSessionStatus.PAUSED
                bot_session.paused_at = datetime.now(timezone.utc)
                bot_session.add_event(
                    event_type="command",
                    message="PAUSE command sent",
                    severity="info",
                    source="bot-service",
                )

                await self.db.commit()
                await self.db.refresh(bot_session)

                return bot_session
            else:
                # Execução síncrona
                k8s_service = await get_kubernetes_service(self.db)
                success, message = await k8s_service.execute_bot_command(command)

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to pause bot session: {message}",
                    )

                await self.db.refresh(bot_session)
                return bot_session

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error pausing bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error pausing bot session: {str(e)}",
            )

    async def resume_bot_session(
        self,
        bot_session_id: UUID,
        user_id: UUID,
        background_tasks: BackgroundTasks | None = None,
    ) -> BotSession:
        """
        Retoma uma sessão de bot pausada.

        Args:
            bot_session_id: ID da sessão
            user_id: ID do usuário
            background_tasks: Tarefas em segundo plano (opcional)

        Returns:
            Sessão de bot atualizada

        Raises:
            HTTPException: Se ocorrer algum erro durante a retomada
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(bot_session_id)
            if not bot_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot session not found",
                )

            # Verificar permissão
            if not await self._check_user_permission(
                user_id, bot_session.subscription_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to manage this session",
                )

            # Verificar estado atual
            if bot_session.status != BotSessionStatus.PAUSED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Session is not paused (current status: {bot_session.status.value})",
                )

            # Criar comando RESUME
            command = BotCommand(
                bot_session_id=bot_session_id,
                command_type=BotCommandType.RESUME,
                sent_by_user_id=user_id,
                source="api",
            )

            self.db.add(command)
            await self.db.commit()
            await self.db.refresh(command)

            # Executa em segundo plano ou sincronicamente
            if background_tasks:
                background_tasks.add_task(self._execute_command_async, command.id)

                # Atualiza o status imediatamente para feedback do usuário
                bot_session.status = BotSessionStatus.RUNNING
                bot_session.resumed_at = datetime.now(timezone.utc)

                # Calcula tempo em pausa
                if bot_session.paused_at:
                    pause_duration = int(
                        (bot_session.resumed_at - bot_session.paused_at).total_seconds()
                    )
                    bot_session.total_paused_time += pause_duration

                bot_session.paused_at = None
                bot_session.add_event(
                    event_type="command",
                    message="RESUME command sent",
                    severity="info",
                    source="bot-service",
                )

                await self.db.commit()
                await self.db.refresh(bot_session)

                return bot_session
            else:
                # Execução síncrona
                k8s_service = await get_kubernetes_service(self.db)
                success, message = await k8s_service.execute_bot_command(command)

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to resume bot session: {message}",
                    )

                await self.db.refresh(bot_session)
                return bot_session

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error resuming bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error resuming bot session: {str(e)}",
            )

    async def restart_bot_session(
        self,
        bot_session_id: UUID,
        user_id: UUID,
        background_tasks: BackgroundTasks | None = None,
    ) -> BotSession:
        """
        Reinicia uma sessão de bot.

        Args:
            bot_session_id: ID da sessão
            user_id: ID do usuário
            background_tasks: Tarefas em segundo plano (opcional)

        Returns:
            Sessão de bot atualizada

        Raises:
            HTTPException: Se ocorrer algum erro durante a reinicialização
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(bot_session_id)
            if not bot_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot session not found",
                )

            # Verificar permissão
            if not await self._check_user_permission(
                user_id, bot_session.subscription_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to manage this session",
                )

            # Criar comando RESTART
            command = BotCommand(
                bot_session_id=bot_session_id,
                command_type=BotCommandType.RESTART,
                sent_by_user_id=user_id,
                source="api",
            )

            self.db.add(command)
            await self.db.commit()
            await self.db.refresh(command)

            # Executa em segundo plano ou sincronicamente
            if background_tasks:
                background_tasks.add_task(self._execute_command_async, command.id)

                # Atualiza o status imediatamente para feedback do usuário
                bot_session.status = BotSessionStatus.STARTING
                bot_session.started_at = None
                bot_session.paused_at = None
                bot_session.resumed_at = None
                bot_session.finished_at = None
                bot_session.add_event(
                    event_type="command",
                    message="RESTART command sent",
                    severity="info",
                    source="bot-service",
                )

                await self.db.commit()
                await self.db.refresh(bot_session)

                return bot_session
            else:
                # Execução síncrona
                k8s_service = await get_kubernetes_service(self.db)
                success, message = await k8s_service.execute_bot_command(command)

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to restart bot session: {message}",
                    )

                await self.db.refresh(bot_session)
                return bot_session

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error restarting bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error restarting bot session: {str(e)}",
            )

    async def get_bot_session(self, session_id: UUID, user_id: UUID) -> BotSession:
        """
        Obtém uma sessão de bot específica.

        Args:
            session_id: ID da sessão
            user_id: ID do usuário

        Returns:
            Sessão de bot

        Raises:
            HTTPException: Se a sessão não for encontrada ou o usuário não tiver permissão
        """
        # Obter sessão
        bot_session = await self._get_bot_session(session_id)
        if not bot_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bot session not found"
            )

        # Verificar permissão
        if not await self._check_user_permission(user_id, bot_session.subscription_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this session",
            )

        return bot_session

    async def get_bot_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> tuple[list[BotSession], int]:
        """
        Obtém todas as sessões de bot de um usuário.

        Args:
            user_id: ID do usuário
            skip: Número de registros a pular
            limit: Limite de registros a retornar
            status: Lista de status para filtrar (opcional)
            order_by: Campo para ordenação
            order_dir: Direção da ordenação ('asc' ou 'desc')

        Returns:
            Tupla com lista de sessões e contagem total
        """
        try:
            # Obter assinaturas do usuário
            result = await self.db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscriptions = result.scalars().all()

            if not subscriptions:
                return [], 0

            subscription_ids = [sub.id for sub in subscriptions]

            # Construir query base
            query = select(BotSession).where(
                BotSession.subscription_id.in_(subscription_ids)
            )

            # Aplicar filtros de status
            if status:
                status_values = []
                for s in status:
                    try:
                        # Tentar converter para enum
                        status_values.append(BotSessionStatus[s.upper()])
                    except (KeyError, ValueError):
                        # Se não for um enum válido, usar o valor literal
                        status_values.append(s)

                query = query.where(BotSession.status.in_(status_values))

            # Aplicar ordenação
            if order_by in BotSession.__annotations__:
                if order_dir.lower() == "asc":
                    query = query.order_by(getattr(BotSession, order_by).asc())
                else:
                    query = query.order_by(getattr(BotSession, order_by).desc())

            # Executar query para contagem
            result = await self.db.execute(query)
            all_sessions = result.scalars().all()
            total = len(all_sessions)

            # Aplicar paginação
            query = query.offset(skip).limit(limit)

            # Incluir relacionamentos
            query = query.options(
                selectinload(BotSession.bot_config),
                selectinload(BotSession.subscription),
            )

            # Executar query final
            result = await self.db.execute(query)
            sessions = result.scalars().all()

            return sessions, total

        except Exception as e:
            logger.error(f"Error getting bot sessions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting bot sessions: {str(e)}",
            )

    async def get_bot_session_status(
        self, session_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        """
        Obtém o status atual de uma sessão de bot.

        Args:
            session_id: ID da sessão
            user_id: ID do usuário

        Returns:
            Dicionário com informações de status

        Raises:
            HTTPException: Se a sessão não for encontrada ou o usuário não tiver permissão
        """
        try:
            # Obter sessão
            bot_session = await self.get_bot_session(session_id, user_id)

            # Verificar se há pod Kubernetes associado
            if (
                not bot_session.kubernetes_pod_name
                or not bot_session.kubernetes_namespace
            ):
                # Sem pod, retorna apenas informações do banco de dados
                return {
                    "bot_status": bot_session.status.value
                    if isinstance(bot_session.status, BotSessionStatus)
                    else str(bot_session.status),
                    "kubernetes_status": None,
                    "pod_status": None,
                    "pod_info": {},
                    "metrics": {
                        "total_applied": bot_session.total_applied,
                        "total_success": bot_session.total_success,
                        "total_failed": bot_session.total_failed,
                        "success_rate": bot_session.success_rate,
                        "total_time": bot_session.total_time,
                    },
                    "is_healthy": bot_session.is_healthy(),
                    "last_heartbeat_at": bot_session.last_heartbeat_at,
                    "last_status_message": bot_session.last_status_message,
                }

            # Obter status do pod
            k8s_service = await get_kubernetes_service(self.db)
            success, status_info = await k8s_service.get_bot_session_status(session_id)

            if not success:
                # Se falhou ao obter status, retorna apenas informações do banco de dados
                return {
                    "bot_status": bot_session.status.value
                    if isinstance(bot_session.status, BotSessionStatus)
                    else str(bot_session.status),
                    "kubernetes_status": bot_session.kubernetes_pod_status.value
                    if isinstance(
                        bot_session.kubernetes_pod_status, KubernetesPodStatus
                    )
                    else str(bot_session.kubernetes_pod_status),
                    "pod_status": None,
                    "pod_info": {},
                    "error": status_info.get("error", "Failed to get pod status"),
                    "metrics": {
                        "total_applied": bot_session.total_applied,
                        "total_success": bot_session.total_success,
                        "total_failed": bot_session.total_failed,
                        "success_rate": bot_session.success_rate,
                        "total_time": bot_session.total_time,
                    },
                    "is_healthy": bot_session.is_healthy(),
                    "last_heartbeat_at": bot_session.last_heartbeat_at,
                    "last_status_message": bot_session.last_status_message,
                }

            # Extrair métricas
            pod_info = status_info.get("pod_info", {})
            annotations = pod_info.get("annotations", {})
            metrics = {
                "total_applied": bot_session.total_applied,
                "total_success": bot_session.total_success,
                "total_failed": bot_session.total_failed,
                "success_rate": bot_session.success_rate,
                "total_time": bot_session.total_time,
            }

            # Adicionar métricas do pod, se disponíveis
            if "bot-applies-count" in annotations:
                try:
                    metrics["pod_total_applied"] = int(annotations["bot-applies-count"])
                except (ValueError, TypeError):
                    pass

            # Retornar informações combinadas
            return {
                "bot_status": status_info.get("bot_status"),
                "kubernetes_status": status_info.get("kubernetes_status"),
                "pod_status": status_info.get("pod_status"),
                "pod_info": status_info.get("pod_info", {}),
                "metrics": metrics,
                "is_healthy": bot_session.is_healthy(),
                "last_heartbeat_at": bot_session.last_heartbeat_at,
                "last_status_message": bot_session.last_status_message,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting bot session status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting bot session status: {str(e)}",
            )

    async def get_bot_session_logs(
        self, session_id: UUID, user_id: UUID, tail_lines: int = 100
    ) -> str:
        """
        Obtém os logs de uma sessão de bot.

        Args:
            session_id: ID da sessão
            user_id: ID do usuário
            tail_lines: Número de linhas a retornar do final do log

        Returns:
            String com os logs

        Raises:
            HTTPException: Se a sessão não for encontrada ou o usuário não tiver permissão
        """
        try:
            # Obter sessão
            bot_session = await self.get_bot_session(session_id, user_id)

            # Verificar se há pod Kubernetes associado
            if (
                not bot_session.kubernetes_pod_name
                or not bot_session.kubernetes_namespace
            ):
                return "Logs not available. Pod not created or already terminated."

            # Obter logs
            k8s_service = await get_kubernetes_service(self.db)
            success, logs = await k8s_service.get_bot_session_logs(
                bot_session_id=session_id, tail_lines=tail_lines
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get logs: {logs}",
                )

            return logs

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting bot session logs: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting bot session logs: {str(e)}",
            )

    # ======================================================
    # GERENCIAMENTO DE AÇÕES DO USUÁRIO
    # ======================================================

    async def get_user_actions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        completed: bool | None = None,
        action_type: list[str] | None = None,
        order_by: str = "requested_at",
        order_dir: str = "desc",
    ) -> tuple[list[BotUserAction], int]:
        """
        Obtém ações do usuário para bots.

        Args:
            user_id: ID do usuário
            skip: Número de registros a pular
            limit: Limite de registros a retornar
            completed: Filtrar por status de conclusão (opcional)
            action_type: Lista de tipos de ação para filtrar (opcional)
            order_by: Campo para ordenação
            order_dir: Direção da ordenação ('asc' ou 'desc')

        Returns:
            Tupla com lista de ações e contagem total
        """
        try:
            # Obter assinaturas do usuário
            result = await self.db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscriptions = result.scalars().all()

            if not subscriptions:
                return [], 0

            subscription_ids = [sub.id for sub in subscriptions]

            # Subconsulta para obter sessões associadas às assinaturas
            session_subquery = select(BotSession.id).where(
                BotSession.subscription_id.in_(subscription_ids)
            )

            # Construir query base
            query = select(BotUserAction).where(
                BotUserAction.bot_session_id.in_(session_subquery)
            )

            # Aplicar filtros
            if completed is not None:
                query = query.where(BotUserAction.is_completed == completed)

            if action_type:
                action_type_values = []
                for t in action_type:
                    try:
                        # Tentar converter para enum
                        action_type_values.append(UserActionType[t.upper()])
                    except (KeyError, ValueError):
                        # Se não for um enum válido, usar o valor literal
                        action_type_values.append(t)

                query = query.where(BotUserAction.action_type.in_(action_type_values))

            # Aplicar ordenação
            if order_by in BotUserAction.__annotations__:
                if order_dir.lower() == "asc":
                    query = query.order_by(getattr(BotUserAction, order_by).asc())
                else:
                    query = query.order_by(getattr(BotUserAction, order_by).desc())

            # Executar query para contagem
            result = await self.db.execute(query)
            all_actions = result.scalars().all()
            total = len(all_actions)

            # Aplicar paginação
            query = query.offset(skip).limit(limit)

            # Incluir relacionamentos
            query = query.options(selectinload(BotUserAction.bot_session))

            # Executar query final
            result = await self.db.execute(query)
            actions = result.scalars().all()

            # Atualizar status de expiração
            for action in actions:
                if (
                    not action.is_completed
                    and action.is_expired()
                    and not action.expired_at
                ):
                    action.expire()

            await self.db.commit()

            return actions, total

        except Exception as e:
            logger.error(f"Error getting user actions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting user actions: {str(e)}",
            )

    async def get_user_action(self, action_id: UUID, user_id: UUID) -> BotUserAction:
        """
        Obtém uma ação do usuário específica.

        Args:
            action_id: ID da ação
            user_id: ID do usuário

        Returns:
            Ação do usuário

        Raises:
            HTTPException: Se a ação não for encontrada ou o usuário não tiver permissão
        """
        try:
            # Obter ação
            result = await self.db.execute(
                select(BotUserAction)
                .where(BotUserAction.id == action_id)
                .options(selectinload(BotUserAction.bot_session))
            )
            action = result.scalars().first()

            if not action:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User action not found",
                )

            # Verificar permissão
            if not await self._check_user_permission(
                user_id, action.bot_session.subscription_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this action",
                )

            # Atualizar status de expiração
            if (
                not action.is_completed
                and action.is_expired()
                and not action.expired_at
            ):
                action.expire()
                await self.db.commit()
                await self.db.refresh(action)

            return action

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user action: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting user action: {str(e)}",
            )

    async def complete_user_action(
        self, action_id: UUID, user_id: UUID, user_input: str
    ) -> BotUserAction:
        """
        Completa uma ação do usuário.

        Args:
            action_id: ID da ação
            user_id: ID do usuário
            user_input: Entrada do usuário

        Returns:
            Ação do usuário atualizada

        Raises:
            HTTPException: Se a ação não for encontrada, já estiver completa ou expirada
        """
        try:
            # Obter ação
            action = await self.get_user_action(action_id, user_id)

            # Verificar se já está completa
            if action.is_completed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Action is already completed",
                )

            # Verificar se expirou
            if action.is_expired():
                action.expire()
                await self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Action has expired"
                )

            # Completar ação
            action.complete(user_input)

            # Adicionar evento
            if hasattr(action, "bot_session"):
                action.bot_session.add_event(
                    event_type="user_action",
                    message=f"User action completed: {action.action_type.value if isinstance(action.action_type, UserActionType) else str(action.action_type)}",
                    severity="info",
                    source="bot-service",
                    user_action_id=action.id,
                )

            await self.db.commit()
            await self.db.refresh(action)

            return action

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error completing user action: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error completing user action: {str(e)}",
            )

    # ======================================================
    # GERENCIAMENTO DE NOTIFICAÇÕES
    # ======================================================

    async def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        read: bool | None = None,
        priority: list[str] | None = None,
        requires_action: bool | None = None,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> tuple[list[BotNotification], int]:
        """
        Obtém notificações do usuário.

        Args:
            user_id: ID do usuário
            skip: Número de registros a pular
            limit: Limite de registros a retornar
            read: Filtrar por status de leitura (opcional)
            priority: Lista de prioridades para filtrar (opcional)
            requires_action: Filtrar por necessidade de ação (opcional)
            order_by: Campo para ordenação
            order_dir: Direção da ordenação ('asc' ou 'desc')

        Returns:
            Tupla com lista de notificações e contagem total
        """
        try:
            # Construir query base
            query = select(BotNotification).where(BotNotification.user_id == user_id)

            # Aplicar filtros
            if read is not None:
                status_value = (
                    BotNotificationStatus.READ if read else BotNotificationStatus.READ
                )
                query = query.where(
                    BotNotification.status == status_value
                    if read
                    else BotNotification.status != status_value
                )

            if priority:
                priority_values = []
                for p in priority:
                    try:
                        # Tentar converter para enum
                        priority_values.append(BotNotificationPriority[p.upper()])
                    except (KeyError, ValueError):
                        # Se não for um enum válido, usar o valor literal
                        priority_values.append(p)

                query = query.where(BotNotification.priority.in_(priority_values))

            if requires_action is not None:
                query = query.where(BotNotification.requires_action == requires_action)

            # Aplicar ordenação
            if order_by in BotNotification.__annotations__:
                if order_dir.lower() == "asc":
                    query = query.order_by(getattr(BotNotification, order_by).asc())
                else:
                    query = query.order_by(getattr(BotNotification, order_by).desc())

            # Executar query para contagem
            result = await self.db.execute(query)
            all_notifications = result.scalars().all()
            total = len(all_notifications)

            # Aplicar paginação
            query = query.offset(skip).limit(limit)

            # Incluir relacionamentos
            query = query.options(
                selectinload(BotNotification.bot_session),
                selectinload(BotNotification.user_action),
            )

            # Executar query final
            result = await self.db.execute(query)
            notifications = result.scalars().all()

            # Atualizar status de expiração
            for notification in notifications:
                if (
                    notification.status != BotNotificationStatus.EXPIRED
                    and not notification.is_active()
                ):
                    notification.mark_as_expired()

            await self.db.commit()

            return notifications, total

        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting user notifications: {str(e)}",
            )

    async def get_user_notification(
        self, notification_id: UUID, user_id: UUID
    ) -> BotNotification:
        """
        Obtém uma notificação específica.

        Args:
            notification_id: ID da notificação
            user_id: ID do usuário

        Returns:
            Notificação

        Raises:
            HTTPException: Se a notificação não for encontrada ou o usuário não for o destinatário
        """
        try:
            # Obter notificação
            result = await self.db.execute(
                select(BotNotification)
                .where(BotNotification.id == notification_id)
                .options(
                    selectinload(BotNotification.bot_session),
                    selectinload(BotNotification.user_action),
                )
            )
            notification = result.scalars().first()

            if not notification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found",
                )

            # Verificar se o usuário é o destinatário
            if notification.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this notification",
                )

            # Atualizar status de expiração
            if (
                notification.status != BotNotificationStatus.EXPIRED
                and not notification.is_active()
            ):
                notification.mark_as_expired()
                await self.db.commit()
                await self.db.refresh(notification)

            return notification

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting notification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting notification: {str(e)}",
            )

    async def mark_notification_as_read(
        self, notification_id: UUID, user_id: UUID
    ) -> BotNotification:
        """
        Marca uma notificação como lida.

        Args:
            notification_id: ID da notificação
            user_id: ID do usuário

        Returns:
            Notificação atualizada

        Raises:
            HTTPException: Se a notificação não for encontrada ou o usuário não for o destinatário
        """
        try:
            # Obter notificação
            notification = await self.get_user_notification(notification_id, user_id)

            # Marcar como lida
            notification.mark_as_read()
            await self.db.commit()
            await self.db.refresh(notification)

            return notification

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking notification as read: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error marking notification as read: {str(e)}",
            )

    async def create_user_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        bot_session_id: UUID,
        priority: BotNotificationPriority = BotNotificationPriority.MEDIUM,
        icon: str | None = None,
        content_html: str | None = None,
        requires_action: bool = False,
        action_url: str | None = None,
        action_text: str | None = None,
        bot_apply_id: int | None = None,
        user_action_id: UUID | None = None,
    ) -> BotNotification:
        """
        Cria uma notificação para o usuário.

        Args:
            user_id: ID do usuário
            title: Título da notificação
            message: Mensagem da notificação
            bot_session_id: ID da sessão do bot associada
            priority: Prioridade da notificação
            icon: Ícone para a notificação (opcional)
            content_html: Conteúdo HTML (opcional)
            requires_action: Se requer ação do usuário
            action_url: URL para ação (opcional)
            action_text: Texto do botão de ação (opcional)
            bot_apply_id: ID da aplicação associada (opcional)
            user_action_id: ID da ação do usuário associada (opcional)

        Returns:
            Notificação criada

        Raises:
            HTTPException: Se a sessão não for encontrada ou o usuário não tiver permissão
        """
        try:
            # Verificar sessão
            bot_session = await self._get_bot_session(bot_session_id)
            if not bot_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot session not found",
                )

            # Criar notificação
            notification = BotNotification(
                bot_session_id=bot_session_id,
                user_id=user_id,
                title=title,
                message=message,
                priority=priority,
                icon=icon,
                content_html=content_html,
                requires_action=requires_action,
                action_url=action_url,
                action_text=action_text,
                bot_apply_id=bot_apply_id,
                user_action_id=user_action_id,
                status=BotNotificationStatus.PENDING,
                source="bot-service",
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Marcar como enviada
            notification.mark_as_sent()
            await self.db.commit()
            await self.db.refresh(notification)

            return notification

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating notification: {str(e)}",
            )

    # ======================================================
    # GERENCIAMENTO DE APLICAÇÕES
    # ======================================================

    async def get_bot_session_applies(
        self,
        bot_session_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> tuple[list[BotApply], int]:
        """
        Obtém aplicações de uma sessão de bot.

        Args:
            bot_session_id: ID da sessão
            user_id: ID do usuário
            skip: Número de registros a pular
            limit: Limite de registros a retornar
            status: Lista de status para filtrar (opcional)
            order_by: Campo para ordenação
            order_dir: Direção da ordenação ('asc' ou 'desc')

        Returns:
            Tupla com lista de aplicações e contagem total

        Raises:
            HTTPException: Se a sessão não for encontrada ou o usuário não tiver permissão
        """
        try:
            # Obter sessão (validação de acesso - verifica se existe e pertence ao usuário)
            _bot_session = await self.get_bot_session(bot_session_id, user_id)

            # Construir query base
            query = select(BotApply).where(BotApply.session_id == bot_session_id)

            # Aplicar filtros
            if status:
                status_values = []
                for s in status:
                    try:
                        # Tentar converter para enum
                        status_values.append(BotApplyStatus[s.upper()].value)
                    except (KeyError, ValueError):
                        # Se não for um enum válido, usar o valor literal
                        status_values.append(s)

                query = query.where(BotApply.status.in_(status_values))

            # Aplicar ordenação
            if order_by in BotApply.__annotations__:
                if order_dir.lower() == "asc":
                    query = query.order_by(getattr(BotApply, order_by).asc())
                else:
                    query = query.order_by(getattr(BotApply, order_by).desc())

            # Executar query para contagem
            result = await self.db.execute(query)
            all_applies = result.scalars().all()
            total = len(all_applies)

            # Aplicar paginação
            query = query.offset(skip).limit(limit)

            # Incluir relacionamentos
            query = query.options(selectinload(BotApply.apply_steps))

            # Executar query final
            result = await self.db.execute(query)
            applies = result.scalars().all()

            return applies, total

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting bot session applies: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting bot session applies: {str(e)}",
            )

    async def get_bot_apply(self, apply_id: int, user_id: UUID) -> BotApply:
        """
        Obtém uma aplicação específica.

        Args:
            apply_id: ID da aplicação
            user_id: ID do usuário

        Returns:
            Aplicação

        Raises:
            HTTPException: Se a aplicação não for encontrada ou o usuário não tiver permissão
        """
        try:
            # Obter aplicação com relacionamentos
            result = await self.db.execute(
                select(BotApply)
                .where(BotApply.id == apply_id)
                .options(
                    selectinload(BotApply.bot_session),
                    selectinload(BotApply.apply_steps),
                    selectinload(BotApply.user_actions),
                )
            )
            apply = result.scalars().first()

            if not apply:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found",
                )

            # Verificar permissão
            if not await self._check_user_permission(
                user_id, apply.bot_session.subscription_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this application",
                )

            return apply

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting bot apply: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting bot apply: {str(e)}",
            )

    # ======================================================
    # GERENCIAMENTO DE EVENTOS
    # ======================================================

    async def get_bot_session_events(
        self,
        bot_session_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        event_type: list[str] | None = None,
        severity: list[str] | None = None,
        since: datetime | None = None,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> tuple[list[BotEvent], int]:
        """
        Obtém eventos de uma sessão de bot.

        Args:
            bot_session_id: ID da sessão
            user_id: ID do usuário
            skip: Número de registros a pular
            limit: Limite de registros a retornar
            event_type: Lista de tipos de evento para filtrar (opcional)
            severity: Lista de severidades para filtrar (opcional)
            since: Data mínima dos eventos (opcional)
            order_by: Campo para ordenação
            order_dir: Direção da ordenação ('asc' ou 'desc')

        Returns:
            Tupla com lista de eventos e contagem total

        Raises:
            HTTPException: Se a sessão não for encontrada ou o usuário não tiver permissão
        """
        try:
            # Obter sessão
            bot_session = await self.get_bot_session(bot_session_id, user_id)

            # Construir query base
            query = select(BotEvent).where(BotEvent.bot_session_id == bot_session_id)

            # Aplicar filtros
            if event_type:
                query = query.where(BotEvent.type.in_(event_type))

            if severity:
                query = query.where(BotEvent.severity.in_(severity))

            if since:
                query = query.where(BotEvent.created_at >= since)

            # Aplicar ordenação
            if order_by in BotEvent.__annotations__:
                if order_dir.lower() == "asc":
                    query = query.order_by(getattr(BotEvent, order_by).asc())
                else:
                    query = query.order_by(getattr(BotEvent, order_by).desc())

            # Executar query para contagem
            result = await self.db.execute(query)
            all_events = result.scalars().all()
            total = len(all_events)

            # Aplicar paginação
            query = query.offset(skip).limit(limit)

            # Executar query final
            result = await self.db.execute(query)
            events = result.scalars().all()

            return events, total

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting bot session events: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting bot session events: {str(e)}",
            )

    # ======================================================
    # COMANDOS DO BOT
    # ======================================================

    async def create_bot_event(self, event: BotEvent) -> bool:
        """
        Cria um evento para uma sessão de bot.

        Args:
            event: Evento a ser criado

        Returns:
            True se criado com sucesso
        """
        try:
            # Verificar sessão
            bot_session = await self._get_bot_session(event.bot_session_id)
            if not bot_session:
                return False

            # Adicionar evento
            self.db.add(event)
            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating bot event: {str(e)}")
            return False

    async def update_bot_heartbeat(
        self, session_id: UUID, metrics: dict[str, Any]
    ) -> bool:
        """
        Atualiza o heartbeat de uma sessão de bot.

        Args:
            session_id: ID da sessão
            metrics: Métricas atualizadas

        Returns:
            True se atualizado com sucesso
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(session_id)
            if not bot_session:
                return False

            # Atualizar timestamp de heartbeat
            bot_session.heartbeat()

            # Atualizar métricas
            if metrics:
                applied = metrics.get("total_applied")
                success = metrics.get("total_success")
                failed = metrics.get("total_failed")

                if applied is not None:
                    bot_session.total_applied = applied
                if success is not None:
                    bot_session.total_success = success
                if failed is not None:
                    bot_session.total_failed = failed

                # Recalcular taxa de sucesso
                if bot_session.total_applied > 0:
                    bot_session.success_rate = round(
                        (bot_session.total_success / bot_session.total_applied) * 100, 2
                    )

            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating bot heartbeat: {str(e)}")
            return False

    async def update_bot_status(
        self,
        session_id: UUID,
        status: BotSessionStatus | None = None,
        message: str | None = None,
        details: str | None = None,
    ) -> bool:
        """
        Atualiza o status de uma sessão de bot.

        Args:
            session_id: ID da sessão
            status: Novo status (opcional)
            message: Mensagem de status (opcional)
            details: Detalhes adicionais (opcional)

        Returns:
            True se atualizado com sucesso
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(session_id)
            if not bot_session:
                return False

            # Atualizar status
            if status:
                bot_session.status = status

            # Atualizar mensagem de status
            if message:
                bot_session.last_status_message = message

                # Adicionar evento
                bot_session.add_event(
                    event_type="status",
                    message=message,
                    severity="info",
                    details=details,
                    source="bot",
                )

            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating bot status: {str(e)}")
            return False

    async def get_pending_commands(self, session_id: UUID) -> list[BotCommand]:
        """
        Obtém comandos pendentes para uma sessão de bot.

        Args:
            session_id: ID da sessão

        Returns:
            Lista de comandos pendentes
        """
        try:
            # Obter comandos não executados
            result = await self.db.execute(
                select(BotCommand)
                .where(
                    BotCommand.bot_session_id == session_id,
                    BotCommand.executed_at.is_(None),
                )
                .order_by(BotCommand.sent_at.asc())
            )

            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting pending commands: {str(e)}")
            return []

    async def update_command_result(
        self,
        command_id: UUID,
        session_id: UUID,
        success: bool,
        error_message: str | None = None,
    ) -> bool:
        """
        Atualiza o resultado da execução de um comando.

        Args:
            command_id: ID do comando
            session_id: ID da sessão
            success: Se a execução foi bem-sucedida
            error_message: Mensagem de erro (opcional)

        Returns:
            True se atualizado com sucesso
        """
        try:
            # Obter comando
            result = await self.db.execute(
                select(BotCommand).where(
                    BotCommand.id == command_id, BotCommand.bot_session_id == session_id
                )
            )
            command = result.scalars().first()

            if not command:
                return False

            # Atualizar resultado
            command.mark_executed(success, error_message)

            # Adicionar evento
            bot_session = await self._get_bot_session(session_id)
            if bot_session:
                severity = "info" if success else "error"
                message = (
                    f"Command {command.command_type.value} executed successfully"
                    if success
                    else f"Command {command.command_type.value} failed: {error_message}"
                )

                bot_session.add_event(
                    event_type="command",
                    message=message,
                    severity=severity,
                    source="bot",
                )

            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating command result: {str(e)}")
            return False

    # ======================================================
    # WEBHOOKS DO BOT
    # ======================================================

    async def create_user_action_from_webhook(
        self, session_id: UUID, action_data: dict[str, Any]
    ) -> BotUserAction | None:
        """
        Cria uma ação para o usuário a partir de um webhook.

        Args:
            session_id: ID da sessão
            action_data: Dados da ação

        Returns:
            Ação criada ou None se falhar
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(session_id)
            if not bot_session:
                return None

            # Extrair dados
            action_type_str = action_data.get("action_type")
            description = action_data.get("description")

            if not action_type_str or not description:
                return None

            # Converter tipo de ação
            try:
                action_type = UserActionType[action_type_str.upper()]
            except (KeyError, ValueError):
                return None

            # Criar ação
            action = BotUserAction(
                bot_session_id=session_id,
                action_type=action_type,
                description=description,
                input_field=action_data.get("input_field"),
                extra_data=action_data.get("extra_data"),
                timeout_seconds=action_data.get("timeout_seconds", 300),
                bot_apply_id=action_data.get("apply_id"),
                context=action_data.get("context"),
            )

            self.db.add(action)

            # Atualizar status da sessão
            bot_session.status = BotSessionStatus.WAITING_INPUT
            bot_session.last_status_message = f"Waiting for user input: {description}"

            # Adicionar evento
            bot_session.add_event(
                event_type="user_action",
                message=f"User action required: {description}",
                severity="info",
                source="bot",
            )

            await self.db.commit()
            await self.db.refresh(action)

            # Criar notificação para o usuário
            await self.notify_user_action_required(action.id)

            return action

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user action from webhook: {str(e)}")
            return None

    async def notify_user_action_required(
        self, action_id: UUID
    ) -> BotNotification | None:
        """
        Cria uma notificação para uma ação que requer intervenção do usuário.

        Args:
            action_id: ID da ação

        Returns:
            Notificação criada ou None se falhar
        """
        try:
            # Obter ação
            result = await self.db.execute(
                select(BotUserAction)
                .where(BotUserAction.id == action_id)
                .options(selectinload(BotUserAction.bot_session))
            )
            action = result.scalars().first()

            if not action or not action.bot_session:
                return None

            # Obter usuário da assinatura
            subscription = await self._get_subscription(
                action.bot_session.subscription_id
            )
            if not subscription:
                return None

            # Criar notificação
            action_url = f"/bot/user-actions/{action_id}"

            notification = BotNotification.create_action_notification(
                bot_session_id=action.bot_session_id,
                user_id=subscription.user_id,
                title=f"Action required: {action.action_type.value}",
                message=action.description,
                action_url=action_url,
                action_text="Respond",
                user_action_id=action.id,
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Marcar como enviada
            notification.mark_as_sent()
            await self.db.commit()

            return notification

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification for user action: {str(e)}")
            return None

    async def notify_session_completion(
        self, session_id: UUID
    ) -> BotNotification | None:
        """
        Cria uma notificação para informar que uma sessão foi concluída.

        Args:
            session_id: ID da sessão

        Returns:
            Notificação criada ou None se falhar
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(session_id)
            if not bot_session:
                return None

            # Obter usuário da assinatura
            subscription = await self._get_subscription(bot_session.subscription_id)
            if not subscription:
                return None

            # Criar notificação
            notification = BotNotification.create_success_notification(
                bot_session_id=session_id,
                user_id=subscription.user_id,
                title="Bot session completed",
                message=f"Your bot session has completed with {bot_session.total_success} successful applications out of {bot_session.total_applied} attempts.",
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Marcar como enviada
            notification.mark_as_sent()
            await self.db.commit()

            return notification

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error creating notification for session completion: {str(e)}"
            )
            return None

    async def notify_session_failure(
        self, session_id: UUID, reason: str
    ) -> BotNotification | None:
        """
        Cria uma notificação para informar que uma sessão falhou.

        Args:
            session_id: ID da sessão
            reason: Motivo da falha

        Returns:
            Notificação criada ou None se falhar
        """
        try:
            # Obter sessão
            bot_session = await self._get_bot_session(session_id)
            if not bot_session:
                return None

            # Obter usuário da assinatura
            subscription = await self._get_subscription(bot_session.subscription_id)
            if not subscription:
                return None

            # Criar notificação
            notification = BotNotification.create_error_notification(
                bot_session_id=session_id,
                user_id=subscription.user_id,
                title="Bot session failed",
                message=f"Your bot session has failed: {reason}. Completed {bot_session.total_success} successful applications out of {bot_session.total_applied} attempts.",
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Marcar como enviada
            notification.mark_as_sent()
            await self.db.commit()

            return notification

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification for session failure: {str(e)}")
            return None

    async def notify_apply_completion(
        self, apply_id: int, success: bool
    ) -> BotNotification | None:
        """
        Cria uma notificação para informar sobre a conclusão de uma aplicação.

        Args:
            apply_id: ID da aplicação
            success: Se a aplicação foi bem-sucedida

        Returns:
            Notificação criada ou None se falhar
        """
        try:
            # Obter aplicação
            result = await self.db.execute(
                select(BotApply)
                .where(BotApply.id == apply_id)
                .options(selectinload(BotApply.bot_session))
            )
            apply = result.scalars().first()

            if not apply or not apply.bot_session:
                return None

            # Obter usuário da assinatura
            subscription = await self._get_subscription(
                apply.bot_session.subscription_id
            )
            if not subscription:
                return None

            # Verificar configuração de notificações
            bot_config = await self._get_bot_config(apply.bot_session.bot_config_id)
            if not bot_config:
                return None

            if success and not bot_config.notify_on_success:
                return None

            if not success and not bot_config.notify_on_failure:
                return None

            # Criar notificação
            if success:
                title = "Application successful"
                message = f"Successfully applied to {apply.job_title} at {apply.company_name or 'company'}."
                notification = BotNotification.create_success_notification(
                    bot_session_id=apply.bot_session.id,
                    user_id=subscription.user_id,
                    title=title,
                    message=message,
                    apply_id=apply.id,
                )
            else:
                title = "Application failed"
                message = f"Failed to apply to {apply.job_title} at {apply.company_name or 'company'}: {apply.failed_reason or 'Unknown error'}."
                notification = BotNotification.create_error_notification(
                    bot_session_id=apply.bot_session.id,
                    user_id=subscription.user_id,
                    title=title,
                    message=message,
                    apply_id=apply.id,
                )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Marcar como enviada
            notification.mark_as_sent()
            await self.db.commit()

            return notification

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification for apply completion: {str(e)}")
            return None


async def get_bot_service(db: AsyncSession | Session = Depends(get_db), nosql_db: SyncSession = Depends(get_nosql_db)) -> BotService:
    return BotService(db=db, nosql_db=nosql_db)
