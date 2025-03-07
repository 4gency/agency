import { createFileRoute, redirect } from "@tanstack/react-router"
import { z } from "zod"
import { UsersService } from "../../client"
import JobPreferencesPage from "../../components/UserSettings/JobPreferences"
import { isLoggedIn } from "../../hooks/useAuth"

const jobPreferencesSearchSchema = z.object({})

export const Route = createFileRoute("/_layout/job-preferences")({
  component: JobPreferencesPage,
  beforeLoad: async () => {
    // Check if user is logged in
    if (!isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }

    try {
      // Fetch subscriptions data
      const subscriptions = await UsersService.getUserSubscriptions()

      // Redirect to root if user is not a subscriber
      if (!subscriptions || subscriptions.length === 0) {
        throw redirect({
          to: "/",
        })
      }
    } catch (error) {
      // If there's an error fetching subscriptions, redirect to home
      throw redirect({
        to: "/",
      })
    }
  },
  validateSearch: (search) => jobPreferencesSearchSchema.parse(search),
})
