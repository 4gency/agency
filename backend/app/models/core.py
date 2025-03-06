# core.py
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from pydantic import EmailStr, field_validator
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Column, Field, ForeignKey, Relationship, SQLModel

# Handle circular imports with TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.bot import (
        BotSession,
        Credentials,
    )


class SubscriptionMetric(Enum):
    """Define os tipos de métricas para assinaturas."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    APPLIES = "applies"


class PaymentRecurrenceStatus(Enum):
    """Define os status de recorrência de pagamento."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PENDING_CANCELLATION = "pending_cancellation"


# Modelo base para usuários
class UserBase(SQLModel):
    """Modelo base com propriedades compartilhadas para usuários."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_subscriber: bool = Field(default=False)
    full_name: str | None = Field(default=None, max_length=255)


# Modelo para criação de usuários via API
class UserCreate(UserBase):
    """Modelo usado na criação de usuários via API."""

    password: str = Field(min_length=8, max_length=40)


# Modelo para registro de usuários
class UserRegister(SQLModel):
    """Modelo usado para registro de novos usuários."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Modelo para atualização de usuários via API
class UserUpdate(UserBase):
    """Modelo usado para atualização de usuários via API."""

    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


# Modelo para atualização do próprio perfil
class UserUpdateMe(SQLModel):
    """Modelo usado por usuários para atualizar seu próprio perfil."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


# Modelo para atualização de senha
class UpdatePassword(SQLModel):
    """Modelo usado para atualização de senha."""

    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Modelo de usuário para o banco de dados
class User(UserBase, table=True):
    """Modelo completo de usuário para armazenamento no banco de dados."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    is_subscriber: bool = Field(default=False)
    stripe_customer_id: str | None = Field(default=None)

    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
    sec_ch_ua: str = Field(
        default='"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"'
    )
    sec_ch_ua_platform: str = Field(default="Windows")

    # Relacionamentos
    subscriptions: list["Subscription"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    payments: list["Payment"] = Relationship(back_populates="user", cascade_delete=True)
    credentials: list["Credentials"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    bot_sessions: list["BotSession"] = Relationship(
        back_populates="user", cascade_delete=True
    )

    def get_active_subscriptions(self) -> list["Subscription"]:
        """Retorna as assinaturas ativas do usuário."""
        return [
            subscription
            for subscription in self.subscriptions
            if subscription.is_active
        ]


# Modelo público de usuário para API
class UserPublic(UserBase):
    """Modelo de usuário para retorno via API."""

    id: uuid.UUID


# Modelo para lista de usuários
class UsersPublic(SQLModel):
    """Modelo para retornar uma lista de usuários via API."""

    data: list[UserPublic]
    count: int


# Modelo para benefícios de planos de assinatura
class SubscriptionPlanBenefit(SQLModel, table=True):
    """Modelo para benefícios incluídos em planos de assinatura."""

    __tablename__ = "subscription_plan_benefit"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subscription_plan_id: uuid.UUID = Field(foreign_key="subscription_plan.id")
    name: str = Field(max_length=100)

    # Relacionamentos
    subscription_plan: "SubscriptionPlan" = Relationship(back_populates="benefits")


# Modelo base para planos de assinatura
class SubscriptionPlanBase(SQLModel):
    """Modelo base para planos de assinatura."""

    name: str
    price: float
    has_badge: bool = Field(default=False)
    badge_text: str = Field(default="", max_length=50)
    button_text: str = Field(default="Subscribe", max_length=50)
    button_enabled: bool = Field(default=True)
    has_discount: bool = Field(default=False)
    price_without_discount: float = Field(default=0.0)
    currency: str = Field(default="USD", max_length=10)
    description: str = Field(default="", max_length=10000)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric = Field(default=SubscriptionMetric.MONTH)
    metric_value: int = Field(default=1)


# Modelo para criação de planos de assinatura
class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Modelo para criação de planos de assinatura via API."""

    benefits: list["SubscriptionPlanBenefitPublic"] = []


# Modelo para atualização de planos de assinatura
class SubscriptionPlanUpdate(SQLModel):
    """Modelo para atualização de planos de assinatura via API."""

    name: str | None = None
    price: float | None = None
    has_badge: bool | None = None
    badge_text: str | None = None
    button_text: str | None = None
    button_enabled: bool | None = None
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
        """Valida que o valor da métrica seja maior que zero."""
        if value is not None and value <= 0:
            raise ValueError("metric_value must be greater than 0")
        return value


# Modelo completo de plano de assinatura
class SubscriptionPlan(SQLModel, table=True):
    """Modelo completo de plano de assinatura para armazenamento no banco de dados."""

    __tablename__ = "subscription_plan"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    price: float
    has_badge: bool = Field(default=False)
    badge_text: str = Field(default="", max_length=50)
    button_text: str = Field(default="Subscribe", max_length=50)
    button_enabled: bool = Field(default=False)

    has_discount: bool = Field(default=False)
    price_without_discount: float = Field(default=0.0)
    currency: str = Field(default="USD", max_length=10)
    description: str = Field(default="", max_length=10000)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric = Field(default=SubscriptionMetric.DAY)
    metric_value: int = Field(default=30)

    stripe_product_id: str | None = Field(default=None, index=True)
    stripe_price_id: str | None = Field(default=None, index=True)

    # Relacionamentos
    benefits: list["SubscriptionPlanBenefit"] = Relationship(
        back_populates="subscription_plan", cascade_delete=True
    )
    subscriptions: list["Subscription"] = Relationship(
        back_populates="subscription_plan",
        cascade_delete=True,
    )
    checkout_sessions: list["CheckoutSession"] = Relationship(back_populates="plan")


# Modelo base para assinaturas
class SubscriptionBase(SQLModel):
    """Modelo base para assinaturas."""

    user_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric
    metric_status: int
    payment_recurrence_status: PaymentRecurrenceStatus = Field(
        default=PaymentRecurrenceStatus.ACTIVE
    )


# Modelo público de assinatura para API
class SubscriptionPublic(SQLModel):
    """Modelo de assinatura para retorno via API."""

    id: uuid.UUID
    user_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    is_active: bool
    metric_type: SubscriptionMetric
    metric_status: int
    payment_recurrence_status: PaymentRecurrenceStatus

    subscription_plan: SubscriptionPlan | None = None


# Modelo estendido de assinatura pública
class SubscriptionPublicExtended(SubscriptionPublic):
    """Modelo estendido de assinatura para retorno via API com pagamentos."""

    payments: list["PaymentPublic"] = []


# Modelo para criação de assinaturas
class SubscriptionCreate(SubscriptionBase):
    """Modelo para criação de assinaturas via API."""

    pass


# Modelo para atualização de assinaturas
class SubscriptionUpdate(SQLModel):
    """Modelo para atualização de assinaturas via API."""

    user_id: uuid.UUID | None = None
    subscription_plan_id: uuid.UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None
    metric_type: SubscriptionMetric | None = None
    metric_status: int | None = None
    payment_recurrence_status: PaymentRecurrenceStatus | None = None


# Modelo completo de assinatura para banco de dados
class Subscription(SQLModel, table=True):
    """Modelo completo de assinatura para armazenamento no banco de dados."""

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
    payment_recurrence_status: PaymentRecurrenceStatus = Field(
        default=PaymentRecurrenceStatus.ACTIVE
    )

    stripe_subscription_id: str | None = Field(default=None, index=True)

    # Relacionamentos
    user: User = Relationship(back_populates="subscriptions")
    subscription_plan: SubscriptionPlan = Relationship(back_populates="subscriptions")
    payments: list["Payment"] = Relationship(back_populates="subscription")

    def extend_subscription(self, plan: SubscriptionPlan | None = None) -> None:
        """
        Estende a assinatura para um novo plano ou renova o atual.

        Args:
            plan: Novo plano de assinatura (opcional).
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
        Renova as métricas da assinatura com base no plano atual.

        Regras:
        1. Se o tipo de métrica do plano for diferente do atual, reseta para o novo tipo
        2. Se for o mesmo tipo, verifica se já expirou para decidir como renovar
        3. Garante que o valor de métrica nunca seja negativo
        """
        plan = self.subscription_plan

        # Se a métrica do plano for diferente da métrica atual, "resetamos" tudo
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
        ATENÇÃO: Executar apenas APÓS renovação das métricas.
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
        Verifica se a assinatura precisa ser desativada com base no tipo de métrica.

        Retorna:
            True se precisar ser desativada, False caso contrário.
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

        # Métrica baseada em crédito de aplicações
        elif self.metric_type == SubscriptionMetric.APPLIES:
            if self.metric_status < 1:
                return True

        return False


# Modelo base para pagamentos
class PaymentBase(SQLModel):
    """Modelo base para pagamentos."""

    subscription_id: uuid.UUID | None = None
    user_id: uuid.UUID
    amount: float
    currency: str = Field(default="USD", max_length=10)
    payment_date: datetime
    payment_status: str = Field(default="pending", max_length=100)
    payment_gateway: str = Field(default="stripe", max_length=50)
    transaction_id: str = Field(max_length=150)


# Modelo para criação de pagamentos
class PaymentCreate(PaymentBase):
    """Modelo para criação de pagamentos via API."""

    pass


# Modelo para atualização de pagamentos
class PaymentUpdate(SQLModel):
    """Modelo para atualização de pagamentos via API."""

    subscription_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    amount: float | None = None
    currency: str | None = None
    payment_date: datetime | None = None
    payment_status: str | None = None
    payment_gateway: str | None = None
    transaction_id: str | None = None
    payment_recurrence_status: PaymentRecurrenceStatus | None = None


# Modelo completo de pagamento para banco de dados
class Payment(SQLModel, table=True):
    """Modelo completo de pagamento para armazenamento no banco de dados."""

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

    # Relacionamentos
    subscription: Subscription = Relationship(back_populates="payments")
    user: User = Relationship(back_populates="payments")


# Modelo público de pagamento para API
class PaymentPublic(SQLModel):
    """Modelo de pagamento para retorno via API."""

    id: uuid.UUID
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    currency: str
    payment_date: datetime
    payment_status: str
    payment_gateway: str
    transaction_id: str


# Modelo para lista de pagamentos
class PaymentsPublic(SQLModel):
    """Modelo para retornar uma lista de pagamentos via API."""

    data: list[PaymentPublic]
    count: int


# Modelo de sessão de checkout
class CheckoutSession(SQLModel, table=True):
    """Modelo para sessões de checkout de pagamento."""

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

    # Relacionamentos
    plan: SubscriptionPlan = Relationship(back_populates="checkout_sessions")


# Modelo para atualização de sessão de checkout
class CheckoutSessionUpdate(SQLModel):
    """Modelo para atualização de sessões de checkout via API."""

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


# Modelo público de sessão de checkout para API
class CheckoutSessionPublic(SQLModel):
    """Modelo de sessão de checkout para retorno via API."""

    id: uuid.UUID
    session_id: str
    session_url: str
    expires_at: datetime


# Modelo genérico para mensagens
class Message(SQLModel):
    """Modelo genérico para mensagens de resposta."""

    message: str


# Modelo para mensagens de erro
class ErrorMessage(SQLModel):
    """Modelo para mensagens de erro."""

    detail: str


# Modelo para tokens JWT
class Token(SQLModel):
    """Modelo para representar tokens JWT de autenticação."""

    access_token: str
    token_type: str = Field(default="bearer")


# Modelo para conteúdo do payload JWT
class TokenPayload(SQLModel):
    """Modelo para o payload contido em tokens JWT."""

    sub: str | None = Field(default=None)


# Modelo para redefinição de senha
class NewPassword(SQLModel):
    """Modelo para redefinição de senha."""

    token: str
    new_password: str = Field(min_length=8, max_length=40)


# Modelo público para benefícios de plano de assinatura
class SubscriptionPlanBenefitPublic(SQLModel):
    """Modelo público para benefícios de plano de assinatura."""

    name: str


# Modelo público para planos de assinatura
class SubscriptionPlanPublic(SQLModel):
    """Modelo público completo para planos de assinatura."""

    id: uuid.UUID
    name: str
    price: float
    has_badge: bool
    badge_text: str
    button_text: str
    button_enabled: bool
    has_discount: bool
    price_without_discount: float
    currency: str
    description: str
    is_active: bool
    metric_type: SubscriptionMetric
    metric_value: int

    benefits: list[SubscriptionPlanBenefitPublic] = []


# Modelo para lista de planos de assinatura
class SubscriptionPlansPublic(SQLModel):
    """Modelo para retornar uma lista de planos de assinatura via API."""

    plans: list[SubscriptionPlanPublic] = []
