import { useQuery, useQueryClient } from "@tanstack/react-query"
import { type UserDashboardStats, BotsService } from "../client"

// Chave para o cache no React Query
export const dashboardStatsCacheKey = ["dashboardStats"] 

export default function useDashboardStats() {
  const queryClient = useQueryClient()
  
  const query = useQuery({
    queryKey: dashboardStatsCacheKey,
    queryFn: async () => {
      try {
        return await BotsService.getUserDashboardStats()
      } catch (error) {
        console.error("Error fetching dashboard stats:", error)
        throw error
      }
    },
    // Configurações para melhorar o cache e evitar múltiplas chamadas
    staleTime: 30000, // 30 segundos
    refetchOnWindowFocus: false,
  })

  // Função para forçar uma atualização dos dados
  const refreshStats = () => {
    return queryClient.invalidateQueries({
      queryKey: dashboardStatsCacheKey,
    })
  }

  // Usamos um objeto vazio com a estrutura correta para evitar erros
  const emptyStats: UserDashboardStats = {
    total_applications: 0,
    successful_applications: 0,
    success_rate: 0,
    failed_applications: 0,
    failure_rate: 0,
    pending_applications: 0,
    timestamp: new Date().toISOString()
  }

  return {
    stats: query.data || emptyStats,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refreshStats,
  }
} 