import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import JobPreferencesPage from "../../components/UserSettings/JobPreferences"

const jobPreferencesSearchSchema = z.object({})

export const Route = createFileRoute("/_layout/job-preferences")({
  component: JobPreferencesPage,
  validateSearch: (search) => jobPreferencesSearchSchema.parse(search),
})
