import { useEffect, useState } from "react"
import { CheckoutService } from "../client/sdk.gen"
import { useNavigate } from "@tanstack/react-router"
import useCustomToast from "./useCustomToast"
import confetti from "canvas-confetti"

interface ApiError {
  response?: {
    status: number
  }
  status?: number
  name?: string
  message?: string
}

interface UseSuccessCheckoutParams {
  authUser: any
  isLoading: boolean
  sessionId?: string
}

export function useProcessSuccessCheckout({ 
  authUser, 
  isLoading, 
  sessionId 
}: UseSuccessCheckoutParams) {
  const [shouldShowCard, setShouldShowCard] = useState(false)
  const navigate = useNavigate()
  const showToast = useCustomToast()

  // Confetti effect
  const triggerConfetti = () => {
    const duration = 1000
    const animationEnd = Date.now() + duration
    const defaults = { 
      startVelocity: 40, 
      spread: 100, 
      ticks: 80, 
      zIndex: -1, // Coloca o confete atrás do modal
      particleCount: 80,
      scalar: 1.5, // Faz os confetes maiores
    }

    const interval = setInterval(() => {
      const timeLeft = animationEnd - Date.now()

      if (timeLeft <= 0) {
        return clearInterval(interval)
      }

      const particleCount = 50 * (timeLeft / duration)
      
      // Confetes emanando do centro
      confetti({
        ...defaults,
        particleCount,
        origin: { x: 0.5, y: 0.5 }, // Centro da tela
        gravity: 0.8, // Um pouco mais de gravidade para que os confetes não subam muito
        disableForReducedMotion: true
      })
    }, 200)
  }

  useEffect(() => {
    if (!isLoading && !authUser) {
      navigate({ to: "/login" })
      return
    }

    if (!sessionId) {
      navigate({ to: "/" })
      showToast("Missing Information", "Session ID is required for checkout verification", "error")
      return
    }

    // Since we've checked sessionId is not null/undefined, we can safely pass it to API
    const validSessionId = sessionId

    async function processCheckout() {
      try {
        // Call the API with sessionId
        await CheckoutService.stripeSuccess({ sessionId: validSessionId })
        
        // Trigger confetti and show card
        triggerConfetti()
        setShouldShowCard(true)
      } catch (error: unknown) {
        console.error("Failed to process checkout:", error)
        
        // Check different possible ways a 404 might be represented
        const apiError = error as ApiError
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
          // For other errors, redirect to the failed page
          navigate({ 
            to: "/checkout-failed", 
            search: { sessionId: validSessionId }
          })
          showToast("Payment Processing Failed", "We were unable to process your payment.", "error")
        }
      }
    }

    if (authUser && sessionId) {
      processCheckout()
    }
  }, [authUser, isLoading, sessionId, navigate, showToast])

  return { shouldShowCard }
} 