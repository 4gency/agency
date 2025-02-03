from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlmodel import Session, select

from app.models.core import (
    Payment,
    PaymentCreate,
    PaymentUpdate,
    Subscription,
    SubscriptionCreate,
    SubscriptionPlan,
    SubscriptionPlanBenefit,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionUpdate,
    User
)


def create_subscription_plan(
    *, session: Session, subscription_plan_create: SubscriptionPlanCreate
) -> SubscriptionPlan:
    sp_data = subscription_plan_create.model_dump(exclude={"benefits"})
    benefits = subscription_plan_create.benefits
    db_obj = SubscriptionPlan.model_validate(sp_data)
    session.add(db_obj)
    
    session.commit()
    session.refresh(db_obj)
    for benefit in benefits:
        db_obj_benefit = SubscriptionPlanBenefit.model_validate(benefit, update={"subscription_plan_id": db_obj.id})
        session.add(db_obj_benefit)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_subscription_plan(
    *,
    session: Session,
    db_subscription_plan: SubscriptionPlan,
    subscription_plan_in: SubscriptionPlanUpdate,
) -> SubscriptionPlan:
    subscription_plan_data = subscription_plan_in.model_dump(exclude_unset=True)
    for key, value in subscription_plan_data.items():
        setattr(db_subscription_plan, key, value)
    session.add(db_subscription_plan)
    session.commit()
    session.refresh(db_subscription_plan)
    return db_subscription_plan


def get_subscription_plan_by_id(
    *, session: Session, id: uuid.UUID
) -> SubscriptionPlan | None:
    return session.get(SubscriptionPlan, id)


def get_subscription_plans(*, session: Session) -> list[SubscriptionPlan]:
    statement = select(SubscriptionPlan)
    return session.exec(statement).all()  # type: ignore


def create_subscription(
    *, session: Session, subscription_create: SubscriptionCreate
) -> Subscription:
    db_obj = Subscription.model_validate(subscription_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_subscription(
    *,
    session: Session,
    db_subscription: Subscription,
    subscription_in: SubscriptionUpdate,
) -> Subscription:
    subscription_data = subscription_in.model_dump(exclude_unset=True)
    for key, value in subscription_data.items():
        setattr(db_subscription, key, value)
    session.add(db_subscription)
    session.commit()
    session.refresh(db_subscription)
    return db_subscription


def get_subscription_by_id(*, session: Session, id: uuid.UUID) -> Subscription | None:
    return session.get(Subscription, id)


def get_subscriptions(*, session: Session) -> list[Subscription]:
    statement = select(Subscription)
    return session.exec(statement).all()  # type: ignore


def create_payment(*, session: Session, payment_create: PaymentCreate) -> Payment:
    db_obj = Payment.model_validate(payment_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def create_sub_payment(
    *, 
    session: Session,
    user: User,
    sub_plan: SubscriptionPlan,
    payment_status: str,
    payment_gateway: str,
    transaction_id: Optional[str] = None,
) -> tuple[Subscription, Payment]:
    sub_cr = SubscriptionCreate(
        user_id=user.id,
        subscription_plan_id=sub_plan.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc), # TODO: calculate end date
        is_active=False,
        metric_type=sub_plan.metric_type,
        metric_status=sub_plan.metric_value,
    )
    subscription = create_subscription(session=session, subscription_create=sub_cr)
    pmt_cr = PaymentCreate(
        subscription_id=subscription.id,
        user_id=user.id,
        amount=sub_plan.price,
        currency=sub_plan.currency,
        payment_date=datetime.now(timezone.utc),
        payment_status=payment_status,
        payment_gateway=payment_gateway,
        transaction_id=transaction_id if transaction_id else str(uuid.uuid4()),
    )
    payment = create_payment(session=session, payment_create=pmt_cr)
    return subscription, payment

def update_payment(
    *, session: Session, db_payment: Payment, payment_in: PaymentUpdate
) -> Payment:
    payment_data = payment_in.model_dump(exclude_unset=True)
    for key, value in payment_data.items():
        setattr(db_payment, key, value)
    session.add(db_payment)
    session.commit()
    session.refresh(db_payment)
    return db_payment


def get_payment_by_id(*, session: Session, id: uuid.UUID) -> Payment | None:
    return session.get(Payment, id)


def get_payments(*, session: Session) -> list[Payment]:
    statement = select(Payment)
    return session.exec(statement).all()  # type: ignore


def delete_subscription_plan(
    *, session: Session, db_subscription_plan: SubscriptionPlan
) -> None:
    session.delete(db_subscription_plan)
    session.commit()
    
def deactivate_subscription_plan(
    *, session: Session, db_subscription_plan: SubscriptionPlan
):
    db_subscription_plan.is_active = False
    session.add(db_subscription_plan)
    session.commit()
    session.refresh(db_subscription_plan)
