import { createFileRoute, redirect } from "@tanstack/react-router"
import { z } from "zod"
import { Pricing } from "../../components/Sidebar/Pricing"
import { isLoggedIn } from "../../hooks/useAuth"

const pricingSearchSchema = z.object({})

export const Route = createFileRoute("/_layout/pricing")({
  component: Pricing,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        //@ts-ignore
        to: "/?redirectTo=pricing",
      })
    }
  },
  validateSearch: (search) => pricingSearchSchema.parse(search),
})
