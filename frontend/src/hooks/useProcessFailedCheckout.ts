import { useEffect, useState } from "react"
import { CheckoutService } from "../client/sdk.gen"
import { useNavigate } from "@tanstack/react-router"
import useCustomToast from "./useCustomToast"

interface ApiError {
  response?: {
    status: number
  }
  status?: number
  name?: string
  message?: string
}

interface UseFailedCheckoutParams {
  authUser: any
  isLoading: boolean
  sessionId?: string
}

export function useProcessFailedCheckout({ 
  authUser, 
  isLoading, 
  sessionId 
}: UseFailedCheckoutParams) {
  const [shouldShowCard, setShouldShowCard] = useState(false)
  const navigate = useNavigate()
  const showToast = useCustomToast()

  useEffect(() => {
    if (!isLoading && !authUser) {
      navigate({ to: "/login" })
      return
    }

    if (!sessionId) {
      navigate({ to: "/" })
      return
    }

    // Since we've checked sessionId is not null/undefined, we can safely pass it to API
    const validSessionId = sessionId

    async function processFailedCheckout() {
      try {
        // Process the failed checkout with stripeCancel
        await CheckoutService.stripeCancel({ sessionId: validSessionId })
        // If the stripeCancel call succeeds, show the failure card
        setShouldShowCard(true)
      } catch (error: unknown) {
        console.error("Error processing failed checkout:", error)
        
        // More robust error checking for 404 responses
        const apiError = error as ApiError
        
        // Check different possible ways a 404 might be represented
        const is404 = 
          (apiError.response && apiError.response.status === 404) || 
          apiError.status === 404 || 
          (apiError.message && apiError.message.includes("404")) ||
          (apiError.name && apiError.name.includes("NotFound"))
          
        if (is404) {
          console.log("404 error detected, redirecting to dashboard")
          // If 404, redirect directly to dashboard without showing any modal
          navigate({ to: "/" })
        } else {
          // For other errors, still show the failure screen to give feedback
          setShouldShowCard(true)
        }
      }
    }

    if (authUser && sessionId) {
      processFailedCheckout()
    }
  }, [authUser, isLoading, sessionId, navigate, showToast])

  return { shouldShowCard }
} 