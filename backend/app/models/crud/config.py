from uuid import UUID

from sqlmodel import Session, select

from app.models.preference import Config, ConfigPublic
from app.models.resume import PlainTextResume, PlainTextResumePublic


# Job preferences CRUD
def create_config(*, session: Session, config: Config) -> Config:
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
    update_dict = config_in.model_dump(exclude_unset=True)

    # Para campos complexos, use model_dump_json para garantir serialização adequada
    if "experience_level" in update_dict:
        update_dict["experience_level"] = config_in.experience_level.model_dump()

    if "job_types" in update_dict:
        update_dict["job_types"] = config_in.job_types.model_dump()

    if "date" in update_dict:
        update_dict["date"] = config_in.date.model_dump()

    for key, value in update_dict.items():
        setattr(config_instance, key, value)

    session.add(config_instance)
    session.commit()
    session.refresh(config_instance)


# Resume CRUD
def create_resume(*, session: Session, resume: PlainTextResume) -> PlainTextResume:
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
    update_dict = resume_in.model_dump(exclude_unset=True)

    # Para campos complexos, use model_dump_json para garantir serialização adequada
    if "personal_information" in update_dict:
        update_dict[
            "personal_information"
        ] = resume_in.personal_information.model_dump()

    if "education_details" in update_dict:
        update_dict["education_details"] = [
            ed.model_dump() for ed in resume_in.education_details
        ]

    if "experience_details" in update_dict:
        update_dict["experience_details"] = [
            exp.model_dump() for exp in resume_in.experience_details
        ]

    if "projects" in update_dict:
        update_dict["projects"] = [p.model_dump() for p in resume_in.projects]

    if "achievements" in update_dict:
        update_dict["achievements"] = [a.model_dump() for a in resume_in.achievements]

    if "certifications" in update_dict:
        update_dict["certifications"] = [
            c.model_dump() for c in resume_in.certifications
        ]

    if "languages" in update_dict:
        update_dict["languages"] = [lang.model_dump() for lang in resume_in.languages]

    if "availability" in update_dict:
        update_dict["availability"] = resume_in.availability.model_dump()

    if "salary_expectations" in update_dict:
        update_dict["salary_expectations"] = resume_in.salary_expectations.model_dump()

    if "self_identification" in update_dict:
        update_dict["self_identification"] = resume_in.self_identification.model_dump()

    if "legal_authorization" in update_dict:
        update_dict["legal_authorization"] = resume_in.legal_authorization.model_dump()

    if "work_preferences" in update_dict:
        update_dict["work_preferences"] = resume_in.work_preferences.model_dump()

    for key, value in update_dict.items():
        setattr(resume_instance, key, value)

    session.add(resume_instance)
    session.commit()
    session.refresh(resume_instance)


def create_user_default_config(user_id: UUID, session: Session) -> Config:
    default_config = Config(
        user_id=user_id,
    )
    return create_config(session=session, config=default_config)


def create_user_default_resume(user_id: UUID, session: Session) -> PlainTextResume:
    default_resume = PlainTextResume(
        user_id=user_id,
    )
    return create_resume(session=session, resume=default_resume)


def create_user_default_configs(
    user_id: UUID, session: Session
) -> tuple[Config, PlainTextResume]:
    config = create_user_default_config(user_id, session)
    resume = create_user_default_resume(user_id, session)

    return config, resume
