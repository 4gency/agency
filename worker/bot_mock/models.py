#!/usr/bin/env python3
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class BotSessionStatus(str, Enum):
    """Status possíveis para uma sessão de bot."""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_INPUT = "waiting"


class BotApplyStatus(str, Enum):
    """Status possíveis para uma aplicação de emprego."""
    SUCCESS = "success"
    FAILED = "failed"


class UserActionType(str, Enum):
    """Tipos de ações que podem ser solicitadas ao usuário."""
    PROVIDE_2FA = "provide_2fa"
    SOLVE_CAPTCHA = "solve_captcha"
    ANSWER_QUESTION = "answer_question"
    CONFIRM_ACTION = "confirm_action"


class BotApplyCreate(BaseModel):
    """Modelo para criar um registro de aplicação."""
    status: BotApplyStatus = BotApplyStatus.SUCCESS
    total_time: int = 0
    job_title: Optional[str] = None
    job_url: Optional[str] = None
    company_name: Optional[str] = None
    failed_reason: Optional[str] = None


class BotEventCreate(BaseModel):
    """Modelo para criar um evento do bot."""
    type: str
    message: str
    severity: str = "info"
    details: Optional[Dict[str, Any]] = None


class BotUserActionCreate(BaseModel):
    """Modelo para criar uma solicitação de ação do usuário."""
    action_type: UserActionType
    description: str
    input_field: Optional[str] = None


class UserActionResponse(BaseModel):
    """Modelo para resposta de uma solicitação de ação do usuário."""
    id: str
    message: str
    action_type: UserActionType
    description: str
    input_field: Optional[str] = None
    requested_at: str


class BotConfigResponse(BaseModel):
    """Modelo para resposta da configuração do bot."""
    user_config: str
    user_resume: str 