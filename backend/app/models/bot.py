import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Column, Field, ForeignKey, Relationship, SQLModel

from app.core.config import settings
from app.models.core import User

# ======================================================
# ENUMERAÇÕES
# ======================================================


class BotSessionStatus(Enum):
    """Estados possíveis para uma sessão do bot."""

    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    COMPLETED = "completed"
    WAITING_INPUT = "waiting"  # Para solicitação de 2FA ou CAPTCHA


class KubernetesPodStatus(Enum):
    """Estados possíveis para um pod no Kubernetes."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    STARTING = "starting"
    PAUSED = "paused"
    FAILED = "failed"
    UNKNOWN = "unknown"
    TERMINATING = "terminating"


class BotApplyStatus(Enum):
    """Status possíveis para uma aplicação."""

    SUCCESS = "success"
    FAILED = "failed"


class UserActionType(Enum):
    """Tipos de ações que o usuário pode precisar executar."""

    PROVIDE_2FA = "provide_2fa"
    SOLVE_CAPTCHA = "solve_captcha"
    ANSWER_QUESTION = "answer_question"
    CONFIRM_ACTION = "confirm_action"


class BotStyleChoice(str, Enum):
    """Estilos visuais disponíveis para o bot."""

    CLOYOLA_GREY = "Cloyola Grey"
    MODERN_BLUE = "Modern Blue"
    MODERN_GREY = "Modern Grey"
    DEFAULT = "Default"
    CLEAN_BLUE = "Clean Blue"


# ======================================================
# MODELOS DO BOT
# ======================================================


class Credentials(SQLModel, table=True):
    """Armazena credenciais do LinkedIn para uso pelo bot."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    email: str
    password: str

    obfuscated_email: str | None = None
    obfuscated_password: str | None = None

    # Relacionamentos
    user: User = Relationship(back_populates="credentials")
    bot_sessions: list["BotSession"] = Relationship(back_populates="credentials")

    def obfuscate_fields(self, plain_password: str) -> None:
        """Gera email parcialmente visível e senha em asteriscos."""
        self.obfuscate_email()
        self.obfuscate_password(plain_password)

    def obfuscate_password(self, plain_password: str) -> None:
        self.obfuscated_password = "*" * len(plain_password)

    def obfuscate_email(self) -> None:
        email_parts = self.email.split("@")

        if len(email_parts[0]) > 2:
            visible_part = email_parts[0][:2]
            hidden_part = "*" * (len(email_parts[0]) - 2)
        else:
            visible_part = email_parts[0][0]
            hidden_part = "*" * (len(email_parts[0]) - 1)

        domain = email_parts[1]
        self.obfuscated_email = f"{visible_part}{hidden_part}@{domain}"


class BotSession(SQLModel, table=True):
    """Sessão do bot."""

    __tablename__ = "bot_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    credentials_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("credentials.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    # Configurações de comportamento
    applies_limit: int = Field(default=200)
    style: BotStyleChoice = Field(default=BotStyleChoice.DEFAULT)

    # Chave de API para autenticação nos endpoints de webhook
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(16))

    # Estado e controle
    status: BotSessionStatus = Field(default=BotSessionStatus.STARTING)

    # Informações do Kubernetes
    kubernetes_pod_name: str = Field(
        default_factory=lambda: f"{settings.KUBERNETES_BOT_PREFIX}-{uuid4().hex[:8]}"
    )
    kubernetes_namespace: str = Field(default=settings.KUBERNETES_NAMESPACE)
    kubernetes_pod_status: KubernetesPodStatus | None = None
    kubernetes_pod_ip: str | None = None

    is_deleted: bool = Field(default=False)

    # Métricas básicas
    total_applied: int = Field(default=0)
    total_success: int = Field(default=0)
    total_failed: int = Field(default=0)

    # Controle de tempo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    resumed_at: datetime | None = None
    paused_at: datetime | None = None
    total_paused_time: int = Field(default=0)
    last_heartbeat_at: datetime | None = None

    # Mensagens
    last_status_message: str | None = None
    error_message: str | None = None

    # Relacionamentos
    user: User = Relationship(back_populates="bot_sessions")
    credentials: Credentials = Relationship(back_populates="bot_sessions")
    bot_applies: list["BotApply"] = Relationship(back_populates="bot_session")
    bot_events: list["BotEvent"] = Relationship(back_populates="bot_session")
    bot_user_actions: list["BotUserAction"] = Relationship(back_populates="bot_session")

    def create(self) -> None:
        """Indica criação do bot."""
        self.add_event("system", "Bot session created")

    def start(self) -> None:
        """Inicia a sessão do bot."""
        self.status = BotSessionStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.last_heartbeat_at = datetime.now(timezone.utc)
        self.add_event("system", "Bot session started")

    def pause(self) -> None:
        """Pausa a sessão do bot."""
        self.status = BotSessionStatus.PAUSED
        self.paused_at = datetime.now(timezone.utc)
        self.add_event("system", "Bot session paused")

    def resume(self) -> None:
        """Retoma a sessão do bot após pausa."""
        # Update session status
        self.status = BotSessionStatus.RUNNING
        self.resumed_at = datetime.now(timezone.utc)

        # Calculate pause duration
        if self.paused_at:
            pause_duration = int((self.resumed_at - self.paused_at).total_seconds())
            self.total_paused_time = (self.total_paused_time or 0) + pause_duration
        self.add_event("system", "Bot session resumed")

    def stop(self) -> None:
        """Para a sessão do bot."""
        self.status = BotSessionStatus.STOPPING
        self.add_event("system", "Bot session stopping")

    def complete(self) -> None:
        """Marca a sessão como concluída."""
        self.status = BotSessionStatus.COMPLETED
        self.finished_at = datetime.now(timezone.utc)
        self.add_event("system", "Bot session completed")

    def fail(self, reason: str) -> None:
        """Marca a sessão como falha."""
        self.status = BotSessionStatus.FAILED
        self.finished_at = datetime.now(timezone.utc)
        self.error_message = reason
        self.add_event("error", f"Bot session failed: {reason}")

    def update_kubernetes_status(
        self, status: KubernetesPodStatus, pod_ip: str | None = None
    ) -> None:
        """Atualiza o status do pod no Kubernetes."""
        self.kubernetes_pod_status = status
        if pod_ip:
            self.kubernetes_pod_ip = pod_ip

    def heartbeat(self) -> None:
        """Atualiza o timestamp do último heartbeat do bot."""
        self.last_heartbeat_at = datetime.now(timezone.utc)

    def wait_for_user_input(self) -> None:
        """Coloca a sessão em modo de espera por entrada do usuário."""
        self.status = BotSessionStatus.WAITING_INPUT
        self.add_event("system", "Waiting for user input")

    def is_healthy(self) -> bool:
        """Verifica se a sessão está saudável (recebendo heartbeats regulares)."""
        if not self.last_heartbeat_at:
            return False

        # Se não recebeu heartbeat nos últimos 2 minutos, não está saudável
        time_since_last_heartbeat = (
            datetime.now(timezone.utc) - self.last_heartbeat_at
        ).total_seconds()
        return time_since_last_heartbeat < 120  # 2 minutos

    def add_event(
        self, event_type: str, message: str, severity: str = "info"
    ) -> "BotEvent | None":
        """Adiciona um evento à sessão."""
        # Verifica se o ID da sessão é válido
        if not self.id:
            # Se a sessão não tem ID, não cria o evento
            return None

        event = BotEvent(
            bot_session_id=self.id, type=event_type, severity=severity, message=message
        )

        # Se o relacionamento bot_events estiver disponível como lista, adicione diretamente
        if hasattr(self, "bot_events") and isinstance(self.bot_events, list):
            self.bot_events.append(event)

        return event


class BotUserAction(SQLModel, table=True):
    """Ação que requer intervenção do usuário, como fornecer token 2FA ou resolver CAPTCHA."""

    __tablename__ = "bot_user_actions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("bot_sessions.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    action_type: UserActionType
    description: str = Field(max_length=1000)

    # Campos específicos para diferentes tipos de ação
    input_field: str | None = Field(
        default=None, max_length=100
    )  # Nome do campo para entrada

    # Estado da ação
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    is_completed: bool = Field(default=False)
    user_input: str | None = Field(default=None, max_length=1000)  # Resposta do usuário

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_user_actions")

    def complete(self, user_input: str) -> None:
        """Marca a ação como concluída com a entrada do usuário."""
        self.is_completed = True
        self.completed_at = datetime.now(timezone.utc)
        self.user_input = user_input

        # Se a sessão estava aguardando, retornar para running
        if (
            hasattr(self, "bot_session")
            and self.bot_session.status == BotSessionStatus.WAITING_INPUT
        ):
            self.bot_session.status = BotSessionStatus.RUNNING


class BotApply(SQLModel, table=True):
    """Aplicação para uma vaga."""

    __tablename__ = "bot_applies"

    id: int | None = Field(default=None, primary_key=True)
    bot_session_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("bot_sessions.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    # Status e progresso
    status: BotApplyStatus = Field(default=BotApplyStatus.SUCCESS)

    # Tempos
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_time: int = 0  # em segundos

    # Informações da vaga
    job_title: str | None = None
    job_url: str | None = None
    company_name: str | None = None

    # Resultado
    failed_reason: str | None = None

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_applies")


class BotEvent(SQLModel, table=True):
    """Evento ocorrido durante a execução do bot."""

    __tablename__ = "bot_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("bot_sessions.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    type: str  # log, error, warning, info, kubernetes, system, user_action
    severity: str = Field(default="info")  # info, warning, error, critical
    message: str
    details: str | None = None  # JSON string with additional details
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_events")


# ======================================================
# API MODELS (para uso nas rotas)
# ======================================================


class CredentialsCreate(SQLModel):
    """Modelo para criação de credenciais."""

    email: str
    password: str


class CredentialsUpdate(SQLModel):
    email: str | None = None
    password: str | None = None


class CredentialsPublic(SQLModel):
    """Modelo para mostrar email e usuário escolher as credenciais para usar"""

    id: UUID
    email: str = Field(description="Obfuscated email")
    password: str = Field(default="********", description="Only asterisks")


class CredentialsInternal(SQLModel):
    id: UUID
    user_id: UUID
    email: str
    password: str

    obfuscated_email: str
    obfuscated_password: str


class ApplyCreate(SQLModel):
    """Modelo para criação de aplicação."""

    bot_session_id: UUID
    status: BotApplyStatus = BotApplyStatus.SUCCESS
    total_time: int = Field(default=0, description="Total time in seconds")

    # Informações da vaga
    job_title: str | None = None
    job_url: str | None = None
    company_name: str | None = None

    # Resultado
    failed_reason: str | None = None


class ApplyPublic(SQLModel):
    bot_session_id: UUID
    status: BotApplyStatus = BotApplyStatus.SUCCESS
    total_time: int = Field(default=0, description="Total time in seconds")

    # Informações da vaga
    job_title: str | None = None
    job_url: str | None = None
    company_name: str | None = None


class UserActionCreate(SQLModel):
    """Modelo para criação de ação do usuário."""

    action_type: UserActionType
    description: str
    input_field: str | None = None


class UserActionPublic(SQLModel):
    action_type: UserActionType
    description: str
    input_field: str | None

    requested_at: datetime


class UserActionUpdate(SQLModel):
    """Modelo para atualização de ação do usuário."""

    user_input: str


class WebhookEvent(SQLModel):
    """Modelo para recebimento de eventos via webhook."""

    event_type: str
    data: dict[str, Any]


# ======================================================
# MODELO DE RESPOSTA PARA ESTATÍSTICAS DO DASHBOARD
# ======================================================


class UserDashboardStats(SQLModel):
    """Estatísticas do usuário para o dashboard."""

    total_applications: int
    successful_applications: int
    success_rate: float
    failed_applications: int
    failure_rate: float
    pending_applications: int
    timestamp: str
