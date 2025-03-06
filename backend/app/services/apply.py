import logging
from typing import cast
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlmodel import Session, or_, select

from app.models.bot import BotApply, BotApplyStatus, BotSession
from app.models.core import User

logger = logging.getLogger(__name__)


class ApplyService:
    """Service for managing bot job applications."""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def create_apply(
        self,
        session_id: UUID,
        total_time: int = 0,
        job_title: str | None = None,
        job_url: str | None = None,
        company_name: str | None = None,
        failed_reason: str | None = None,
        status: BotApplyStatus = BotApplyStatus.SUCCESS,
    ) -> BotApply | None:
        """Create a new job application record"""
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
                total_time=total_time,
                job_title=job_title,
                job_url=job_url,
                company_name=company_name,
                status=status,
                failed_reason=failed_reason,
            )

            self.db.add(apply)

            # Update session metrics
            session.total_applied += 1
            if status == BotApplyStatus.SUCCESS:
                session.total_success += 1
            else:
                session.total_failed += 1

            self.db.add(session)
            self.db.commit()
            self.db.refresh(apply)

            return apply

        except Exception as e:
            logger.error(f"Error creating bot apply: {str(e)}")
            self.db.rollback()
            return None

    def get_apply_by_id(self, apply_id: int, user: User) -> BotApply:
        """Get a specific application by ID with permission check"""
        apply = self.db.exec(select(BotApply).where(BotApply.id == apply_id)).first()

        if not apply:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        # Check if user has access to this application
        session = self.db.exec(
            select(BotSession).where(BotSession.id == apply.bot_session_id)
        ).first()

        if not session or (session.user_id != user.id and not user.is_superuser):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this application",
            )

        return apply

    def get_session_applies(
        self,
        session_id: UUID,
        user: User,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
    ) -> tuple[list[BotApply], int]:
        """Get applications for a session with pagination and filtering"""
        # First verify permission to access this session
        session = self.db.exec(
            select(BotSession).where(BotSession.id == session_id)
        ).first()

        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Bot session not found",
            )

        if session.user_id != user.id and not user.is_superuser:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this session",
            )

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
        query = query.offset(skip).limit(limit).order_by(BotApply.created_at.desc())  # type: ignore

        applies = self.db.exec(query).all() or []

        return cast(list[BotApply], applies), total

    def get_user_applies(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
    ) -> tuple[list[BotApply], int]:
        """Get all applications for a user across all sessions"""
        # Get all sessions for this user
        user_sessions = self.db.exec(
            select(BotSession).where(BotSession.user_id == user_id)
        ).all()

        session_ids = [session.id for session in user_sessions]

        if not session_ids:
            return [], 0

        # Build query for applications from these sessions
        query = select(BotApply).where(BotApply.bot_session_id.in_(session_ids))  # type: ignore

        # Apply status filter
        if status:
            status_conditions = []
            for s in status:
                try:
                    status_conditions.append(
                        BotApply.status == BotApplyStatus[s.upper()]
                    )
                except (KeyError, ValueError):
                    logger.warning(f"Invalid apply status value: {s}")
                    continue

            if status_conditions:
                query = query.where(or_(*status_conditions))

        # Get total count
        all_applies = self.db.exec(query).all()
        total = len(all_applies)

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(BotApply.created_at.desc())  # type: ignore

        applies = self.db.exec(query).all() or []

        return cast(list[BotApply], applies), total

    def update_apply_status(
        self, apply_id: int, status: BotApplyStatus, failed_reason: str | None = None
    ) -> BotApply | None:
        """Update the status of an application"""
        apply = self.db.exec(select(BotApply).where(BotApply.id == apply_id)).first()

        if not apply:
            return None

        # Get the session to update its metrics
        session = self.db.exec(
            select(BotSession).where(BotSession.id == apply.bot_session_id)
        ).first()

        if not session:
            logger.error(f"Session not found for apply ID {apply_id}")
            return None

        # Update session metrics based on status change
        if apply.status != status:
            if apply.status == BotApplyStatus.SUCCESS:
                session.total_success -= 1
            else:
                session.total_failed -= 1

            if status == BotApplyStatus.SUCCESS:
                session.total_success += 1
            else:
                session.total_failed += 1

        # Update apply
        apply.status = status
        if failed_reason:
            apply.failed_reason = failed_reason

        self.db.add(apply)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(apply)

        return apply

    def delete_apply(self, apply_id: int, user: User) -> bool:
        """Delete an application record with permission check"""
        apply = self.get_apply_by_id(apply_id, user)  # This already checks permissions

        try:
            # Update session metrics
            session = self.db.exec(
                select(BotSession).where(BotSession.id == apply.bot_session_id)
            ).first()

            if session:
                session.total_applied -= 1
                if apply.status == BotApplyStatus.SUCCESS:
                    session.total_success -= 1
                else:
                    session.total_failed -= 1

                self.db.add(session)

            # Delete the application
            self.db.delete(apply)
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error deleting application: {str(e)}")
            self.db.rollback()
            return False
