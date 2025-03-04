// This file is auto-generated by @hey-api/openapi-ts

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

export type CheckoutSessionPublic = {
  id: string
  session_id: string
  session_url: string
  expires_at: string
}

export type CheckoutSessionUpdate = {
  payment_gateway?: string | null
  session_id?: string | null
  session_url?: string | null
  user_id?: string | null
  status?: string | null
  subscription_plan_id?: string | null
  payment_status?: string | null
  created_at?: string | null
  expires_at?: string | null
  updated_at?: string | null
}

export type ConfigPublic = {
  remote?: boolean
  hybrid?: boolean
  onsite?: boolean
  experience_level?: ExperienceLevel
  job_types?: JobTypes
  date?: Date
  positions?: Array<string>
  locations?: Array<string>
  apply_once_at_company?: boolean
  distance?: number
  company_blacklist?: Array<string>
  title_blacklist?: Array<string>
  location_blacklist?: Array<string>
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

export type ErrorMessage = {
  detail: string
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

export type PaymentPublic = {
  id: string
  subscription_id: string
  user_id: string
  amount: number
  currency: string
  payment_date: string
  payment_status: string
  payment_gateway: string
  transaction_id: string
}

export type PaymentRecurrenceStatus =
  | "active"
  | "canceled"
  | "pending_cancellation"

export type PaymentsPublic = {
  data: Array<PaymentPublic>
  count: number
}

export type PersonalInformation = {
  name?: string
  surname?: string
  date_of_birth?: string
  country?: string
  city?: string
  address?: string
  zip_code?: string
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

export type SubscriptionPlan = {
  id?: string
  name: string
  price: number
  has_badge?: boolean
  badge_text?: string
  button_text?: string
  button_enabled?: boolean
  has_discount?: boolean
  price_without_discount?: number
  currency?: string
  description?: string
  is_active?: boolean
  metric_type?: SubscriptionMetric
  metric_value?: number
  stripe_product_id?: string | null
  stripe_price_id?: string | null
}

export type SubscriptionPlanBenefitPublic = {
  name: string
}

export type SubscriptionPlanCreate = {
  name: string
  price: number
  has_badge?: boolean
  badge_text?: string
  button_text?: string
  button_enabled?: boolean
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
  has_badge: boolean
  badge_text: string
  button_text: string
  button_enabled: boolean
  has_discount: boolean
  price_without_discount: number
  currency: string
  description: string
  is_active: boolean
  metric_type: SubscriptionMetric
  metric_value: number
  benefits?: Array<SubscriptionPlanBenefitPublic>
}

export type SubscriptionPlansPublic = {
  plans?: Array<SubscriptionPlanPublic>
}

export type SubscriptionPlanUpdate = {
  name?: string | null
  price?: number | null
  has_badge?: boolean | null
  badge_text?: string | null
  button_text?: string | null
  button_enabled?: boolean | null
  has_discount?: boolean | null
  price_without_discount?: number | null
  currency?: string | null
  description?: string | null
  is_active?: boolean | null
  metric_type?: SubscriptionMetric | null
  metric_value?: number | null
  benefits?: Array<SubscriptionPlanBenefitPublic> | null
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
  payment_recurrence_status: PaymentRecurrenceStatus
  subscription_plan?: SubscriptionPlan | null
}

export type SubscriptionPublicExtended = {
  id: string
  user_id: string
  subscription_plan_id: string
  start_date: string
  end_date: string
  is_active: boolean
  metric_type: SubscriptionMetric
  metric_status: number
  payment_recurrence_status: PaymentRecurrenceStatus
  subscription_plan?: SubscriptionPlan | null
  payments?: Array<PaymentPublic>
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
  is_subscriber?: boolean
  full_name?: string | null
  password: string
}

export type UserPublic = {
  email: string
  is_active?: boolean
  is_superuser?: boolean
  is_subscriber?: boolean
  full_name?: string | null
  id: string
}

export type UserRegister = {
  email: string
  password: string
  full_name?: string | null
}

export type UsersPublic = {
  data: Array<UserPublic>
  count: number
}

export type UserUpdate = {
  email?: string | null
  is_active?: boolean
  is_superuser?: boolean
  is_subscriber?: boolean
  full_name?: string | null
  password?: string | null
}

export type UserUpdateMe = {
  full_name?: string | null
  email?: string | null
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

export type StripeSuccessData = {
  sessionId: string
}

export type StripeSuccessResponse = Message

export type GetStripeCheckoutSessionByIdData = {
  sessionId: string
}

export type GetStripeCheckoutSessionByIdResponse = CheckoutSessionPublic

export type UpdateStripeCheckoutSessionData = {
  requestBody: CheckoutSessionUpdate
  sessionId: string
}

export type UpdateStripeCheckoutSessionResponse = CheckoutSessionPublic

export type GetStripeCheckoutSessionsData = {
  limit?: number
  skip?: number
}

export type GetStripeCheckoutSessionsResponse = Array<CheckoutSessionPublic>

export type CreateStripeCheckoutSessionData = {
  subscriptionPlanId: string
}

export type CreateStripeCheckoutSessionResponse = CheckoutSessionPublic

export type StripeWebhookData = {
  stripeSignature?: string
}

export type StripeWebhookResponse = Message

export type StripeCancelData = {
  sessionId: string
}

export type StripeCancelResponse = Message

export type GetConfigData = {
  subscriptionId: string
}

export type GetConfigResponse = ConfigPublic

export type UpdateConfigData = {
  requestBody: ConfigPublic
  subscriptionId: string
}

export type UpdateConfigResponse = unknown

export type GetPlainTextResumeData = {
  subscriptionId: string
}

export type GetPlainTextResumeResponse = PlainTextResumePublic

export type UpdatePlainTextResumeData = {
  requestBody: PlainTextResumePublic
  subscriptionId: string
}

export type UpdatePlainTextResumeResponse = unknown

export type LoginAccessTokenData = {
  formData: Body_login_login_access_token
}

export type LoginAccessTokenResponse = Token

export type TestTokenResponse = UserPublic

export type RecoverPasswordData = {
  email: string
}

export type RecoverPasswordResponse = Message

export type ResetPasswordData = {
  requestBody: NewPassword
}

export type ResetPasswordResponse = Message

export type RecoverPasswordHtmlContentData = {
  email: string
}

export type RecoverPasswordHtmlContentResponse = string

export type ReadPaymentsByCurrentUserData = {
  limit?: number
  skip?: number
}

export type ReadPaymentsByCurrentUserResponse = PaymentsPublic

export type ReadPaymentsByUserIdData = {
  limit?: number
  skip?: number
  userId: string
}

export type ReadPaymentsByUserIdResponse = PaymentsPublic

export type ReadPaymentsData = {
  limit?: number
  skip?: number
}

export type ReadPaymentsResponse = PaymentsPublic

export type ReadSubscriptionPlansData = {
  onlyActive?: boolean
}

export type ReadSubscriptionPlansResponse = SubscriptionPlansPublic

export type CreateSubscriptionPlanData = {
  requestBody: SubscriptionPlanCreate
}

export type CreateSubscriptionPlanResponse = SubscriptionPlanPublic

export type ReadSubscriptionPlanData = {
  id: string
}

export type ReadSubscriptionPlanResponse = SubscriptionPlanPublic

export type UpdateSubscriptionPlanData = {
  id: string
  requestBody: SubscriptionPlanUpdate
}

export type UpdateSubscriptionPlanResponse = Message

export type DeleteSubscriptionPlanData = {
  id: string
}

export type DeleteSubscriptionPlanResponse = Message

export type GetUserSubscriptionsData = {
  onlyActive?: boolean | null
}

export type GetUserSubscriptionsResponse = Array<SubscriptionPublic>

export type GetUserSubscriptionData = {
  subscriptionId: string
}

export type GetUserSubscriptionResponse = SubscriptionPublicExtended

export type GetUserSubscriptionsByIdData = {
  onlyActive?: boolean | null
  userId: string
}

export type GetUserSubscriptionsByIdResponse = Array<SubscriptionPublic>

export type CancelUserSubscriptionData = {
  subscriptionId: string
}

export type CancelUserSubscriptionResponse = Message

export type ReactivateUserSubscriptionData = {
  subscriptionId: string
}

export type ReactivateUserSubscriptionResponse = Message

export type CancelUserSubscriptionByIdData = {
  subscriptionId: string
  userId: string
}

export type CancelUserSubscriptionByIdResponse = Message

export type ReactivateUserSubscriptionByIdData = {
  subscriptionId: string
  userId: string
}

export type ReactivateUserSubscriptionByIdResponse = Message

export type ReadUsersData = {
  limit?: number
  skip?: number
}

export type ReadUsersResponse = UsersPublic

export type CreateUserData = {
  requestBody: UserCreate
}

export type CreateUserResponse = UserPublic

export type ReadUserMeResponse = UserPublic

export type UpdateUserMeData = {
  requestBody: UserUpdateMe
}

export type UpdateUserMeResponse = UserPublic

export type UpdatePasswordMeData = {
  requestBody: UpdatePassword
}

export type UpdatePasswordMeResponse = Message

export type RegisterUserData = {
  requestBody: UserRegister
}

export type RegisterUserResponse = UserPublic

export type ReadUserByIdData = {
  userId: string
}

export type ReadUserByIdResponse = UserPublic

export type UpdateUserData = {
  requestBody: UserUpdate
  userId: string
}

export type UpdateUserResponse = UserPublic

export type DeleteUserData = {
  userId: string
}

export type DeleteUserResponse = Message

export type TestEmailData = {
  emailTo: string
}

export type TestEmailResponse = Message

export type HealthCheckResponse = boolean
