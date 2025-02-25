import { createFileRoute, redirect } from "@tanstack/react-router"
import { z } from "zod"
import JobPreferencesPage from "../../components/UserSettings/JobPreferences"
import { isLoggedIn } from "../../hooks/useAuth"
import { UsersService } from "../../client"

const jobPreferencesSearchSchema = z.object({})

export const Route = createFileRoute("/_layout/job-preferences")({
  component: JobPreferencesPage,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }

    const subscriptions = await UsersService.getUserSubscriptions()
    if (!subscriptions || subscriptions.length === 0) {
      throw redirect({
        to: "/",
      })
    }
  },
  validateSearch: (search) => jobPreferencesSearchSchema.parse(search),
})
