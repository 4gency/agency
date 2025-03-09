import datetime
from typing import Any, ClassVar, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr
from pydantic import Field as PField
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import JSON, Column, Field, SQLModel


class PersonalInformation(BaseModel):
    name: str = PField(description="First name", examples=["John"])
    surname: str = PField(description="Last name", examples=["Doe"])
    date_of_birth: str = PField(
        description="Date of birth in ISO format",
        examples=[
            (datetime.date.today() - datetime.timedelta(days=30 * 365)).isoformat()
        ],
    )
    country: str = PField(description="Country of residence", examples=["USA"])
    city: str = PField(description="City of residence", examples=["New York"])
    address: str = PField(description="Street address", examples=["123 Main St"])
    zip_code: str = PField(description="Postal/ZIP code", examples=["10001"])
    phone_prefix: str = PField(description="Phone country code", examples=["+1"])
    phone: str = PField(
        description="Phone number without country code", examples=["123456789"]
    )
    email: EmailStr = PField(
        description="Email address", examples=["john.doe@email.com"]
    )
    github: str = PField(
        description="GitHub profile URL", examples=["https://github.com/john_doe"]
    )
    linkedin: str = PField(
        description="LinkedIn profile URL",
        examples=["https://linkedin.com/in/john_doe"],
    )


class EducationDetails(BaseModel):
    education_level: str = PField(
        description="Highest level of education", examples=["Bachelor's Degree"]
    )
    institution: str = PField(
        description="Educational institution name", examples=["University of New York"]
    )
    field_of_study: str = PField(
        description="Major or field of study", examples=["Computer Science"]
    )
    final_evaluation_grade: str = PField(
        description="Final grade or GPA", examples=["A"]
    )
    start_date: str = PField(description="Year education started", examples=["2018"])
    year_of_completion: str = PField(
        description="Year education completed", examples=["2022"]
    )
    exam: list[str] = PField(
        description="Standardized tests taken", examples=[["GRE", "TOEFL"]]
    )


class ExperienceDetail(BaseModel):
    position: str = PField(description="Job title", examples=["Software Engineer"])
    company: str = PField(description="Company name", examples=["Google"])
    employment_period: str = PField(
        description="Period of employment", examples=["2020 - 2022"]
    )
    location: str = PField(description="Job location", examples=["New York"])
    industry: str = PField(description="Industry sector", examples=["Technology"])
    key_responsibilities: list[str] = PField(
        description="Main job responsibilities",
        examples=[["Developed new features", "Fixed bugs"]],
    )
    skills_acquired: list[str] = PField(
        description="Skills gained during employment",
        examples=[["Python", "Django", "React"]],
    )


class Project(BaseModel):
    name: str = PField(description="Project name", examples=["My awesome CRUD app"])
    description: str = PField(
        description="Project description",
        examples=["A CRUD app that does CRUD operations"],
    )
    link: str = PField(description="Project URL", examples=["www.myawesomecrud.com"])


class Achievement(BaseModel):
    name: str = PField(
        description="Achievement title", examples=["Employee of the month"]
    )
    description: str = PField(
        description="Achievement description",
        examples=["Awarded for being the best employee"],
    )


class Certification(BaseModel):
    name: str = PField(
        description="Certification name", examples=["Python Certification"]
    )
    description: str = PField(
        description="Certification description", examples=["Certified Python Developer"]
    )


class Language(BaseModel):
    language: str = PField(description="Language name", examples=["English"])
    proficiency: str = PField(
        description="Language proficiency level", examples=["Native"]
    )


class Availability(BaseModel):
    notice_period: str = PField(
        description="Required notice period", examples=["1 month"]
    )


class SalaryExpectations(BaseModel):
    salary_range_usd: str = PField(
        description="Expected salary range in USD", examples=["90000 - 110000"]
    )


class SelfIdentification(BaseModel):
    gender: str = PField(description="Gender", examples=["Male"])
    pronouns: str = PField(description="Preferred pronouns", examples=["He/Him"])
    veteran: bool = PField(description="Veteran status", examples=[False])
    disability: bool = PField(description="Disability status", examples=[False])
    ethnicity: str = PField(description="Ethnicity", examples=["Hispanic"])


class LegalAuthorization(BaseModel):
    eu_work_authorization: bool = PField(
        description="Has EU work authorization", examples=[False]
    )
    us_work_authorization: bool = PField(
        description="Has US work authorization", examples=[False]
    )
    requires_us_visa: bool = PField(description="Requires US visa", examples=[False])
    requires_us_sponsorship: bool = PField(
        description="Requires US sponsorship", examples=[False]
    )
    requires_eu_visa: bool = PField(description="Requires EU visa", examples=[False])
    legally_allowed_to_work_in_eu: bool = PField(
        description="Legally allowed to work in EU", examples=[False]
    )
    legally_allowed_to_work_in_us: bool = PField(
        description="Legally allowed to work in US", examples=[False]
    )
    requires_eu_sponsorship: bool = PField(
        description="Requires EU sponsorship", examples=[False]
    )
    canada_work_authorization: bool = PField(
        description="Has Canada work authorization", examples=[False]
    )
    requires_canada_visa: bool = PField(
        description="Requires Canada visa", examples=[False]
    )
    legally_allowed_to_work_in_canada: bool = PField(
        description="Legally allowed to work in Canada", examples=[False]
    )
    requires_canada_sponsorship: bool = PField(
        description="Requires Canada sponsorship", examples=[False]
    )
    uk_work_authorization: bool = PField(
        description="Has UK work authorization", examples=[False]
    )
    requires_uk_visa: bool = PField(description="Requires UK visa", examples=[False])
    legally_allowed_to_work_in_uk: bool = PField(
        description="Legally allowed to work in UK", examples=[False]
    )
    requires_uk_sponsorship: bool = PField(
        description="Requires UK sponsorship", examples=[False]
    )


class WorkPreferences(BaseModel):
    remote_work: bool = PField(description="Open to remote work", examples=[True])
    in_person_work: bool = PField(description="Open to in-person work", examples=[True])
    open_to_relocation: bool = PField(description="Open to relocation", examples=[True])
    willing_to_complete_assessments: bool = PField(
        description="Willing to complete assessments", examples=[True]
    )
    willing_to_undergo_drug_tests: bool = PField(
        description="Willing to undergo drug tests", examples=[True]
    )
    willing_to_undergo_background_checks: bool = PField(
        description="Willing to undergo background checks", examples=[True]
    )


class PlainTextResumePublic(BaseModel):
    personal_information: PersonalInformation = PField(
        description="Personal contact information"
    )
    education_details: list[EducationDetails] = PField(
        description="Educational background"
    )
    experience_details: list[ExperienceDetail] = PField(description="Work experience")
    projects: list[Project] = PField(description="Personal or professional projects")
    achievements: list[Achievement] = PField(description="Notable achievements")
    certifications: list[Certification] = PField(
        description="Professional certifications"
    )
    languages: list[Language] = PField(description="Languages spoken")
    interests: list[str] = PField(
        description="Personal interests and hobbies", examples=[["Reading", "Swimming"]]
    )
    availability: Availability = PField(description="Work availability information")
    salary_expectations: SalaryExpectations = PField(description="Salary expectations")
    self_identification: SelfIdentification = PField(
        description="Self-identification information"
    )
    legal_authorization: LegalAuthorization = PField(
        description="Work authorization status"
    )
    work_preferences: WorkPreferences = PField(description="Work preferences")


class PlainTextResume(SQLModel, table=True):
    __tablename__: ClassVar[str] = "plain_text_resumes"

    id: int | None = Field(default=None, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    personal_information: dict[str, Any] = Field(sa_column=Column(JSON))
    education_details: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    experience_details: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    projects: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    achievements: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    certifications: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    languages: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    interests: list[str] = Field(sa_column=Column(JSON))
    availability: dict[str, Any] = Field(sa_column=Column(JSON))
    salary_expectations: dict[str, Any] = Field(sa_column=Column(JSON))
    self_identification: dict[str, Any] = Field(sa_column=Column(JSON))
    legal_authorization: dict[str, Any] = Field(sa_column=Column(JSON))
    work_preferences: dict[str, Any] = Field(sa_column=Column(JSON))


def generate_plain_text_resume_yaml(
    resume: Union["PlainTextResume", "PlainTextResumePublic"],
) -> str:
    """
    Generate a YAML string from a PlainTextResume or PlainTextResumePublic object that matches
    the exact format required by the validation function.

    Args:
        resume: The PlainTextResume or PlainTextResumePublic object containing resume data

    Returns:
        The generated YAML as a string
    """
    # Check if we're dealing with PlainTextResumePublic or PlainTextResume
    is_public = not hasattr(resume, "user_id")

    # Helper function to get boolean values as "Yes"/"No" strings
    def bool_to_yes_no(value: bool) -> str:
        return "Yes" if value else "No"

    # Helper function to get a field from the object based on the type
    def get_field(obj, field_name) -> Any:
        if is_public:
            return getattr(obj, field_name)
        else:
            # If it's a dict in PlainTextResume
            return obj.get(field_name)

    # Start building the YAML string
    yaml_str = "personal_information:\n"
    personal_info = resume.personal_information
    for field in [
        "name",
        "surname",
        "date_of_birth",
        "country",
        "city",
        "address",
        "zip_code",
        "phone_prefix",
        "phone",
        "email",
        "github",
        "linkedin",
    ]:
        value = (
            get_field(personal_info, field) if is_public else personal_info.get(field)  # type: ignore
        )
        yaml_str += f'  {field}: "{value}"\n'

    # Education details
    yaml_str += "\neducation_details:\n"
    education_list = resume.education_details
    for edu in education_list:
        yaml_str += (
            '  - education_level: "' + get_field(edu, "education_level") + '"\n'  # type: ignore
            if is_public
            else '  - education_level: "' + edu.get("education_level") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    institution: "' + get_field(edu, "institution") + '"\n'  # type: ignore
            if is_public
            else '    institution: "' + edu.get("institution") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    field_of_study: "' + get_field(edu, "field_of_study") + '"\n'  # type: ignore
            if is_public
            else '    field_of_study: "' + edu.get("field_of_study") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    final_evaluation_grade: "'
            + get_field(edu, "final_evaluation_grade")  # type: ignore
            + '"\n'
            if is_public
            else '    final_evaluation_grade: "'
            + edu.get("final_evaluation_grade")  # type: ignore
            + '"\n'
        )
        yaml_str += (
            '    start_date: "' + get_field(edu, "start_date") + '"\n'  # type: ignore
            if is_public
            else '    start_date: "' + edu.get("start_date") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    year_of_completion: "' + get_field(edu, "year_of_completion") + '"\n'  # type: ignore
            if is_public
            else '    year_of_completion: "' + edu.get("year_of_completion") + '"\n'  # type: ignore
        )

        # Handle exams differently based on the structure
        yaml_str += "    exam:\n"
        if is_public:
            # Handle if it's a list in PlainTextResumePublic
            if isinstance(get_field(edu, "exam"), list):
                exams = get_field(edu, "exam")
                for i, exam in enumerate(exams):  # type: ignore
                    yaml_str += f'      exam_name_{i+1}: "{exam}"\n'
            else:
                # If it's not a list, we assume it's a nested object
                exam_obj = get_field(edu, "exam")
                for key, value in exam_obj.items():  # type: ignore
                    yaml_str += f'      {key}: "{value}"\n'
        else:
            # Handle if it's in PlainTextResume
            if isinstance(edu.get("exam"), list):  # type: ignore
                exams = edu.get("exam")  # type: ignore
                for i, exam in enumerate(exams):  # type: ignore
                    yaml_str += f'      exam_name_{i+1}: "{exam}"\n'
            else:
                # If it's not a list, we assume it's a nested dictionary
                exam_obj = edu.get("exam", {})  # type: ignore
                for key, value in exam_obj.items():
                    yaml_str += f'      {key}: "{value}"\n'

    # Experience details
    yaml_str += "\nexperience_details:\n"
    exp_list = resume.experience_details
    for exp in exp_list:
        yaml_str += (
            '  - position: "' + get_field(exp, "position") + '"\n'  # type: ignore
            if is_public
            else '  - position: "' + exp.get("position") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    company: "' + get_field(exp, "company") + '"\n'  # type: ignore
            if is_public
            else '    company: "' + exp.get("company") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    employment_period: "' + get_field(exp, "employment_period") + '"\n'  # type: ignore
            if is_public
            else '    employment_period: "' + exp.get("employment_period") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    location: "' + get_field(exp, "location") + '"\n'  # type: ignore
            if is_public
            else '    location: "' + exp.get("location") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    industry: "' + get_field(exp, "industry") + '"\n'  # type: ignore
            if is_public
            else '    industry: "' + exp.get("industry") + '"\n'  # type: ignore
        )

        # Key responsibilities
        yaml_str += "    key_responsibilities:\n"
        responsibilities = (
            get_field(exp, "key_responsibilities")
            if is_public
            else exp.get("key_responsibilities")  # type: ignore
        )
        for i, resp in enumerate(responsibilities):  # type: ignore
            yaml_str += f'      - responsibility_{i+1}: "{resp}"\n'

        # Skills acquired
        yaml_str += "    skills_acquired:\n"
        skills = (
            get_field(exp, "skills_acquired")
            if is_public
            else exp.get("skills_acquired")  # type: ignore
        )
        for skill in skills:  # type: ignore
            yaml_str += f'      - "{skill}"\n'

    # Projects
    yaml_str += "\nprojects:\n"
    projects = resume.projects
    for project in projects:
        yaml_str += (
            '  - name: "' + get_field(project, "name") + '"\n'  # type: ignore
            if is_public
            else '  - name: "' + project.get("name") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    description: "' + get_field(project, "description") + '"\n'  # type: ignore
            if is_public
            else '    description: "' + project.get("description") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    link: "' + get_field(project, "link") + '"\n'  # type: ignore
            if is_public
            else '    link: "' + project.get("link") + '"\n'  # type: ignore
        )

    # Achievements
    yaml_str += "\nachievements:\n"
    achievements = resume.achievements
    for achievement in achievements:
        yaml_str += (
            '  - name: "' + get_field(achievement, "name") + '"\n'  # type: ignore
            if is_public
            else '  - name: "' + achievement.get("name") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    description: "' + get_field(achievement, "description") + '"\n'  # type: ignore
            if is_public
            else '    description: "' + achievement.get("description") + '"\n'  # type: ignore
        )

    # Certifications
    yaml_str += "\ncertifications:\n"
    certifications = resume.certifications
    for cert in certifications:
        yaml_str += (
            '  - name: "' + get_field(cert, "name") + '"\n'  # type: ignore
            if is_public
            else '  - name: "' + cert.get("name") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    description: "' + get_field(cert, "description") + '"\n'  # type: ignore
            if is_public
            else '    description: "' + cert.get("description") + '"\n'  # type: ignore
        )

    # Languages
    yaml_str += "\nlanguages:\n"
    languages = resume.languages
    for lang in languages:
        yaml_str += (
            '  - language: "' + get_field(lang, "language") + '"\n'  # type: ignore
            if is_public
            else '  - language: "' + lang.get("language") + '"\n'  # type: ignore
        )
        yaml_str += (
            '    proficiency: "' + get_field(lang, "proficiency") + '"\n'  # type: ignore
            if is_public
            else '    proficiency: "' + lang.get("proficiency") + '"\n'  # type: ignore
        )

    # Interests
    yaml_str += "\ninterests:\n"
    interests = resume.interests
    for interest in interests:
        yaml_str += f'  - "{interest}"\n'

    # Availability
    yaml_str += "\navailability:\n"
    availability = resume.availability
    yaml_str += (
        '  notice_period: "' + get_field(availability, "notice_period") + '"\n'  # type: ignore
        if is_public
        else '  notice_period: "' + availability.get("notice_period") + '"\n'  # type: ignore
    )

    # Salary expectations
    yaml_str += "\nsalary_expectations:\n"
    salary = resume.salary_expectations
    yaml_str += (
        '  salary_range_usd: "' + get_field(salary, "salary_range_usd") + '"\n'  # type: ignore
        if is_public
        else '  salary_range_usd: "' + salary.get("salary_range_usd") + '"\n'  # type: ignore
    )

    # Self identification
    yaml_str += "\nself_identification:\n"
    self_id = resume.self_identification
    yaml_str += (
        '  gender: "' + get_field(self_id, "gender") + '"\n'  # type: ignore
        if is_public
        else '  gender: "' + self_id.get("gender") + '"\n'  # type: ignore
    )
    yaml_str += (
        '  pronouns: "' + get_field(self_id, "pronouns") + '"\n'  # type: ignore
        if is_public
        else '  pronouns: "' + self_id.get("pronouns") + '"\n'  # type: ignore
    )
    yaml_str += (
        '  veteran: "' + bool_to_yes_no(get_field(self_id, "veteran")) + '"\n'  # type: ignore
        if is_public
        else '  veteran: "' + bool_to_yes_no(self_id.get("veteran")) + '"\n'  # type: ignore
    )
    yaml_str += (
        '  disability: "' + bool_to_yes_no(get_field(self_id, "disability")) + '"\n'  # type: ignore
        if is_public
        else '  disability: "' + bool_to_yes_no(self_id.get("disability")) + '"\n'  # type: ignore
    )
    yaml_str += (
        '  ethnicity: "' + get_field(self_id, "ethnicity") + '"\n'  # type: ignore
        if is_public
        else '  ethnicity: "' + self_id.get("ethnicity") + '"\n'  # type: ignore
    )

    # Legal authorization
    yaml_str += "\nlegal_authorization:\n"
    legal = resume.legal_authorization
    legal_fields = [
        "eu_work_authorization",
        "us_work_authorization",
        "requires_us_visa",
        "requires_us_sponsorship",
        "requires_eu_visa",
        "legally_allowed_to_work_in_eu",
        "legally_allowed_to_work_in_us",
        "requires_eu_sponsorship",
        "canada_work_authorization",
        "requires_canada_visa",
        "legally_allowed_to_work_in_canada",
        "requires_canada_sponsorship",
        "uk_work_authorization",
        "requires_uk_visa",
        "legally_allowed_to_work_in_uk",
        "requires_uk_sponsorship",
    ]

    for field in legal_fields:
        value = get_field(legal, field) if is_public else legal.get(field)  # type: ignore
        yaml_str += f'  {field}: "{bool_to_yes_no(value)}"\n'  # type: ignore

    # Work preferences
    yaml_str += "\nwork_preferences:\n"
    prefs = resume.work_preferences
    pref_fields = [
        "remote_work",
        "in_person_work",
        "open_to_relocation",
        "willing_to_complete_assessments",
        "willing_to_undergo_drug_tests",
        "willing_to_undergo_background_checks",
    ]

    for field in pref_fields:
        value = get_field(prefs, field) if is_public else prefs.get(field)  # type: ignore
        yaml_str += f'  {field}: "{bool_to_yes_no(value)}"\n'  # type: ignore

    return yaml_str
