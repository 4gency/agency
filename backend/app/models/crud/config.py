from app.models.preference import Config
from app.models.resume import PlainTextResume


# Job preferences CRUD
def create_config(*, session, config: Config) -> Config:
    session.save(config)
    return config


def get_config(*, session, subscription_id: str) -> Config | None:
    config = session.find_one(Config, Config.subscription_id == subscription_id)
    return config


def update_config(*, session, config_instance: Config, new_config_data: dict) -> None:
    config_instance.model_update(new_config_data)
    session.save(config_instance)


# Resume CRUD
def create_resume(*, session, resume: PlainTextResume) -> PlainTextResume:
    session.save(resume)
    return resume


def get_resume(*, session, subscription_id: str) -> PlainTextResume | None:
    resume = session.find_one(
        PlainTextResume, PlainTextResume.subscription_id == subscription_id
    )
    return resume


def update_resume(
    *, session, resume_instance: PlainTextResume, new_resume_data: dict
) -> None:
    resume_instance.model_update(new_resume_data)
    session.save(resume_instance)


def create_subscription_default_configs(subscription_id: str, nosql_session) -> None:
    default_config = Config(
        subscription_id=subscription_id,  # type: ignore
    )
    default_resume = PlainTextResume(
        subscription_id=subscription_id,  # type: ignore
    )
    create_config(session=nosql_session, config=default_config)
    create_resume(session=nosql_session, resume=default_resume)
