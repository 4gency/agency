import { useNavigate } from "@tanstack/react-router"
import { useRef, useState } from "react"
import { CheckoutService } from "../client"
import useAuth from "./useAuth"
import useCustomToast from "./useCustomToast"

export const useCheckoutHandler = () => {
  const { user, isLoading: isAuthLoading } = useAuth()
  const navigate = useNavigate()
  const showToast = useCustomToast()
  // Track loading state per plan ID
  const [loadingPlans, setLoadingPlans] = useState<Record<string, boolean>>({})
  // Maintain a ref to the last checkout timestamp to prevent duplicate clicks
  const lastCheckoutAttempt = useRef<number>(0)
  // Timeout for debouncing
  const DEBOUNCE_TIME = 1000 // 1 second
  // Keep track of ongoing checkout creation promises
  const ongoingCheckouts = useRef<Record<string, Promise<any>>>({})

  // Check if a specific plan is in loading state
  const isPlanLoading = (planId: string): boolean => !!loadingPlans[planId]

  // Check if any plan is in loading state
  const isAnyPlanLoading = (): boolean =>
    Object.values(loadingPlans).some((loading) => loading)

  // Save selected plan ID for non-logged in users
  const saveSelectedPlan = (planId: string) => {
    try {
      // Store both the ID and a timestamp
      const planData = {
        id: planId,
        timestamp: Date.now(),
      }
      localStorage.setItem("selected_sub_plan_id", JSON.stringify(planData))
    } catch (error) {
      console.error("Error saving plan to localStorage:", error)
      // Fallback to just saving the ID
      localStorage.setItem("selected_sub_plan_id", planId)
    }
  }

  // Check if there's a selected plan and create the checkout if necessary
  const checkForSelectedPlan = async () => {
    try {
      // Get the stored plan data
      const storedPlan = localStorage.getItem("selected_sub_plan_id")
      if (!storedPlan) return

      // Clear the selected plan ID before proceeding to prevent loops
      localStorage.removeItem("selected_sub_plan_id")

      let planId: string
      try {
        // Try to parse as JSON (new format with timestamp)
        const planData = JSON.parse(storedPlan)
        planId = planData.id

        // Check if the stored plan selection is too old (e.g., 24 hours)
        const ONE_DAY = 24 * 60 * 60 * 1000
        if (Date.now() - planData.timestamp > ONE_DAY) {
          showToast(
            "Subscription Selection Expired",
            "Your subscription selection has expired. Please select a plan again.",
            "error",
          )
          return
        }
      } catch (e) {
        // Fallback for old format (just the ID)
        planId = storedPlan
      }

      // Create checkout session and redirect
      await createAndRedirectToCheckout(planId)
    } catch (error) {
      console.error("Error checking for selected plan:", error)
      showToast(
        "Checkout Error",
        "There was an error processing your subscription selection.",
        "error",
      )
    }
  }

  // Create a checkout session and redirect to it
  const createAndRedirectToCheckout = async (planId: string) => {
    // Check for debounce
    const now = Date.now()
    if (now - lastCheckoutAttempt.current < DEBOUNCE_TIME) {
      return
    }

    // Check if this plan is already loading
    if (isPlanLoading(planId)) {
      return
    }

    // If there's an ongoing checkout for this plan, reuse that promise
    if (planId in ongoingCheckouts.current) {
      return ongoingCheckouts.current[planId]
    }

    // Set loading state and update timestamp
    setLoadingPlans((prev) => ({ ...prev, [planId]: true }))
    lastCheckoutAttempt.current = now

    // Create a new checkout promise
    const checkoutPromise = (async () => {
      try {
        const checkoutSession =
          await CheckoutService.createStripeCheckoutSession({
            subscriptionPlanId: planId,
          })

        if (checkoutSession.session_url) {
          // Add an event for the "beforeunload" to handle closing the tab/window
          const handleBeforeUnload = () => {
            // Clear loading state if the page is unloaded
            setLoadingPlans((prev) => ({ ...prev, [planId]: false }))
          }

          window.addEventListener("beforeunload", handleBeforeUnload, {
            once: true,
          })

          // Redirect to Stripe checkout
          window.location.href = checkoutSession.session_url
          return checkoutSession
        }
        throw new Error("No checkout URL returned")
      } catch (error: any) {
        let errorMessage = "There was an error creating your checkout session."

        // Provide more specific error messages
        if (error.status === 404) {
          errorMessage = "The subscription plan is no longer available."
        } else if (error.status === 403) {
          errorMessage = "You don't have permission to subscribe to this plan."
        } else if (error.status >= 500) {
          errorMessage = "Server error. Please try again later."
        } else if (!navigator.onLine) {
          errorMessage =
            "You appear to be offline. Please check your internet connection."
        }

        console.error("Error creating checkout session:", error)
        showToast("Checkout Error", errorMessage, "error")
        throw error
      } finally {
        // Clear loading state and ongoing checkout reference
        setLoadingPlans((prev) => ({ ...prev, [planId]: false }))
        delete ongoingCheckouts.current[planId]
      }
    })()

    // Store the promise for reuse if another click happens
    ongoingCheckouts.current[planId] = checkoutPromise

    return checkoutPromise
  }

  // Handle the subscribe button click
  const handleSubscribeClick = async (planId: string) => {
    // Prevent action if already loading
    if (isPlanLoading(planId)) return

    // User is not logged in - save selection and redirect to signup
    if (!user && !isAuthLoading) {
      saveSelectedPlan(planId)
      navigate({ to: "/signup" })
      return
    }

    // User is logged in - create checkout session and redirect
    if (user) {
      try {
        await createAndRedirectToCheckout(planId)
      } catch (error) {
        // Error is already handled in createAndRedirectToCheckout
      }
    }
  }

  return {
    handleSubscribeClick,
    checkForSelectedPlan,
    isPlanLoading,
    isAnyPlanLoading,
  }
}
