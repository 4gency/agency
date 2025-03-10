from uuid import UUID

from sqlmodel import Session, select

from app.models.core import User
from app.models.preference import Config, ConfigPublic
from app.models.resume import PlainTextResume, PlainTextResumePublic


# Job preferences CRUD
def create_config(*, session: Session, config_in: ConfigPublic, user: User) -> Config:
    config = Config(user_id=user.id, **config_in.model_dump())

    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def get_config(*, session: Session, user_id: UUID) -> Config | None:
    statement = select(Config).where(Config.user_id == user_id)
    return session.exec(statement).first()


def update_config(
    *, session: Session, config_instance: Config, config_in: ConfigPublic
) -> None:
    """
    Atualiza completamente a configuração existente (operação PUT idempotente).

    Args:
        session: Sessão do banco de dados
        config_instance: Instância existente da configuração
        config_in: Dados completos da nova configuração
    """
    config_data = config_in.model_dump()

    user_id = config_instance.user_id
    obj_id = config_instance.id

    for key, value in config_data.items():
        setattr(config_instance, key, value)

    config_instance.user_id = user_id
    config_instance.id = obj_id

    session.add(config_instance)
    session.commit()
    session.refresh(config_instance)


# Resume CRUD
def create_resume(
    *, session: Session, resume_in: PlainTextResumePublic, user: User
) -> PlainTextResume:
    resume = PlainTextResume(user_id=user.id, **resume_in.model_dump())

    session.add(resume)
    session.commit()
    session.refresh(resume)
    return resume


def get_resume(*, session: Session, user_id: UUID) -> PlainTextResume | None:
    statement = select(PlainTextResume).where(PlainTextResume.user_id == user_id)
    return session.exec(statement).first()


def update_resume(
    *,
    session: Session,
    resume_instance: PlainTextResume,
    resume_in: PlainTextResumePublic,
) -> None:
    """
    Atualiza completamente o resumo existente (operação PUT idempotente).

    Args:
        session: Sessão do banco de dados
        resume_instance: Instância existente do resumo
        resume_in: Dados completos do novo resumo
    """
    resume_data = resume_in.model_dump()

    user_id = resume_instance.user_id
    obj_id = resume_instance.id

    for key, value in resume_data.items():
        setattr(resume_instance, key, value)

    resume_instance.user_id = user_id
    resume_instance.id = obj_id

    session.add(resume_instance)
    session.commit()
    session.refresh(resume_instance)
