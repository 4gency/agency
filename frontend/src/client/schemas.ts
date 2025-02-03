export const $Achievement = {
	properties: {
		name: {
	type: 'string',
	default: 'Employee of the month',
},
		description: {
	type: 'string',
	default: 'Awarded for being the best employee',
},
	},
} as const;

export const $Availability = {
	properties: {
		notice_period: {
	type: 'string',
	default: '1 month',
},
	},
} as const;

export const $Body_login_login_access_token = {
	properties: {
		grant_type: {
	type: 'any-of',
	contains: [{
	type: 'string',
	pattern: 'password',
}, {
	type: 'null',
}],
},
		username: {
	type: 'string',
	isRequired: true,
},
		password: {
	type: 'string',
	isRequired: true,
},
		scope: {
	type: 'string',
	default: '',
},
		client_id: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		client_secret: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $Certification = {
	properties: {
		name: {
	type: 'string',
	default: 'Python Certification',
},
		description: {
	type: 'string',
	default: 'Certified Python Developer',
},
	},
} as const;

export const $CheckoutSession = {
	properties: {
		id: {
	type: 'string',
	format: 'uuid',
},
		payment_gateway: {
	type: 'string',
	default: 'stripe',
	maxLength: 50,
},
		session_id: {
	type: 'string',
	isRequired: true,
	maxLength: 100,
},
		session_url: {
	type: 'string',
	isRequired: true,
	maxLength: 500,
},
		user_id: {
	type: 'string',
	isRequired: true,
	format: 'uuid',
},
		status: {
	type: 'string',
	default: 'open',
	maxLength: 50,
},
		payment_status: {
	type: 'string',
	default: 'unpaid',
	maxLength: 50,
},
		created_at: {
	type: 'string',
	default: '2025-02-02T07:53:01.732141Z',
	format: 'date-time',
},
		expires_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		updated_at: {
	type: 'string',
	default: '2025-02-02T07:53:01.732697Z',
	format: 'date-time',
},
	},
} as const;

export const $CheckoutSessionPublic = {
	properties: {
		session_id: {
	type: 'string',
	isRequired: true,
},
		session_url: {
	type: 'string',
	isRequired: true,
},
		expires_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $ConfigPublic = {
	properties: {
		remote: {
	type: 'boolean',
	default: true,
},
		experience_level: {
	type: 'ExperienceLevel',
	default: [],
},
		job_types: {
	type: 'JobTypes',
	default: [],
},
		date: {
	type: 'Date',
	default: [],
},
		positions: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [
    "Developer"
],
},
		locations: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [
    "USA"
],
},
		apply_once_at_company: {
	type: 'boolean',
	default: true,
},
		distance: {
	type: 'number',
	default: 0,
},
		company_blacklist: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [],
},
		title_blacklist: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [],
},
		job_applicants_threshold: {
	type: 'JobApplicantsThreshold',
	default: [],
},
	},
} as const;

export const $Date = {
	properties: {
		all_time: {
	type: 'boolean',
	default: true,
},
		month: {
	type: 'boolean',
	default: false,
},
		week: {
	type: 'boolean',
	default: false,
},
		hours: {
	type: 'boolean',
	default: false,
},
	},
} as const;

export const $EducationDetails = {
	properties: {
		education_level: {
	type: 'string',
	default: "Bachelor's Degree",
},
		institution: {
	type: 'string',
	default: 'University of New York',
},
		field_of_study: {
	type: 'string',
	default: 'Computer Science',
},
		final_evaluation_grade: {
	type: 'string',
	default: 'A',
},
		start_date: {
	type: 'string',
	default: '2018',
},
		year_of_completion: {
	type: 'string',
	default: '2022',
},
		exam: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [
    "GRE",
    "TOEFL"
],
},
	},
} as const;

export const $ExperienceDetail = {
	properties: {
		position: {
	type: 'string',
	default: 'Software Engineer',
},
		company: {
	type: 'string',
	default: 'Google',
},
		employment_period: {
	type: 'string',
	default: '2020 - 2022',
},
		location: {
	type: 'string',
	default: 'New York',
},
		industry: {
	type: 'string',
	default: 'Technology',
},
		key_responsibilities: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [
    "Developed new features",
    "Fixed bugs"
],
},
		skills_acquired: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [
    "Python",
    "Django",
    "React"
],
},
	},
} as const;

export const $ExperienceLevel = {
	properties: {
		intership: {
	type: 'boolean',
	default: true,
},
		entry: {
	type: 'boolean',
	default: true,
},
		associate: {
	type: 'boolean',
	default: true,
},
		mid_senior_level: {
	type: 'boolean',
	default: true,
},
		director: {
	type: 'boolean',
	default: true,
},
		executive: {
	type: 'boolean',
	default: true,
},
	},
} as const;

export const $HTTPValidationError = {
	properties: {
		detail: {
	type: 'array',
	contains: {
		type: 'ValidationError',
	},
},
	},
} as const;

export const $JobApplicantsThreshold = {
	properties: {
		min_applicants: {
	type: 'number',
	default: 0,
},
		max_applicants: {
	type: 'number',
	default: 10000,
},
	},
} as const;

export const $JobTypes = {
	properties: {
		full_time: {
	type: 'boolean',
	default: true,
},
		contract: {
	type: 'boolean',
	default: true,
},
		part_time: {
	type: 'boolean',
	default: true,
},
		temporary: {
	type: 'boolean',
	default: true,
},
		internship: {
	type: 'boolean',
	default: true,
},
		other: {
	type: 'boolean',
	default: true,
},
		volunteer: {
	type: 'boolean',
	default: true,
},
	},
} as const;

export const $Language = {
	properties: {
		language: {
	type: 'string',
	default: 'English',
},
		proficiency: {
	type: 'string',
	default: 'Native',
},
	},
} as const;

export const $LegalAuthorization = {
	properties: {
		eu_work_authorization: {
	type: 'boolean',
	default: false,
},
		us_work_authorization: {
	type: 'boolean',
	default: false,
},
		requires_us_visa: {
	type: 'boolean',
	default: false,
},
		requires_us_sponsorship: {
	type: 'boolean',
	default: false,
},
		requires_eu_visa: {
	type: 'boolean',
	default: false,
},
		legally_allowed_to_work_in_eu: {
	type: 'boolean',
	default: false,
},
		legally_allowed_to_work_in_us: {
	type: 'boolean',
	default: false,
},
		requires_eu_sponsorship: {
	type: 'boolean',
	default: false,
},
		canada_work_authorization: {
	type: 'boolean',
	default: false,
},
		requires_canada_visa: {
	type: 'boolean',
	default: false,
},
		legally_allowed_to_work_in_canada: {
	type: 'boolean',
	default: false,
},
		requires_canada_sponsorship: {
	type: 'boolean',
	default: false,
},
		uk_work_authorization: {
	type: 'boolean',
	default: false,
},
		requires_uk_visa: {
	type: 'boolean',
	default: false,
},
		legally_allowed_to_work_in_uk: {
	type: 'boolean',
	default: false,
},
		requires_uk_sponsorship: {
	type: 'boolean',
	default: false,
},
	},
} as const;

export const $Message = {
	properties: {
		message: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $NewPassword = {
	properties: {
		token: {
	type: 'string',
	isRequired: true,
},
		new_password: {
	type: 'string',
	isRequired: true,
	maxLength: 40,
	minLength: 8,
},
	},
} as const;

export const $PersonalInformation = {
	properties: {
		name: {
	type: 'string',
	default: 'John',
},
		surname: {
	type: 'string',
	default: 'Doe',
},
		date_of_birth: {
	type: 'string',
	default: '1995-02-10',
},
		country: {
	type: 'string',
	default: 'USA',
},
		city: {
	type: 'string',
	default: 'New York',
},
		address: {
	type: 'string',
	default: '123 Main St',
},
		phone_prefix: {
	type: 'string',
	default: '+1',
},
		phone: {
	type: 'string',
	default: '123456789',
},
		email: {
	type: 'string',
	default: 'john.doe@email.com',
	format: 'email',
},
		github: {
	type: 'string',
	default: 'https://github.com/john_doe',
},
		linkedin: {
	type: 'string',
	default: 'https://linkedin.com/in/john_doe',
},
	},
} as const;

export const $PlainTextResumePublic = {
	properties: {
		personal_information: {
	type: 'PersonalInformation',
	default: [],
},
		education_details: {
	type: 'array',
	contains: {
		type: 'EducationDetails',
	},
	default: [
    {
        "education_level": "Bachelor's Degree",
        "institution": "University of New York",
        "field_of_study": "Computer Science",
        "final_evaluation_grade": "A",
        "start_date": "2018",
        "year_of_completion": "2022",
        "exam": [
            "GRE",
            "TOEFL"
        ]
    }
],
},
		experience_details: {
	type: 'array',
	contains: {
		type: 'ExperienceDetail',
	},
	default: [
    {
        "position": "Software Engineer",
        "company": "Google",
        "employment_period": "2020 - 2022",
        "location": "New York",
        "industry": "Technology",
        "key_responsibilities": [
            "Developed new features",
            "Fixed bugs"
        ],
        "skills_acquired": [
            "Python",
            "Django",
            "React"
        ]
    }
],
},
		projects: {
	type: 'array',
	contains: {
		type: 'Project',
	},
	default: [
    {
        "name": "My awesome CRUD app",
        "description": "A CRUD app that does CRUD operations",
        "link": "www.myawesomecrud.com"
    }
],
},
		achievements: {
	type: 'array',
	contains: {
		type: 'Achievement',
	},
	default: [
    {
        "name": "Employee of the month",
        "description": "Awarded for being the best employee"
    }
],
},
		certifications: {
	type: 'array',
	contains: {
		type: 'Certification',
	},
	default: [
    {
        "name": "Python Certification",
        "description": "Certified Python Developer"
    }
],
},
		languages: {
	type: 'array',
	contains: {
		type: 'Language',
	},
	default: [
    {
        "language": "English",
        "proficiency": "Native"
    }
],
},
		interests: {
	type: 'array',
	contains: {
	type: 'string',
},
	default: [
    "Reading",
    "Swimming"
],
},
		availability: {
	type: 'Availability',
	default: [],
},
		salary_expectations: {
	type: 'SalaryExpectations',
	default: [],
},
		self_identification: {
	type: 'SelfIdentification',
	default: [],
},
		legal_authorization: {
	type: 'LegalAuthorization',
	default: [],
},
		work_preferences: {
	type: 'WorkPreferences',
	default: [],
},
	},
} as const;

export const $Project = {
	properties: {
		name: {
	type: 'string',
	default: 'My awesome CRUD app',
},
		description: {
	type: 'string',
	default: 'A CRUD app that does CRUD operations',
},
		link: {
	type: 'string',
	default: 'www.myawesomecrud.com',
},
	},
} as const;

export const $SalaryExpectations = {
	properties: {
		salary_range_usd: {
	type: 'string',
	default: '90000 - 110000',
},
	},
} as const;

export const $SelfIdentification = {
	properties: {
		gender: {
	type: 'string',
	default: 'Male',
},
		pronouns: {
	type: 'string',
	default: 'He/Him',
},
		veteran: {
	type: 'boolean',
	default: false,
},
		disability: {
	type: 'boolean',
	default: false,
},
		ethnicity: {
	type: 'string',
	default: 'Hispanic',
},
	},
} as const;

export const $SubscriptionMetric = {
	type: 'Enum',
	enum: ['day','week','month','year','applies',],
} as const;

export const $SubscriptionPlanBenefitPublic = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $SubscriptionPlanCreate = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		price: {
	type: 'number',
	isRequired: true,
},
		is_best_choice: {
	type: 'boolean',
	default: false,
},
		has_discount: {
	type: 'boolean',
	default: false,
},
		price_without_discount: {
	type: 'number',
	default: 0,
},
		currency: {
	type: 'string',
	default: 'USD',
	maxLength: 10,
},
		description: {
	type: 'string',
	default: '',
	maxLength: 10000,
},
		is_active: {
	type: 'boolean',
	default: true,
},
		metric_type: {
	type: 'SubscriptionMetric',
	default: "month",
},
		metric_value: {
	type: 'number',
	default: 1,
},
		benefits: {
	type: 'array',
	contains: {
		type: 'SubscriptionPlanBenefitPublic',
	},
	default: [],
},
	},
} as const;

export const $SubscriptionPlanPublic = {
	properties: {
		id: {
	type: 'string',
	isRequired: true,
	format: 'uuid',
},
		name: {
	type: 'string',
	isRequired: true,
},
		price: {
	type: 'number',
	isRequired: true,
},
		is_best_choice: {
	type: 'boolean',
	isRequired: true,
},
		has_discount: {
	type: 'boolean',
	isRequired: true,
},
		price_without_discount: {
	type: 'number',
	isRequired: true,
},
		currency: {
	type: 'string',
	isRequired: true,
},
		description: {
	type: 'string',
	isRequired: true,
},
		is_active: {
	type: 'boolean',
	isRequired: true,
},
		metric_type: {
	type: 'SubscriptionMetric',
	isRequired: true,
},
		metric_value: {
	type: 'number',
	isRequired: true,
},
		benefits: {
	type: 'array',
	contains: {
		type: 'SubscriptionPlanBenefitPublic',
	},
	default: [],
},
	},
} as const;

export const $SubscriptionPlanUpdate = {
	properties: {
		name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		price: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		is_best_choice: {
	type: 'any-of',
	contains: [{
	type: 'boolean',
}, {
	type: 'null',
}],
},
		has_discount: {
	type: 'any-of',
	contains: [{
	type: 'boolean',
}, {
	type: 'null',
}],
},
		price_without_discount: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		currency: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		description: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		is_active: {
	type: 'any-of',
	contains: [{
	type: 'boolean',
}, {
	type: 'null',
}],
},
		metric_type: {
	type: 'any-of',
	contains: [{
	type: 'SubscriptionMetric',
}, {
	type: 'null',
}],
},
		metric_value: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		benefits: {
	type: 'any-of',
	contains: [{
	type: 'array',
	contains: {
		type: 'SubscriptionPlanBenefitPublic',
	},
}, {
	type: 'null',
}],
},
	},
} as const;

export const $SubscriptionPlansPublic = {
	properties: {
		plans: {
	type: 'array',
	contains: {
		type: 'SubscriptionPlanPublic',
	},
	default: [],
},
	},
} as const;

export const $SubscriptionPublic = {
	properties: {
		id: {
	type: 'string',
	isRequired: true,
	format: 'uuid',
},
		user_id: {
	type: 'string',
	isRequired: true,
	format: 'uuid',
},
		subscription_plan_id: {
	type: 'string',
	isRequired: true,
	format: 'uuid',
},
		start_date: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		end_date: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		is_active: {
	type: 'boolean',
	isRequired: true,
},
		metric_type: {
	type: 'SubscriptionMetric',
	isRequired: true,
},
		metric_status: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $Token = {
	properties: {
		access_token: {
	type: 'string',
	isRequired: true,
},
		token_type: {
	type: 'string',
	default: 'bearer',
},
	},
} as const;

export const $UpdatePassword = {
	properties: {
		current_password: {
	type: 'string',
	isRequired: true,
	maxLength: 40,
	minLength: 8,
},
		new_password: {
	type: 'string',
	isRequired: true,
	maxLength: 40,
	minLength: 8,
},
	},
} as const;

export const $UserCreate = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
	format: 'email',
	maxLength: 255,
},
		is_active: {
	type: 'boolean',
	default: true,
},
		is_superuser: {
	type: 'boolean',
	default: false,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
	maxLength: 255,
}, {
	type: 'null',
}],
},
		password: {
	type: 'string',
	isRequired: true,
	maxLength: 40,
	minLength: 8,
},
	},
} as const;

export const $UserPublic = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
	format: 'email',
	maxLength: 255,
},
		is_active: {
	type: 'boolean',
	default: true,
},
		is_superuser: {
	type: 'boolean',
	default: false,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
	maxLength: 255,
}, {
	type: 'null',
}],
},
		id: {
	type: 'string',
	isRequired: true,
	format: 'uuid',
},
	},
} as const;

export const $UserRegister = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
	format: 'email',
	maxLength: 255,
},
		password: {
	type: 'string',
	isRequired: true,
	maxLength: 40,
	minLength: 8,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
	maxLength: 255,
}, {
	type: 'null',
}],
},
	},
} as const;

export const $UserUpdate = {
	properties: {
		email: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'email',
	maxLength: 255,
}, {
	type: 'null',
}],
},
		is_active: {
	type: 'boolean',
	default: true,
},
		is_superuser: {
	type: 'boolean',
	default: false,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
	maxLength: 255,
}, {
	type: 'null',
}],
},
		password: {
	type: 'any-of',
	contains: [{
	type: 'string',
	maxLength: 40,
	minLength: 8,
}, {
	type: 'null',
}],
},
	},
} as const;

export const $UserUpdateMe = {
	properties: {
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
	maxLength: 255,
}, {
	type: 'null',
}],
},
		email: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'email',
	maxLength: 255,
}, {
	type: 'null',
}],
},
	},
} as const;

export const $UsersPublic = {
	properties: {
		data: {
	type: 'array',
	contains: {
		type: 'UserPublic',
	},
	isRequired: true,
},
		count: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $ValidationError = {
	properties: {
		loc: {
	type: 'array',
	contains: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'number',
}],
},
	isRequired: true,
},
		msg: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $WorkPreferences = {
	properties: {
		remote_work: {
	type: 'boolean',
	default: true,
},
		in_person_work: {
	type: 'boolean',
	default: true,
},
		open_to_relocation: {
	type: 'boolean',
	default: true,
},
		willing_to_complete_assessments: {
	type: 'boolean',
	default: true,
},
		willing_to_undergo_drug_tests: {
	type: 'boolean',
	default: true,
},
		willing_to_undergo_background_checks: {
	type: 'boolean',
	default: true,
},
	},
} as const;