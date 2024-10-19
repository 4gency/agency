from datetime import datetime
from enum import Enum
import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

class SubscriptionMetric(Enum):
    DAYS = 1
    APPLIES = 2

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
    
    subscriptions: list["Subscription"] = Relationship(back_populates="user")
    payments: list["Payment"] = Relationship(back_populates="user")

# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
    
class SubscriptionPlan(SQLModel, table=True):
    __tablename__ = "subscription_plan"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    price: float
    has_discount: bool = Field(default=False)
    price_with_discount: float = Field(default=0.0)
    currency: str = Field(default='USD', max_length=10)
    description: str = Field(default="", max_length=10000)
    is_active: bool = Field(default=True)
    metric_type: SubscriptionMetric = Field(default=SubscriptionMetric.DAYS)
    metric_value: int = Field(default=30)
    
    subscriptions: list["Subscription"] = Relationship(back_populates="subscription_plan")
    
class Subscription(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    subscription_plan_id: uuid.UUID = Field(foreign_key="subscription_plan.id")
    start_date: datetime
    end_date: datetime
    is_active: bool = Field(default=True)
    metric_status: int
    
    user: User = Relationship(back_populates="subscriptions")
    subscription_plan: SubscriptionPlan = Relationship(back_populates="subscriptions")
    payment: "Payment" = Relationship(back_populates="subscription")
    
class Payment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subscription_id: uuid.UUID = Field(foreign_key="subscription.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    amount: float
    currency: str = Field(default='USD', max_length=10)
    payment_date: datetime
    payment_status: str = Field(default="success", max_length=100)
    payment_gateway: str = Field(max_length=50)  # e.g., Stripe, BoaCompra
    transaction_id: str = Field(max_length=150)
    
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
