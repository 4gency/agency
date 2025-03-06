import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, or_, select

from app.core.security import decrypt_password, encrypt_password
from app.models.bot import (
    BotApply,
    BotApplyStatus,
    BotConfig,
    BotEvent,
    BotSession,
    BotSessionStatus,
    LinkedInCredentials,
)

logger = logging.getLogger(__name__)


class BotService:
    """
    Simplified service for managing LinkedIn application bots.
    Integrates directly with Kubernetes to manage bot lifecycle.
    """

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    # ======================================================
    # CONFIGURATION MANAGEMENT
    # ======================================================

    def get_bot_config(self, config_id: UUID, user_id: UUID) -> BotConfig:
        """Get a bot configuration"""
        config = self.db.exec(
            select(BotConfig).where(BotConfig.id == config_id)
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found",
            )

        if config.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this configuration",
            )

        return config

    def create_bot_config(
        self, user_id: UUID, name: str, config_yaml: str, resume_yaml: str
    ) -> BotConfig:
        """Create a new bot configuration"""
        # Create configuration with minimal required fields
        new_config = BotConfig(
            user_id=user_id,
            name=name,
            config_yaml=config_yaml,
            resume_yaml=resume_yaml,
            max_applies_per_session=200,  # Default value
            kubernetes_namespace="bot-jobs",  # Default namespace
            kubernetes_resources_cpu="500m",
            kubernetes_resources_memory="1Gi",
        )

        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)

        return new_config

    def update_bot_config(
        self, config_id: UUID, user_id: UUID, update_data: dict[str, Any]
    ) -> BotConfig:
        """Update an existing bot configuration"""
        config = self.get_bot_config(config_id, user_id)

        # Update fields
        for key, value in update_data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        config.updated_at = datetime.now(timezone.utc)

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        return config

    def delete_bot_config(self, config_id: UUID, user_id: UUID) -> bool:
        """Delete a bot configuration"""
        config = self.get_bot_config(config_id, user_id)

        # Check if config is being used by any active sessions
        query = select(BotSession).where(
            BotSession.bot_config_id == config_id,
            or_(
                BotSession.status == BotSessionStatus.RUNNING,
                BotSession.status == BotSessionStatus.STARTING,
                BotSession.status == BotSessionStatus.PAUSED,
            ),
        )
        active_sessions = self.db.exec(query).all()

        if active_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete configuration in use by {len(active_sessions)} active sessions",
            )

        self.db.delete(config)
        self.db.commit()

        return True

    def get_user_bot_configs(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[BotConfig]:
        """Get all bot configurations for a user"""
        # Use a simpler ordering expression to avoid typing issues
        configs = self.db.exec(
            select(BotConfig)
            .where(BotConfig.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(
                "updated_at DESC"
            )  # Using string column name to avoid typing issues
        ).all()

        return list(configs)

    # ======================================================
    # LINKEDIN CREDENTIALS MANAGEMENT
    # ======================================================

    def get_linkedin_credentials(self, user_id: UUID) -> LinkedInCredentials | None:
        """Get LinkedIn credentials for a user"""
        credentials = self.db.exec(
            select(LinkedInCredentials).where(LinkedInCredentials.user_id == user_id)
        ).first()

        if credentials and credentials.password:
            try:
                credentials.password = decrypt_password(credentials.password)
            except Exception as e:
                logger.error(f"Error decrypting password: {str(e)}")

        return credentials

    def create_or_update_linkedin_credentials(
        self, user_id: UUID, email: str, password: str
    ) -> LinkedInCredentials:
        """Create or update LinkedIn credentials"""
        # Check if credentials already exist
        existing = self.db.exec(
            select(LinkedInCredentials).where(LinkedInCredentials.user_id == user_id)
        ).first()

        encrypted_password = encrypt_password(password)

        if existing:
            existing.email = email
            existing.password = encrypted_password
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)

            # Return with decrypted password for immediate use
            existing.password = password
            return existing

        # Create new credentials
        new_credentials = LinkedInCredentials(
            user_id=user_id,
            email=email,
            password=encrypted_password,
        )

        self.db.add(new_credentials)
        self.db.commit()
        self.db.refresh(new_credentials)

        # Return with decrypted password for immediate use
        new_credentials.password = password
        return new_credentials

    # ======================================================
    # BOT SESSION MANAGEMENT
    # ======================================================

    def create_bot_session(
        self, user_id: UUID, bot_config_id: UUID, applies_limit: int | None = None
    ) -> BotSession:
        """Create a new bot session"""
        # Check if bot config exists and belongs to user
        config = self.get_bot_config(bot_config_id, user_id)

        # Check if LinkedIn credentials exist
        credentials = self.get_linkedin_credentials(user_id)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn credentials required",
            )

        # Set default limit if not provided
        if applies_limit is None:
            applies_limit = config.max_applies_per_session

        # Create session
        session = BotSession(
            user_id=user_id,
            bot_config_id=config.id,
            applies_limit=applies_limit,
            status=BotSessionStatus.STARTING,
            api_key=secrets.token_urlsafe(16),  # Generate API key
            kubernetes_namespace=config.kubernetes_namespace or "bot-jobs",
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Add initial event
        event = BotEvent(
            bot_session_id=session.id,
            type="system",
            message="Bot session created",
            severity="info",
        )

        self.db.add(event)
        self.db.commit()

        return session

    def get_bot_session(self, session_id: UUID, user_id: UUID) -> BotSession:
        """Get a bot session"""
        session = self.db.exec(
            select(BotSession).where(BotSession.id == session_id)
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bot session not found"
            )

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this session",
            )

        return session

    def get_user_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
    ) -> tuple[list[BotSession], int]:
        """Get all bot sessions for a user"""
        # Build query
        query = select(BotSession).where(BotSession.user_id == user_id)

        # Apply status filter
        if status:
            status_conditions = []
            for s in status:
                try:
                    status_conditions.append(
                        BotSession.status == BotSessionStatus[s.upper()]
                    )
                except (KeyError, ValueError):
                    # Skip invalid status values instead of comparing strings
                    logger.warning(f"Invalid session status value: {s}")
                    continue

            if status_conditions:
                query = query.where(or_(*status_conditions))

        # Get total count
        all_sessions = self.db.exec(query).all()
        total = len(all_sessions)

        # Apply pagination and ordering
        query = (
            query.offset(skip).limit(limit).order_by("created_at DESC")
        )  # Using string column name

        sessions = self.db.exec(query).all()

        return cast(list[BotSession], sessions), total

    def start_bot_session(self, session_id: UUID, user_id: UUID) -> BotSession:
        """Start a bot session"""
        # Get session
        session = self.get_bot_session(session_id, user_id)

        # Verify session is in a valid state to start
        if session.status not in [BotSessionStatus.STARTING, BotSessionStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is in {session.status} state, cannot start",
            )

        # Get config
        config = self.get_bot_config(session.bot_config_id, user_id)

        assert config

        # Get credentials
        credentials = self.get_linkedin_credentials(user_id)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn credentials required",
            )

        try:
            # Create bot container directly (skipping Kubernetes manager)
            pod_name = f"bot-{session.id.hex[:8]}"

            # TODO: This is where we would integrate with Kubernetes
            # For the MVP, we'll just simulate pod creation

            # Update session with "running" status
            session.status = BotSessionStatus.RUNNING
            session.started_at = datetime.now(timezone.utc)
            session.kubernetes_pod_name = pod_name
            session.last_heartbeat_at = datetime.now(timezone.utc)

            # Add event
            event = BotEvent(
                bot_session_id=session.id,
                type="system",
                message="Bot started",
                severity="info",
            )

            self.db.add(event)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # In a real implementation, we would launch the bot here
            # For MVP, we'll just update the DB and return

            return session

        except Exception as e:
            logger.exception(f"Error starting bot session: {str(e)}")

            # Update session on failure
            session.status = BotSessionStatus.FAILED
            session.error_message = f"Failed to start: {str(e)}"

            # Add error event
            event = BotEvent(
                bot_session_id=session.id,
                type="error",
                message=f"Failed to start: {str(e)}",
                severity="error",
            )

            self.db.add(event)
            self.db.add(session)
            self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error starting bot session: {str(e)}",
            )

    def stop_bot_session(self, session_id: UUID, user_id: UUID) -> BotSession:
        """Stop a bot session"""
        # Get session
        session = self.get_bot_session(session_id, user_id)

        # Verify session is in a valid state to stop
        if session.status in [
            BotSessionStatus.STOPPED,
            BotSessionStatus.COMPLETED,
            BotSessionStatus.FAILED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is already in final state: {session.status}",
            )

        try:
            # TODO: This is where we would stop the Kubernetes pod
            # For the MVP, we'll just update the status

            # Update session status
            session.status = BotSessionStatus.STOPPED
            session.finished_at = datetime.now(timezone.utc)

            # Add event
            event = BotEvent(
                bot_session_id=session.id,
                type="system",
                message="Bot stopped",
                severity="info",
            )

            self.db.add(event)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            return session

        except Exception as e:
            logger.exception(f"Error stopping bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error stopping bot session: {str(e)}",
            )

    def pause_bot_session(self, session_id: UUID, user_id: UUID) -> BotSession:
        """Pause a bot session"""
        # Get session
        session = self.get_bot_session(session_id, user_id)

        # Verify session is running
        if session.status != BotSessionStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is not running (current status: {session.status})",
            )

        try:
            # Update session status
            session.status = BotSessionStatus.PAUSED
            session.updated_at = datetime.now(timezone.utc)

            # Add event
            event = BotEvent(
                bot_session_id=session.id,
                type="system",
                message="Bot paused",
                severity="info",
            )

            self.db.add(event)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # TODO: In a real implementation, we would send a pause command to the bot

            return session

        except Exception as e:
            logger.exception(f"Error pausing bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error pausing bot session: {str(e)}",
            )

    def resume_bot_session(self, session_id: UUID, user_id: UUID) -> BotSession:
        """Resume a paused bot session"""
        # Get session
        session = self.get_bot_session(session_id, user_id)

        # Verify session is paused
        if session.status != BotSessionStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is not paused (current status: {session.status})",
            )

        try:
            # Update session status
            session.status = BotSessionStatus.RUNNING
            session.resumed_at = datetime.now(timezone.utc)

            # Calculate pause duration
            if session.paused_at:
                pause_duration = int(
                    (session.resumed_at - session.paused_at).total_seconds()
                )
                session.total_paused_time = (
                    session.total_paused_time or 0
                ) + pause_duration

            # Add event
            event = BotEvent(
                bot_session_id=session.id,
                type="system",
                message="Bot resumed",
                severity="info",
            )

            self.db.add(event)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # TODO: In a real implementation, we would send a resume command to the bot

            return session

        except Exception as e:
            logger.exception(f"Error resuming bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error resuming bot session: {str(e)}",
            )

    # ======================================================
    # BOT METRICS AND MONITORING
    # ======================================================

    def update_bot_metrics(
        self,
        session_id: UUID,
        total_applied: int,
        total_success: int,
        total_failed: int,
    ) -> bool:
        """Update bot metrics"""
        try:
            session = self.db.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not session:
                logger.error(f"Session {session_id} not found for metrics update")
                return False

            session.total_applied = total_applied
            session.total_success = total_success
            session.total_failed = total_failed
            session.last_heartbeat_at = datetime.now(timezone.utc)

            self.db.add(session)
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error updating bot metrics: {str(e)}")
            return False

    def record_bot_apply(
        self,
        session_id: UUID,
        job_id: str,
        job_title: str,
        job_url: str,
        company_name: str,
        success: bool = False,
        status: BotApplyStatus = BotApplyStatus.STARTED,
        failed_reason: str | None = None,
    ) -> BotApply | None:
        """Record a job application"""
        try:
            # Check if session exists
            session = self.db.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not session:
                logger.error(f"Session {session_id} not found for apply record")
                return None

            # Create apply record
            apply = BotApply(
                bot_session_id=session_id,
                job_id=job_id,
                job_title=job_title,
                job_url=job_url,
                company_name=company_name,
                status=status,
                started_at=datetime.now(timezone.utc),
                failed=not success,
                failed_reason=failed_reason if not success else None,
                progress=100 if success or failed_reason else 0,
            )

            if success or failed_reason:
                apply.completed_at = datetime.now(timezone.utc)
                apply.total_time = (
                    0  # Would calculate real time in a full implementation
                )

            self.db.add(apply)

            # Update session metrics
            session.total_applied += 1
            if success:
                session.total_success += 1
            elif failed_reason:
                session.total_failed += 1

            self.db.add(session)
            self.db.commit()
            self.db.refresh(apply)

            return apply

        except Exception as e:
            logger.error(f"Error recording bot apply: {str(e)}")
            return None

    def add_bot_event(
        self,
        session_id: UUID,
        event_type: str,
        message: str,
        severity: str = "info",
        details: dict[str, Any] | None = None,
    ) -> BotEvent | None:
        """Add a bot event"""
        try:
            # Check if session exists
            session = self.db.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not session:
                logger.error(f"Session {session_id} not found for event")
                return None

            # Create event
            event = BotEvent(
                bot_session_id=session_id,
                type=event_type,
                message=message,
                severity=severity,
                details=json.dumps(details) if details else None,
            )

            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            return event

        except Exception as e:
            logger.error(f"Error adding bot event: {str(e)}")
            return None

    def get_session_events(
        self,
        session_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        event_type: list[str] | None = None,
    ) -> tuple[list[BotEvent], int]:
        """Get events for a session"""
        # Verify permission
        session = self.get_bot_session(session_id, user_id)
        assert session

        # Build query
        query = select(BotEvent).where(BotEvent.bot_session_id == session_id)

        # Apply event type filter
        if event_type:
            event_conditions = []
            for t in event_type:
                event_conditions.append(BotEvent.type == t)

            if event_conditions:
                query = query.where(or_(*event_conditions))

        # Get total count
        all_events = self.db.exec(query).all()
        total = len(all_events)

        # Apply pagination and ordering
        query = (
            query.offset(skip).limit(limit).order_by("created_at DESC")
        )  # Using string column name

        events = self.db.exec(query).all()

        return cast(list[BotEvent], events), total

    def get_session_applies(
        self,
        session_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
    ) -> tuple[list[BotApply], int]:
        """Get applications for a session"""
        # Verify permission
        session = self.get_bot_session(session_id, user_id)
        assert session

        # Build query
        query = select(BotApply).where(BotApply.bot_session_id == session_id)

        # Apply status filter
        if status:
            status_conditions = []
            for s in status:
                try:
                    status_conditions.append(
                        BotApply.status == BotApplyStatus[s.upper()]
                    )
                except (KeyError, ValueError):
                    # Skip invalid status values instead of comparing strings
                    logger.warning(f"Invalid apply status value: {s}")
                    continue

            if status_conditions:
                query = query.where(or_(*status_conditions))

        # Get total count
        all_applies = self.db.exec(query).all()
        total = len(all_applies)

        # Apply pagination and ordering
        query = (
            query.offset(skip).limit(limit).order_by("started_at DESC")
        )  # Using string column name

        applies = self.db.exec(query).all() or []

        return cast(list[BotApply], applies), total
