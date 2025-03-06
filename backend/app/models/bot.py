import enum
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from app.models.core import User
from sqlmodel import Field, Relationship, SQLModel

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
    FAILED = "failed"
    UNKNOWN = "unknown"
    TERMINATING = "terminating"

class BotApplyStatus(Enum):
    """Status possíveis para uma aplicação."""
    AWAITING = "awaiting"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
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

class LinkedInCredentials(SQLModel, table=True):
    """Armazena credenciais do LinkedIn para uso pelo bot."""
    __tablename__ = "linkedin_credentials"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    email: str
    password: str
    
    # Relacionamentos
    user: User = Relationship(back_populates="linkedin_credentials")

class BotConfig(SQLModel, table=True):
    """Configuração do bot."""
    __tablename__ = "bot_configs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    name: str = Field(max_length=100)
    
    # Configuração de infraestrutura
    kubernetes_namespace: str = Field(default="bot-jobs", max_length=50)
    kubernetes_resources_cpu: str = Field(default="500m", max_length=20)
    kubernetes_resources_memory: str = Field(default="1Gi", max_length=20)
    
    # Configuração de armazenamento
    config_yaml: str = Field()  # Conteúdo YAML da configuração
    resume_yaml: str = Field()  # Conteúdo YAML do currículo
    
    # Configurações de comportamento
    max_applies_per_session: int = Field(default=200)
    
    # Controle de tempo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    user: User = Relationship(back_populates="bot_configs")
    bot_sessions: List["BotSession"] = Relationship(back_populates="bot_config")

class BotSession(SQLModel, table=True):
    """Sessão do bot."""
    __tablename__ = "bot_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    bot_config_id: UUID = Field(foreign_key="bot_configs.id")
    
    # Chave de API para autenticação nos endpoints de webhook
    api_key: str = Field(default_factory=lambda: str(uuid4()))
    
    # Estado e controle
    status: BotSessionStatus = Field(default=BotSessionStatus.STARTING)
    
    # Informações do Kubernetes
    kubernetes_pod_name: str = Field(default_factory=lambda: f"bot-{uuid4().hex[:8]}")
    kubernetes_namespace: str = Field(default="bot-jobs")
    kubernetes_pod_status: Optional[KubernetesPodStatus] = None
    kubernetes_pod_ip: Optional[str] = None
    
    # Métricas básicas
    total_applied: int = Field(default=0)
    total_success: int = Field(default=0)
    total_failed: int = Field(default=0)
    
    # Limites
    applies_limit: int = Field(default=50)
    
    # Controle de tempo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    last_heartbeat_at: Optional[datetime] = None
    
    # Mensagens
    last_status_message: Optional[str] = None
    error_message: Optional[str] = None
    
    # Relacionamentos
    user: User = Relationship(back_populates="bot_sessions")
    bot_config: BotConfig = Relationship(back_populates="bot_sessions")
    bot_applies: List["BotApply"] = Relationship(back_populates="bot_session")
    bot_events: List["BotEvent"] = Relationship(back_populates="bot_session")
    bot_user_actions: List["BotUserAction"] = Relationship(back_populates="bot_session")
    
    def start(self) -> None:
        """Inicia a sessão do bot."""
        self.status = BotSessionStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.last_heartbeat_at = datetime.now(timezone.utc)
        self.add_event("system", "Bot session started")
    
    def pause(self) -> None:
        """Pausa a sessão do bot."""
        self.status = BotSessionStatus.PAUSED
        self.add_event("system", "Bot session paused")
    
    def resume(self) -> None:
        """Retoma a sessão do bot após pausa."""
        self.status = BotSessionStatus.RUNNING
        self.last_heartbeat_at = datetime.now(timezone.utc)
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
    
    def update_kubernetes_status(self, status: KubernetesPodStatus, pod_ip: Optional[str] = None) -> None:
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
        time_since_last_heartbeat = (datetime.now(timezone.utc) - self.last_heartbeat_at).total_seconds()
        return time_since_last_heartbeat < 120  # 2 minutos
    
    def add_event(self, event_type: str, message: str, severity: str = "info") -> "BotEvent":
        """Adiciona um evento à sessão."""
        event = BotEvent(
            bot_session_id=self.id,
            type=event_type,
            severity=severity,
            message=message
        )
        
        # Se o relacionamento bot_events estiver disponível como lista, adicione diretamente
        if hasattr(self, "bot_events") and isinstance(self.bot_events, list):
            self.bot_events.append(event)
        
        return event

class BotUserAction(SQLModel, table=True):
    """Ação que requer intervenção do usuário, como fornecer token 2FA ou resolver CAPTCHA."""
    __tablename__ = "bot_user_actions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(foreign_key="bot_sessions.id")
    action_type: UserActionType
    description: str = Field(max_length=1000)

    # Campos específicos para diferentes tipos de ação
    input_field: Optional[str] = Field(default=None, max_length=100)  # Nome do campo para entrada
    extra_data: Optional[str] = Field(default=None, max_length=5000)  # Dados adicionais (URL da imagem CAPTCHA, etc.)

    # Estado da ação
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    is_completed: bool = Field(default=False)
    user_input: Optional[str] = Field(default=None, max_length=1000)  # Resposta do usuário

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_user_actions")
    
    def complete(self, user_input: str) -> None:
        """Marca a ação como concluída com a entrada do usuário."""
        self.is_completed = True
        self.completed_at = datetime.now(timezone.utc)
        self.user_input = user_input

        # Se a sessão estava aguardando, retornar para running
        if hasattr(self, "bot_session") and self.bot_session.status == BotSessionStatus.WAITING_INPUT:
            self.bot_session.status = BotSessionStatus.RUNNING

class BotApply(SQLModel, table=True):
    """Aplicação para uma vaga."""
    __tablename__ = "bot_applies"

    id: int | None = Field(default=None, primary_key=True)
    bot_session_id: UUID = Field(foreign_key="bot_sessions.id")
    
    # Status e progresso
    status: BotApplyStatus = Field(default=BotApplyStatus.AWAITING)
    progress: int = Field(default=0)  # 0-100% de progresso
    
    # Tempos
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_time: Optional[int] = None  # em segundos
    
    # Informações da vaga
    job_id: str
    job_title: str
    job_url: str
    company_name: Optional[str] = None
    
    # Informações adicionais da vaga
    job_description: Optional[str] = None
    job_location: Optional[str] = None
    
    # Resultado
    failed: bool = Field(default=False)
    failed_reason: Optional[str] = None
    
    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_applies")
    
    def complete(self, success: bool, reason: Optional[str] = None) -> None:
        """Marca a aplicação como concluída."""
        self.completed_at = datetime.now(timezone.utc)
        
        # Calcular tempo total
        if self.started_at:
            self.total_time = int((self.completed_at - self.started_at).total_seconds())
        
        if success:
            self.status = BotApplyStatus.SUCCESS
            self.progress = 100
        else:
            self.status = BotApplyStatus.FAILED
            self.failed = True
            self.failed_reason = reason
        
        # Atualizar contadores na sessão
        if hasattr(self, "bot_session"):
            if success:
                self.bot_session.total_success += 1
            else:
                self.bot_session.total_failed += 1
            self.bot_session.total_applied += 1

class BotEvent(SQLModel, table=True):
    """Evento ocorrido durante a execução do bot."""
    __tablename__ = "bot_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(foreign_key="bot_sessions.id")
    
    type: str  # log, error, warning, info, kubernetes, system, user_action
    severity: str = Field(default="info")  # info, warning, error, critical
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_events")

# ======================================================
# API MODELS (para uso nas rotas)
# ======================================================

class UserCreate(SQLModel):
    """Modelo para criação de usuário."""
    email: str
    name: str

class CredentialsCreate(SQLModel):
    """Modelo para criação de credenciais."""
    email: str
    password: str

class BotConfigCreate(SQLModel):
    """Modelo para criação de configuração do bot."""
    name: str
    config_yaml: str
    resume_yaml: str
    max_applies_per_session: int = 50
    kubernetes_namespace: str = "bot-jobs"

class SessionCreate(SQLModel):
    """Modelo para criação de sessão do bot."""
    bot_config_id: UUID
    applies_limit: int = 50

class KubernetesStatusUpdate(SQLModel):
    """Modelo para atualização de status do Kubernetes."""
    pod_status: KubernetesPodStatus
    pod_ip: Optional[str] = None

class ApplyCreate(SQLModel):
    """Modelo para criação de aplicação."""
    job_id: str
    job_title: str
    job_url: str
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    job_location: Optional[str] = None

class UserActionCreate(SQLModel):
    """Modelo para criação de ação do usuário."""
    action_type: UserActionType
    description: str
    input_field: Optional[str] = None
    extra_data: Optional[str] = None

class UserActionUpdate(SQLModel):
    """Modelo para atualização de ação do usuário."""
    user_input: str

class WebhookEvent(SQLModel):
    """Modelo para recebimento de eventos via webhook."""
    event_type: str
    data: dict
