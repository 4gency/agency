import { useQuery, useQueryClient } from "@tanstack/react-query"
import { type BotSession, BotsService } from "../client"

// Chave para o cache no React Query
export const sessionsCacheKey = ["botSessions"] 

export default function useSessionsData() {
  const queryClient = useQueryClient()
  
  const query = useQuery({
    queryKey: sessionsCacheKey,
    queryFn: async () => {
      try {
        const response = await BotsService.getBotSessions()
        return response.items || []
      } catch (error) {
        console.error("Error fetching bot sessions:", error)
        throw error
      }
    },
    // Configurações para melhorar o cache e evitar múltiplas chamadas
    staleTime: 30000, // 30 segundos 
    refetchOnWindowFocus: false,
  })

  // Função para forçar uma atualização dos dados
  const refetchSessions = () => {
    return queryClient.invalidateQueries({
      queryKey: sessionsCacheKey,
    })
  }

  return {
    sessions: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetchSessions,
  }
} 