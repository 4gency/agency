from pydantic import BaseModel


class PersonalInformation(BaseModel):
    name: str
    surname: str
    date_of_birth: str
    country: str
    city: str
    address: str
    phone_prefix: str
    phone: str
    email: str
    github: str
    linkedin: str
    
class EducationDetails(BaseModel):
    education_level: str
    institution: str
    field_of_study: str
    final_evaluation_grade: str
    start_date: str
    year_of_completion: str
    exam: list[str]
    
class ExperienceDetail(BaseModel):
    position: str
    company: str
    employment_period: str
    location: str
    industry: str
    key_responsibilities: list[str]
    skills_acquired: list[str]
    
class Project(BaseModel):
    name: str
    description: str
    link: str
    
class Achievement(BaseModel):
    name: str
    description: str
    
class Certification(BaseModel):
    name: str
    description: str
    
class Language(BaseModel):
    language: str
    proficiency: str
    
class availability(BaseModel):
    notice_period: str
    
class SalaryExpectations(BaseModel):
    salary_range_usd: str
    
class SelfIdentification(BaseModel):
    gender: str
    pronouns: str
    veteran: bool
    disability: bool
    ethnicity: str
    
class LegalAuthorization(BaseModel):
    eu_work_authorization: bool
    us_work_authorization: bool
    requires_us_visa: bool
    requires_us_sponsorship: bool
    requires_eu_visa: bool
    legally_allowed_to_work_in_eu: bool
    legally_allowed_to_work_in_us: bool
    requires_eu_sponsorship: bool
    canada_work_authorization: bool
    requires_canada_visa: bool
    legally_allowed_to_work_in_canada: bool
    requires_canada_sponsorship: bool
    uk_work_authorization: bool
    requires_uk_visa: bool
    legally_allowed_to_work_in_uk: bool
    requires_uk_sponsorship: bool
    
class WorkPreferences(BaseModel):
    remote_work: bool
    in_person_work: bool
    open_to_relocation: bool
    willing_to_complete_assessments: bool
    willing_to_undergo_drug_tests: bool
    willing_to_undergo_background_checks: bool

class PlainTextResume:
    personal_information: PersonalInformation
    education_details: list[EducationDetails]
    experience_details: list[ExperienceDetail]
    projects: list[Project]
    achievements: list[Achievement]
    certifications: list[Certification]
    languages: list[Language]
    interests: list[str]
    availability: availability
    salary_expectations: SalaryExpectations
    self_identification: SelfIdentification
    legal_authorization: LegalAuthorization
    work_preferences: WorkPreferences