import datetime
import json
from typing import Dict, List, Optional, ClassVar, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr
from sqlalchemy import ForeignKey
from sqlmodel import Field, SQLModel, JSON, Column

from sqlalchemy.dialects.postgresql import UUID as PGUUID


class PersonalInformation(BaseModel):
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


class EducationDetails(BaseModel):
    education_level: str = "Bachelor's Degree"
    institution: str = "University of New York"
    field_of_study: str = "Computer Science"
    final_evaluation_grade: str = "A"
    start_date: str = "2018"
    year_of_completion: str = "2022"
    exam: List[str] = ["GRE", "TOEFL"]


class ExperienceDetail(BaseModel):
    position: str = "Software Engineer"
    company: str = "Google"
    employment_period: str = "2020 - 2022"
    location: str = "New York"
    industry: str = "Technology"
    key_responsibilities: List[str] = ["Developed new features", "Fixed bugs"]
    skills_acquired: List[str] = ["Python", "Django", "React"]


class Project(BaseModel):
    name: str = "My awesome CRUD app"
    description: str = "A CRUD app that does CRUD operations"
    link: str = "www.myawesomecrud.com"


class Achievement(BaseModel):
    name: str = "Employee of the month"
    description: str = "Awarded for being the best employee"


class Certification(BaseModel):
    name: str = "Python Certification"
    description: str = "Certified Python Developer"


class Language(BaseModel):
    language: str = "English"
    proficiency: str = "Native"


class Availability(BaseModel):
    notice_period: str = "1 month"


class SalaryExpectations(BaseModel):
    salary_range_usd: str = "90000 - 110000"


class SelfIdentification(BaseModel):
    gender: str = "Male"
    pronouns: str = "He/Him"
    veteran: bool = False
    disability: bool = False
    ethnicity: str = "Hispanic"


class LegalAuthorization(BaseModel):
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


class WorkPreferences(BaseModel):
    remote_work: bool = True
    in_person_work: bool = True
    open_to_relocation: bool = True
    willing_to_complete_assessments: bool = True
    willing_to_undergo_drug_tests: bool = True
    willing_to_undergo_background_checks: bool = True


class PlainTextResumePublic(BaseModel):
    personal_information: PersonalInformation = PersonalInformation()
    education_details: List[EducationDetails] = [
        EducationDetails(),
    ]
    experience_details: List[ExperienceDetail] = [
        ExperienceDetail(),
    ]
    projects: List[Project] = [
        Project(),
    ]
    achievements: List[Achievement] = [
        Achievement(),
    ]
    certifications: List[Certification] = [
        Certification(),
    ]
    languages: List[Language] = [
        Language(),
    ]
    interests: List[str] = ["Reading", "Swimming"]
    availability: Availability = Availability()
    salary_expectations: SalaryExpectations = SalaryExpectations()
    self_identification: SelfIdentification = SelfIdentification()
    legal_authorization: LegalAuthorization = LegalAuthorization()
    work_preferences: WorkPreferences = WorkPreferences()

    class Config:
        extra = "ignore"


class PlainTextResume(SQLModel, table=True):
    __tablename__: ClassVar[str] = "plain_text_resumes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    personal_information: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(PersonalInformation().model_dump_json()), 
        sa_column=Column(JSON)
    )
    education_details: List[Dict[str, Any]] = Field(
        default_factory=lambda: [json.loads(EducationDetails().model_dump_json())], 
        sa_column=Column(JSON)
    )
    experience_details: List[Dict[str, Any]] = Field(
        default_factory=lambda: [json.loads(ExperienceDetail().model_dump_json())], 
        sa_column=Column(JSON)
    )
    projects: List[Dict[str, Any]] = Field(
        default_factory=lambda: [json.loads(Project().model_dump_json())], 
        sa_column=Column(JSON)
    )
    achievements: List[Dict[str, Any]] = Field(
        default_factory=lambda: [json.loads(Achievement().model_dump_json())], 
        sa_column=Column(JSON)
    )
    certifications: List[Dict[str, Any]] = Field(
        default_factory=lambda: [json.loads(Certification().model_dump_json())], 
        sa_column=Column(JSON)
    )
    languages: List[Dict[str, Any]] = Field(
        default_factory=lambda: [json.loads(Language().model_dump_json())], 
        sa_column=Column(JSON)
    )
    interests: List[str] = Field(
        default_factory=lambda: ["Reading", "Swimming"], 
        sa_column=Column(JSON)
    )
    availability: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(Availability().model_dump_json()), 
        sa_column=Column(JSON)
    )
    salary_expectations: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(SalaryExpectations().model_dump_json()), 
        sa_column=Column(JSON)
    )
    self_identification: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(SelfIdentification().model_dump_json()), 
        sa_column=Column(JSON)
    )
    legal_authorization: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(LegalAuthorization().model_dump_json()), 
        sa_column=Column(JSON)
    )
    work_preferences: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(WorkPreferences().model_dump_json()), 
        sa_column=Column(JSON)
    )
