import logging
from datetime import datetime, timezone
from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.integrations.kubernetes import kubernetes_manager
from app.models.bot import (
    BotSession,
    BotSessionStatus,
    BotStyleChoice,
    KubernetesPodStatus,
)
from app.models.core import User

logger = logging.getLogger(__name__)


class BotService:
    """
    Service for managing LinkedIn application bot sessions.
    Focuses on core session lifecycle management.
    """

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def save_session(self, session: BotSession) -> BotSession:
        """Helper method to save a session, commit changes and refresh the object"""
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    # ======================================================
    # BOT SESSION MANAGEMENT
    # ======================================================

    def create_bot_session(
        self,
        user_id: UUID,
        credentials_id: UUID,
        applies_limit: int = 200,
        style: BotStyleChoice = BotStyleChoice.DEFAULT,
    ) -> BotSession:
        """Create a new bot session"""
        try:
            # Create session
            session = BotSession(
                user_id=user_id,
                credentials_id=credentials_id,
                applies_limit=applies_limit,
                status=BotSessionStatus.STARTING,
                style=style,
            )

            session = self.save_session(session)

            # Add creation event
            session.create()

            self.db.commit()
        except Exception as e:
            logger.exception(f"Error creating bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating bot session: {str(e)}",
            ) from e

        return session

    def get_bot_session(
        self, session_id: UUID, user: User, show_deleted: bool = True
    ) -> BotSession:
        """Get a bot session with permission check"""
        session = self.db.exec(
            select(BotSession).where(BotSession.id == session_id)
        ).first()

        if not session or (not show_deleted and session.is_deleted):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bot session not found"
            )

        if session.user_id != user.id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this session",
            )

        return session

    def get_user_sessions(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        show_deleted: bool = True,
    ) -> tuple[list[BotSession], int]:
        """Get all bot sessions for a user with pagination and filtering"""
        # Build query
        query = select(BotSession).where(BotSession.user_id == user.id)

        if not show_deleted:
            query = query.where(BotSession.is_deleted == False)

        # TODO: Apply status filter if provided
        # if status:
        #     status_conditions = []
        #     for s in status:
        #         try:
        #             status_conditions.append(
        #                 BotSession.status == BotSessionStatus[s.upper()]
        #             )
        #         except (KeyError, ValueError):
        #             logger.warning(f"Invalid session status value: {s}")
        #             continue

        #     if status_conditions:
        #         query = query.where(or_(*status_conditions))

        # Get total count for pagination
        all_sessions = self.db.exec(query).all()
        total = len(all_sessions)

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(BotSession.created_at.desc())  # type: ignore

        sessions = self.db.exec(query).all()

        return cast(list[BotSession], sessions), total

    def start_bot_session(self, session_id: UUID, user: User) -> BotSession:
        """Start a bot session"""
        # Get session with permission check
        session = self.get_bot_session(session_id, user)

        # Verify session is in a valid state to start
        if session.status not in [BotSessionStatus.STARTING, BotSessionStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is in {session.status} state, cannot start",
            )

        try:
            # Update session state
            session.start()
            session.kubernetes_pod_name = (
                f"{settings.KUBERNETES_BOT_PREFIX}-{session.id.hex[:8]}"
            )
            session.last_heartbeat_at = datetime.now(timezone.utc)

            if kubernetes_manager.initialized:
                result, message = kubernetes_manager.create_bot_deployment(session)

                if not result:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error creating bot deployment: {message}",
                    )

            # Save changes
            return self.save_session(session)

        except Exception as e:
            logger.exception(f"Error starting bot session: {str(e)}")

            # Update session on failure
            session.status = BotSessionStatus.FAILED
            session.error_message = f"Failed to start: {str(e)}"
            session.add_event("error", f"Failed to start: {str(e)}", "error")
            self.save_session(session)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error starting bot session: {str(e)}",
            )

    def stop_bot_session(self, session_id: UUID, user: User) -> BotSession:
        """Stop a bot session"""
        # Get session with permission check
        session = self.get_bot_session(session_id, user)

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
            # Update session state
            session.stop()

            if kubernetes_manager.initialized:
                result, message = kubernetes_manager.delete_bot(
                    session.kubernetes_pod_name
                )

                if not result:
                    logger.error(f"Error deleting bot session: {message}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error deleting bot session",
                    )

            session.complete()

            # Save changes
            return self.save_session(session)

        except Exception as e:
            logger.exception(f"Error stopping bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error stopping bot session: {str(e)}",
            ) from e

    def pause_bot_session(self, session_id: UUID, user: User) -> BotSession:
        """Pause a bot session"""
        # Get session with permission check
        session = self.get_bot_session(session_id, user)

        # Verify session is running
        if session.status != BotSessionStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is not running (current status: {session.status})",
            )

        try:
            # Update session state
            session.pause()

            if kubernetes_manager.initialized:
                result, message = kubernetes_manager.pause_bot(
                    session.kubernetes_pod_name
                )

                if not result:
                    logger.error(f"Error pausing bot session: {message}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error pausing bot session",
                    )

            # Save changes
            return self.save_session(session)

        except Exception as e:
            logger.exception(f"Error pausing bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error pausing bot session: {str(e)}",
            ) from e

    def resume_bot_session(self, session_id: UUID, user: User) -> BotSession:
        """Resume a paused bot session"""
        # Get session with permission check
        session = self.get_bot_session(session_id, user)

        # Verify session is paused
        if session.status != BotSessionStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is not paused (current status: {session.status})",
            )

        try:
            # Update session state
            session.resume()

            if kubernetes_manager.initialized:
                result, message = kubernetes_manager.resume_bot(
                    session.kubernetes_pod_name
                )

                if not result:
                    logger.error(f"Error resuming bot session: {message}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error resuming bot session",
                    )

            # Save changes
            return self.save_session(session)

        except Exception as e:
            logger.exception(f"Error resuming bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error resuming bot session: {str(e)}",
            ) from e

    def update_heartbeat(self, session_id: UUID) -> bool:
        """Update session heartbeat to show it's still alive"""
        try:
            session = self.db.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not session:
                logger.error(f"Session {session_id} not found for heartbeat update")
                return False

            if kubernetes_manager.initialized:
                pod_status, pod_message = kubernetes_manager.get_bot_status(
                    session.kubernetes_pod_name
                )

                if not pod_status:
                    logger.error(f"Error getting bot status: {pod_message}")
                    return False

                if pod_status == KubernetesPodStatus.PAUSED:
                    session.status = BotSessionStatus.PAUSED
                elif pod_status == KubernetesPodStatus.RUNNING:
                    session.status = BotSessionStatus.RUNNING
                elif pod_status == KubernetesPodStatus.STARTING:
                    session.status = BotSessionStatus.STARTING

            # Update heartbeat
            session.heartbeat()

            # Save changes
            self.db.add(session)
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error updating session heartbeat: {str(e)}")
            return False

    def update_session_status(
        self,
        session_id: UUID,
        status: BotSessionStatus,
        status_message: str | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Update a session's status"""
        try:
            session = self.db.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not session:
                logger.error(f"Session {session_id} not found for status update")
                return False

            # Update status
            session.status = status

            # Update optional fields if provided
            if status_message:
                session.last_status_message = status_message

            if error_message:
                session.error_message = error_message

            # Set finished_at for terminal states
            if (
                status
                in [
                    BotSessionStatus.STOPPED,
                    BotSessionStatus.COMPLETED,
                    BotSessionStatus.FAILED,
                ]
                and not session.finished_at
            ):
                session.finished_at = datetime.now(timezone.utc)

            # Save changes
            self.db.add(session)
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error updating session status: {str(e)}")
            return False

    def delete_bot_session(self, session_id: UUID, user: User) -> bool:
        """Delete a bot session (if in terminal state)"""
        # Get session with permission check
        session = self.get_bot_session(session_id, user)

        # Check if session is in a terminal state
        if session.status not in [
            BotSessionStatus.STOPPED,
            BotSessionStatus.COMPLETED,
            BotSessionStatus.FAILED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete session that is not in a terminal state",
            )

        try:
            session.is_deleted = True

            # ensure pod is deleted
            if kubernetes_manager.initialized:
                result, message = kubernetes_manager.delete_bot(
                    session.kubernetes_pod_name
                )

                if not result:
                    pass  # don't raise error if pod is not found

            self.db.add(session)
            self.db.commit()

            return True

        except Exception as e:
            logger.exception(f"Error deleting bot session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting bot session: {str(e)}",
            )
