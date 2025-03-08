from typing import List, Optional, ClassVar, Dict, Any
import json
from uuid import UUID

from pydantic import BaseModel, model_validator
from sqlalchemy import ForeignKey
from sqlmodel import Field, SQLModel, JSON, Column

from sqlalchemy.dialects.postgresql import UUID as PGUUID


class ExperienceLevel(BaseModel):
    intership: bool = True
    entry: bool = True
    associate: bool = True
    mid_senior_level: bool = True
    director: bool = True
    executive: bool = True

    def dict(self) -> Dict[str, Any]:
        return self.model_dump()


class JobTypes(BaseModel):
    full_time: bool = True
    contract: bool = True
    part_time: bool = True
    temporary: bool = True
    internship: bool = True
    other: bool = True
    volunteer: bool = True

    def dict(self) -> Dict[str, Any]:
        return self.model_dump()


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

    def dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ConfigPublic(BaseModel):
    remote: bool = True
    hybrid: bool = True
    onsite: bool = True

    experience_level: ExperienceLevel = ExperienceLevel()
    job_types: JobTypes = JobTypes()
    date: Date = Date(all_time=True)
    positions: List[str] = [
        "Developer",
    ]
    locations: List[str] = [
        "USA",
    ]

    apply_once_at_company: bool = True
    distance: int = 100

    company_blacklist: List[str] = [
        "Wayfair",
    ]
    title_blacklist: List[str] = [
        "DBA",
    ]
    location_blacklist: List[str] = [
        "Brazil",
    ]

    class Config:
        extra = "ignore"


class Config(SQLModel, table=True):
    __tablename__: ClassVar[str] = "job_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
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

    experience_level: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(ExperienceLevel().model_dump_json()), 
        sa_column=Column(JSON)
    )
    job_types: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(JobTypes().model_dump_json()), 
        sa_column=Column(JSON)
    )
    date: Dict[str, Any] = Field(
        default_factory=lambda: json.loads(Date(all_time=True).model_dump_json()), 
        sa_column=Column(JSON)
    )
    positions: List[str] = Field(
        default_factory=lambda: ["Developer"], 
        sa_column=Column(JSON)
    )
    locations: List[str] = Field(
        default_factory=lambda: ["USA"], 
        sa_column=Column(JSON)
    )

    apply_once_at_company: bool = True
    distance: int = 100

    company_blacklist: List[str] = Field(
        default_factory=lambda: ["Wayfair"], 
        sa_column=Column(JSON)
    )
    title_blacklist: List[str] = Field(
        default_factory=lambda: ["DBA"], 
        sa_column=Column(JSON)
    )
    location_blacklist: List[str] = Field(
        default_factory=lambda: ["Brazil"], 
        sa_column=Column(JSON)
    )
