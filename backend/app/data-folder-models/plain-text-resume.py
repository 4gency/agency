# personal_information:
#   name: "[Your Name]"
#   surname: "[Your Surname]"
#   date_of_birth: "[Your Date of Birth]"
#   country: "[Your Country]"
#   city: "[Your City]"
#   address: "[Your Address]"
#   phone_prefix: "[Your Phone Prefix]"
#   phone: "[Your Phone Number]"
#   email: "[Your Email Address]"
#   github: "[Your GitHub Profile URL]"
#   linkedin: "[Your LinkedIn Profile URL]"

# education_details:
#   - education_level: "[Your Education Level]"
#     institution: "[Your Institution]"
#     field_of_study: "[Your Field of Study]"
#     final_evaluation_grade: "[Your Final Evaluation Grade]"
#     start_date: "[Start Date]"
#     year_of_completion: "[Year of Completion]"
#     exam:
#       exam_name_1: "[Grade]"
#       exam_name_2: "[Grade]"
#       exam_name_3: "[Grade]"
#       exam_name_4: "[Grade]"
#       exam_name_5: "[Grade]"
#       exam_name_6: "[Grade]"

# experience_details:
#   - position: "[Your Position]"
#     company: "[Company Name]"
#     employment_period: "[Employment Period]"
#     location: "[Location]"
#     industry: "[Industry]"
#     key_responsibilities:
#       - responsibility_1: "[Responsibility Description]"
#       - responsibility_2: "[Responsibility Description]"
#       - responsibility_3: "[Responsibility Description]"
#     skills_acquired:
#       - "[Skill]"
#       - "[Skill]"
#       - "[Skill]"

#   - position: "[Your Position]"
#     company: "[Company Name]"
#     employment_period: "[Employment Period]"
#     location: "[Location]"
#     industry: "[Industry]"
#     key_responsibilities:
#       - responsibility_1: "[Responsibility Description]"
#       - responsibility_2: "[Responsibility Description]"
#       - responsibility_3: "[Responsibility Description]"
#     skills_acquired:
#       - "[Skill]"
#       - "[Skill]"
#       - "[Skill]"

# projects:
#   - name: "[Project Name]"
#     description: "[Project Description]"
#     link: "[Project Link]"

#   - name: "[Project Name]"
#     description: "[Project Description]"
#     link: "[Project Link]"

# achievements:
#   - name: "[Achievement Name]"
#     description: "[Achievement Description]"
#   - name: "[Achievement Name]"
#     description: "[Achievement Description]"

# certifications:
#   - name: "[Certification Name]"
#     description: "[Certification Description]"
#   - name: "[Certification Name]"
#     description: "[Certification Description]"

# languages:
#   - language: "[Language]"
#     proficiency: "[Proficiency Level]"
#   - language: "[Language]"
#     proficiency: "[Proficiency Level]"

# interests:
#   - "[Interest]"
#   - "[Interest]"
#   - "[Interest]"

# availability:
#   notice_period: "[Notice Period]"

# salary_expectations:
#   salary_range_usd: "[Salary Range]"

# self_identification:
#   gender: "[Gender]"
#   pronouns: "[Pronouns]"
#   veteran: "[Yes/No]"
#   disability: "[Yes/No]"
#   ethnicity: "[Ethnicity]"


# legal_authorization:
#   eu_work_authorization: "[Yes/No]"
#   us_work_authorization: "[Yes/No]"
#   requires_us_visa: "[Yes/No]"
#   requires_us_sponsorship: "[Yes/No]"
#   requires_eu_visa: "[Yes/No]"
#   legally_allowed_to_work_in_eu: "[Yes/No]"
#   legally_allowed_to_work_in_us: "[Yes/No]"
#   requires_eu_sponsorship: "[Yes/No]"
#   canada_work_authorization: "[Yes/No]"
#   requires_canada_visa: "[Yes/No]"
#   legally_allowed_to_work_in_canada: "[Yes/No]"
#   requires_canada_sponsorship: "[Yes/No]"
#   uk_work_authorization: "[Yes/No]"
#   requires_uk_visa: "[Yes/No]"
#   legally_allowed_to_work_in_uk: "[Yes/No]"
#   requires_uk_sponsorship: "[Yes/No]"


# work_preferences:
#   remote_work: "[Yes/No]"
#   in_person_work: "[Yes/No]"
#   open_to_relocation: "[Yes/No]"
#   willing_to_complete_assessments: "[Yes/No]"
#   willing_to_undergo_drug_tests: "[Yes/No]"
#   willing_to_undergo_background_checks: "[Yes/No]"

from typing import Literal
from unittest.util import strclass
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