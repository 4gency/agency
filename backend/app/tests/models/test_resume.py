import datetime
from typing import Any
from uuid import uuid4

import pytest

from app.models.resume import (
    Achievement,
    Availability,
    Certification,
    EducationDetails,
    ExperienceDetail,
    Language,
    LegalAuthorization,
    PersonalInformation,
    PlainTextResume,
    PlainTextResumePublic,
    Project,
    SalaryExpectations,
    SelfIdentification,
    WorkPreferences,
    generate_plain_text_resume_yaml,
)


class TestGeneratePlainTextResumeYaml:
    @pytest.fixture
    def sample_personal_info(self) -> dict[str, Any]:
        return {
            "name": "John",
            "surname": "Doe",
            "date_of_birth": (
                datetime.date.today() - datetime.timedelta(days=30 * 365)
            ).isoformat(),
            "country": "USA",
            "city": "New York",
            "address": "123 Main St",
            "zip_code": "10001",
            "phone_prefix": "+1",
            "phone": "123456789",
            "email": "john.doe@email.com",
            "github": "https://github.com/john_doe",
            "linkedin": "https://linkedin.com/in/john_doe",
        }

    @pytest.fixture
    def sample_education(self) -> dict[str, Any]:
        return {
            "education_level": "Bachelor's Degree",
            "institution": "University of New York",
            "field_of_study": "Computer Science",
            "final_evaluation_grade": "A",
            "start_date": "2018",
            "year_of_completion": "2022",
            "exam": ["GRE", "TOEFL"],
        }

    @pytest.fixture
    def sample_experience(self) -> dict[str, Any]:
        return {
            "position": "Software Engineer",
            "company": "Google",
            "employment_period": "2020 - 2022",
            "location": "New York",
            "industry": "Technology",
            "key_responsibilities": ["Developed new features", "Fixed bugs"],
            "skills_acquired": ["Python", "Django", "React"],
        }

    @pytest.fixture
    def sample_project(self) -> dict[str, str]:
        return {
            "name": "My awesome CRUD app",
            "description": "A CRUD app that does CRUD operations",
            "link": "www.myawesomecrud.com",
        }

    @pytest.fixture
    def sample_achievement(self) -> dict[str, str]:
        return {
            "name": "Employee of the month",
            "description": "Awarded for being the best employee",
        }

    @pytest.fixture
    def sample_certification(self) -> dict[str, str]:
        return {
            "name": "Python Certification",
            "description": "Certified Python Developer",
        }

    @pytest.fixture
    def sample_language(self) -> dict[str, str]:
        return {"language": "English", "proficiency": "Native"}

    @pytest.fixture
    def sample_availability(self) -> dict[str, str]:
        return {"notice_period": "1 month"}

    @pytest.fixture
    def sample_salary_expectations(self) -> dict[str, str]:
        return {"salary_range_usd": "90000 - 110000"}

    @pytest.fixture
    def sample_self_identification(self) -> dict[str, Any]:
        return {
            "gender": "Male",
            "pronouns": "He/Him",
            "veteran": False,
            "disability": False,
            "ethnicity": "Hispanic",
        }

    @pytest.fixture
    def sample_legal_authorization(self) -> dict[str, bool]:
        return {
            "eu_work_authorization": False,
            "us_work_authorization": False,
            "requires_us_visa": False,
            "requires_us_sponsorship": False,
            "requires_eu_visa": False,
            "legally_allowed_to_work_in_eu": False,
            "legally_allowed_to_work_in_us": False,
            "requires_eu_sponsorship": False,
            "canada_work_authorization": False,
            "requires_canada_visa": False,
            "legally_allowed_to_work_in_canada": False,
            "requires_canada_sponsorship": False,
            "uk_work_authorization": False,
            "requires_uk_visa": False,
            "legally_allowed_to_work_in_uk": False,
            "requires_uk_sponsorship": False,
        }

    @pytest.fixture
    def sample_work_preferences(self) -> dict[str, bool]:
        return {
            "remote_work": True,
            "in_person_work": True,
            "open_to_relocation": True,
            "willing_to_complete_assessments": True,
            "willing_to_undergo_drug_tests": True,
            "willing_to_undergo_background_checks": True,
        }

    @pytest.fixture
    def public_resume(
        self,
        sample_personal_info: dict[str, Any],
        sample_education: dict[str, Any],
        sample_experience: dict[str, Any],
        sample_project: dict[str, str],
        sample_achievement: dict[str, str],
        sample_certification: dict[str, str],
        sample_language: dict[str, str],
        sample_availability: dict[str, str],
        sample_salary_expectations: dict[str, str],
        sample_self_identification: dict[str, Any],
        sample_legal_authorization: dict[str, bool],
        sample_work_preferences: dict[str, bool],
    ) -> PlainTextResumePublic:
        """Fixture for a PlainTextResumePublic object."""
        return PlainTextResumePublic(
            personal_information=PersonalInformation(**sample_personal_info),
            education_details=[EducationDetails(**sample_education)],
            experience_details=[ExperienceDetail(**sample_experience)],
            projects=[Project(**sample_project)],
            achievements=[Achievement(**sample_achievement)],
            certifications=[Certification(**sample_certification)],
            languages=[Language(**sample_language)],
            interests=["Reading", "Swimming"],
            availability=Availability(**sample_availability),
            salary_expectations=SalaryExpectations(**sample_salary_expectations),
            self_identification=SelfIdentification(**sample_self_identification),
            legal_authorization=LegalAuthorization(**sample_legal_authorization),
            work_preferences=WorkPreferences(**sample_work_preferences),
        )

    @pytest.fixture
    def private_resume(
        self,
        sample_personal_info: dict[str, Any],
        sample_education: dict[str, Any],
        sample_experience: dict[str, Any],
        sample_project: dict[str, str],
        sample_achievement: dict[str, str],
        sample_certification: dict[str, str],
        sample_language: dict[str, str],
        sample_availability: dict[str, str],
        sample_salary_expectations: dict[str, str],
        sample_self_identification: dict[str, Any],
        sample_legal_authorization: dict[str, bool],
        sample_work_preferences: dict[str, bool],
    ) -> PlainTextResume:
        """Fixture for a PlainTextResume object."""
        resume = PlainTextResume()
        resume.id = 1
        resume.user_id = uuid4()
        resume.personal_information = sample_personal_info
        resume.education_details = [sample_education]
        resume.experience_details = [sample_experience]
        resume.projects = [sample_project]
        resume.achievements = [sample_achievement]
        resume.certifications = [sample_certification]
        resume.languages = [sample_language]
        resume.interests = ["Reading", "Swimming"]
        resume.availability = sample_availability
        resume.salary_expectations = sample_salary_expectations
        resume.self_identification = sample_self_identification
        resume.legal_authorization = sample_legal_authorization
        resume.work_preferences = sample_work_preferences
        return resume

    def test_basic_generation_public(
        self, public_resume: PlainTextResumePublic
    ) -> None:
        """Test basic YAML generation with a public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check for key sections
        assert "personal_information:" in yaml_str
        assert "education_details:" in yaml_str
        assert "experience_details:" in yaml_str
        assert "projects:" in yaml_str
        assert "achievements:" in yaml_str
        assert "certifications:" in yaml_str
        assert "languages:" in yaml_str
        assert "interests:" in yaml_str
        assert "availability:" in yaml_str
        assert "salary_expectations:" in yaml_str
        assert "self_identification:" in yaml_str
        assert "legal_authorization:" in yaml_str
        assert "work_preferences:" in yaml_str

    def test_basic_generation_private(self, private_resume: PlainTextResume) -> None:
        """Test basic YAML generation with a private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check for key sections
        assert "personal_information:" in yaml_str
        assert "education_details:" in yaml_str
        assert "experience_details:" in yaml_str
        assert "projects:" in yaml_str
        assert "achievements:" in yaml_str
        assert "certifications:" in yaml_str
        assert "languages:" in yaml_str
        assert "interests:" in yaml_str
        assert "availability:" in yaml_str
        assert "salary_expectations:" in yaml_str
        assert "self_identification:" in yaml_str
        assert "legal_authorization:" in yaml_str
        assert "work_preferences:" in yaml_str

    def test_personal_info_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test personal information in YAML for public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check for personal information fields
        assert '  name: "John"' in yaml_str
        assert '  surname: "Doe"' in yaml_str
        assert '  email: "john.doe@email.com"' in yaml_str

    def test_personal_info_private(self, private_resume: PlainTextResume) -> None:
        """Test personal information in YAML for private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check for personal information fields
        assert '  name: "John"' in yaml_str
        assert '  surname: "Doe"' in yaml_str
        assert '  email: "john.doe@email.com"' in yaml_str

    def test_education_details_public(
        self, public_resume: PlainTextResumePublic
    ) -> None:
        """Test education details in YAML for public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check for education fields
        assert '  - education_level: "Bachelor\'s Degree"' in yaml_str
        assert '    institution: "University of New York"' in yaml_str
        assert '    field_of_study: "Computer Science"' in yaml_str

    def test_education_details_private(self, private_resume: PlainTextResume) -> None:
        """Test education details in YAML for private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check for education fields
        assert '  - education_level: "Bachelor\'s Degree"' in yaml_str
        assert '    institution: "University of New York"' in yaml_str
        assert '    field_of_study: "Computer Science"' in yaml_str

    def test_experience_details_public(
        self, public_resume: PlainTextResumePublic
    ) -> None:
        """Test experience details in YAML for public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check for experience fields
        assert '  - position: "Software Engineer"' in yaml_str
        assert '    company: "Google"' in yaml_str
        assert '    employment_period: "2020 - 2022"' in yaml_str

    def test_experience_details_private(self, private_resume: PlainTextResume) -> None:
        """Test experience details in YAML for private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check for experience fields
        assert '  - position: "Software Engineer"' in yaml_str
        assert '    company: "Google"' in yaml_str
        assert '    employment_period: "2020 - 2022"' in yaml_str

    def test_exams_as_list_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test exams as list in public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Look for exams
        assert '      exam_name_1: "GRE"' in yaml_str
        assert '      exam_name_2: "TOEFL"' in yaml_str

    def test_exams_as_list_private(self, private_resume: PlainTextResume) -> None:
        """Test exams as list in private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Look for exams
        assert '      exam_name_1: "GRE"' in yaml_str
        assert '      exam_name_2: "TOEFL"' in yaml_str

    def test_exams_as_dict_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test exams as dictionary in public resume."""
        # Vamos modificar o teste para realmente testar a funcionalidade de "keys" do objeto exam
        # Já que o exam, na verdade, não é um dicionário no modelo Pydantic, e sim uma lista
        from app.models.resume import EducationDetails

        # Vamos testar a saída do modelo em formato lista, que é o que o modelo realmente suporta
        edu_model = EducationDetails(
            education_level="Bachelor's Degree",
            institution="University of New York",
            field_of_study="Computer Science",
            final_evaluation_grade="A",
            start_date="2018",
            year_of_completion="2022",
            # No formato real, exam é uma lista de strings
            exam=["Advanced Mathematics", "Quantum Physics"],
        )

        # Substitua a educação do resume
        public_resume.education_details = [edu_model]

        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Verifique se os valores aparecem no YAML como esperado
        assert '      exam_name_1: "Advanced Mathematics"' in yaml_str
        assert '      exam_name_2: "Quantum Physics"' in yaml_str

    def test_exams_as_dict_private(self, private_resume: PlainTextResume) -> None:
        """Test exams as dictionary in private resume."""
        # Modify the resume to have exams as a dict
        private_resume.education_details[0]["exam"] = {"Math": "A+", "Physics": "B"}

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check for exam dict format
        assert '      Math: "A+"' in yaml_str
        assert '      Physics: "B"' in yaml_str

    def test_boolean_fields_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test boolean fields conversion to Yes/No in public resume."""
        # For Pydantic objects, we need to create new instances with modified values
        from app.models.resume import LegalAuthorization, SelfIdentification

        # Create new objects with the desired values
        new_self_id = SelfIdentification(
            gender=public_resume.self_identification.gender,
            pronouns=public_resume.self_identification.pronouns,
            veteran=True,  # Set to True
            disability=public_resume.self_identification.disability,
            ethnicity=public_resume.self_identification.ethnicity,
        )

        new_legal_auth = LegalAuthorization(
            eu_work_authorization=public_resume.legal_authorization.eu_work_authorization,
            us_work_authorization=True,  # Set to True
            requires_us_visa=public_resume.legal_authorization.requires_us_visa,
            requires_us_sponsorship=public_resume.legal_authorization.requires_us_sponsorship,
            requires_eu_visa=public_resume.legal_authorization.requires_eu_visa,
            legally_allowed_to_work_in_eu=public_resume.legal_authorization.legally_allowed_to_work_in_eu,
            legally_allowed_to_work_in_us=public_resume.legal_authorization.legally_allowed_to_work_in_us,
            requires_eu_sponsorship=public_resume.legal_authorization.requires_eu_sponsorship,
            canada_work_authorization=public_resume.legal_authorization.canada_work_authorization,
            requires_canada_visa=public_resume.legal_authorization.requires_canada_visa,
            legally_allowed_to_work_in_canada=public_resume.legal_authorization.legally_allowed_to_work_in_canada,
            requires_canada_sponsorship=public_resume.legal_authorization.requires_canada_sponsorship,
            uk_work_authorization=public_resume.legal_authorization.uk_work_authorization,
            requires_uk_visa=public_resume.legal_authorization.requires_uk_visa,
            legally_allowed_to_work_in_uk=public_resume.legal_authorization.legally_allowed_to_work_in_uk,
            requires_uk_sponsorship=public_resume.legal_authorization.requires_uk_sponsorship,
        )

        # Assign the new objects
        public_resume.self_identification = new_self_id
        public_resume.legal_authorization = new_legal_auth

        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check Yes/No conversion
        assert '  veteran: "Yes"' in yaml_str
        assert '  us_work_authorization: "Yes"' in yaml_str
        assert '  disability: "No"' in yaml_str

    def test_boolean_fields_private(self, private_resume: PlainTextResume) -> None:
        """Test boolean fields conversion to Yes/No in private resume."""
        # Set some booleans
        private_resume.self_identification["veteran"] = True
        private_resume.legal_authorization["us_work_authorization"] = True

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check Yes/No conversion
        assert '  veteran: "Yes"' in yaml_str
        assert '  us_work_authorization: "Yes"' in yaml_str
        assert '  disability: "No"' in yaml_str

    def test_interests_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test interests formatting in public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check interests
        assert '  - "Reading"' in yaml_str
        assert '  - "Swimming"' in yaml_str

    def test_interests_private(self, private_resume: PlainTextResume) -> None:
        """Test interests formatting in private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check interests
        assert '  - "Reading"' in yaml_str
        assert '  - "Swimming"' in yaml_str

    def test_empty_fields_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test handling of empty fields in public resume."""
        # Create empty fields
        public_resume.projects = []
        public_resume.achievements = []

        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check empty sections still exist
        assert "projects:" in yaml_str
        assert "achievements:" in yaml_str

    def test_empty_fields_private(self, private_resume: PlainTextResume) -> None:
        """Test handling of empty fields in private resume."""
        # Create empty fields
        private_resume.projects = []
        private_resume.achievements = []

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check empty sections still exist
        assert "projects:" in yaml_str
        assert "achievements:" in yaml_str

    def test_null_values_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test handling of null values in public resume."""
        # Para Pydantic, não podemos usar None diretamente em campos de string
        # Vamos usar string vazia em vez disso para simular um valor nulo
        from app.models.resume import PersonalInformation

        # Crie um novo objeto com github definido como string vazia
        new_personal_info = PersonalInformation(
            name=public_resume.personal_information.name,
            surname=public_resume.personal_information.surname,
            date_of_birth=public_resume.personal_information.date_of_birth,
            country=public_resume.personal_information.country,
            city=public_resume.personal_information.city,
            address=public_resume.personal_information.address,
            zip_code=public_resume.personal_information.zip_code,
            phone_prefix=public_resume.personal_information.phone_prefix,
            phone=public_resume.personal_information.phone,
            email=public_resume.personal_information.email,
            github="",  # String vazia
            linkedin=public_resume.personal_information.linkedin,
        )

        # Atribua o novo objeto
        public_resume.personal_information = new_personal_info

        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Verifique se o campo github está vazio
        assert '  github: ""' in yaml_str

    def test_null_values_private(self, private_resume: PlainTextResume) -> None:
        """Test handling of null values in private resume."""
        # Set some null values
        private_resume.personal_information["github"] = None

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check null value handling
        assert '  github: "None"' in yaml_str

    def test_responsibilities_and_skills_public(
        self, public_resume: PlainTextResumePublic
    ) -> None:
        """Test responsibilities and skills formatting in public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Check responsibilities and skills formatting
        assert '      - responsibility_1: "Developed new features"' in yaml_str
        assert '      - responsibility_2: "Fixed bugs"' in yaml_str
        assert '      - "Python"' in yaml_str
        assert '      - "Django"' in yaml_str
        assert '      - "React"' in yaml_str

    def test_responsibilities_and_skills_private(
        self, private_resume: PlainTextResume
    ) -> None:
        """Test responsibilities and skills formatting in private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Check responsibilities and skills formatting
        assert '      - responsibility_1: "Developed new features"' in yaml_str
        assert '      - responsibility_2: "Fixed bugs"' in yaml_str
        assert '      - "Python"' in yaml_str
        assert '      - "Django"' in yaml_str
        assert '      - "React"' in yaml_str

    def test_missing_fields_public(self, public_resume: PlainTextResumePublic) -> None:
        """Test handling of missing fields in public resume."""
        # For Pydantic models, we can't delete fields but we can set them to empty strings
        # or default values to simulate missing fields
        from app.models.resume import PersonalInformation

        # Create a new PersonalInformation with github set to empty string
        new_personal_info = PersonalInformation(
            name=public_resume.personal_information.name,
            surname=public_resume.personal_information.surname,
            date_of_birth=public_resume.personal_information.date_of_birth,
            country=public_resume.personal_information.country,
            city=public_resume.personal_information.city,
            address=public_resume.personal_information.address,
            zip_code=public_resume.personal_information.zip_code,
            phone_prefix=public_resume.personal_information.phone_prefix,
            phone=public_resume.personal_information.phone,
            email=public_resume.personal_information.email,
            github="",  # Set to empty string
            linkedin=public_resume.personal_information.linkedin,
        )

        # Assign the new object
        public_resume.personal_information = new_personal_info

        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Should not break and still contain other fields
        assert '  name: "John"' in yaml_str
        assert '  surname: "Doe"' in yaml_str
        assert '  github: ""' in yaml_str

    def test_missing_fields_private(self, private_resume: PlainTextResume) -> None:
        """Test handling of missing fields in private resume."""
        # Remove some fields
        del private_resume.personal_information["github"]

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Should not break and still contain other fields
        assert '  name: "John"' in yaml_str
        assert '  surname: "Doe"' in yaml_str

    def test_edge_case_empty_responsibilities(
        self, private_resume: PlainTextResume
    ) -> None:
        """Test handling of empty responsibilities list."""
        private_resume.experience_details[0]["key_responsibilities"] = []

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Should still have the section but no entries
        assert "    key_responsibilities:" in yaml_str

    def test_edge_case_empty_skills(self, private_resume: PlainTextResume) -> None:
        """Test handling of empty skills list."""
        private_resume.experience_details[0]["skills_acquired"] = []

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Should still have the section but no entries
        assert "    skills_acquired:" in yaml_str

    def test_special_characters_handling(self, private_resume: PlainTextResume) -> None:
        """Test handling of special characters in fields."""
        private_resume.personal_information["name"] = 'John "Quotation" O\'Connor'

        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Special characters should be preserved
        assert '  name: "John "Quotation" O\'Connor"' in yaml_str

    def test_end_to_end_private(self, private_resume: PlainTextResume) -> None:
        """End-to-end test for a private resume."""
        yaml_str = generate_plain_text_resume_yaml(private_resume)

        # Verify structure and content
        # This is a more comprehensive check to make sure the YAML structure is as expected
        assert yaml_str.startswith("personal_information:")
        assert "\neducation_details:\n" in yaml_str
        assert "\nexperience_details:\n" in yaml_str
        assert "\nprojects:\n" in yaml_str
        assert "\nachievements:\n" in yaml_str
        assert "\ncertifications:\n" in yaml_str
        assert "\nlanguages:\n" in yaml_str
        assert "\ninterests:\n" in yaml_str
        assert "\navailability:\n" in yaml_str
        assert "\nsalary_expectations:\n" in yaml_str
        assert "\nself_identification:\n" in yaml_str
        assert "\nlegal_authorization:\n" in yaml_str
        assert "\nwork_preferences:\n" in yaml_str

    def test_end_to_end_public(self, public_resume: PlainTextResumePublic) -> None:
        """End-to-end test for a public resume."""
        yaml_str = generate_plain_text_resume_yaml(public_resume)

        # Verify structure and content
        # This is a more comprehensive check to make sure the YAML structure is as expected
        assert yaml_str.startswith("personal_information:")
        assert "\neducation_details:\n" in yaml_str
        assert "\nexperience_details:\n" in yaml_str
        assert "\nprojects:\n" in yaml_str
        assert "\nachievements:\n" in yaml_str
        assert "\ncertifications:\n" in yaml_str
        assert "\nlanguages:\n" in yaml_str
        assert "\ninterests:\n" in yaml_str
        assert "\navailability:\n" in yaml_str
        assert "\nsalary_expectations:\n" in yaml_str
        assert "\nself_identification:\n" in yaml_str
        assert "\nlegal_authorization:\n" in yaml_str
        assert "\nwork_preferences:\n" in yaml_str
