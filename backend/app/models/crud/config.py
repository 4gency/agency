from odmantic.session import SyncSession

from app.models.preference import Config, ConfigPublic
from app.models.resume import PlainTextResume, PlainTextResumePublic


# Job preferences CRUD
def create_config(*, session: SyncSession, config: Config) -> Config:
    session.save(config)
    return config


def get_config(*, session: SyncSession, subscription_id: str) -> Config | None:
    config = session.find_one(Config, Config.subscription_id == subscription_id)
    return config


def update_config(
    *, session: SyncSession, config_instance: Config, config_in: ConfigPublic
) -> None:
    update_dict = config_in.model_dump(exclude_unset=True)
    config_instance.model_update(update_dict)
    session.save(config_instance)


# Resume CRUD
def create_resume(*, session: SyncSession, resume: PlainTextResume) -> PlainTextResume:
    session.save(resume)
    return resume


def get_resume(*, session: SyncSession, subscription_id: str) -> PlainTextResume | None:
    resume = session.find_one(
        PlainTextResume, PlainTextResume.subscription_id == subscription_id
    )
    return resume


def update_resume(
    *,
    session: SyncSession,
    resume_instance: PlainTextResume,
    resume_in: PlainTextResumePublic,
) -> None:
    new_resume_data = resume_in.model_dump(exclude_unset=True)
    resume_instance.model_update(new_resume_data)
    session.save(resume_instance)


def create_subscription_default_configs(
    subscription_id: str, nosql_session: SyncSession
) -> None:
    default_config = Config(
        subscription_id=subscription_id,  # type: ignore
    )
    default_resume = PlainTextResume(
        subscription_id=subscription_id,  # type: ignore
    )
    create_config(session=nosql_session, config=default_config)
    create_resume(session=nosql_session, resume=default_resume)
