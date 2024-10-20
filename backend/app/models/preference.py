from odmantic import Field, Model


class ExperienceLevel(Model):
    intership: bool
    entry: bool
    associate: bool
    mid_senior_level: bool
    director: bool
    executive: bool
    
class JobTypes(Model):
    full_time: bool
    contract: bool
    part_time: bool
    temporary: bool
    internship: bool
    other: bool
    volunteer: bool

class Date(Model):
    # only one can be true
    all_time: bool
    month: bool
    week: bool
    hours: bool
    
class Positions(Model):
    positions: list[str]
    
class Locations(Model):
    locations: list[str]
    
class CompanyBlacklist(Model):
    company_blacklist: list[str]
    
class TitleBlacklist(Model):
    title_blacklist: list[str] = Field(default=[])
    
class JobApplicantsThreshold(Model):
    min_applicants: int = Field(default=0)
    max_applicants: int = Field(default=10000)

class ConfigPublic(Model, extra='ignore'):
    remote: bool = Field(default=True)
    
    experience_level: ExperienceLevel
    job_types: JobTypes
    date: Date
    positions: Positions
    locations: Locations
    
    apply_once_at_company: bool = Field(default=True)
    distance: int = Field(default=0)
    
    company_blacklist: CompanyBlacklist
    title_blacklist: TitleBlacklist
    
    job_applicants_threshold: JobApplicantsThreshold

class Config(ConfigPublic):
    user_id: str
    llm_model_type: str = Field(default='openai')
    llm_model: str = Field(default='gpt-4o-mini')
    # llm_api_url: str = 'https://api.pawan.krd/cosmosrp/v1'

    model_config = {
        "collection": "preferences",
    }