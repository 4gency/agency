import { createFileRoute, redirect } from "@tanstack/react-router"
import { isLoggedIn } from "../../hooks/useAuth"
import OnboardingPage from "../../components/Onboarding/OnboardingPage"

export const Route = createFileRoute("/onboarding/")({
  component: OnboardingPage,
  beforeLoad: async () => {
    // Check if user is logged in
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
        search: {
          redirect: "/onboarding",
        },
      })
    }
  },
}) 