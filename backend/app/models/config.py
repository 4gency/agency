from pydantic import BaseModel


class ExperienceLevel(BaseModel):
    intership: bool
    entry: bool
    associate: bool
    mid_senior_level: bool
    director: bool
    executive: bool
    
class JobTypes(BaseModel):
    full_time: bool
    contract: bool
    part_time: bool
    temporary: bool
    internship: bool
    other: bool
    volunteer: bool

class Date(BaseModel):
    # only one can be true
    all_time: bool
    month: bool
    week: bool
    hours: bool
    
class Positions(BaseModel):
    positions: list[str]
    
class Locations(BaseModel):
    locations: list[str]
    
class CompanyBlacklist(BaseModel):
    company_blacklist: list[str] = ["Crossover", "wayfair"]
    
class TitleBlacklist(BaseModel):
    title_blacklist: list[str] = []
    
class JobApplicantsThreshold(BaseModel):
    min_applicants: int = 0
    max_applicants: int = 100

class Config(BaseModel, extra='ignore'):
    remote: bool = True
    
    experience_level: ExperienceLevel
    job_types: JobTypes
    date: Date
    positions: Positions
    locations: Locations
    
    apply_once_at_company: bool = True
    distance: int = 100
    
    company_blacklist: CompanyBlacklist
    title_blacklist: TitleBlacklist
    
    job_applicants_threshold: JobApplicantsThreshold
    
    llm_model_type: str = 'openai'
    llm_model: str = 'gpt-4o-mini'
    # llm_api_url: str = 'https://api.pawan.krd/cosmosrp/v1'
