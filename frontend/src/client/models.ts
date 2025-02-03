export type Achievement = {
  name?: string
  description?: string
}

export type Availability = {
  notice_period?: string
}

export type Body_login_login_access_token = {
  grant_type?: string | null
  username: string
  password: string
  scope?: string
  client_id?: string | null
  client_secret?: string | null
}

export type Certification = {
  name?: string
  description?: string
}

export type CheckoutSession = {
  id?: string
  payment_gateway?: string
  session_id: string
  session_url: string
  user_id: string
  status?: string
  payment_status?: string
  created_at?: string
  expires_at: string
  updated_at?: string
}

export type CheckoutSessionPublic = {
  session_id: string
  session_url: string
  expires_at: string
}

export type ConfigPublic = {
  remote?: boolean
  experience_level?: ExperienceLevel
  job_types?: JobTypes
  date?: Date
  positions?: Array<string>
  locations?: Array<string>
  apply_once_at_company?: boolean
  distance?: number
  company_blacklist?: Array<string>
  title_blacklist?: Array<string>
  job_applicants_threshold?: JobApplicantsThreshold
}

export type Date = {
  all_time?: boolean
  month?: boolean
  week?: boolean
  hours?: boolean
}

export type EducationDetails = {
  education_level?: string
  institution?: string
  field_of_study?: string
  final_evaluation_grade?: string
  start_date?: string
  year_of_completion?: string
  exam?: Array<string>
}

export type ExperienceDetail = {
  position?: string
  company?: string
  employment_period?: string
  location?: string
  industry?: string
  key_responsibilities?: Array<string>
  skills_acquired?: Array<string>
}

export type ExperienceLevel = {
  intership?: boolean
  entry?: boolean
  associate?: boolean
  mid_senior_level?: boolean
  director?: boolean
  executive?: boolean
}

export type HTTPValidationError = {
  detail?: Array<ValidationError>
}

export type JobApplicantsThreshold = {
  min_applicants?: number
  max_applicants?: number
}

export type JobTypes = {
  full_time?: boolean
  contract?: boolean
  part_time?: boolean
  temporary?: boolean
  internship?: boolean
  other?: boolean
  volunteer?: boolean
}

export type Language = {
  language?: string
  proficiency?: string
}

export type LegalAuthorization = {
  eu_work_authorization?: boolean
  us_work_authorization?: boolean
  requires_us_visa?: boolean
  requires_us_sponsorship?: boolean
  requires_eu_visa?: boolean
  legally_allowed_to_work_in_eu?: boolean
  legally_allowed_to_work_in_us?: boolean
  requires_eu_sponsorship?: boolean
  canada_work_authorization?: boolean
  requires_canada_visa?: boolean
  legally_allowed_to_work_in_canada?: boolean
  requires_canada_sponsorship?: boolean
  uk_work_authorization?: boolean
  requires_uk_visa?: boolean
  legally_allowed_to_work_in_uk?: boolean
  requires_uk_sponsorship?: boolean
}

export type Message = {
  message: string
}

export type NewPassword = {
  token: string
  new_password: string
}

export type PersonalInformation = {
  name?: string
  surname?: string
  date_of_birth?: string
  country?: string
  city?: string
  address?: string
  phone_prefix?: string
  phone?: string
  email?: string
  github?: string
  linkedin?: string
}

export type PlainTextResumePublic = {
  personal_information?: PersonalInformation
  education_details?: Array<EducationDetails>
  experience_details?: Array<ExperienceDetail>
  projects?: Array<Project>
  achievements?: Array<Achievement>
  certifications?: Array<Certification>
  languages?: Array<Language>
  interests?: Array<string>
  availability?: Availability
  salary_expectations?: SalaryExpectations
  self_identification?: SelfIdentification
  legal_authorization?: LegalAuthorization
  work_preferences?: WorkPreferences
}

export type Project = {
  name?: string
  description?: string
  link?: string
}

export type SalaryExpectations = {
  salary_range_usd?: string
}

export type SelfIdentification = {
  gender?: string
  pronouns?: string
  veteran?: boolean
  disability?: boolean
  ethnicity?: string
}

export type SubscriptionMetric = "day" | "week" | "month" | "year" | "applies"

export type SubscriptionPlanBenefitPublic = {
  name: string
}

export type SubscriptionPlanCreate = {
  name: string
  price: number
  is_best_choice?: boolean
  has_discount?: boolean
  price_without_discount?: number
  currency?: string
  description?: string
  is_active?: boolean
  metric_type?: SubscriptionMetric
  metric_value?: number
  benefits?: Array<SubscriptionPlanBenefitPublic>
}

export type SubscriptionPlanPublic = {
  id: string
  name: string
  price: number
  is_best_choice: boolean
  has_discount: boolean
  price_without_discount: number
  currency: string
  description: string
  is_active: boolean
  metric_type: SubscriptionMetric
  metric_value: number
  benefits?: Array<SubscriptionPlanBenefitPublic>
}

export type SubscriptionPlanUpdate = {
  name?: string | null
  price?: number | null
  is_best_choice?: boolean | null
  has_discount?: boolean | null
  price_without_discount?: number | null
  currency?: string | null
  description?: string | null
  is_active?: boolean | null
  metric_type?: SubscriptionMetric | null
  metric_value?: number | null
  benefits?: Array<SubscriptionPlanBenefitPublic> | null
}

export type SubscriptionPlansPublic = {
  plans?: Array<SubscriptionPlanPublic>
}

export type SubscriptionPublic = {
  id: string
  user_id: string
  subscription_plan_id: string
  start_date: string
  end_date: string
  is_active: boolean
  metric_type: SubscriptionMetric
  metric_status: number
}

export type Token = {
  access_token: string
  token_type?: string
}

export type UpdatePassword = {
  current_password: string
  new_password: string
}

export type UserCreate = {
  email: string
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
  password: string
}

export type UserPublic = {
  email: string
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
  id: string
}

export type UserRegister = {
  email: string
  password: string
  full_name?: string | null
}

export type UserUpdate = {
  email?: string | null
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
  password?: string | null
}

export type UserUpdateMe = {
  full_name?: string | null
  email?: string | null
}

export type UsersPublic = {
  data: Array<UserPublic>
  count: number
}

export type ValidationError = {
  loc: Array<string | number>
  msg: string
  type: string
}

export type WorkPreferences = {
  remote_work?: boolean
  in_person_work?: boolean
  open_to_relocation?: boolean
  willing_to_complete_assessments?: boolean
  willing_to_undergo_drug_tests?: boolean
  willing_to_undergo_background_checks?: boolean
}
