// hooks/useSubscriptions.ts
import { useQuery } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { type SubscriptionPublic, UsersService } from "../client"

export default function useSubscriptions() {
  const query = useQuery<SubscriptionPublic[], AxiosError>({
    queryKey: ["subscriptions"],
    queryFn: () => UsersService.getUserSubscriptions(),
  })
  return query
}
