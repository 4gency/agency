import { createFileRoute, redirect } from "@tanstack/react-router"
import { z } from "zod"
import JobPreferencesPage from "../../components/UserSettings/JobPreferences"
import { isLoggedIn } from "../../hooks/useAuth"

const jobPreferencesSearchSchema = z.object({})

export const Route = createFileRoute("/_layout/job-preferences")({
  component: JobPreferencesPage,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  validateSearch: (search) => jobPreferencesSearchSchema.parse(search),
})
