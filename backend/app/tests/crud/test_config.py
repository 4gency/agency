from sqlmodel import Session

from app.models.crud.config import (
    create_config,
    create_resume,
    create_user_default_config,
    create_user_default_configs,
    create_user_default_resume,
    get_config,
    get_resume,
    update_config,
    update_resume,
)
from app.models.preference import Config, ConfigPublic, Date, ExperienceLevel, JobTypes
from app.models.resume import PlainTextResume, PlainTextResumePublic
from app.tests.utils.user import create_random_user


# ------------------------------------------------------------------------------
# Tests for Config (Job Preferences) CRUD
#
def test_create_config(db: Session) -> None:
    user = create_random_user(db)
    config = Config(user_id=user.id)
    created_config = create_config(session=db, config=config)
    assert created_config.user_id == user.id

    fetched_config = get_config(session=db, user_id=user.id)
    assert fetched_config is not None
    assert fetched_config.user_id == user.id


def test_update_config(db: Session) -> None:
    user = create_random_user(db)
    # Create a default config document.
    config = Config(user_id=user.id)
    create_config(session=db, config=config)

    # Get from database to ensure it's properly loaded
    config = get_config(session=db, user_id=user.id)
    assert config is not None

    # Create the base objects for the update
    experience_level = ExperienceLevel()
    job_types = JobTypes()
    date = Date(all_time=True)

    # Prepare an update via ConfigPublic.
    update_data = ConfigPublic(
        remote=False,
        hybrid=False,
        onsite=True,
        experience_level=experience_level,
        job_types=job_types,
        date=date,
        positions=["Tester"],
        locations=["Canada"],
        apply_once_at_company=False,
        distance=50,
        company_blacklist=["BadCompany"],
        title_blacklist=["Intern"],
        location_blacklist=["Mexico"],
    )
    update_config(session=db, config_instance=config, config_in=update_data)

    updated_config = get_config(session=db, user_id=user.id)
    assert updated_config is not None
    assert updated_config.remote is False
    assert updated_config.hybrid is False
    assert updated_config.positions == ["Tester"]
    assert updated_config.locations == ["Canada"]
    assert updated_config.distance == 50


# ------------------------------------------------------------------------------
# Tests for Resume CRUD
#
def test_create_resume(db: Session) -> None:
    user = create_random_user(db)
    resume = PlainTextResume(user_id=user.id)
    created_resume = create_resume(session=db, resume=resume)
    assert created_resume.user_id == user.id

    fetched_resume = get_resume(session=db, user_id=user.id)
    assert fetched_resume is not None
    assert fetched_resume.user_id == user.id


def test_update_resume(db: Session) -> None:
    user = create_random_user(db)
    # Create a default resume document.
    resume = PlainTextResume(user_id=user.id)
    create_resume(session=db, resume=resume)

    # Get from database to ensure it's properly loaded
    resume = get_resume(session=db, user_id=user.id)
    assert resume is not None

    # Prepare an update via PlainTextResumePublic (e.g., updating interests).
    updated_resume_data = PlainTextResumePublic(
        interests=["Coding", "Music"]
        # Additional fields can be updated as needed.
    )
    update_resume(session=db, resume_instance=resume, resume_in=updated_resume_data)

    fetched_resume = get_resume(session=db, user_id=user.id)
    assert fetched_resume is not None
    assert fetched_resume.interests == ["Coding", "Music"]


# ------------------------------------------------------------------------------
# Tests for Default Configs/Resumes Creation
#
def test_create_user_default_config(db: Session) -> None:
    user = create_random_user(db)
    config = create_user_default_config(user_id=user.id, session=db)
    assert config.user_id == user.id

    fetched_config = get_config(session=db, user_id=user.id)
    assert fetched_config is not None


def test_create_user_default_resume(db: Session) -> None:
    user = create_random_user(db)
    resume = create_user_default_resume(user_id=user.id, session=db)
    assert resume.user_id == user.id

    fetched_resume = get_resume(session=db, user_id=user.id)
    assert fetched_resume is not None


def test_create_user_default_configs(db: Session) -> None:
    user = create_random_user(db)
    config, resume = create_user_default_configs(user_id=user.id, session=db)
    assert config.user_id == user.id
    assert resume.user_id == user.id

    fetched_config = get_config(session=db, user_id=user.id)
    fetched_resume = get_resume(session=db, user_id=user.id)
    assert fetched_config is not None
    assert fetched_resume is not None
