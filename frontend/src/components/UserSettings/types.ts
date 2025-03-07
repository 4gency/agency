export interface PersonalInformation {
  name: string
  surname: string
  date_of_birth?: string
  email: string
  country?: string
  city?: string
  address?: string
  zip_code?: string
  phone_prefix?: string
  phone?: string
  linkedin?: string
  github?: string
}

export interface Education {
  institution: string
  degree: string
  field_of_study?: string
  start_date: string
  end_date?: string
  current?: boolean
  description?: string
}

export interface WorkExperience {
  company: string
  position: string
  start_date: string
  end_date?: string
  current?: boolean
  description?: string
  location?: string
}

export interface Project {
  name: string
  description?: string
  url?: string
  start_date?: string
  end_date?: string
  current?: boolean
}

export interface Language {
  name: string
  level: string
}

export interface SalaryExpectation {
  minimum?: number
  maximum?: number
  currency?: string
}

export interface WorkPreference {
  remote?: boolean
  hybrid?: boolean
  on_site?: boolean
  relocation?: boolean
}

export interface ResumeForm {
  personal_information: PersonalInformation
  education: Education[]
  work_experience: WorkExperience[]
  projects: Project[]
  skills: string[]
  languages: Language[]
  availability?: string
  salary_expectation: SalaryExpectation
  work_preference: WorkPreference
  interests: string[]
}
