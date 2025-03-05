from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import func, select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models.core import Payment, PaymentPublic, PaymentsPublic

router = APIRouter()


@router.get(
    "",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=PaymentsPublic,
)
def read_payments(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve all payments.
    """
    count_statement = select(func.count()).select_from(Payment)
    count = session.exec(count_statement).one()

    statement = select(Payment).offset(skip).limit(limit)
    payments = session.exec(statement).all()
    payments_public = [PaymentPublic.model_validate(p) for p in payments]

    return PaymentsPublic(data=payments_public, count=count)
