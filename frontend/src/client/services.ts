import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type { Body_login_login_access_token,Message,NewPassword,Token,UserPublic,SubscriptionPublic,UpdatePassword,UserCreate,UserRegister,UsersPublic,UserUpdate,UserUpdateMe,ConfigPublic,PlainTextResumePublic,SubscriptionPlanCreate,SubscriptionPlanPublic,SubscriptionPlansPublic,SubscriptionPlanUpdate } from './models';

export type LoginData = {
        LoginAccessToken: {
                    formData: Body_login_login_access_token
                    
                };
RecoverPassword: {
                    email: string
                    
                };
ResetPassword: {
                    requestBody: NewPassword
                    
                };
RecoverPasswordHtmlContent: {
                    email: string
                    
                };
    }

export type UsersData = {
        ReadUsers: {
                    limit?: number
skip?: number
                    
                };
CreateUser: {
                    requestBody: UserCreate
                    
                };
UpdateUserMe: {
                    requestBody: UserUpdateMe
                    
                };
UpdatePasswordMe: {
                    requestBody: UpdatePassword
                    
                };
RegisterUser: {
                    requestBody: UserRegister
                    
                };
ReadUserById: {
                    userId: string
                    
                };
UpdateUser: {
                    requestBody: UserUpdate
userId: string
                    
                };
DeleteUser: {
                    userId: string
                    
                };
GetUserSubscriptions: {
                    onlyActive?: boolean | null
                    
                };
    }

export type UtilsData = {
        TestEmail: {
                    emailTo: string
                    
                };
    }

export type ConfigsData = {
        GetConfig: {
                    subscriptionId: string
                    
                };
UpdateConfig: {
                    requestBody: ConfigPublic
subscriptionId: string
                    
                };
GetPlainTextResume: {
                    subscriptionId: string
                    
                };
UpdatePlainTextResume: {
                    requestBody: PlainTextResumePublic
subscriptionId: string
                    
                };
    }

export type SubscriptionData = {
        CreateSubscriptionPlan: {
                    requestBody: SubscriptionPlanCreate
                    
                };
ReadSubscriptionPlan: {
                    id: string
                    
                };
UpdateSubscriptionPlan: {
                    id: string
requestBody: SubscriptionPlanUpdate
                    
                };
DeleteSubscriptionPlan: {
                    id: string
                    
                };
    }

export type CheckoutData = {
        GetStripeCheckoutSession: {
                    subscriptionPlanId: string
                    
                };
    }

export class LoginService {

	/**
	 * Login Access Token
	 * OAuth2 compatible token login, get an access token for future requests
	 * @returns Token Successful Response
	 * @throws ApiError
	 */
	public static loginAccessToken(data: LoginData['LoginAccessToken']): CancelablePromise<Token> {
		const {
formData,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/login/access-token',
			formData: formData,
			mediaType: 'application/x-www-form-urlencoded',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Test Token
	 * Test access token
	 * @returns UserPublic Successful Response
	 * @throws ApiError
	 */
	public static testToken(): CancelablePromise<UserPublic> {
				return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/login/test-token',
		});
	}

	/**
	 * Recover Password
	 * Password Recovery
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static recoverPassword(data: LoginData['RecoverPassword']): CancelablePromise<Message> {
		const {
email,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/password-recovery/{email}',
			path: {
				email
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Reset Password
	 * Reset password
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static resetPassword(data: LoginData['ResetPassword']): CancelablePromise<Message> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/reset-password/',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Recover Password Html Content
	 * HTML Content for Password Recovery
	 * @returns string Successful Response
	 * @throws ApiError
	 */
	public static recoverPasswordHtmlContent(data: LoginData['RecoverPasswordHtmlContent']): CancelablePromise<string> {
		const {
email,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/password-recovery-html-content/{email}',
			path: {
				email
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class UsersService {

	/**
	 * Read Users
	 * Retrieve users.
	 * @returns UsersPublic Successful Response
	 * @throws ApiError
	 */
	public static readUsers(data: UsersData['ReadUsers'] = {}): CancelablePromise<UsersPublic> {
		const {
skip = 0,
limit = 100,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/users/',
			query: {
				skip, limit
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Create User
	 * Create new user.
	 * @returns UserPublic Successful Response
	 * @throws ApiError
	 */
	public static createUser(data: UsersData['CreateUser']): CancelablePromise<UserPublic> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/users/',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Read User Me
	 * Get current user.
	 * @returns UserPublic Successful Response
	 * @throws ApiError
	 */
	public static readUserMe(): CancelablePromise<UserPublic> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/users/me',
		});
	}

	/**
	 * Delete User Me
	 * Delete own user.
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static deleteUserMe(): CancelablePromise<Message> {
				return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/users/me',
		});
	}

	/**
	 * Update User Me
	 * Update own user.
	 * @returns UserPublic Successful Response
	 * @throws ApiError
	 */
	public static updateUserMe(data: UsersData['UpdateUserMe']): CancelablePromise<UserPublic> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PATCH',
			url: '/api/v1/users/me',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Update Password Me
	 * Update own password.
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static updatePasswordMe(data: UsersData['UpdatePasswordMe']): CancelablePromise<Message> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PATCH',
			url: '/api/v1/users/me/password',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Register User
	 * Create new user without the need to be logged in.
	 * @returns UserPublic Successful Response
	 * @throws ApiError
	 */
	public static registerUser(data: UsersData['RegisterUser']): CancelablePromise<UserPublic> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/users/signup',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Read User By Id
	 * Get a specific user by id.
	 * @returns UserPublic Successful Response
	 * @throws ApiError
	 */
	public static readUserById(data: UsersData['ReadUserById']): CancelablePromise<UserPublic> {
		const {
userId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/users/{user_id}',
			path: {
				user_id: userId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Update User
	 * Update a user.
	 * @returns UserPublic Successful Response
	 * @throws ApiError
	 */
	public static updateUser(data: UsersData['UpdateUser']): CancelablePromise<UserPublic> {
		const {
userId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PATCH',
			url: '/api/v1/users/{user_id}',
			path: {
				user_id: userId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Delete User
	 * Delete a user.
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static deleteUser(data: UsersData['DeleteUser']): CancelablePromise<Message> {
		const {
userId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/users/{user_id}',
			path: {
				user_id: userId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get User Subscriptions
	 * Get user subscription.
	 * @returns SubscriptionPublic Successful Response
	 * @throws ApiError
	 */
	public static getUserSubscriptions(data: UsersData['GetUserSubscriptions'] = {}): CancelablePromise<Array<SubscriptionPublic>> {
		const {
onlyActive,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/users/me/subscriptions',
			query: {
				only_active: onlyActive
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class UtilsService {

	/**
	 * Test Email
	 * Test emails.
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static testEmail(data: UtilsData['TestEmail']): CancelablePromise<Message> {
		const {
emailTo,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/utils/test-email/',
			query: {
				email_to: emailTo
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Health Check
	 * @returns boolean Successful Response
	 * @throws ApiError
	 */
	public static healthCheck(): CancelablePromise<boolean> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/utils/health-check/',
		});
	}

}

export class ConfigsService {

	/**
	 * Get Config
	 * @returns ConfigPublic Successful Response
	 * @throws ApiError
	 */
	public static getConfig(data: ConfigsData['GetConfig']): CancelablePromise<ConfigPublic> {
		const {
subscriptionId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/configs/{subscription_id}/job-preferences',
			path: {
				subscription_id: subscriptionId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Update Config
	 * Update config.
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static updateConfig(data: ConfigsData['UpdateConfig']): CancelablePromise<unknown> {
		const {
subscriptionId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PUT',
			url: '/api/v1/configs/{subscription_id}/job-preferences',
			path: {
				subscription_id: subscriptionId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Plain Text Resume
	 * @returns PlainTextResumePublic Successful Response
	 * @throws ApiError
	 */
	public static getPlainTextResume(data: ConfigsData['GetPlainTextResume']): CancelablePromise<PlainTextResumePublic> {
		const {
subscriptionId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/configs/{subscription_id}/resume',
			path: {
				subscription_id: subscriptionId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Update Plain Text Resume
	 * Update plain text resume.
	 * @throws ApiError
	 */
	public static updatePlainTextResume(data: ConfigsData['UpdatePlainTextResume']): CancelablePromise<void> {
		const {
subscriptionId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PUT',
			url: '/api/v1/configs/{subscription_id}/resume',
			path: {
				subscription_id: subscriptionId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
				500: `Successful Response`,
			},
		});
	}

}

export class SubscriptionService {

	/**
	 * Read Subscription Plans
	 * Retrieve subscription plans (public endpoint).
	 * @returns SubscriptionPlansPublic Successful Response
	 * @throws ApiError
	 */
	public static readSubscriptionPlans(): CancelablePromise<SubscriptionPlansPublic> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/subscription/plans',
		});
	}

	/**
	 * Create Subscription Plan
	 * Create new subscription plan (superuser only).
	 * @returns SubscriptionPlanPublic Successful Response
	 * @throws ApiError
	 */
	public static createSubscriptionPlan(data: SubscriptionData['CreateSubscriptionPlan']): CancelablePromise<SubscriptionPlanPublic> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/subscription/plans',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Read Subscription Plan
	 * Get subscription plan by ID (public endpoint).
	 * @returns SubscriptionPlanPublic Successful Response
	 * @throws ApiError
	 */
	public static readSubscriptionPlan(data: SubscriptionData['ReadSubscriptionPlan']): CancelablePromise<SubscriptionPlanPublic> {
		const {
id,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/subscription/plans/{id}',
			path: {
				id
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Update Subscription Plan
	 * Update a subscription plan (superuser only).
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static updateSubscriptionPlan(data: SubscriptionData['UpdateSubscriptionPlan']): CancelablePromise<Message> {
		const {
id,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PUT',
			url: '/api/v1/subscription/plans/{id}',
			path: {
				id
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Delete Subscription Plan
	 * Delete a subscription plan (superuser only).
	 * @returns Message Successful Response
	 * @throws ApiError
	 */
	public static deleteSubscriptionPlan(data: SubscriptionData['DeleteSubscriptionPlan']): CancelablePromise<Message> {
		const {
id,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/subscription/plans/{id}',
			path: {
				id
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class CheckoutService {

	/**
	 * Get Stripe Checkout Session
	 * Get Stripe checkout session.
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static getStripeCheckoutSession(data: CheckoutData['GetStripeCheckoutSession']): CancelablePromise<unknown> {
		const {
subscriptionPlanId,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/checkout/stripe/checkout-session',
			query: {
				subscription_plan_id: subscriptionPlanId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}