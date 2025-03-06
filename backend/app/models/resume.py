import datetime

from odmantic import EmbeddedModel, Field, Model
from sqlmodel import SQLModel, EmailStr


class PersonalInformation(EmbeddedModel):
    name: str = "John"
    surname: str = "Doe"
    date_of_birth: str = (
        datetime.date.today() - datetime.timedelta(days=30 * 365)
    ).isoformat()
    country: str = "USA"
    city: str = "New York"
    address: str = "123 Main St"
    zip_code: str = "10001"
    phone_prefix: str = "+1"
    phone: str = "123456789"
    email: EmailStr = "john.doe@email.com"
    github: str = "https://github.com/john_doe"
    linkedin: str = "https://linkedin.com/in/john_doe"


class EducationDetails(EmbeddedModel):
    education_level: str = "Bachelor's Degree"
    institution: str = "University of New York"
    field_of_study: str = "Computer Science"
    final_evaluation_grade: str = "A"
    start_date: str = "2018"
    year_of_completion: str = "2022"
    exam: list[str] = ["GRE", "TOEFL"]


class ExperienceDetail(EmbeddedModel):
    position: str = "Software Engineer"
    company: str = "Google"
    employment_period: str = "2020 - 2022"
    location: str = "New York"
    industry: str = "Technology"
    key_responsibilities: list[str] = ["Developed new features", "Fixed bugs"]
    skills_acquired: list[str] = ["Python", "Django", "React"]


class Project(EmbeddedModel):
    name: str = "My awesome CRUD app"
    description: str = "A CRUD app that does CRUD operations"
    link: str = "www.myawesomecrud.com"


class Achievement(EmbeddedModel):
    name: str = "Employee of the month"
    description: str = "Awarded for being the best employee"


class Certification(EmbeddedModel):
    name: str = "Python Certification"
    description: str = "Certified Python Developer"


class Language(EmbeddedModel):
    language: str = "English"
    proficiency: str = "Native"


class Availability(EmbeddedModel):
    notice_period: str = "1 month"


class SalaryExpectations(EmbeddedModel):
    salary_range_usd: str = "90000 - 110000"


class SelfIdentification(EmbeddedModel):
    gender: str = "Male"
    pronouns: str = "He/Him"
    veteran: bool = False
    disability: bool = False
    ethnicity: str = "Hispanic"


class LegalAuthorization(EmbeddedModel):
    eu_work_authorization: bool = False
    us_work_authorization: bool = False
    requires_us_visa: bool = False
    requires_us_sponsorship: bool = False
    requires_eu_visa: bool = False
    legally_allowed_to_work_in_eu: bool = False
    legally_allowed_to_work_in_us: bool = False
    requires_eu_sponsorship: bool = False
    canada_work_authorization: bool = False
    requires_canada_visa: bool = False
    legally_allowed_to_work_in_canada: bool = False
    requires_canada_sponsorship: bool = False
    uk_work_authorization: bool = False
    requires_uk_visa: bool = False
    legally_allowed_to_work_in_uk: bool = False
    requires_uk_sponsorship: bool = False


class WorkPreferences(EmbeddedModel):
    remote_work: bool = True
    in_person_work: bool = True
    open_to_relocation: bool = True
    willing_to_complete_assessments: bool = True
    willing_to_undergo_drug_tests: bool = True
    willing_to_undergo_background_checks: bool = True


class PlainTextResumePublic(BaseModel, extra="ignore"):
    personal_information: PersonalInformation = PersonalInformation()
    education_details: list[EducationDetails] = [
        EducationDetails(),
    ]
    experience_details: list[ExperienceDetail] = [
        ExperienceDetail(),
    ]
    projects: list[Project] = [
        Project(),
    ]
    achievements: list[Achievement] = [
        Achievement(),
    ]
    certifications: list[Certification] = [
        Certification(),
    ]
    languages: list[Language] = [
        Language(),
    ]
    interests: list[str] = ["Reading", "Swimming"]
    availability: Availability = Availability()
    salary_expectations: SalaryExpectations = SalaryExpectations()
    self_identification: SelfIdentification = SelfIdentification()
    legal_authorization: LegalAuthorization = LegalAuthorization()
    work_preferences: WorkPreferences = WorkPreferences()


class PlainTextResume(Model):
    subscription_id: str = Field(index=True, unique=True)
    user_id: str

    personal_information: PersonalInformation = PersonalInformation()
    education_details: list[EducationDetails] = [
        EducationDetails(),
    ]
    experience_details: list[ExperienceDetail] = [
        ExperienceDetail(),
    ]
    projects: list[Project] = [
        Project(),
    ]
    achievements: list[Achievement] = [
        Achievement(),
    ]
    certifications: list[Certification] = [
        Certification(),
    ]
    languages: list[Language] = [
        Language(),
    ]
    interests: list[str] = ["Reading", "Swimming"]
    availability: Availability = Availability()
    salary_expectations: SalaryExpectations = SalaryExpectations()
    self_identification: SelfIdentification = SelfIdentification()
    legal_authorization: LegalAuthorization = LegalAuthorization()
    work_preferences: WorkPreferences = WorkPreferences()

    model_config = {
        "collection": "plain_text_resumes",  # type: ignore[typeddict-unknown-key]
    }
