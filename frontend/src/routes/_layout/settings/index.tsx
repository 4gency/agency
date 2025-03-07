import { createFileRoute } from "@tanstack/react-router"

// @ts-ignore - This route will be properly registered when the app runs
export const Route = createFileRoute("/_layout/settings/")({
  component: () => null,
})
