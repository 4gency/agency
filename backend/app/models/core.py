import uuid
from datetime import datetime
from enum import Enum

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel


class SubscriptionMetric(Enum):
    DAY = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4
    APPLY = 5


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
    stripe_customer_id: str | None = Field(default=None, index=True)

    subscriptions: list["Subscription"] = Relationship(back_populates="user")
    payments: list["Payment"] = Relationship(back_populates="user")


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class SubscriptionPlanBase(SQLModel):
    name: str
    price: float
    has_discount: bool = Field(default=False)
    price_with_discount: float = Field(default=0.0)
    currency: str = Field(default="USD", max_length=10)
    description: str = Field(default="", max_length=10000)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric = Field(default=SubscriptionMetric.DAY)
    metric_value: int = Field(default=30)


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class SubscriptionPlanUpdate(SQLModel):
    name: str | None = None
    price: float | None = None
    has_discount: bool | None = None
    price_with_discount: float | None = None
    currency: str | None = None
    description: str | None = None
    is_active: bool | None = None
    metric_type: SubscriptionMetric | None = None
    metric_value: int | None = None
    
    @field_validator('metric_value')
    def check_metric_value(cls, value):
        if value is not None and value <= 0:
            raise ValueError("metric_value must be greater than 0")
        return value


class SubscriptionPlan(SQLModel, table=True):
    __tablename__ = "subscription_plan"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    price: float
    has_discount: bool = Field(default=False)
    price_with_discount: float = Field(default=0.0)
    currency: str = Field(default="USD", max_length=10)
    description: str = Field(default="", max_length=10000)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric = Field(default=SubscriptionMetric.DAY)
    metric_value: int = Field(default=30)
    
    stripe_product_id: str | None = Field(default=None, index=True)
    stripe_price_id: str | None = Field(default=None, index=True)

    subscriptions: list["Subscription"] = Relationship(
        back_populates="subscription_plan"
    )


class SubscriptionBase(SQLModel):
    user_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    is_active: bool = Field(default=True)
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
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    subscription_plan_id: uuid.UUID = Field(foreign_key="subscription_plan.id")
    start_date: datetime
    end_date: datetime
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric
    metric_status: int
    
    stripe_subscription_id: str | None = Field(default=None, index=True)

    user: User = Relationship(back_populates="subscriptions")
    subscription_plan: SubscriptionPlan = Relationship(back_populates="subscriptions")
    payment: "Payment" = Relationship(back_populates="subscription")

    def need_to_deactivate(self) -> bool:
        if self.metric_type == SubscriptionMetric.DAY:
            if self.end_date < datetime.now():  # TODO: make it utc
                return True
        elif self.metric_type == SubscriptionMetric.APPLY:
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


    subscription: Subscription = Relationship(back_populates="payment")
    user: User = Relationship(back_populates="payments")


# Generic message
class Message(SQLModel):
    message: str


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


class SubscriptionPlanPublic(SQLModel):
    id: uuid.UUID
    name: str
    price: float
    has_discount: bool
    price_with_discount: float
    currency: str
    description: str
    is_active: bool
    metric_type: SubscriptionMetric
    metric_value: int
    
    stripe_product_id: str | None
    stripe_price_id: str | None


class SubscriptionPlansPublic(SQLModel):
    plans: list[SubscriptionPlanPublic]
