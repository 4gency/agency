import { useQuery, useQueryClient } from "@tanstack/react-query"
import { SubscriptionPlansService } from "../client"

// Chave para o cache no React Query
export const getSubscriptionPlansCacheKey = (onlyActive: boolean) => 
  ["subscriptionPlans", { onlyActive }]

export default function useSubscriptionPlans(onlyActive: boolean = false) {
  const queryClient = useQueryClient()
  
  const query = useQuery({
    queryKey: getSubscriptionPlansCacheKey(onlyActive),
    queryFn: async () => {
      try {
        const response = await SubscriptionPlansService.readSubscriptionPlans({
          onlyActive,
        })
        return response.plans || []
      } catch (error) {
        console.error(`Error fetching subscription plans (onlyActive=${onlyActive}):`, error)
        throw error
      }
    },
    // Configurações para melhorar o cache e evitar múltiplas chamadas
    staleTime: 5 * 60 * 1000, // 5 minutos de cache
    refetchOnWindowFocus: false,
  })

  // Função para forçar uma atualização dos dados
  const refetchPlans = () => {
    return queryClient.invalidateQueries({
      queryKey: getSubscriptionPlansCacheKey(onlyActive),
    })
  }

  return {
    plans: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetchPlans,
  }
} 