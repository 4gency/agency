from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, model_validator
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import JSON, Column, Field, SQLModel


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
        values = [self.all_time, self.month, self.week, self.hours]
        if sum(values) != 1:
            # If none or more than one is selected, set all_time to True and others to False
            self.all_time = True
            self.month = self.week = self.hours = False
        return self


class ConfigPublic(BaseModel):
    remote: bool = True
    hybrid: bool = True
    onsite: bool = True

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

    llm_model_type: str = "openai"
    llm_model: str = "gpt-4o-mini"
    # llm_api_url: str = 'https://api.pawan.krd/cosmosrp/v1'

    remote: bool = True
    hybrid: bool = True
    onsite: bool = True

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
