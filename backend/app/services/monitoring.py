import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.bot import BotSession, BotSessionStatus, KubernetesPodStatus

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring and maintaining bot sessions."""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def check_stalled_sessions(self, timeout_minutes: int = 10) -> list[BotSession]:
        """Find sessions that appear to be stalled (no heartbeat updates)"""
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                minutes=timeout_minutes
            )

            # Get running sessions that haven't had a heartbeat since the cutoff
            # Use a more robust query to handle potential None values
            query = (
                select(BotSession)
                .where(BotSession.status == BotSessionStatus.RUNNING)
                .where(
                    # This handles cases where last_heartbeat_at might be None
                    (BotSession.last_heartbeat_at is None)
                    | (BotSession.last_heartbeat_at < cutoff_time)  # type: ignore
                )
            )

            return list(self.db.exec(query).all())

        except Exception as e:
            logger.error(f"Error checking for stalled sessions: {str(e)}")
            return []

    def check_zombie_sessions(self) -> list[BotSession]:
        """Find zombie sessions (running but pod is gone or failed)"""
        # In a real implementation, this would check Kubernetes for actual pod status
        # For the MVP, we'll just look for sessions that have been running for too long
        try:
            # Get sessions that have been running for more than 24 hours
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

            query = (
                select(BotSession)
                .where(BotSession.status == BotSessionStatus.RUNNING)
                .where(
                    # Handle cases where started_at might be None
                    (BotSession.started_at is None)
                    | (BotSession.started_at < cutoff_time)  # type: ignore
                )
            )

            return list(self.db.exec(query).all())

        except Exception as e:
            logger.error(f"Error checking for zombie sessions: {str(e)}")
            return []

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health metrics"""
        try:
            # Get session counts by status
            status_counts = {}
            for status in BotSessionStatus:
                query = (
                    select(func.count())
                    .select_from(BotSession)
                    .where(BotSession.status == status)
                )
                count = self.db.exec(query).one()
                status_counts[status.value] = count

            # Get recent sessions (last 24 hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_query = (
                select(func.count())
                .select_from(BotSession)
                .where(BotSession.created_at > cutoff_time)
            )
            recent_count = self.db.exec(recent_query).one()

            # Get sessions with errors
            error_query = (
                select(func.count())
                .select_from(BotSession)
                .where(BotSession.status == BotSessionStatus.FAILED)
            )
            error_count = self.db.exec(error_query).one()

            # Construct health report
            return {
                "total_sessions": sum(status_counts.values()),
                "status_counts": status_counts,
                "recent_sessions": recent_count,
                "error_sessions": error_count,
                "stalled_sessions": len(self.check_stalled_sessions()),
                "zombie_sessions": len(self.check_zombie_sessions()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def update_session_pod_status(
        self,
        session_id: UUID,
        pod_status: KubernetesPodStatus,
        pod_ip: str | None = None,
    ) -> bool:
        """Update a session with current pod status"""
        try:
            session = self.db.exec(
                select(BotSession).where(BotSession.id == session_id)
            ).first()

            if not session:
                logger.error(f"Session {session_id} not found for status update")
                return False

            # Update Kubernetes status
            session.kubernetes_pod_status = pod_status
            if pod_ip:
                session.kubernetes_pod_ip = pod_ip

            # Update session status based on pod status
            if pod_status == KubernetesPodStatus.RUNNING:
                if session.status not in [
                    BotSessionStatus.RUNNING,
                    BotSessionStatus.PAUSED,
                    BotSessionStatus.WAITING_INPUT,
                ]:
                    session.status = BotSessionStatus.RUNNING

            elif pod_status == KubernetesPodStatus.SUCCEEDED:
                session.status = BotSessionStatus.COMPLETED
                if not session.finished_at:
                    session.finished_at = datetime.now(timezone.utc)

            elif pod_status == KubernetesPodStatus.FAILED:
                session.status = BotSessionStatus.FAILED
                if not session.finished_at:
                    session.finished_at = datetime.now(timezone.utc)
                if not session.error_message:
                    session.error_message = "Pod failed in Kubernetes"

            # Save changes
            self.db.add(session)
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error updating session pod status: {str(e)}")
            self.db.rollback()
            return False

    def get_user_dashboard_stats(self, user_id: UUID) -> dict[str, Any]:
        """Get statistics for a user's dashboard."""
        try:
            # Get all sessions for the user
            query = select(BotSession).where(BotSession.user_id == user_id)
            sessions = self.db.exec(query).all()
            
            # Calculate total applications
            total_applications = sum(s.total_applied or 0 for s in sessions)
            successful_applications = sum(s.total_success or 0 for s in sessions)
            failed_applications = sum(s.total_failed or 0 for s in sessions)
            
            # Calculate pending applications (total - success - failed)
            pending_applications = total_applications - successful_applications - failed_applications
            
            # Calculate success and failure rates
            success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0
            failure_rate = (failed_applications / total_applications * 100) if total_applications > 0 else 0
            
            # Compile statistics
            return {
                "total_applications": total_applications,
                "successful_applications": successful_applications,
                "success_rate": round(success_rate, 1),
                "failed_applications": failed_applications,
                "failure_rate": round(failure_rate, 1),
                "pending_applications": pending_applications,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting user dashboard stats: {str(e)}")
            return {
                "total_applications": 0,
                "successful_applications": 0,
                "success_rate": 0.0,
                "failed_applications": 0,
                "failure_rate": 0.0,
                "pending_applications": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            }

    def cleanup_completed_sessions(self, older_than_days: int = 30) -> int:
        """Archive or clean up old completed sessions"""
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=older_than_days)

            # First, get completed and failed sessions with finished_at not null
            sessions_not_null = self.db.exec(
                select(BotSession).where(
                    (BotSession.status == BotSessionStatus.COMPLETED)
                    | (BotSession.status == BotSessionStatus.FAILED),
                    BotSession.finished_at is not None,
                )
            ).all()

            # Then filter them to find the ones older than cutoff
            old_sessions = [
                session
                for session in sessions_not_null
                if session.finished_at and session.finished_at < cutoff_time
            ]

            count = len(old_sessions)

            # In a real implementation, we might archive these to long-term storage
            # For the MVP, we'll just log that we found them
            logger.info(f"Found {count} old completed sessions that could be archived")

            return count

        except Exception as e:
            logger.error(f"Error cleaning up completed sessions: {str(e)}")
            return 0

    def get_session_statistics(
        self, user_id: UUID | None = None, days: int = 30
    ) -> dict[str, Any]:
        """Get statistics about bot sessions"""
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

            # Base query for sessions in the time period
            query = select(BotSession).where(BotSession.created_at > cutoff_time)

            # If user_id is provided, filter by user
            if user_id:
                query = query.where(BotSession.user_id == user_id)

            sessions = self.db.exec(query).all()

            # Calculate statistics
            total_sessions = len(sessions)
            completed_sessions = sum(
                bool(s.status == BotSessionStatus.COMPLETED) for s in sessions
            )
            failed_sessions = sum(
                bool(s.status == BotSessionStatus.FAILED) for s in sessions
            )

            total_applies = sum(s.total_applied for s in sessions)
            total_success = sum(s.total_success for s in sessions)
            total_failed_applies = sum(s.total_failed for s in sessions)

            # Success rate (avoid division by zero)
            success_rate = (
                (total_success / total_applies * 100) if total_applies > 0 else 0
            )

            # Calculate average applies per session for completed sessions
            completed_session_list = [
                s for s in sessions if s.status == BotSessionStatus.COMPLETED
            ]
            avg_applies = (
                sum(s.total_applied for s in completed_session_list)
                / len(completed_session_list)
                if completed_session_list
                else 0
            )

            # Calculate average session duration
            durations = []
            for s in completed_session_list:
                if s.started_at and s.finished_at:
                    duration = (s.finished_at - s.started_at).total_seconds()
                    # Subtract paused time if tracked
                    if s.total_paused_time:
                        duration -= s.total_paused_time
                    durations.append(duration)

            avg_duration = sum(durations) / len(durations) if durations else 0

            # Compile statistics
            stats = {
                "period_days": days,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "failed_sessions": failed_sessions,
                "completion_rate": (completed_sessions / total_sessions * 100)
                if total_sessions > 0
                else 0,
                "total_applies": total_applies,
                "successful_applies": total_success,
                "failed_applies": total_failed_applies,
                "apply_success_rate": success_rate,
                "avg_applies_per_session": avg_applies,
                "avg_session_duration_seconds": avg_duration,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting session statistics: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
