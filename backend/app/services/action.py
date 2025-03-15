import logging
from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.integrations.kubernetes import kubernetes_manager
from app.models.bot import BotSession, BotSessionStatus, BotUserAction, UserActionType
from app.models.core import User

logger = logging.getLogger(__name__)


class UserActionService:
    """Service for managing user interaction with bots."""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def create_user_action(
        self,
        session: BotSession,
        action_type: UserActionType,
        description: str,
        input_field: str | None = None,
    ) -> BotUserAction | None:
        """Create a new user action for a bot session"""
        try:
            # Create user action
            action = BotUserAction(
                bot_session_id=session.id,
                action_type=action_type,
                description=description,
                input_field=input_field,
            )

            # Update session status to waiting
            session.status = BotSessionStatus.WAITING_INPUT
            session.last_status_message = f"Waiting for user input: {description}"

            # TODO: ALERT USER IN EMAIL AND INTERFACE

            # Add to database
            self.db.add(action)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(action)

            return action

        except Exception as e:
            logger.error(f"Error creating user action: {str(e)}")
            self.db.rollback()
            return None

    def get_action_by_id(self, action_id: UUID, user: User) -> BotUserAction:
        """Get a specific user action by ID with permission check"""
        action = self.db.exec(
            select(BotUserAction).where(BotUserAction.id == action_id)
        ).first()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User action not found"
            )

        # Check if user has access to this action
        session = self.db.exec(
            select(BotSession).where(BotSession.id == action.bot_session_id)
        ).first()

        if not session or (session.user_id != user.id and not user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this user action",
            )

        return action

    def get_session_actions(
        self,
        session_id: UUID,
        user: User,
        skip: int = 0,
        limit: int = 100,
        include_completed: bool = False,
    ) -> tuple[list[BotUserAction], int]:
        """Get user actions for a session with pagination and filtering"""
        # First verify permission to access this session
        session = self.db.exec(
            select(BotSession).where(BotSession.id == session_id)
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bot session not found"
            )

        if session.user_id != user.id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this session",
            )

        # Build query
        query = select(BotUserAction).where(BotUserAction.bot_session_id == session_id)

        # Filter out completed actions if requested
        if not include_completed:
            query = query.where(BotUserAction.is_completed is False)

        # Get total count
        all_actions = self.db.exec(query).all()
        total = len(all_actions)

        # Apply pagination and ordering (most recent first)
        query = (
            query.offset(skip).limit(limit).order_by(BotUserAction.requested_at.desc())  # type: ignore
        )

        actions = self.db.exec(query).all()

        return cast(list[BotUserAction], actions), total

    def get_user_pending_actions(self, user_id: UUID) -> list[BotUserAction]:
        """Get all pending user actions across all sessions for a user"""
        # Get all sessions for this user
        user_sessions = self.db.exec(
            select(BotSession).where(BotSession.user_id == user_id)
        ).all()

        session_ids = [session.id for session in user_sessions]

        if not session_ids:
            return []

        # Build query for pending actions from these sessions
        query = (
            select(BotUserAction)
            .where(BotUserAction.bot_session_id.in_(session_ids))  # type: ignore
            .where(BotUserAction.is_completed is False)
            .order_by(BotUserAction.requested_at.desc())  # type: ignore
        )

        actions = self.db.exec(query).all()

        return cast(list[BotUserAction], actions)

    def complete_action(
        self, action_id: UUID, session_id: UUID, user: User, user_input: str
    ) -> BotUserAction:
        """Complete a user action with the provided input"""
        # Get the action and verify permissions
        action = self.get_action_by_id(action_id, user)

        if action.bot_session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found",
            )

        if action.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This action has already been completed",
            )

        try:
            # Mark action as completed
            action.is_completed = True
            action.completed_at = datetime.now(timezone.utc)
            action.user_input = user_input

            # Update session status if it was waiting for this action
            session = self.db.exec(
                select(BotSession).where(BotSession.id == action.bot_session_id)
            ).first()

            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found",
                )

            if session and session.status == BotSessionStatus.WAITING_INPUT:
                # Check if there are other pending actions for this session
                other_pending = self.db.exec(
                    select(BotUserAction)
                    .where(BotUserAction.bot_session_id == session.id)
                    .where(BotUserAction.id != action.id)
                    .where(BotUserAction.is_completed is False)
                ).first()

                # If no other pending actions, set session back to running
                if not other_pending:
                    session.status = BotSessionStatus.RUNNING
                    session.last_status_message = "Continuing after user input"
                    self.db.add(session)

            # Save changes
            self.db.add(action)
            self.db.commit()
            self.db.refresh(action)

            if kubernetes_manager.initialized:
                success, message, status_code = kubernetes_manager.send_request_to_bot(
                    session.kubernetes_pod_name,
                    "POST",
                    f"/action/{action.id}",
                    data=action.model_dump(mode="json"),
                )

                if not success or not (status_code and status_code < 399):
                    logger.error(f"Error sending request to bot: {message}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error sending request to bot",
                    )

            return action

        except Exception as e:
            logger.error(f"Error completing user action: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error completing user action: {str(e)}",
            )

    def cancel_action(self, action_id: UUID, user: User) -> bool:
        """Cancel a user action (mark as completed but with cancelled status)"""
        # Get the action and verify permissions
        action = self.get_action_by_id(action_id, user)

        if action.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This action has already been completed",
            )

        try:
            # Mark action as completed with cancelled status
            action.is_completed = True
            action.completed_at = datetime.now(timezone.utc)
            action.user_input = "CANCELLED"

            # Update session status if it was waiting for this action
            session = self.db.exec(
                select(BotSession).where(BotSession.id == action.bot_session_id)
            ).first()

            if session and session.status == BotSessionStatus.WAITING_INPUT:
                # Check if there are other pending actions for this session
                other_pending = self.db.exec(
                    select(BotUserAction)
                    .where(BotUserAction.bot_session_id == session.id)
                    .where(BotUserAction.id != action.id)
                    .where(BotUserAction.is_completed is False)
                ).first()

                # If no other pending actions, set session back to running
                if not other_pending:
                    session.status = BotSessionStatus.RUNNING
                    session.last_status_message = (
                        "Continuing after user action cancellation"
                    )
                    self.db.add(session)

            # Save changes
            self.db.add(action)
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error cancelling user action: {str(e)}")
            self.db.rollback()
            return False

    def delete_action(self, action_id: UUID, user: User) -> bool:
        """Delete a user action (only if it's not completed)"""
        # Get the action and verify permissions
        action = self.get_action_by_id(action_id, user)

        if action.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed actions cannot be deleted",
            )

        try:
            self.db.delete(action)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error deleting user action: {str(e)}")
            self.db.rollback()
            return False

    def get_actions_by_type(
        self,
        user_id: UUID,
        action_type: UserActionType,
        include_completed: bool = False,
    ) -> list[BotUserAction]:
        """Get all actions of a specific type for a user"""
        # Get all sessions for this user
        user_sessions = self.db.exec(
            select(BotSession).where(BotSession.user_id == user_id)
        ).all()

        session_ids = [session.id for session in user_sessions]

        if not session_ids:
            return []

        # Build query for actions of this type
        query = (
            select(BotUserAction)
            .where(BotUserAction.bot_session_id.in_(session_ids))  # type: ignore
            .where(BotUserAction.action_type == action_type)
        )

        # Filter completed if requested
        if not include_completed:
            query = query.where(BotUserAction.is_completed is False)

        # Order by most recent first
        query = query.order_by(BotUserAction.requested_at.desc())  # type: ignore

        actions = self.db.exec(query).all()

        return cast(list[BotUserAction], actions)

    def expire_old_actions(self, timeout_hours: int = 24) -> int:
        """Mark old pending actions as expired (auto-cancelled)"""
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)

            # Find pending actions older than the cutoff
            query = (
                select(BotUserAction)
                .where(BotUserAction.is_completed is False)
                .where(BotUserAction.requested_at < cutoff_time)
            )

            old_actions = self.db.exec(query).all()

            # Mark each as completed with EXPIRED status
            for action in old_actions:
                action.is_completed = True
                action.completed_at = datetime.now(timezone.utc)
                action.user_input = "EXPIRED"
                self.db.add(action)

                # Log the expiration
                logger.info(f"Action {action.id} expired after {timeout_hours} hours")

            # Commit changes
            self.db.commit()

            return len(old_actions)

        except Exception as e:
            logger.error(f"Error expiring old actions: {str(e)}")
            self.db.rollback()
            return 0
