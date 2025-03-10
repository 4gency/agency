from typing import Any, ClassVar, Union
from uuid import UUID

from pydantic import BaseModel, model_validator
from sqlalchemy import JSON, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Field, Relationship, SQLModel

from app.models.core import User


class ExperienceLevel(BaseModel):
    intership: bool = True
    entry: bool = True
    associate: bool = True
    mid_senior_level: bool = True
    director: bool = True
    executive: bool = True


class JobTypes(BaseModel):
    full_time: bool = True
    contract: bool = True
    part_time: bool = True
    temporary: bool = True
    internship: bool = True
    other: bool = True
    volunteer: bool = True


class Date(BaseModel):
    all_time: bool = True
    month: bool = False
    week: bool = False
    hours: bool = False  # 24_hours

    @model_validator(mode="after")
    def validate_only_one_can_be_true(self) -> "Date":
        # Ensuring only one time period is selected
        time_values = [self.all_time, self.month, self.week, self.hours]
        # If none are selected, set all_time to True
        if not any(time_values):
            self.all_time = True
        # If more than one is selected, prioritize all_time, then month, then week, then hours
        elif sum(time_values) > 1:
            # Reset all to False first
            self.all_time = False
            self.month = False
            self.week = False
            self.hours = False
            temp = self.model_dump()
            # Then set the one with highest priority to True
            if temp["all_time"]:
                self.all_time = True
            elif temp["month"]:
                self.month = True
            elif temp["week"]:
                self.week = True
            elif temp["hours"]:
                self.hours = True
        return self


class ConfigPublic(BaseModel):
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
    distance: int = 100

    company_blacklist: list[str] = [
        "Wayfair",
    ]
    title_blacklist: list[str] = [
        "DBA",
    ]
    location_blacklist: list[str] = [
        "Brazil",
    ]

    class Config:
        extra = "ignore"


class Config(SQLModel, table=True):
    __tablename__: ClassVar[str] = "job_preferences"

    id: int | None = Field(default=None, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    user: User = Relationship(back_populates="config")

    llm_model_type: str = "openai"
    llm_model: str = "gpt-4o-mini"
    # llm_api_url: str = 'https://api.pawan.krd/cosmosrp/v1'

    remote: bool = True

    experience_level: dict[str, Any] = Field(
        default_factory=lambda: ExperienceLevel().model_dump(),
        sa_column=Column(JSON),
    )
    job_types: dict[str, Any] = Field(
        default_factory=lambda: JobTypes().model_dump(),
        sa_column=Column(JSON),
    )
    date: dict[str, Any] = Field(
        default_factory=lambda: Date(all_time=True).model_dump(),
        sa_column=Column(JSON),
    )
    positions: list[str] = Field(
        default_factory=lambda: ["Developer"], sa_column=Column(JSON)
    )
    locations: list[str] = Field(
        default_factory=lambda: ["USA"], sa_column=Column(JSON)
    )

    apply_once_at_company: bool = True
    distance: int = 100

    company_blacklist: list[str] = Field(
        default_factory=lambda: ["Wayfair"], sa_column=Column(JSON)
    )
    title_blacklist: list[str] = Field(
        default_factory=lambda: ["DBA"], sa_column=Column(JSON)
    )
    location_blacklist: list[str] = Field(
        default_factory=lambda: ["Brazil"], sa_column=Column(JSON)
    )


def generate_config_yaml(config: Union["Config", "ConfigPublic"]) -> str:
    """
    Generate a YAML string from a Config or ConfigPublic object that matches
    the exact format required by the validation function.

    Args:
        config: The Config or ConfigPublic object containing job preferences

    Returns:
        The generated YAML as a string
    """
    # Check if we're dealing with ConfigPublic or Config
    is_config_public = not hasattr(config, "user_id")

    # Helper function to safely access fields from either object type
    def safe_get_dict_value(
        obj: dict[str, Any] | Any, field: str, default: Any = None
    ) -> Any:
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)

    # Helper function to safely access boolean attributes
    def safe_get_bool(
        obj: dict[str, Any] | Any, field: str, default: bool = False
    ) -> bool:
        value = safe_get_dict_value(obj, field, default)
        return bool(value)

    # Helper function to get experience level values
    def get_exp_level(field: str) -> bool:
        if is_config_public:
            # ConfigPublic has direct attributes
            exp_level = config.experience_level
            # Handle the typo in the model (intership vs internship)
            if field == "internship":
                return bool(getattr(exp_level, "intership", False))
            return bool(getattr(exp_level, field.replace("-", "_"), False))
        else:
            # Config has a dict
            if field == "internship":
                return bool(
                    safe_get_dict_value(config.experience_level, "intership", False)
                )
            return bool(
                safe_get_dict_value(
                    config.experience_level, field.replace("-", "_"), False
                )
            )

    # Helper function to get job type values
    def get_job_type(field: str) -> bool:
        if is_config_public:
            job_types = config.job_types
            return bool(getattr(job_types, field.replace("-", "_"), False))
        else:
            return bool(
                safe_get_dict_value(config.job_types, field.replace("-", "_"), False)
            )

    # Helper function to get date values
    def get_date(field: str) -> bool:
        if is_config_public:
            date = config.date
            if field == "all time":
                return bool(getattr(date, "all_time", False))
            elif field == "24 hours":
                return bool(getattr(date, "hours", False))
            return bool(getattr(date, field, False))
        else:
            if field == "all time":
                return bool(safe_get_dict_value(config.date, "all_time", False))
            elif field == "24 hours":
                return bool(safe_get_dict_value(config.date, "hours", False))
            return bool(safe_get_dict_value(config.date, field, False))

    # Construct the YAML string manually to ensure exact format
    yaml_str = f"remote: {safe_get_bool(config, 'remote')}\n\n"

    # Experience Level
    yaml_str += "experienceLevel:\n"
    for field in [
        "internship",
        "entry",
        "associate",
        "mid-senior level",
        "director",
        "executive",
    ]:
        yaml_str += f"  {field}: {safe_get_bool(config, field)}\n"
    yaml_str += "\n"

    # Job Types
    yaml_str += "jobTypes:\n"
    for field in [
        "full-time",
        "contract",
        "part-time",
        "temporary",
        "internship",
        "other",
        "volunteer",
    ]:
        yaml_str += f"  {field}: {safe_get_bool(config, field)}\n"
    yaml_str += "\n"

    # Date
    yaml_str += "date:\n"
    for field in ["all time", "month", "week", "24 hours"]:
        yaml_str += f"  {field}: {safe_get_bool(config, field)}\n"
    yaml_str += "\n"

    # Positions
    yaml_str += "positions:\n"
    for position in config.positions:
        yaml_str += f"  - {position}\n"
    yaml_str += "\n"

    # Locations
    yaml_str += "locations:\n"
    for location in config.locations:
        yaml_str += f"  - {location}\n"
    yaml_str += "\n"

    # Apply once at company
    yaml_str += (
        f"apply_once_at_company: {safe_get_bool(config, 'apply_once_at_company')}\n\n"
    )

    # Distance
    yaml_str += f"distance: {safe_get_dict_value(config, 'distance', 100)}\n\n"

    # Company blacklist
    yaml_str += "company_blacklist:\n"
    if safe_get_dict_value(config, "company_blacklist", []):
        for company in safe_get_dict_value(config, "company_blacklist", []):
            yaml_str += f"  - {company}\n"
    yaml_str += "\n"

    # Title blacklist
    yaml_str += "title_blacklist:\n"
    if safe_get_dict_value(config, "title_blacklist", []):
        for title in safe_get_dict_value(config, "title_blacklist", []):
            yaml_str += f"  - {title}\n"
    yaml_str += "\n"

    # Location blacklist
    yaml_str += "location_blacklist:\n"
    if safe_get_dict_value(config, "location_blacklist", []):
        for loc in safe_get_dict_value(config, "location_blacklist", []):
            yaml_str += f"  - {loc}\n"
    yaml_str += "\n"

    # Add job_applicants_threshold if in the config or example
    if hasattr(config, "job_applicants_threshold"):
        yaml_str += "job_applicants_threshold:\n"
        threshold = getattr(
            config,
            "job_applicants_threshold",
            {"min_applicants": 0, "max_applicants": 10000},
        )
        yaml_str += f"  min_applicants: {threshold.get('min_applicants', 0)}\n"
        yaml_str += f"  max_applicants: {threshold.get('max_applicants', 10000)}\n\n"

    # LLM model type and model
    yaml_str += f"llm_model_type: {getattr(config, 'llm_model_type', 'openai')}\n"
    yaml_str += f"llm_model: '{getattr(config, 'llm_model', 'gpt-4o-mini')}'\n"

    # Add commented llm_api_url if it exists in the config
    llm_api_url = getattr(config, "llm_api_url", None)
    if hasattr(config, "llm_api_url") and llm_api_url:
        yaml_str += f"# llm_api_url: '{llm_api_url}'\n"

    return yaml_str
