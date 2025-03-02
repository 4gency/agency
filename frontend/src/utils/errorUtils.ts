/**
 * Interface for common API error structure
 */
export interface ApiError {
  response?: {
    status: number
  }
  status?: number
  name?: string
  message?: string
}

/**
 * Checks if an error object represents a 404 Not Found error
 * @param error The error object to check
 * @returns boolean indicating if the error is a 404
 */
export function is404Error(error: unknown): boolean {
  const apiError = error as ApiError
  
  return !!(
    (apiError.response && apiError.response.status === 404) || 
    apiError.status === 404 || 
    (apiError.message && apiError.message.includes("404")) ||
    (apiError.name && apiError.name.includes("NotFound"))
  )
} 