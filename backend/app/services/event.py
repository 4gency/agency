import json
import logging
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, or_, select

from app.models.bot import BotEvent, BotSession
from app.models.core import User

logger = logging.getLogger(__name__)


class EventService:
    """Service for managing bot events."""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db

    def add_event(
        self,
        session_id: UUID,
        event_type: str,
        message: str,
        severity: str = "info",
        details: dict[str, Any] | None = None,
    ) -> BotEvent | None:
        """Add a new event to a bot session"""
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
            self.db.rollback()
            return None

    def get_event_by_id(self, event_id: UUID, user: User) -> BotEvent:
        """Get a specific event by ID with permission check"""
        event = self.db.exec(select(BotEvent).where(BotEvent.id == event_id)).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )

        # Check if user has access to this event
        session = self.db.exec(
            select(BotSession).where(BotSession.id == event.bot_session_id)
        ).first()

        if not session or (session.user_id != user.id and not user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this event",
            )

        return event

    def get_session_events(
        self,
        session_id: UUID,
        user: User,
        skip: int = 0,
        limit: int = 100,
        event_type: list[str] | None = None,
        severity: list[str] | None = None,
    ) -> tuple[list[BotEvent], int]:
        """Get events for a session with pagination and filtering"""
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
        query = select(BotEvent).where(BotEvent.bot_session_id == session_id)

        # Apply event type filter
        if event_type:
            event_conditions = [BotEvent.type == t for t in event_type]
            if event_conditions:
                query = query.where(or_(*event_conditions))

        # Apply severity filter
        if severity:
            severity_conditions = [BotEvent.severity == s for s in severity]
            if severity_conditions:
                query = query.where(or_(*severity_conditions))

        # Get total count
        all_events = self.db.exec(query).all()
        total = len(all_events)

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(BotEvent.created_at.desc())

        events = self.db.exec(query).all()

        return cast(list[BotEvent], events), total

    def get_user_events(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        event_type: list[str] | None = None,
        severity: list[str] | None = None,
    ) -> tuple[list[BotEvent], int]:
        """Get all events for a user across all sessions"""
        # Get all sessions for this user
        user_sessions = self.db.exec(
            select(BotSession).where(BotSession.user_id == user_id)
        ).all()

        session_ids = [session.id for session in user_sessions]

        if not session_ids:
            return [], 0

        # Build query for events from these sessions
        query = select(BotEvent).where(BotEvent.bot_session_id.in_(session_ids))

        # Apply event type filter
        if event_type:
            event_conditions = [BotEvent.type == t for t in event_type]
            if event_conditions:
                query = query.where(or_(*event_conditions))

        # Apply severity filter
        if severity:
            severity_conditions = [BotEvent.severity == s for s in severity]
            if severity_conditions:
                query = query.where(or_(*severity_conditions))

        # Get total count
        all_events = self.db.exec(query).all()
        total = len(all_events)

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(BotEvent.created_at.desc())

        events = self.db.exec(query).all()

        return cast(list[BotEvent], events), total

    def delete_event(self, event_id: UUID, user: User) -> bool:
        """Delete an event with permission check"""
        event = self.get_event_by_id(event_id, user)  # This already checks permissions

        try:
            self.db.delete(event)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            self.db.rollback()
            return False

    def delete_session_events(self, session_id: UUID, user: User) -> int:
        """Delete all events for a session with permission check"""
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

        try:
            # Get all events for this session
            events = self.db.exec(
                select(BotEvent).where(BotEvent.bot_session_id == session_id)
            ).all()

            count = len(events)

            # Delete all events
            for event in events:
                self.db.delete(event)

            self.db.commit()
            return count

        except Exception as e:
            logger.error(f"Error deleting session events: {str(e)}")
            self.db.rollback()
            return 0
