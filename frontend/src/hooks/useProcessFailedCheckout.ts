import { useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { CheckoutService } from "../client/sdk.gen"
import { is404Error } from "../utils/errorUtils"
import useCustomToast from "./useCustomToast"

interface UseFailedCheckoutParams {
  authUser: any
  isLoading: boolean
  sessionId?: string
}

export function useProcessFailedCheckout({
  authUser,
  isLoading,
  sessionId,
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

    // Using function expression instead of function declaration
    const processFailedCheckout = async () => {
      try {
        // Process the failed checkout with stripeCancel
        await CheckoutService.stripeCancel({ sessionId: validSessionId })
        // If the stripeCancel call succeeds, show the failure card
        setShouldShowCard(true)
      } catch (error: unknown) {
        console.error("Error processing failed checkout:", error)

        // Use the utility function to check for 404 errors
        if (is404Error(error)) {
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
