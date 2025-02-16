from odmantic import EmbeddedModel, Field, Model
from pydantic import BaseModel


class ExperienceLevel(EmbeddedModel):
    intership: bool = True
    entry: bool = True
    associate: bool = True
    mid_senior_level: bool = True
    director: bool = True
    executive: bool = True


class JobTypes(EmbeddedModel):
    full_time: bool = True
    contract: bool = True
    part_time: bool = True
    temporary: bool = True
    internship: bool = True
    other: bool = True
    volunteer: bool = True


class Date(EmbeddedModel):
    all_time: bool = True
    month: bool = False
    week: bool = False
    hours: bool = False

    # @model_validator(mode="after") # TODO: uncomment this
    # def validate_only_one_can_be_true(self) -> Self:
    #     if sum([self.all_time, self.month, self.week, self.hours]) > 1:
    #         raise ValueError("Only one date can be selected")
    #     return self


class JobApplicantsThreshold(EmbeddedModel):
    min_applicants: int = 0
    max_applicants: int = 10000


class ConfigPublic(BaseModel, extra="ignore"):
    remote: bool = True

    experience_level: ExperienceLevel = ExperienceLevel()
    job_types: JobTypes = JobTypes()
    date: Date = Date(all_time=True)
    positions: list[str] = [
        "Developer",
    ]
    locations: list[str] = [
        "USA",
    ]

    apply_once_at_company: bool = True
    distance: int = 0

    company_blacklist: list[str] = []
    title_blacklist: list[str] = []

    job_applicants_threshold: JobApplicantsThreshold = JobApplicantsThreshold()


class Config(Model):
    subscription_id: str = Field(index=True, unique=True)
    user_id: str

    llm_model_type: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o-mini")
    # llm_api_url: str = 'https://api.pawan.krd/cosmosrp/v1'

    remote: bool = True

    experience_level: ExperienceLevel = ExperienceLevel()
    job_types: JobTypes = JobTypes()
    date: Date = Date(all_time=True)
    positions: list[str] = [
        "Developer",
    ]
    locations: list[str] = [
        "USA",
    ]

    apply_once_at_company: bool = True
    distance: int = 0

    company_blacklist: list[str] = []
    title_blacklist: list[str] = []

    job_applicants_threshold: JobApplicantsThreshold = JobApplicantsThreshold()

    class Config:
        collection: str = "configs"
