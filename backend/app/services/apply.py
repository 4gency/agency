import logging
from typing import cast
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import String, desc
from sqlalchemy import cast as sa_cast
from sqlmodel import Session, col, func, or_, select

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

    def get_apply_by_id(self, apply_id: int, session_id: UUID, user: User) -> BotApply:
        """Get a specific application by ID with permission check"""
        apply = self.db.exec(select(BotApply).where(BotApply.id == apply_id)).first()

        if not apply or apply.bot_session_id != session_id:
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

        # Apply status filter - garantindo filtragem eficiente no banco de dados
        if status and len(status) > 0:
            # Normalize status para lowercase
            status_lower = [s.lower() for s in status if s]
            if status_lower:
                # Cria condições de filtro para cada status na lista
                # Convertendo os valores de enumeração para string antes de comparar
                status_conditions = [
                    sa_cast(BotApply.status, String).lower() == s for s in status_lower
                ]
                # Combina as condições com OR
                query = query.where(or_(*status_conditions))

        # Primeiro obtém o total com os filtros aplicados (sem paginação)
        filtered_count_query = select(func.count()).select_from(query.subquery())
        total = self.db.exec(filtered_count_query).one() or 0

        # Adiciona ordenação e paginação
        paginated_query = (
            query.order_by(desc(col(BotApply.created_at))).offset(skip).limit(limit)
        )

        # Executa a consulta
        applies = self.db.exec(paginated_query).all() or []

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
        query = select(BotApply).where(col(BotApply.bot_session_id).in_(session_ids))

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
        query = query.offset(skip).limit(limit).order_by(desc(col(BotApply.created_at)))

        applies = self.db.exec(query).all() or []

        return cast(list[BotApply], applies), total

    def get_applies_summary(
        self, session_id: UUID, user: User
    ) -> tuple[int, dict[str, int], dict[str, int], int, list[BotApply]]:
        """
        Get a summary of job applications for a specific bot session.

        Returns:
            - total_applies: Total number of applications
            - status_counts: Dictionary with counts by status
            - company_counts: Dictionary with counts by company
            - total_time: Total time spent on applications in seconds
            - latest_applies: List of the most recent applications
        """
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

        # Get all applies for this session
        applies = self.db.exec(
            select(BotApply)
            .where(BotApply.bot_session_id == session_id)
            .order_by(desc(col(BotApply.created_at)))
        ).all()

        # Process applies to create summary data
        status_counts: dict[str, int] = {"success": 0, "failed": 0}
        company_counts: dict[str, int] = {}
        total_time = 0

        for apply in applies:
            # Count by status - garantindo que use as chaves corretas
            # Converte para o valor do enum sem o prefixo da classe
            if apply.status == BotApplyStatus.SUCCESS:
                status_counts["success"] += 1
            elif apply.status == BotApplyStatus.FAILED:
                status_counts["failed"] += 1

            # Count by company
            if apply.company_name:
                if apply.company_name in company_counts:
                    company_counts[apply.company_name] += 1
                else:
                    company_counts[apply.company_name] = 1

            # Sum total time
            total_time += apply.total_time or 0

        # Get the latest applies (limiting to 5)
        latest_applies = applies[:5] if applies else []

        return (
            len(applies),
            status_counts,
            company_counts,
            total_time,
            cast(list[BotApply], latest_applies),
        )

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

    def delete_apply(self, apply_id: int, session_id: UUID, user: User) -> bool:
        """Delete an application record with permission check"""
        apply = self.get_apply_by_id(
            apply_id, session_id, user
        )  # This already checks permissions

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
