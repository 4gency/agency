import { createFileRoute, redirect } from "@tanstack/react-router";
import { z } from "zod";
import { isLoggedIn } from "../../hooks/useAuth";
import { Pricing } from "../../components/Sidebar/Pricing";

const jobPreferencesSearchSchema = z.object({});

export const Route = createFileRoute("/_layout/pricing")({
  component: Pricing,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        //@ts-ignore
        to: "/?redirectTo=pricing",
      });
    }
  },
  validateSearch: (search) => jobPreferencesSearchSchema.parse(search),
});
