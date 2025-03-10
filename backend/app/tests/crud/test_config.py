import pytest
from sqlmodel import Session

from app.models.crud.config import (
    create_config,
    create_resume,
    get_config,
    get_resume,
    update_config,
    update_resume,
)
from app.models.preference import ConfigPublic, Date, ExperienceLevel, JobTypes
from app.models.resume import PlainTextResumePublic
from app.tests.utils.user import create_random_user


@pytest.fixture
def config_in() -> ConfigPublic:
    """Fixture para criar um objeto ConfigPublic com dados pré-definidos."""
    # Criar objetos para os componentes
    experience_level = ExperienceLevel(
        intership=True,
        entry=True,
        associate=True,
        mid_senior_level=True,
        director=False,
        executive=False,
    )

    job_types = JobTypes(
        full_time=True,
        contract=True,
        part_time=False,
        temporary=False,
        internship=True,
        other=False,
        volunteer=False,
    )

    date = Date(all_time=True, month=False, week=False, hours=False)

    return ConfigPublic(
        remote=True,
        experience_level=experience_level,
        job_types=job_types,
        date=date,
        positions=["Backend Developer", "Full Stack Developer", "Python Developer"],
        locations=["United States", "Canada", "Remote"],
        apply_once_at_company=True,
        distance=75,
        company_blacklist=["BadCompany Inc", "ToxicWork LLC"],
        title_blacklist=["Sales", "Marketing"],
        location_blacklist=["Antarctica", "North Pole"],
    )


@pytest.fixture
def plain_text_in() -> PlainTextResumePublic:
    """Fixture para criar um objeto PlainTextResumePublic com dados pré-definidos."""

    # Dados pessoais
    personal_information = {
        "name": "John",
        "surname": "Doe",
        "date_of_birth": "1990-01-01",
        "country": "USA",
        "city": "New York",
        "address": "123 Main St",
        "zip_code": "10001",
        "phone_prefix": "+1",
        "phone": "555-123-4567",
        "email": "john.doe@example.com",
        "github": "https://github.com/johndoe",
        "linkedin": "https://linkedin.com/in/johndoe",
    }

    # Educação
    education_details = [
        {
            "education_level": "Bachelor's Degree",
            "institution": "University of New York",
            "field_of_study": "Computer Science",
            "final_evaluation_grade": "A",
            "start_date": "2010",
            "year_of_completion": "2014",
            "exam": ["GRE", "TOEFL"],
        }
    ]

    # Experiência profissional
    experience_details = [
        {
            "position": "Software Engineer",
            "company": "Tech Solutions Inc.",
            "employment_period": "2014-2020",
            "location": "New York",
            "industry": "Technology",
            "key_responsibilities": [
                "Developed web applications",
                "Maintained legacy code",
            ],
            "skills_acquired": ["Python", "JavaScript", "SQL"],
        }
    ]

    # Projetos
    projects = [
        {
            "name": "Personal Website",
            "description": "Created a portfolio website to showcase projects",
            "link": "https://johndoe.dev",
        }
    ]

    # Conquistas
    achievements = [
        {
            "name": "Employee of the Year",
            "description": "Awarded for outstanding contribution to the team",
        }
    ]

    # Certificações
    certifications = [
        {
            "name": "AWS Certified Developer",
            "description": "Associate level certification for AWS development",
        }
    ]

    # Idiomas
    languages = [
        {"language": "English", "proficiency": "Native"},
        {"language": "Spanish", "proficiency": "Intermediate"},
    ]

    # Outros dados
    return PlainTextResumePublic(
        personal_information=personal_information,  # type: ignore
        education_details=education_details,  # type: ignore
        experience_details=experience_details,  # type: ignore
        projects=projects,  # type: ignore
        achievements=achievements,  # type: ignore
        certifications=certifications,  # type: ignore
        languages=languages,  # type: ignore
        interests=["Coding", "Music", "Hiking"],
        availability={"notice_period": "2 weeks"},  # type: ignore
        salary_expectations={"salary_range_usd": "80000-100000"},  # type: ignore
        self_identification={
            "gender": "Male",
            "pronouns": "He/Him",
            "veteran": False,
            "disability": False,
            "ethnicity": "White",
        },  # type: ignore
        legal_authorization={
            "eu_work_authorization": False,
            "us_work_authorization": True,
            "requires_us_visa": False,
            "requires_us_sponsorship": False,
            "requires_eu_visa": True,
            "legally_allowed_to_work_in_eu": False,
            "legally_allowed_to_work_in_us": True,
            "requires_eu_sponsorship": True,
            "canada_work_authorization": False,
            "requires_canada_visa": True,
            "legally_allowed_to_work_in_canada": False,
            "requires_canada_sponsorship": True,
            "uk_work_authorization": False,
            "requires_uk_visa": True,
            "legally_allowed_to_work_in_uk": False,
            "requires_uk_sponsorship": True,
        },  # type: ignore
        work_preferences={
            "remote_work": True,
            "in_person_work": True,
            "open_to_relocation": True,
            "willing_to_complete_assessments": True,
            "willing_to_undergo_drug_tests": True,
            "willing_to_undergo_background_checks": True,
        },  # type: ignore
    )


# ------------------------------------------------------------------------------
# Tests for Config (Job Preferences) CRUD
#
def test_create_config(db: Session, config_in: ConfigPublic) -> None:
    user = create_random_user(db)
    created_config = create_config(session=db, config_in=config_in, user=user)
    assert created_config.user_id == user.id

    fetched_config = get_config(session=db, user_id=user.id)
    assert fetched_config is not None
    assert fetched_config.user_id == user.id


def test_update_config(db: Session, config_in: ConfigPublic) -> None:
    user = create_random_user(db)
    # Create a default config document.
    config = create_config(session=db, config_in=config_in, user=user)

    # Get from database to ensure it's properly loaded
    config_result = get_config(session=db, user_id=user.id)
    assert config_result is not None

    # Create the base objects for the update
    experience_level = ExperienceLevel()
    job_types = JobTypes()
    date = Date(all_time=True)

    # Prepare an update via ConfigPublic.
    update_data = ConfigPublic(
        remote=False,
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
    assert updated_config.positions == ["Tester"]
    assert updated_config.locations == ["Canada"]
    assert updated_config.distance == 50


# ------------------------------------------------------------------------------
# Tests for Resume CRUD
#
def test_create_resume(db: Session, plain_text_in: PlainTextResumePublic) -> None:
    user = create_random_user(db)
    created_resume = create_resume(session=db, user=user, resume_in=plain_text_in)
    assert created_resume.user_id == user.id

    fetched_resume = get_resume(session=db, user_id=user.id)
    assert fetched_resume is not None
    assert fetched_resume.user_id == user.id


def test_update_resume(db: Session, plain_text_in: PlainTextResumePublic) -> None:
    user = create_random_user(db)
    # Create a default resume document.
    resume = create_resume(session=db, user=user, resume_in=plain_text_in)

    # Get from database to ensure it's properly loaded
    resume_result = get_resume(session=db, user_id=user.id)
    assert resume_result is not None

    plain_text_in.interests = ["Skate", "Sing"]

    update_resume(session=db, resume_instance=resume, resume_in=plain_text_in)

    fetched_resume = get_resume(session=db, user_id=user.id)
    assert fetched_resume is not None
    assert fetched_resume.interests == ["Skate", "Sing"]
