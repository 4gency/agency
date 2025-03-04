# bot.py
import enum
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.models.core import (
    Subscription,
    SubscriptionMetric,
    User,
)

# ======================================================
# ENUMERAÇÕES
# ======================================================


class BotSessionStatus(Enum):
    """Estados possíveis para uma sessão do bot."""

    STARTING = "starting"  # Inicializando
    RUNNING = "running"  # Em execução
    PAUSED = "paused"  # Pausado pelo usuário
    STOPPING = "stopping"  # Em processo de parada
    STOPPED = "stopped"  # Parado pelo usuário
    FAILED = "failed"  # Falhou por erro
    COMPLETED = "completed"  # Concluído com sucesso
    WAITING_INPUT = "waiting"  # Aguardando input do usuário (2FA, etc)


class KubernetesPodStatus(Enum):
    """Estados possíveis para um pod no Kubernetes."""

    PENDING = "pending"  # Pod está sendo criado
    RUNNING = "running"  # Pod está em execução
    SUCCEEDED = "succeeded"  # Pod concluiu sua execução com sucesso
    FAILED = "failed"  # Pod falhou
    UNKNOWN = "unknown"  # Estado desconhecido
    TERMINATING = "terminating"  # Pod está sendo terminado


class BotCommandType(Enum):
    """Tipos de comandos que podem ser enviados ao bot."""

    START = "start"  # Iniciar o bot
    PAUSE = "pause"  # Pausar o bot
    RESUME = "resume"  # Retomar após pausa
    STOP = "stop"  # Parar o bot
    UPDATE_CONFIG = "update_config"  # Atualizar configuração
    RESTART = "restart"  # Reiniciar o bot


class UserActionType(Enum):
    """Tipos de ações que o usuário pode precisar executar."""

    PROVIDE_2FA = "provide_2fa"  # Fornecer token 2FA
    SOLVE_CAPTCHA = "solve_captcha"  # Resolver CAPTCHA
    ANSWER_QUESTION = "answer_question"  # Responder pergunta específica
    CONFIRM_ACTION = "confirm_action"  # Confirmar uma ação
    UPLOAD_FILE = "upload_file"  # Enviar arquivo adicional


class BotNotificationPriority(Enum):
    """Prioridades para notificações."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BotNotificationStatus(Enum):
    """Status possíveis para notificações."""

    PENDING = "pending"  # Aguardando envio
    SENT = "sent"  # Enviada
    FAILED = "failed"  # Falha no envio
    READ = "read"  # Lida pelo usuário
    EXPIRED = "expired"  # Expirada (não mais relevante)


class BotApplyStatus(Enum):
    """Status possíveis para uma aplicação."""

    AWAITING = "awaiting"  # Aguardando início
    STARTED = "started"  # Iniciada
    IN_PROGRESS = "in_progress"  # Em progresso
    FORM_FILLING = "form_filling"  # Preenchendo formulário
    UPLOADED = "uploaded"  # Enviando documentos
    SUBMITTED = "submitted"  # Submetida
    SUCCESS = "success"  # Concluída com sucesso
    FAILED = "failed"  # Falhou


class BotStyleChoice(str, enum.Enum):
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
    """
    Armazena credenciais do LinkedIn para uso pelo bot.
    """

    __tablename__ = "linkedin_credentials"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    subscription_id: UUID = Field(foreign_key="subscription.id", unique=True)
    user_id: UUID = Field(foreign_key="user.id")

    email: str
    password: str  # Em produção deve ser criptografado

    # Relacionamentos
    subscription: Subscription = Relationship(back_populates="linkedin_credentials")
    user: User = Relationship(back_populates="linkedin_credentials")


class BotConfiguration(SQLModel, table=True):
    """
    Configurações específicas do bot para cada assinatura.
    """

    __tablename__ = "bot_configurations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    subscription_id: UUID = Field(foreign_key="subscription.id", unique=True)
    user_id: UUID = Field(foreign_key="user.id")

    style_choice: BotStyleChoice = Field(default=BotStyleChoice.MODERN_BLUE)
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
    sec_ch_ua: str = Field(
        default='"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"'
    )
    sec_ch_ua_platform: str = Field(default="Windows")

    # Relacionamentos
    subscription: Subscription = Relationship(back_populates="bot_configuration")
    user: User = Relationship(back_populates="bot_configurations")


class BotConfig(SQLModel, table=True):
    """
    Configuração do bot. Armazena referências para os arquivos YAML de configuração e currículo.
    """

    __tablename__ = "bot_config"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    subscription_id: UUID = Field(foreign_key="subscription.id")
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=1000)

    # Configuração de infraestrutura
    cloud_provider: str = Field(
        default="https://br-se1.magaluobjects.com", max_length=200
    )
    kubernetes_namespace: str = Field(default="bot-jobs", max_length=50)
    kubernetes_resources_cpu: str = Field(
        default="500m", max_length=20
    )  # Requisição de CPU
    kubernetes_resources_memory: str = Field(
        default="1Gi", max_length=20
    )  # Requisição de memória
    kubernetes_limits_cpu: str = Field(default="1000m", max_length=20)  # Limite de CPU
    kubernetes_limits_memory: str = Field(
        default="2Gi", max_length=20
    )  # Limite de memória

    # Configuração de armazenamento
    config_bucket: str = Field(default="configs", max_length=50)
    config_yaml_key: str = Field(max_length=1000)
    config_yaml_created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    config_version: int = Field(default=1)

    # Histórico de configurações para rollback
    config_yaml_previous_key: str | None = Field(default=None, max_length=1000)
    config_yaml_previous_created_at: datetime | None = Field(default=None)

    # Currículo
    resume_bucket: str = Field(default="resumes", max_length=50)
    resume_yaml_key: str = Field(max_length=1000)
    resume_yaml_created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    resume_version: int = Field(default=1)

    # Histórico de currículos para rollback
    resume_yaml_previous_key: str | None = Field(default=None, max_length=1000)
    resume_yaml_previous_created_at: datetime | None = Field(default=None)

    # Configurações de comportamento
    max_applies_per_session: int = Field(default=50)  # Máximo de aplicações por sessão
    max_applies_per_day: int = Field(default=100)  # Máximo de aplicações por dia
    allow_dynamic_updates: bool = Field(
        default=False
    )  # Permite atualização de config durante execução
    auto_restart_on_failure: bool = Field(
        default=True
    )  # Reinicia automaticamente em caso de falha
    max_auto_restarts: int = Field(
        default=3
    )  # Número máximo de reinicializações automáticas

    # Configurações de notificação
    notify_on_success: bool = Field(default=True)
    notify_on_failure: bool = Field(default=True)
    notify_on_action_required: bool = Field(default=True)

    # Controle de tempo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    user: User = Relationship(back_populates="bot_configs")
    subscription: Subscription = Relationship(back_populates="bot_configs")
    bot_sessions: list["BotSession"] = Relationship(back_populates="bot_config")

    def update_config(self, new_yaml_key: str) -> None:
        """Atualiza a configuração YAML e armazena a versão anterior."""
        self.config_yaml_previous_key = self.config_yaml_key
        self.config_yaml_previous_created_at = self.config_yaml_created_at

        self.config_yaml_key = new_yaml_key
        self.config_yaml_created_at = datetime.now(timezone.utc)
        self.config_version += 1
        self.updated_at = datetime.now(timezone.utc)

    def update_resume(self, new_yaml_key: str) -> None:
        """Atualiza o YAML do currículo e armazena a versão anterior."""
        self.resume_yaml_previous_key = self.resume_yaml_key
        self.resume_yaml_previous_created_at = self.resume_yaml_created_at

        self.resume_yaml_key = new_yaml_key
        self.resume_yaml_created_at = datetime.now(timezone.utc)
        self.resume_version += 1
        self.updated_at = datetime.now(timezone.utc)

    def rollback_config(self) -> bool:
        """Reverte para a versão anterior da configuração, se disponível."""
        if not self.config_yaml_previous_key:
            return False

        # Troca atual e anterior
        current_key = self.config_yaml_key
        current_created_at = self.config_yaml_created_at

        self.config_yaml_key = self.config_yaml_previous_key
        self.config_yaml_created_at = self.config_yaml_previous_created_at

        self.config_yaml_previous_key = current_key
        self.config_yaml_previous_created_at = current_created_at

        self.updated_at = datetime.now(timezone.utc)
        return True

    def rollback_resume(self) -> bool:
        """Reverte para a versão anterior do currículo, se disponível."""
        if not self.resume_yaml_previous_key:
            return False

        # Troca atual e anterior
        current_key = self.resume_yaml_key
        current_created_at = self.resume_yaml_created_at

        self.resume_yaml_key = self.resume_yaml_previous_key
        self.resume_yaml_created_at = self.resume_yaml_previous_created_at

        self.resume_yaml_previous_key = current_key
        self.resume_yaml_previous_created_at = current_created_at

        self.updated_at = datetime.now(timezone.utc)
        return True


class BotSession(SQLModel, table=True):
    """
    Sessão do bot. Representa uma execução do bot com métricas e estado.
    """

    __tablename__ = "bot_session"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    subscription_id: UUID = Field(foreign_key="subscription.id")
    bot_config_id: UUID = Field(foreign_key="bot_config.id")

    # Estado e controle
    status: BotSessionStatus = Field(default=BotSessionStatus.STARTING)
    config_version: int = Field(default=1)  # Versão da configuração utilizada
    resume_version: int = Field(default=1)  # Versão do currículo utilizado
    config_yaml: str | None = Field(default=None)  # Conteúdo do YAML de configuração
    resume_yaml: str | None = Field(default=None)  # Conteúdo do YAML de currículo

    # Informações do Kubernetes
    kubernetes_pod_name: str | None = Field(default=None, max_length=100)
    kubernetes_namespace: str | None = Field(default=None, max_length=100)
    kubernetes_pod_status: KubernetesPodStatus | None = Field(default=None)
    kubernetes_node: str | None = Field(default=None, max_length=100)
    kubernetes_pod_ip: str | None = Field(default=None, max_length=50)
    kubernetes_log_url: str | None = Field(default=None, max_length=500)

    # Métricas
    calculated_metrics: bool = Field(default=False)
    total_time: int = Field(default=0)  # em segundos
    total_applied: int = Field(default=0)
    total_success: int = Field(default=0)
    total_failed: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    average_time_per_apply: float = Field(default=0.0)
    average_time_per_success: float = Field(default=0.0)
    average_time_per_failed: float = Field(default=0.0)
    crashes_count: int = Field(default=0)

    # Limites
    applies_limit: int = Field(default=100)  # Limite de aplicações para esta sessão
    time_limit: int | None = Field(
        default=None
    )  # Limite de tempo em segundos (opcional)

    # Controle de tempo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = Field(default=None)
    paused_at: datetime | None = Field(default=None)
    resumed_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    last_heartbeat_at: datetime | None = Field(
        default=None
    )  # Último sinal de vida do pod

    # Histórico de tempo de execução (para calcular o tempo total excluindo pausas)
    total_paused_time: int = Field(default=0)  # em segundos

    # Mensagens
    last_status_message: str | None = Field(default=None, max_length=1000)
    error_message: str | None = Field(default=None, max_length=2000)

    # Status de validação
    linkedin_credentials_valid: bool = Field(default=False)
    config_valid: bool = Field(default=False)
    resume_valid: bool = Field(default=False)

    # Relacionamentos
    subscription: Subscription = Relationship(back_populates="bot_sessions")
    bot_config: BotConfig = Relationship(back_populates="bot_sessions")
    bot_applies: list["BotApply"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )
    bot_events: list["BotEvent"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )
    bot_notifications: list["BotNotification"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )
    bot_commands: list["BotCommand"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )
    bot_user_actions: list["BotUserAction"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )

    def start(self) -> None:
        """Inicia a sessão do bot."""
        now = datetime.now(timezone.utc)

        if self.status == BotSessionStatus.STARTING:
            self.status = BotSessionStatus.RUNNING
            self.started_at = now
            self.last_heartbeat_at = now
            self.add_event("system", "Bot session started")

        elif self.status == BotSessionStatus.PAUSED:
            self.status = BotSessionStatus.RUNNING
            # Calcular tempo em pausa
            pause_duration = (
                int((now - self.paused_at).total_seconds()) if self.paused_at else 0
            )
            self.total_paused_time += pause_duration
            self.resumed_at = now
            self.last_heartbeat_at = now
            self.paused_at = None
            self.add_event("system", "Bot session resumed after pause")

    def pause(self) -> None:
        """Pausa a sessão do bot."""
        if self.status == BotSessionStatus.RUNNING:
            self.status = BotSessionStatus.PAUSED
            self.paused_at = datetime.now(timezone.utc)
            self.add_event("system", "Bot session paused by user")

    def stop(self) -> None:
        """Inicia o processo de parada do bot."""
        if self.status not in [
            BotSessionStatus.STOPPED,
            BotSessionStatus.COMPLETED,
            BotSessionStatus.FAILED,
        ]:
            self.status = BotSessionStatus.STOPPING
            self.add_event("system", "Bot session stopping - cleanup in progress")

    def complete(self) -> None:
        """Marca a sessão como concluída com sucesso."""
        self.status = BotSessionStatus.COMPLETED
        self.finished_at = datetime.now(timezone.utc)
        self.update_metrics()
        self.add_event("system", "Bot session completed successfully")

    def fail(self, reason: str) -> None:
        """Marca a sessão como falha."""
        self.status = BotSessionStatus.FAILED
        self.finished_at = datetime.now(timezone.utc)
        self.error_message = reason
        self.update_metrics()
        self.add_event("error", f"Bot session failed: {reason}")

    def update_kubernetes_status(
        self, status: KubernetesPodStatus, node: str = None, pod_ip: str = None
    ) -> None:
        """Atualiza o status do pod no Kubernetes."""
        self.kubernetes_pod_status = status
        if node:
            self.kubernetes_node = node
        if pod_ip:
            self.kubernetes_pod_ip = pod_ip

        status_str = (
            status.value if isinstance(status, KubernetesPodStatus) else str(status)
        )
        self.add_event("kubernetes", f"Pod status changed to {status_str}")

    def heartbeat(self) -> None:
        """Atualiza o timestamp do último heartbeat do bot."""
        self.last_heartbeat_at = datetime.now(timezone.utc)

    def update_metrics(self) -> None:
        """
        Atualiza as métricas da sessão, como total de aplicações, sucesso, falhas, taxa de sucesso e tempo médio por ação.
        """
        # Certifique-se de que temos acesso às aplicações através do relacionamento
        applies = self.bot_applies if hasattr(self, "bot_applies") else []

        # Contadores básicos
        self.total_applied = len(applies)
        self.total_success = len(
            [
                apply
                for apply in applies
                if apply.status == BotApplyStatus.SUCCESS.value
                or apply.status == "success"
            ]
        )
        self.total_failed = len(
            [
                apply
                for apply in applies
                if apply.status == BotApplyStatus.FAILED.value
                or apply.status == "failed"
            ]
        )

        # Taxa de sucesso
        if self.total_applied > 0:
            self.success_rate = round(
                (self.total_success / self.total_applied) * 100, 2
            )
        else:
            self.success_rate = 0.0

        # Cálculo de tempo
        now = datetime.now(timezone.utc)
        if self.finished_at:
            end_time = self.finished_at
        else:
            end_time = now

        # Tempo total (excluindo pausas)
        if self.started_at:
            raw_total_time = int((end_time - self.started_at).total_seconds())
            self.total_time = raw_total_time - self.total_paused_time
        else:
            self.total_time = 0

        # Tempo médio por aplicação
        times_per_apply = [
            apply.total_time for apply in applies if apply.total_time is not None
        ]
        times_per_success = [
            apply.total_time
            for apply in applies
            if apply.status in (BotApplyStatus.SUCCESS.value, "success")
            and apply.total_time is not None
        ]
        times_per_failed = [
            apply.total_time
            for apply in applies
            if apply.status in (BotApplyStatus.FAILED.value, "failed")
            and apply.total_time is not None
        ]

        self.average_time_per_apply = (
            sum(times_per_apply) / len(times_per_apply) if times_per_apply else 0
        )
        self.average_time_per_success = (
            sum(times_per_success) / len(times_per_success) if times_per_success else 0
        )
        self.average_time_per_failed = (
            sum(times_per_failed) / len(times_per_failed) if times_per_failed else 0
        )

        # Marcar métricas como calculadas
        self.calculated_metrics = True

        # Registrar evento
        self.add_event("system", "Session metrics updated")

    def add_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        details: str = None,
        source: str = None,
    ) -> "BotEvent":
        """Adiciona um evento à sessão."""
        event = BotEvent(
            bot_session_id=self.id,
            type=event_type,
            severity=severity,
            message=message,
            details=details,
            source=source or "system",
        )

        # Se o relacionamento bot_events estiver disponível como lista, adicione diretamente
        if hasattr(self, "bot_events") and isinstance(self.bot_events, list):
            self.bot_events.append(event)

        return event

    def is_healthy(self) -> bool:
        """Verifica se a sessão está saudável (recebendo heartbeats regulares)."""
        if not self.last_heartbeat_at:
            return False

        # Se não recebeu heartbeat nos últimos 2 minutos, não está saudável
        time_since_last_heartbeat = (
            datetime.now(timezone.utc) - self.last_heartbeat_at
        ).total_seconds()
        return time_since_last_heartbeat < 120  # 2 minutos

    def should_auto_restart(self) -> bool:
        """Verifica se a sessão deve ser reiniciada automaticamente."""
        if self.status != BotSessionStatus.FAILED:
            return False

        # Verifica na configuração se auto_restart está habilitado
        if not self.bot_config.auto_restart_on_failure:
            return False

        # Verifica se não excedeu o limite de reinicializações
        if self.crashes_count >= self.bot_config.max_auto_restarts:
            return False

        return True

    def need_deactivate_subscription(self) -> bool:
        """Verifica se a assinatura deve ser desativada com base nas métricas."""
        if self.subscription.metric_type == SubscriptionMetric.APPLIES:
            # Se usou todas as aplicações disponíveis
            return self.total_applied >= self.subscription.metric_status
        return False


class BotCommand(SQLModel, table=True):
    """
    Comando enviado ao bot. Registra comandos como iniciar, pausar, parar, etc.
    """

    __tablename__ = "bot_command"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(foreign_key="bot_session.id")
    command_type: BotCommandType
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: datetime | None = Field(default=None)
    executed_successfully: bool | None = Field(default=None)
    error_message: str | None = Field(default=None, max_length=1000)

    # Parâmetros adicionais do comando (pode ser útil para comandos como update_config)
    parameters: str | None = Field(default=None, max_length=1000)

    # Metadados
    sent_by_user_id: UUID | None = Field(foreign_key="user.id")
    source: str = Field(
        default="dashboard", max_length=50
    )  # dashboard, api, scheduler, etc.

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_commands")
    sent_by_user: User | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[BotCommand.sent_by_user_id]"}
    )

    def mark_executed(self, success: bool, error_message: str = None) -> None:
        """Marca o comando como executado."""
        self.executed_at = datetime.now(timezone.utc)
        self.executed_successfully = success
        self.error_message = error_message

    def as_dict(self) -> dict[str, Any]:
        """Converte o comando para um dicionário para envio ao bot."""
        result = {
            "command": self.command_type.value,
            "command_id": str(self.id),
            "sent_at": self.sent_at.isoformat(),
        }

        if self.parameters:
            result["parameters"] = self.parameters

        return result


class BotUserAction(SQLModel, table=True):
    """
    Ação que requer intervenção do usuário, como fornecer token 2FA ou resolver CAPTCHA.
    """

    __tablename__ = "bot_user_action"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(foreign_key="bot_session.id")
    action_type: UserActionType
    description: str = Field(max_length=1000)

    # Campos específicos para diferentes tipos de ação
    input_field: str | None = Field(
        default=None, max_length=100
    )  # Nome do campo para entrada
    extra_data: str | None = Field(
        default=None, max_length=5000
    )  # Dados adicionais (URL da imagem CAPTCHA, etc.)

    # Estado da ação
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = Field(default=None)
    expired_at: datetime | None = Field(default=None)
    is_completed: bool = Field(default=False)
    user_input: str | None = Field(default=None, max_length=1000)  # Resposta do usuário

    # Tentativas
    max_attempts: int = Field(default=3)
    current_attempts: int = Field(default=0)

    # Timeout
    timeout_seconds: int = Field(default=300)  # 5 minutos por padrão

    # Metadados
    bot_apply_id: int | None = Field(default=None, foreign_key="bot_apply.id")
    context: str | None = Field(
        default=None, max_length=5000
    )  # Contexto da ação (ex: página atual)

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_user_actions")
    bot_apply: Optional["BotApply"] = Relationship(back_populates="user_actions")
    bot_events: list["BotEvent"] = Relationship(
        back_populates="user_action",
        sa_relationship_kwargs={
            "foreign_keys": "[BotEvent.user_action_id]",
            "overlaps": "bot_events",
        },
    )
    bot_notifications: list["BotNotification"] = Relationship(
        back_populates="user_action",
        sa_relationship_kwargs={"foreign_keys": "[BotNotification.user_action_id]"},
    )

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
            self.bot_session.add_event(
                "user_action", f"User action completed: {self.action_type.value}"
            )

    def increment_attempt(self) -> bool:
        """
        Incrementa o contador de tentativas e verifica se atingiu o máximo.
        Retorna True se ainda há tentativas disponíveis, False caso contrário.
        """
        self.current_attempts += 1
        return self.current_attempts < self.max_attempts

    def is_expired(self) -> bool:
        """Verifica se a solicitação de ação expirou."""
        if self.expired_at:
            return datetime.now(timezone.utc) > self.expired_at

        # Se não tiver expired_at definido, calcular baseado em timeout_seconds
        elapsed = (datetime.now(timezone.utc) - self.requested_at).total_seconds()
        return elapsed > self.timeout_seconds

    def expire(self) -> None:
        """Marca a ação como expirada."""
        self.expired_at = datetime.now(timezone.utc)

        # Criar evento notificando expiração
        if hasattr(self, "bot_session"):
            self.bot_session.add_event(
                "user_action",
                f"User action expired: {self.action_type.value}",
                severity="warning",
            )


class BotEvent(SQLModel, table=True):
    """
    Evento ocorrido durante a execução do bot. Utilizado para logging e auditoria.
    """

    __tablename__ = "bot_event"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(foreign_key="bot_session.id")

    # Tipos mais específicos de eventos
    type: str = Field(
        max_length=50
    )  # log, error, warning, info, kubernetes, system, user_action, etc.
    severity: str = Field(
        default="info", max_length=20
    )  # info, warning, error, critical

    message: str = Field(max_length=1000)
    details: str | None = Field(
        default=None, max_length=5000
    )  # Detalhes estruturados (pode ser JSON)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Rastreabilidade
    source: str | None = Field(
        default=None, max_length=100
    )  # Componente que gerou o evento

    # Referências
    bot_apply_id: int | None = Field(default=None, foreign_key="bot_apply.id")
    user_action_id: UUID | None = Field(default=None, foreign_key="bot_user_action.id")

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_events")
    bot_apply: Optional["BotApply"] = Relationship(
        back_populates="events",
        sa_relationship_kwargs={
            "foreign_keys": "[BotEvent.bot_apply_id]",
            "overlaps": "bot_apply",
        },
    )
    user_action: BotUserAction | None = Relationship(
        back_populates="bot_events",
        sa_relationship_kwargs={
            "foreign_keys": "[BotEvent.user_action_id]",
            "overlaps": "bot_events",
        },
    )

    @classmethod
    def create_system_event(
        cls,
        bot_session_id: UUID,
        message: str,
        severity: str = "info",
        details: str = None,
    ) -> "BotEvent":
        """Cria um evento do sistema."""
        return cls(
            bot_session_id=bot_session_id,
            type="system",
            severity=severity,
            message=message,
            details=details,
            source="system",
        )

    @classmethod
    def create_error_event(
        cls, bot_session_id: UUID, message: str, details: str = None
    ) -> "BotEvent":
        """Cria um evento de erro."""
        return cls(
            bot_session_id=bot_session_id,
            type="error",
            severity="error",
            message=message,
            details=details,
            source="system",
        )


class BotApply(SQLModel, table=True):
    """
    Aplicação para uma vaga. Representa uma tentativa de aplicação para uma vaga específica.
    """

    __tablename__ = "bot_apply"

    id: int = Field(primary_key=True)
    session_id: UUID = Field(foreign_key="bot_session.id")

    # Status e progresso
    status: str = Field(max_length=20)  # Usar BotApplyStatus.value
    progress: int = Field(default=0)  # 0-100% de progresso

    # Tempos
    started_at: datetime
    completed_at: datetime | None = Field(default=None)
    total_time: int | None = Field(default=None)  # em segundos

    # Informações da vaga
    job_id: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=255)
    job_description: str | None = Field(default=None, max_length=10000)
    job_url: str | None = Field(default=None, max_length=500)
    job_location: str | None = Field(default=None, max_length=255)
    job_salary: str | None = Field(default=None, max_length=100)
    job_type: str | None = Field(
        default=None, max_length=100
    )  # Full-time, part-time, etc.

    company_name: str | None = Field(default=None, max_length=255)
    company_website: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)

    # Informações do currículo utilizado
    resume_bucket: str = Field(max_length=50)
    resume_pdf: str | None = Field(default=None, max_length=100)
    resume_version: int = Field(default=1)

    # Resultado e métricas
    match_score: float | None = Field(
        default=None
    )  # 0-100% de compatibilidade com a vaga
    required_skills_matched: int | None = Field(
        default=None
    )  # Número de habilidades requeridas correspondidas
    total_required_skills: int | None = Field(
        default=None
    )  # Número total de habilidades requeridas

    # Informações de falha
    failed: bool = Field(default=False)
    failed_reason: str | None = Field(default=None, max_length=10000)
    failed_at_stage: str | None = Field(
        default=None, max_length=100
    )  # Em qual etapa falhou
    screenshot_url: str | None = Field(
        default=None, max_length=500
    )  # URL do screenshot da falha

    # Metadados
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    application_reference: str | None = Field(
        default=None, max_length=100
    )  # Referência externa/ID da aplicação

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_applies")
    apply_steps: list["BotApplyStep"] = Relationship(
        back_populates="bot_apply", cascade_delete=True
    )
    user_actions: list[BotUserAction] = Relationship(back_populates="bot_apply")
    events: list[BotEvent] = Relationship(
        back_populates="bot_apply",
        sa_relationship_kwargs={
            "foreign_keys": "[BotEvent.bot_apply_id]",
            "overlaps": "bot_apply",
        },
    )
    notifications: list["BotNotification"] = Relationship(
        back_populates="bot_apply",
        sa_relationship_kwargs={"foreign_keys": "[BotNotification.bot_apply_id]"},
    )

    def complete(self, success: bool, reason: str = None) -> None:
        """Marca a aplicação como concluída."""
        self.completed_at = datetime.now(timezone.utc)

        # Calcular tempo total
        if self.started_at:
            self.total_time = int((self.completed_at - self.started_at).total_seconds())

        # Definir status final
        if success:
            self.status = BotApplyStatus.SUCCESS.value
            self.progress = 100
        else:
            self.status = BotApplyStatus.FAILED.value
            self.failed = True
            self.failed_reason = reason

        # Criar evento
        if hasattr(self, "bot_session"):
            event_type = "application_success" if success else "application_failed"
            severity = "info" if success else "warning"
            message = (
                f"Application completed: {self.job_title}"
                if success
                else f"Application failed: {reason}"
            )

            self.bot_session.add_event(
                event_type=event_type,
                message=message,
                severity=severity,
                source="application",
                details=reason,
            )

    def update_progress(self, progress: int, stage: str = None) -> None:
        """Atualiza o progresso da aplicação."""
        self.progress = min(100, max(0, progress))  # Garantir que esteja entre 0-100

        if stage and hasattr(self, "bot_session"):
            self.bot_session.add_event(
                event_type="application_progress",
                message=f"Application progress: {stage} ({self.progress}%)",
                severity="info",
                source="application",
            )

    def add_step(self, name: str, details: str = None) -> "BotApplyStep":
        """Adiciona um passo à aplicação."""
        step_number = len(self.apply_steps) + 1 if hasattr(self, "apply_steps") else 1

        step = BotApplyStep(
            bot_apply_id=self.id,
            step_number=step_number,
            step_name=name,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            details=details,
        )

        if hasattr(self, "apply_steps") and isinstance(self.apply_steps, list):
            self.apply_steps.append(step)

        return step


class BotApplyStep(SQLModel, table=True):
    """
    Etapa de uma aplicação. Representa um passo específico no processo de aplicação.
    """

    __tablename__ = "bot_apply_step"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_apply_id: int = Field(foreign_key="bot_apply.id")

    step_number: int  # Ordem do passo
    step_name: str = Field(max_length=100)  # Nome descritivo do passo
    status: str = Field(max_length=20)  # pending, in_progress, completed, failed

    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration: int | None = Field(default=None)  # Duração em segundos

    details: str | None = Field(default=None, max_length=5000)  # Detalhes do passo
    error: str | None = Field(default=None, max_length=1000)  # Erro, se houver
    screenshot_url: str | None = Field(
        default=None, max_length=500
    )  # URL do screenshot deste passo

    # Relacionamentos
    bot_apply: BotApply = Relationship(back_populates="apply_steps")

    def complete(
        self, success: bool = True, error: str = None, details: str = None
    ) -> None:
        """Marca o passo como concluído."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = "completed" if success else "failed"

        if self.started_at:
            self.duration = int((self.completed_at - self.started_at).total_seconds())

        if error:
            self.error = error

        if details:
            self.details = details

    def update_details(self, details: str) -> None:
        """Atualiza os detalhes do passo."""
        self.details = details


class BotNotification(SQLModel, table=True):
    """
    Notificação enviada pelo bot ao usuário.
    """

    __tablename__ = "bot_notification"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_session_id: UUID = Field(foreign_key="bot_session.id")

    title: str = Field(max_length=255)
    message: str = Field(max_length=1000)
    priority: BotNotificationPriority = Field(default=BotNotificationPriority.MEDIUM)
    status: BotNotificationStatus = Field(default=BotNotificationStatus.PENDING)

    # Conteúdo e formatação
    content_html: str | None = Field(
        default=None, max_length=10000
    )  # Versão em HTML da mensagem
    icon: str | None = Field(
        default=None, max_length=100
    )  # Ícone a exibir (ex: "success", "error", "warning")

    # Ação necessária?
    requires_action: bool = Field(default=False)
    action_url: str | None = Field(
        default=None, max_length=500
    )  # URL para ação, se aplicável
    action_text: str | None = Field(
        default=None, max_length=100
    )  # Texto do botão de ação

    # Referências
    bot_apply_id: int | None = Field(default=None, foreign_key="bot_apply.id")
    user_action_id: UUID | None = Field(default=None, foreign_key="bot_user_action.id")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = Field(default=None)
    read_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)

    # Metadados
    user_id: UUID = Field(foreign_key="user.id")  # Destinatário
    source: str = Field(
        default="bot", max_length=50
    )  # Origem da notificação (bot, system, etc.)

    # Relacionamentos
    bot_session: BotSession = Relationship(back_populates="bot_notifications")
    bot_apply: BotApply | None = Relationship(
        back_populates="notifications",
        sa_relationship_kwargs={
            "foreign_keys": "[BotNotification.bot_apply_id]",
            "overlaps": "notifications",
        },
    )
    user_action: BotUserAction | None = Relationship(
        back_populates="bot_notifications",
        sa_relationship_kwargs={
            "foreign_keys": "[BotNotification.user_action_id]",
            "overlaps": "bot_notifications",
        },
    )
    user: User = Relationship(back_populates="bot_notifications")
    notification_channels: list["BotNotificationChannel"] = Relationship(
        back_populates="bot_notification"
    )

    def mark_as_sent(self) -> None:
        """Marca a notificação como enviada."""
        self.status = BotNotificationStatus.SENT
        self.sent_at = datetime.now(timezone.utc)

    def mark_as_read(self) -> None:
        """Marca a notificação como lida pelo usuário."""
        if self.status != BotNotificationStatus.READ:
            self.status = BotNotificationStatus.READ
            self.read_at = datetime.now(timezone.utc)

    def mark_as_failed(self) -> None:
        """Marca a notificação como falha no envio."""
        self.status = BotNotificationStatus.FAILED

    def mark_as_expired(self) -> None:
        """Marca a notificação como expirada."""
        self.status = BotNotificationStatus.EXPIRED
        if not self.expires_at:
            self.expires_at = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """Verifica se a notificação está ativa (não expirada)."""
        if self.status == BotNotificationStatus.EXPIRED:
            return False

        if not self.expires_at:
            return True

        return datetime.now(timezone.utc) < self.expires_at

    @classmethod
    def create_success_notification(
        cls,
        bot_session_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        apply_id: int = None,
    ) -> "BotNotification":
        """Cria uma notificação de sucesso."""
        return cls(
            bot_session_id=bot_session_id,
            user_id=user_id,
            title=title,
            message=message,
            priority=BotNotificationPriority.LOW,
            icon="success",
            bot_apply_id=apply_id,
            source="bot",
        )

    @classmethod
    def create_error_notification(
        cls,
        bot_session_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        apply_id: int = None,
    ) -> "BotNotification":
        """Cria uma notificação de erro."""
        return cls(
            bot_session_id=bot_session_id,
            user_id=user_id,
            title=title,
            message=message,
            priority=BotNotificationPriority.HIGH,
            icon="error",
            bot_apply_id=apply_id,
            source="bot",
        )

    @classmethod
    def create_action_notification(
        cls,
        bot_session_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        action_url: str,
        action_text: str,
        user_action_id: UUID = None,
    ) -> "BotNotification":
        """Cria uma notificação que requer ação do usuário."""
        return cls(
            bot_session_id=bot_session_id,
            user_id=user_id,
            title=title,
            message=message,
            priority=BotNotificationPriority.HIGH,
            icon="action_required",
            requires_action=True,
            action_url=action_url,
            action_text=action_text,
            user_action_id=user_action_id,
            source="bot",
        )


class BotNotificationChannel(SQLModel, table=True):
    """
    Canal de notificação. Representa um canal específico (email, SMS, push) para envio de notificação.
    """

    __tablename__ = "bot_notification_channel"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bot_notification_id: UUID = Field(foreign_key="bot_notification.id")
    channel: str = Field(max_length=50)  # email, sms, dashboard, push, etc.
    status: str = Field(max_length=50)  # sent, failed, pending, etc.

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = Field(default=None)

    # Detalhes específicos do canal
    recipient: str | None = Field(
        default=None, max_length=255
    )  # Endereço de email, número de telefone, etc.
    error_message: str | None = Field(
        default=None, max_length=1000
    )  # Mensagem de erro, se houver

    # Relacionamentos
    bot_notification: BotNotification = Relationship(
        back_populates="notification_channels"
    )

    def mark_as_sent(self) -> None:
        """Marca o canal como tendo enviado a notificação com sucesso."""
        self.status = "sent"
        self.sent_at = datetime.now(timezone.utc)

    def mark_as_failed(self, error_message: str = None) -> None:
        """Marca o canal como tendo falhado no envio da notificação."""
        self.status = "failed"
        self.error_message = error_message


# ======================================================
# API MODELS (para uso nas rotas)
# ======================================================


class LinkedInCredentialsCreate(SQLModel):
    """Modelo para criação de credenciais do LinkedIn."""

    email: str
    password: str


class LinkedInCredentialsPublic(SQLModel):
    """Modelo público para credenciais do LinkedIn (sem expor a senha)."""

    email: str
    subscription_id: UUID


class BotConfigurationCreate(SQLModel):
    """Modelo para criação de configurações específicas do bot."""

    style_choice: BotStyleChoice = BotStyleChoice.MODERN_BLUE
    user_agent: str | None = None
    sec_ch_ua: str | None = None
    sec_ch_ua_platform: str | None = None


class BotConfigurationPublic(SQLModel):
    """Modelo público para configurações específicas do bot."""

    id: UUID
    subscription_id: UUID
    style_choice: BotStyleChoice
    user_agent: str
    sec_ch_ua: str
    sec_ch_ua_platform: str


class BotConfigCreate(SQLModel):
    """Modelo para criação de configuração do bot."""

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    max_applies_per_session: int = Field(default=50)
    max_applies_per_day: int = Field(default=100)
    allow_dynamic_updates: bool = Field(default=False)
    auto_restart_on_failure: bool = Field(default=True)
    max_auto_restarts: int = Field(default=3)
    notify_on_success: bool = Field(default=True)
    notify_on_failure: bool = Field(default=True)
    notify_on_action_required: bool = Field(default=True)


class BotConfigUpdate(SQLModel):
    """Modelo para atualização de configuração do bot."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    max_applies_per_session: int | None = None
    max_applies_per_day: int | None = None
    allow_dynamic_updates: bool | None = None
    auto_restart_on_failure: bool | None = None
    max_auto_restarts: int | None = None
    notify_on_success: bool | None = None
    notify_on_failure: bool | None = None
    notify_on_action_required: bool | None = None


class BotConfigPublic(SQLModel):
    """Modelo público para configuração do bot."""

    id: UUID
    name: str
    description: str | None
    max_applies_per_session: int
    max_applies_per_day: int
    allow_dynamic_updates: bool
    auto_restart_on_failure: bool
    max_auto_restarts: int
    config_version: int
    resume_version: int
    created_at: datetime
    updated_at: datetime


class BotSessionCreate(SQLModel):
    """Modelo para criação de sessão do bot."""

    subscription_id: UUID
    bot_config_id: UUID
    applies_limit: int | None = None
    time_limit: int | None = None


class BotSessionUpdate(SQLModel):
    """Modelo para atualização de sessão do bot."""

    status: BotSessionStatus | None = None
    kubernetes_pod_name: str | None = None
    kubernetes_namespace: str | None = None
    kubernetes_pod_status: KubernetesPodStatus | None = None
    kubernetes_pod_ip: str | None = None
    applies_limit: int | None = None
    time_limit: int | None = None
    last_status_message: str | None = None
    error_message: str | None = None


class BotSessionPublic(SQLModel):
    """Modelo público básico para sessão do bot."""

    id: UUID
    subscription_id: UUID
    bot_config_id: UUID
    status: str
    kubernetes_pod_status: str | None
    total_applied: int
    total_success: int
    total_failed: int
    success_rate: float
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    last_heartbeat_at: datetime | None
    is_healthy: bool
    last_status_message: str | None
    error_message: str | None


class BotSessionDetailPublic(BotSessionPublic):
    """Modelo público detalhado para sessão do bot."""

    total_time: int
    average_time_per_apply: float
    average_time_per_success: float
    average_time_per_failed: float
    crashes_count: int
    kubernetes_pod_name: str | None
    kubernetes_namespace: str | None
    kubernetes_node: str | None
    kubernetes_pod_ip: str | None
    kubernetes_log_url: str | None
    applies_limit: int
    time_limit: int | None
    config_version: int
    resume_version: int
    paused_at: datetime | None
    resumed_at: datetime | None


class BotCommandCreate(SQLModel):
    """Modelo para criação de comando do bot."""

    command_type: BotCommandType
    parameters: str | None = None


class BotCommandPublic(SQLModel):
    """Modelo público para comando do bot."""

    id: UUID
    bot_session_id: UUID
    command_type: str
    sent_at: datetime
    executed_at: datetime | None
    executed_successfully: bool | None
    error_message: str | None
    parameters: str | None
    sent_by_user_id: UUID | None
    source: str


class BotUserActionCreate(SQLModel):
    """Modelo para criação de ação do usuário."""

    action_type: UserActionType
    description: str
    input_field: str | None = None
    extra_data: str | None = None
    max_attempts: int = Field(default=3)
    timeout_seconds: int = Field(default=300)
    bot_apply_id: int | None = None
    context: str | None = None


class BotUserActionUpdate(SQLModel):
    """Modelo para atualização de ação do usuário."""

    user_input: str
    current_attempts: int | None = None


class BotUserActionPublic(SQLModel):
    """Modelo público para ação do usuário."""

    id: UUID
    bot_session_id: UUID
    action_type: str
    description: str
    input_field: str | None
    extra_data: str | None
    requested_at: datetime
    completed_at: datetime | None
    expired_at: datetime | None
    is_completed: bool
    user_input: str | None
    max_attempts: int
    current_attempts: int
    timeout_seconds: int
    is_expired: bool
    bot_apply_id: int | None
    context: str | None


class BotApplyPublic(SQLModel):
    """Modelo público básico para aplicação do bot."""

    id: int
    session_id: UUID
    status: str
    progress: int
    started_at: datetime
    completed_at: datetime | None
    total_time: int | None
    job_id: str | None
    job_title: str | None
    job_url: str | None
    company_name: str | None
    linkedin_url: str | None
    failed: bool
    failed_reason: str | None
    match_score: float | None


class BotApplyDetailPublic(BotApplyPublic):
    """Modelo público detalhado para aplicação do bot."""

    job_description: str | None
    job_location: str | None
    job_salary: str | None
    job_type: str | None
    company_website: str | None
    resume_bucket: str
    resume_pdf: str | None
    resume_version: int
    required_skills_matched: int | None
    total_required_skills: int | None
    failed_at_stage: str | None
    screenshot_url: str | None
    created_at: datetime
    application_reference: str | None
    steps: list["BotApplyStepPublic"] = []


class BotApplyStepPublic(SQLModel):
    """Modelo público para etapa de aplicação do bot."""

    id: UUID
    bot_apply_id: int
    step_number: int
    step_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration: int | None
    details: str | None
    error: str | None
    screenshot_url: str | None


class BotEventPublic(SQLModel):
    """Modelo público para evento do bot."""

    id: UUID
    bot_session_id: UUID
    type: str
    severity: str
    message: str
    details: str | None
    created_at: datetime
    source: str | None
    bot_apply_id: int | None
    user_action_id: UUID | None


class BotNotificationPublic(SQLModel):
    """Modelo público para notificação do bot."""

    id: UUID
    bot_session_id: UUID
    title: str
    message: str
    priority: str
    status: str
    content_html: str | None
    icon: str | None
    requires_action: bool
    action_url: str | None
    action_text: str | None
    created_at: datetime
    sent_at: datetime | None
    read_at: datetime | None
    expires_at: datetime | None
    user_id: UUID
    source: str
    bot_apply_id: int | None
    user_action_id: UUID | None
    is_active: bool


class BotNotificationUpdate(SQLModel):
    """Modelo para atualização de notificação do bot."""

    status: BotNotificationStatus | None = None
