import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlmodel import Session, select

from app.integrations.kubernetes import get_kubernetes_manager
from app.models.bot import (
    BotConfig,
    BotSession,
    BotSessionStatus,
    LinkedInCredentials,
)
from app.models.core import Subscription

logger = logging.getLogger(__name__)

# These methods should be added to the BotService class


async def _deploy_bot_to_kubernetes(
    self, session_id: UUID, bot_config_id: UUID, credentials_id: UUID
) -> None:
    """
    Implanta um pod do bot no Kubernetes.
    Esta função é executada em background.

    Args:
        session_id: ID da sessão do bot
        bot_config_id: ID da configuração do bot
        credentials_id: ID das credenciais do LinkedIn
    """
    # Use a session within this method scope
    with Session(self.engine) as session:
        try:
            # Get session, config, and credentials
            bot_session = session.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not bot_session:
                logger.error(f"Bot session {session_id} not found during deployment")
                return

            bot_config_id = bot_session.bot_config_id
            bot_config = session.exec(
                select(BotConfig).where(BotConfig.id == bot_config_id)
            ).first()

            if not bot_config:
                logger.error(f"Bot config {bot_config_id} not found during deployment")
                bot_session.status = BotSessionStatus.ERROR
                bot_session.error_message = "Configuration not found"
                session.add(bot_session)
                session.commit()
                return

            credentials = session.exec(
                select(LinkedInCredentials).where(
                    LinkedInCredentials.id == credentials_id
                )
            ).first()

            if not credentials:
                logger.error(
                    f"LinkedIn credentials {credentials_id} not found during deployment"
                )
                bot_session.status = BotSessionStatus.ERROR
                bot_session.error_message = "LinkedIn credentials not found"
                session.add(bot_session)
                session.commit()
                return

            # Update session status to STARTING
            bot_session.status = BotSessionStatus.STARTING
            session.add(bot_session)
            session.commit()

            # Get configuration as YAML
            config_yaml = await self._get_config_yaml(bot_config_id)

            # Get Kubernetes manager
            kubernetes_manager = get_kubernetes_manager()

            # Create bot pod
            success, pod_name, namespace = kubernetes_manager.create_bot_pod(
                session_id=str(session_id),
                config_yaml=config_yaml,
                linkedin_username=credentials.username,
                linkedin_password=credentials.password,
                api_key=bot_session.api_key,
                webhook_url=f"{self.webhook_base_url}/bot/{session_id}",
            )

            if success:
                # Update session with Kubernetes info
                bot_session.kubernetes_pod_name = pod_name
                bot_session.kubernetes_namespace = namespace
                session.add(bot_session)
                session.commit()

                logger.info(
                    f"Bot pod {pod_name} created successfully for session {session_id}"
                )

                # Create initial "starting" event
                self._create_bot_event(
                    session=session,
                    session_id=session_id,
                    event_type="system",
                    data={
                        "message": "Bot started",
                        "status": "starting",
                    },
                )
            else:
                # Update session status to ERROR
                bot_session.status = BotSessionStatus.ERROR
                bot_session.error_message = "Failed to create Kubernetes pod"
                session.add(bot_session)
                session.commit()

                logger.error(f"Failed to create bot pod for session {session_id}")

                # Create error event
                self._create_bot_event(
                    session=session,
                    session_id=session_id,
                    event_type="system",
                    data={
                        "message": "Failed to start bot",
                        "status": "error",
                        "error": "Kubernetes pod creation failed",
                    },
                )

        except Exception as e:
            logger.exception(f"Error deploying bot to Kubernetes: {str(e)}")
            try:
                # Update session status to ERROR
                bot_session = session.exec(
                    select(BotSession).where(BotSession.id == session_id)
                ).first()

                if bot_session:
                    bot_session.status = BotSessionStatus.ERROR
                    bot_session.error_message = f"Error during deployment: {str(e)}"
                    session.add(bot_session)
                    session.commit()

                    # Create error event
                    self._create_bot_event(
                        session=session,
                        session_id=session_id,
                        event_type="system",
                        data={
                            "message": "Error starting bot",
                            "status": "error",
                            "error": str(e),
                        },
                    )
            except Exception as inner_e:
                logger.exception(f"Error updating bot session status: {str(inner_e)}")


async def stop_bot_session(
    self,
    session_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: UUID | None = None,
) -> BotSession:
    """
    Para uma sessão de bot em execução.

    Args:
        session_id: ID da sessão do bot
        background_tasks: Tarefas em background (FastAPI)
        user_id: ID do usuário (para verificação de permissão, opcional)

    Returns:
        Sessão de bot atualizada
    """
    # Get bot session
    bot_session = self.db.exec(
        select(BotSession).where(BotSession.id == session_id)
    ).first()

    if not bot_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot session {session_id} not found",
        )

    # Check if user has permission
    if user_id and bot_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to stop this bot session",
        )

    # Check if session is in a stoppable state
    stoppable_states = [
        BotSessionStatus.CREATED,
        BotSessionStatus.STARTING,
        BotSessionStatus.RUNNING,
        BotSessionStatus.PAUSED,
    ]

    if bot_session.status not in stoppable_states:
        # If already stopped or completed, just return
        if bot_session.status in [BotSessionStatus.STOPPED, BotSessionStatus.COMPLETED]:
            return bot_session

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot stop bot session in {bot_session.status} state",
        )

    # Update status to STOPPING
    bot_session.status = BotSessionStatus.STOPPING
    self.db.add(bot_session)
    self.db.commit()
    self.db.refresh(bot_session)

    # Stop bot pod in background
    background_tasks.add_task(self._stop_bot_kubernetes_pod, session_id=session_id)

    return bot_session


async def _stop_bot_kubernetes_pod(self, session_id: UUID) -> None:
    """
    Para o pod do bot no Kubernetes.
    Esta função é executada em background.

    Args:
        session_id: ID da sessão do bot
    """
    # Use a session within this method scope
    with Session(self.engine) as session:
        try:
            # Get Kubernetes manager to terminate pod
            kubernetes_manager = get_kubernetes_manager()

            # Get bot session
            bot_session = session.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not bot_session:
                logger.error(
                    f"Bot session {session_id} not found during pod termination"
                )
                return

            if bot_session.kubernetes_pod_name and bot_session.kubernetes_namespace:
                # Terminate the pod
                await kubernetes_manager.terminate_pod(
                    namespace=bot_session.kubernetes_namespace,
                    pod_name=bot_session.kubernetes_pod_name,
                )

                logger.info(
                    f"Terminated pod {bot_session.kubernetes_pod_name} for session {session_id}"
                )

            # Update session status
            bot_session.status = BotSessionStatus.STOPPED
            bot_session.stopped_at = datetime.now(timezone.utc)
            session.add(bot_session)
            session.commit()

            # Create event
            self._create_bot_event(
                session=session,
                session_id=session_id,
                event_type="system",
                data={"message": "Bot stopped", "status": "stopped"},
            )

        except Exception as e:
            logger.exception(f"Error stopping bot pod: {str(e)}")
            try:
                bot_session = session.exec(
                    select(BotSession).where(BotSession.id == session_id)
                ).first()

                if bot_session:
                    # Still mark as stopped, even if error occurred
                    bot_session.status = BotSessionStatus.STOPPED
                    bot_session.stopped_at = datetime.now(timezone.utc)
                    bot_session.error_message = f"Error during stop: {str(e)}"
                    session.add(bot_session)
                    session.commit()

                    # Create error event
                    self._create_bot_event(
                        session=session,
                        session_id=session_id,
                        event_type="system",
                        data={
                            "message": "Error stopping bot",
                            "status": "error",
                            "error": str(e),
                        },
                    )
            except Exception as inner_e:
                logger.exception(f"Error updating bot session status: {str(inner_e)}")


# Continuing with other methods...
# These would follow the same pattern of using synchronous SQLModel sessions
# and calling get_kubernetes_manager() without awaiting it


async def _get_active_subscription_id(self, user_id: UUID) -> UUID | None:
    """
    Gets the active subscription ID for the user.

    Args:
        user_id: User ID

    Returns:
        Subscription ID if found, None otherwise
    """
    # This is a simplified example
    subscription = self.db.exec(
        select(Subscription).where(
            (Subscription.user_id == user_id) & Subscription.is_active
        )
    ).first()

    return subscription.id if subscription else None


async def create_bot_session_with_yaml(
    self,
    user_id: UUID,
    _config_yaml: str,
    _resume_yaml: str,
    background_tasks: BackgroundTasks,
    session_name: str | None = None,
    description: str | None = None,
) -> BotSession:
    """
    Creates a new bot session with provided YAML configurations.

    Args:
        user_id: ID do usuário dono da sessão
        _config_yaml: YAML configuration (prefixed with _ as it's passed but used indirectly)
        _resume_yaml: YAML resume (prefixed with _ as it's passed but used indirectly)
        background_tasks: Background tasks object for async operations
        session_name: Optional name for the session
        description: Optional description for the session
    """
    # Use provided YAMLs directly instead of using them as variables
    # that are never used again

    # Create a new bot session
    bot_session = BotSession(
        user_id=user_id,
        name=session_name or "Bot Session",
        description=description or "",
        status=BotSessionStatus.STARTING.value,
    )

    # Salvar a sessão no banco de dados
    self.db.add(bot_session)
    self.db.commit()
    self.db.refresh(bot_session)

    # Iniciar a implantação do bot em background
    background_tasks.add_task(
        self._deploy_bot_to_kubernetes,
        session_id=bot_session.id,
        bot_config_id=bot_session.bot_config_id,
        credentials_id=bot_session.credentials_id,
    )

    return bot_session
