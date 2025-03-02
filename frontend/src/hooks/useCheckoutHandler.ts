import { useNavigate } from "@tanstack/react-router"
import { CheckoutService } from "../client"
import useCustomToast from "./useCustomToast"
import useAuth from "./useAuth"
import { useState } from "react"

export const useCheckoutHandler = () => {
  const { user, isLoading: isAuthLoading } = useAuth()
  const navigate = useNavigate()
  const showToast = useCustomToast()
  const [isCheckoutLoading, setIsCheckoutLoading] = useState(false)

  // Save selected plan ID for non-logged in users
  const saveSelectedPlan = (planId: string) => {
    localStorage.setItem("selected_sub_plan_id", planId)
  }

  // Check if there's a selected plan and create the checkout if necessary
  const checkForSelectedPlan = async () => {
    const selectedPlanId = localStorage.getItem("selected_sub_plan_id")
    if (selectedPlanId) {
      try {
        // Clear the selected plan ID before redirecting to prevent loops
        localStorage.removeItem("selected_sub_plan_id")
        // Create checkout session and redirect
        await createAndRedirectToCheckout(selectedPlanId)
      } catch (error) {
        console.error("Error creating checkout for selected plan:", error)
        showToast(
          "Checkout Error",
          "There was an error creating your checkout session.",
          "error"
        )
      }
    }
  }

  // Create a checkout session and redirect to it
  const createAndRedirectToCheckout = async (planId: string) => {
    if (isCheckoutLoading) return
    
    try {
      setIsCheckoutLoading(true)
      const checkoutSession = await CheckoutService.createStripeCheckoutSession({
        subscriptionPlanId: planId
      })
      
      if (checkoutSession.session_url) {
        // Redirect to Stripe checkout
        window.location.href = checkoutSession.session_url
      } else {
        throw new Error("No checkout URL returned")
      }
    } catch (error) {
      console.error("Error creating checkout session:", error)
      showToast(
        "Checkout Error",
        "There was an error creating your checkout session.",
        "error"
      )
    } finally {
      setIsCheckoutLoading(false)
    }
  }

  // Handle the subscribe button click
  const handleSubscribeClick = async (planId: string) => {
    if (isCheckoutLoading) return
    
    if (!user && !isAuthLoading) {
      // User is not logged in, save the selection and redirect to signup
      saveSelectedPlan(planId)
      navigate({ to: "/signup" })
    } else if (user) {
      // User is logged in, create checkout session and redirect
      await createAndRedirectToCheckout(planId)
    }
  }

  return {
    handleSubscribeClick,
    checkForSelectedPlan,
    isCheckoutLoading
  }
} 