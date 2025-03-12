#!/usr/bin/env python3
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class BotSessionStatus(str, Enum):
    """Possible statuses for a bot session."""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_INPUT = "waiting"


class BotApplyStatus(str, Enum):
    """Possible statuses for a job application."""
    SUCCESS = "success"
    FAILED = "failed"


class UserActionType(str, Enum):
    """Types of actions that can be requested from the user."""
    PROVIDE_2FA = "provide_2fa"
    SOLVE_CAPTCHA = "solve_captcha"
    ANSWER_QUESTION = "answer_question"
    CONFIRM_ACTION = "confirm_action"


class BotApplyCreate(BaseModel):
    """Model for creating an application record."""
    status: BotApplyStatus = BotApplyStatus.SUCCESS
    total_time: int = 0
    job_title: Optional[str] = None
    job_url: Optional[str] = None
    company_name: Optional[str] = None
    failed_reason: Optional[str] = None


class BotEventCreate(BaseModel):
    """Model for creating a bot event."""
    type: str
    message: str
    severity: str = "info"
    details: Optional[Dict[str, Any]] = None


class BotUserActionCreate(BaseModel):
    """Model for creating a user action request."""
    action_type: UserActionType
    description: str
    input_field: Optional[str] = None


class UserActionResponse(BaseModel):
    """Model for a user action request response."""
    id: str
    message: str
    action_type: UserActionType
    description: str
    input_field: Optional[str] = None
    requested_at: str


class BotConfigResponse(BaseModel):
    """Model for bot configuration response."""
    user_config: str
    user_resume: str 