import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from dateutil.relativedelta import relativedelta
from pydantic import EmailStr, field_validator
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Column, Field, ForeignKey, Relationship, SQLModel


class SubscriptionMetric(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    APPLIES = "applies"


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    full_name: str | None = Field(default=None, max_length=255)


# properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    is_subscriber: bool = Field(default=False)
    stripe_customer_id: str | None = Field(default=None)

    subscriptions: list["Subscription"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    payments: list["Payment"] = Relationship(back_populates="user", cascade_delete=True)

    def get_active_subscriptions(self) -> list["Subscription"]:
        """
        return active subscriptions
        """
        return [
            subscription
            for subscription in self.subscriptions
            if subscription.is_active
        ]


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    is_subscriber: bool


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class SubscriptionPlanBenefit(SQLModel, table=True):
    __tablename__ = "subscription_plan_benefit"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subscription_plan_id: uuid.UUID = Field(foreign_key="subscription_plan.id")
    name: str = Field(max_length=100)

    subscription_plan: "SubscriptionPlan" = Relationship(back_populates="benefits")


class SubscriptionPlanBase(SQLModel):
    name: str
    price: float
    has_badge: bool = Field(default=False)
    badge_text: str = Field(default="", max_length=50)
    button_text: str = Field(default="Subscribe", max_length=50)
    has_discount: bool = Field(default=False)
    price_without_discount: float = Field(default=0.0)
    currency: str = Field(default="USD", max_length=10)
    description: str = Field(default="", max_length=10000)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric = Field(default=SubscriptionMetric.MONTH)
    metric_value: int = Field(default=1)


class SubscriptionPlanCreate(SubscriptionPlanBase):
    benefits: list["SubscriptionPlanBenefitPublic"] = []


class SubscriptionPlanUpdate(SQLModel):
    name: str | None = None
    price: float | None = None
    has_badge: bool | None = None
    badge_text: str | None = None
    button_text: str | None = None
    has_discount: bool | None = None
    price_without_discount: float | None = None
    currency: str | None = None
    description: str | None = None
    is_active: bool | None = None
    metric_type: SubscriptionMetric | None = None
    metric_value: int | None = None
    benefits: list["SubscriptionPlanBenefitPublic"] | None = None

    @field_validator("metric_value")
    def check_metric_value(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("metric_value must be greater than 0")
        return value


class SubscriptionPlan(SQLModel, table=True):
    __tablename__ = "subscription_plan"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    price: float
    has_badge: bool = Field(default=False)
    badge_text: str = Field(default="", max_length=50)
    button_text: str = Field(default="Subscribe", max_length=50)

    has_discount: bool = Field(default=False)
    price_without_discount: float = Field(default=0.0)
    currency: str = Field(default="USD", max_length=10)
    description: str = Field(default="", max_length=10000)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric = Field(default=SubscriptionMetric.DAY)
    metric_value: int = Field(default=30)

    stripe_product_id: str | None = Field(default=None, index=True)
    stripe_price_id: str | None = Field(default=None, index=True)

    benefits: list["SubscriptionPlanBenefit"] = Relationship(
        back_populates="subscription_plan", cascade_delete=True
    )
    subscriptions: list["Subscription"] = Relationship(
        back_populates="subscription_plan",
        cascade_delete=True,
    )
    checkout_sessions: list["CheckoutSession"] = Relationship(back_populates="plan")


class SubscriptionBase(SQLModel):
    user_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric
    metric_status: int


class SubscriptionPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    is_active: bool
    metric_type: SubscriptionMetric
    metric_status: int


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(SQLModel):
    user_id: uuid.UUID | None = None
    subscription_plan_id: uuid.UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None
    metric_type: SubscriptionMetric | None = None
    metric_status: int | None = None


class Subscription(SQLModel, table=True):
    __tablename__ = "subscription"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    subscription_plan_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("subscription_plan.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    start_date: datetime
    end_date: datetime | None = Field(None, nullable=True)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric
    metric_status: int

    stripe_subscription_id: str | None = Field(default=None, index=True)

    user: User = Relationship(back_populates="subscriptions")
    subscription_plan: SubscriptionPlan = Relationship(back_populates="subscriptions")
    payments: list["Payment"] = Relationship(back_populates="subscription")
    bot_sessions: list["BotSession"] = Relationship(back_populates="subscription")

    def extend_subscription(self, plan: SubscriptionPlan | None = None) -> None:
        """
        Extende a assinatura para um novo plano (caso fornecido) ou renova o atual.
        Depois de renovar métricas, recalcula a data de término.
        """
        # Caso seja fornecido um plano diferente, atualiza o plano da assinatura
        if plan and plan != self.subscription_plan:
            self.subscription_plan = plan

        # Atualiza métricas de acordo com o self.subscription_plan
        self.renew_metrics()

        # Recalcula a data de término com base nas métricas atualizadas
        self.calculate_end_date()

    def renew_metrics(self) -> None:
        """
        Renova as métricas da assinatura com base em self.subscription_plan.

        Regras genéricas:
          1. Se o tipo de métrica do plano for diferente do atual,
             zera o tipo para o novo e define o status como o valor base do plano.
          2. Se o tipo de métrica for o mesmo, checa se a assinatura já expirou:
             - Se estiver expirada, reseta o metric_status com o valor base do plano.
             - Se ainda estiver ativa, soma o valor base do plano ao metric_status atual.
          3. Garante que metric_status nunca fique negativo.
        """
        plan = self.subscription_plan

        # Se a métrica do plano for diferente da métrica atual, “resetamos” tudo
        if plan.metric_type != self.metric_type:
            self.metric_type = plan.metric_type
            self.metric_status = max(0, plan.metric_value)
            return

        # A métrica é a mesma do plano
        # Verificamos se a assinatura já deveria estar desativada
        if self.need_to_deactivate():
            # Se já expirou ou não tem créditos, reiniciamos o 'metric_status'
            self.metric_status = max(0, plan.metric_value)
        else:
            # Se ainda está ativa, simplesmente acumulamos
            if self.metric_status < 0:
                self.metric_status = 0
            self.metric_status += plan.metric_value

    def calculate_end_date(self) -> None:
        """
        Calcula a data de término da assinatura baseado no tipo de métrica.
        ATENÇÃO: Caso for renovar as métricas, fazer apenas APÓS a renovação das métricas.
        """
        if self.metric_type == SubscriptionMetric.DAY:
            self.end_date = self.start_date + timedelta(days=self.metric_status)
        elif self.metric_type == SubscriptionMetric.WEEK:
            self.end_date = self.start_date + timedelta(weeks=self.metric_status)
        elif self.metric_type == SubscriptionMetric.MONTH:
            self.end_date = self.start_date + relativedelta(months=self.metric_status)
        elif self.metric_type == SubscriptionMetric.YEAR:
            self.end_date = self.start_date + relativedelta(years=self.metric_status)
        elif self.metric_type == SubscriptionMetric.APPLIES:
            self.end_date = None

    def need_to_deactivate(self) -> bool:
        """
        Verifica se a assinatura precisa ser desativada baseado no tipo de métrica.

        Retorna True se:
          - Para métricas baseadas em tempo (DAY, WEEK, MONTH, YEAR), a data de término (end_date)
            já tiver passado (considerando UTC).
          - Para métrica APPLIES, o metric_status seja menor que 1 (por exemplo, sem créditos).
        Caso contrário, retorna False.
        """
        now_utc = datetime.now(timezone.utc)

        # Métricas baseadas em tempo
        if self.metric_type in [
            SubscriptionMetric.DAY,
            SubscriptionMetric.WEEK,
            SubscriptionMetric.MONTH,
            SubscriptionMetric.YEAR,
        ]:
            # Se não há end_date ou já passou, precisa desativar
            if self.end_date is None or self.end_date < now_utc:
                return True

        # Métrica baseada em crédito
        elif self.metric_type == SubscriptionMetric.APPLIES:
            if self.metric_status < 1:
                return True

        return False


class PaymentBase(SQLModel):
    subscription_id: uuid.UUID | None = None
    user_id: uuid.UUID
    amount: float
    currency: str = Field(default="USD", max_length=10)
    payment_date: datetime
    payment_status: str = Field(default="pending", max_length=100)
    payment_gateway: str = Field(default="stripe", max_length=50)
    transaction_id: str = Field(max_length=150)


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(SQLModel):
    subscription_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    amount: float | None = None
    currency: str | None = None
    payment_date: datetime | None = None
    payment_status: str | None = None
    payment_gateway: str | None = None
    transaction_id: str | None = None


class Payment(SQLModel, table=True):
    __tablename__ = "payment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subscription_id: uuid.UUID = Field(foreign_key="subscription.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    amount: float
    currency: str = Field(default="USD", max_length=10)
    payment_date: datetime
    payment_status: str = Field(default="pending", max_length=100)
    payment_gateway: str = Field(
        default="stripe", max_length=50
    )  # e.g., Stripe, BoaCompra
    transaction_id: str = Field(index=True)

    subscription: Subscription = Relationship(back_populates="payments")
    user: User = Relationship(back_populates="payments")


class PaymentPublic(SQLModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    currency: str
    payment_date: datetime
    payment_status: str
    payment_gateway: str
    transaction_id: str


class PaymentsPublic(SQLModel):
    data: list[PaymentPublic]
    count: int


class CheckoutSession(SQLModel, table=True):
    __tablename__ = "checkout_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    payment_gateway: str = Field(
        default="stripe", max_length=50
    )  # e.g., Stripe, BoaCompra
    session_id: str = Field(index=True, max_length=100)
    session_url: str = Field(max_length=500)
    user_id: uuid.UUID
    status: str = Field(default="open", max_length=50)  # open, complete, or expired
    subscription_plan_id: uuid.UUID = Field(foreign_key="subscription_plan.id")
    payment_status: str = Field(
        default="unpaid", max_length=50
    )  # paid, unpaid, or no_payment_required

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field()
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    plan: "SubscriptionPlan" = Relationship(back_populates="checkout_sessions")


class CheckoutSessionUpdate(SQLModel):
    payment_gateway: str | None = None
    session_id: str | None = None
    session_url: str | None = None
    user_id: uuid.UUID | None = None
    status: str | None = None
    subscription_plan_id: uuid.UUID | None = None
    payment_status: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    updated_at: datetime | None = None


class CheckoutSessionPublic(SQLModel):
    id: uuid.UUID
    session_id: str
    session_url: str
    expires_at: datetime


# Generic message
class Message(SQLModel):
    message: str


class ErrorMessage(SQLModel):
    detail: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = Field(default="bearer")


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = Field(default=None)


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class SubscriptionPlanBenefitPublic(SQLModel):
    name: str


class SubscriptionPlanPublic(SQLModel):
    id: uuid.UUID
    name: str
    price: float
    has_badge: bool = Field(default=False)
    badge_text: str
    button_text: str
    has_discount: bool
    price_without_discount: float
    currency: str
    description: str
    is_active: bool
    metric_type: SubscriptionMetric
    metric_value: int

    benefits: list[SubscriptionPlanBenefitPublic] = []


class SubscriptionPlansPublic(SQLModel):
    plans: list[SubscriptionPlanPublic] = []


class BotSession(SQLModel, table=True):
    __tablename__ = "bot_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subscription_id: uuid.UUID = Field(foreign_key="subscription.id")
    status: str = Field(default="starting", max_length=10)

    bot_config_id: uuid.UUID = Field(foreign_key="bot_config.id")

    # Metrics
    calculated_metrics: bool = False
    total_time: int = 0  # in seconds
    total_applied: int = 0
    total_success: int = 0
    total_failed: int = 0
    success_rate: float = 0.0
    average_time_per_apply: float = 0.0
    average_time_per_success: float = 0.0
    average_time_per_failed: float = 0.0
    crashes_count: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = Field(nullable=True)

    subscription: Subscription = Relationship(back_populates="bot_sessions")
    bot_config: "BotConfig" = Relationship(back_populates="bot_sessions")
    bot_applies: list["BotApply"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )
    bot_events: list["BotEvent"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )
    bot_notifications: list["BotNotification"] = Relationship(
        back_populates="bot_session", cascade_delete=True
    )

    def update_metrics(self) -> None:
        """
        Atualiza as métricas da sessão, como total de aplicações, sucesso, falhas, taxa de sucesso e tempo médio por ação.
        """
        if not self.finished_at or not isinstance(self.finished_at, datetime):
            raise ValueError("Session must be finished to calculate metrics")

        self.total_applied = len(self.bot_applies)
        self.total_success = len(
            [apply for apply in self.bot_applies if apply.status == "success"]
        )
        self.total_failed = len(
            [apply for apply in self.bot_applies if apply.status == "failed"]
        )
        self.success_rate = (
            self.total_success / self.total_applied if self.total_applied > 0 else 0.0
        )
        self.total_time = int((self.finished_at - self.created_at).total_seconds())

        total_time_applies = sum([apply.total_time for apply in self.bot_applies])
        total_time_success = sum(
            [
                apply.total_time
                for apply in self.bot_applies
                if apply.status == "success"
            ]
        )
        total_time_failed = sum(
            [apply.total_time for apply in self.bot_applies if apply.status == "failed"]
        )

        self.average_time_per_apply = (
            total_time_applies / self.total_applied if self.total_applied > 0 else 0.0
        )
        self.average_time_per_success = (
            total_time_success / self.total_success if self.total_success > 0 else 0.0
        )
        self.average_time_per_failed = (
            total_time_failed / self.total_failed if self.total_failed > 0 else 0.0
        )


class BotConfig(SQLModel, table=True):
    __tablename__ = "bot_config"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    cloud_provider: str = Field("https://br-se1.magaluobjects.com", max_length=50)

    config_bucket: str = Field("configs", max_length=50)
    config_yaml_key: str = Field(max_length=1000)
    config_yaml_created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    resume_bucket: str = Field("resumes", max_length=50)
    resume_yaml_key: str = Field(max_length=1000)
    resume_yaml_created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    bot_sessions: list[BotSession] = Relationship(back_populates="bot_config")


class BotApply(SQLModel, table=True):
    __tablename__ = "bot_apply"

    id: int = Field(primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="bot_session.id")
    started_at: datetime
    total_time: int  # in seconds
    status: str = Field(
        max_length=10
    )  # Literal["awaiting", "started", "success", "failed"]

    resume_bucket: str = Field(max_length=50)
    resume_pdf: str | None = Field(max_length=100, nullable=True)

    failed: bool = False
    failed_reason: str | None = Field(max_length=10000, nullable=True)
    company_name: str | None = Field(max_length=255, nullable=True)
    linkedin_url: str | None = Field(max_length=255, nullable=True)

    bot_session: BotSession = Relationship(back_populates="bot_applies")


class BotEvent(SQLModel, table=True):
    __tablename__ = "bot_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    bot_session_id: uuid.UUID = Field(foreign_key="bot_session.id")
    type: str = Field(max_length=50)  # notification, command, token_request, etc.
    message: str = Field(max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    bot_session: BotSession = Relationship(back_populates="bot_events")


class BotNotification(SQLModel, table=True):
    __tablename__ = "bot_notification"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    bot_session_id: uuid.UUID = Field(foreign_key="bot_session.id")
    title: str = Field(max_length=255)
    message: str = Field(max_length=1000)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = Field(nullable=True)

    bot_session: BotSession = Relationship(back_populates="bot_notifications")
    notification_channels: list["BotNotificationChannel"] = Relationship(
        back_populates="bot_notification"
    )


class BotNotificationChannel(SQLModel, table=True):
    __tablename__ = "bot_notification_channel"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    bot_notification_id: uuid.UUID = Field(foreign_key="bot_notification.id")
    channel: str = Field(max_length=50)
    status: str = Field(max_length=50)  # sent, failed, pending, etc.

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = Field(nullable=True)

    bot_notification: BotNotification = Relationship(
        back_populates="notification_channels"
    )
