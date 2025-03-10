export interface PersonalInformation {
  name: string
  surname: string
  date_of_birth: string
  email: string
  country: string
  city: string
  address: string
  zip_code: string
  phone_prefix: string
  phone: string
  linkedin: string
  github: string
}

export interface Education {
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date: string
  current?: boolean
  final_evaluation_grade: string
  exam: string[]
}

export interface WorkExperience {
  company: string
  position: string
  start_date: string
  end_date: string
  current?: boolean
  description: string
  location: string
  industry: string
  skills_acquired: string[]
}

export interface Project {
  name: string
  description: string
  url: string
}

export interface Language {
  name: string
  level: string
}

export interface SalaryExpectation {
  minimum?: number
  maximum?: number
}

export interface Achievement {
  name: string
  description: string
}

export interface Certification {
  name: string
  description: string
}

export interface SelfIdentification {
  gender: string
  pronouns: string
  veteran: boolean
  disability: boolean
  ethnicity: string
}

export interface LegalAuthorization {
  eu_work_authorization: boolean
  us_work_authorization: boolean
  requires_us_visa: boolean
  requires_us_sponsorship: boolean
  requires_eu_visa: boolean
  legally_allowed_to_work_in_eu: boolean
  legally_allowed_to_work_in_us: boolean
  requires_eu_sponsorship: boolean
  canada_work_authorization: boolean
  requires_canada_visa: boolean
  legally_allowed_to_work_in_canada: boolean
  requires_canada_sponsorship: boolean
  uk_work_authorization: boolean
  requires_uk_visa: boolean
  legally_allowed_to_work_in_uk: boolean
  requires_uk_sponsorship: boolean
}

export interface WorkPreference {
  remote: boolean
  hybrid?: boolean
  on_site: boolean
  relocation: boolean
  willing_to_complete_assessments: boolean
  willing_to_undergo_drug_tests: boolean
  willing_to_undergo_background_checks: boolean
}

export interface ResumeForm {
  personal_information: PersonalInformation
  education: Education[]
  work_experience: WorkExperience[]
  projects: Project[]
  skills: string[]
  languages: Language[]
  achievements: Achievement[]
  certifications: Certification[]
  availability: string
  salary_expectation: SalaryExpectation
  work_preference: WorkPreference
  interests: string[]
  self_identification: SelfIdentification
  legal_authorization: LegalAuthorization
}
