
from sqlmodel import Session

from app.models.core import User


def update_user_active_subscriptions(session: Session, user: User) -> None:
    subscriptions = filter(lambda sub: sub.is_active, user.subscriptions)
    
    for sub in subscriptions:
        if sub.need_to_deactivate:
            sub.is_active = False
            session.add(sub)
            session.commit()
            session.refresh(user)