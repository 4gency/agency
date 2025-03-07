import { createFileRoute, redirect } from "@tanstack/react-router"
import { UsersService } from "../../client"
import ResumePage from "../../components/UserSettings/Resume"
import { isLoggedIn } from "../../hooks/useAuth"

export const Route = createFileRoute("/_layout/resume")({
  component: ResumePage,
  beforeLoad: async () => {
    // Check if the user is logged in
    if (!isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }

    try {
      // If the user is logged in, fetch their subscriptions
      const subscriptions = await UsersService.getUserSubscriptions()

      // If the user has no subscriptions, redirect to root
      if (!subscriptions || subscriptions.length === 0) {
        throw redirect({
          to: "/",
        })
      }

      return {
        subscriptions,
      }
    } catch (error) {
      // If there's an error or the user has no subscriptions, redirect
      throw redirect({
        to: "/",
      })
    }
  },
})
