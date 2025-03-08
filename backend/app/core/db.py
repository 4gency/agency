from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import settings
from app.models import crud
from app.models.bot import *  # noqa
from app.models.core import *  # noqa
from app.models.preference import Config # noqa
from app.models.resume import PlainTextResume # noqa

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def init_db(session: Session) -> str | None:
    # TODO: comment this out after first run
    SQLModel.metadata.create_all(engine)
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)  # noqa
    ).first()
    if not user:
        user_in = UserCreate(  # noqa
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
        return str(user.id)
    return None
