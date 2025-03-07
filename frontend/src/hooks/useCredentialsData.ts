import { useQuery, useQueryClient } from "@tanstack/react-query"
import { type GetUserCredentialsResponse, CredentialsService } from "../client"

// Chave para o cache no React Query
export const credentialsCacheKey = ["userCredentials"] 

export default function useCredentialsData() {
  const queryClient = useQueryClient()
  
  const query = useQuery({
    queryKey: credentialsCacheKey,
    queryFn: async () => {
      try {
        const response = await CredentialsService.getUserCredentials()
        return response.items || []
      } catch (error) {
        console.error("Error fetching credentials:", error)
        throw error
      }
    },
    // Configurações para melhorar o cache e evitar múltiplas chamadas
    staleTime: 30000, // 30 segundos
    refetchOnWindowFocus: false,
  })

  // Função para forçar uma atualização dos dados
  const refetchCredentials = () => {
    return queryClient.invalidateQueries({
      queryKey: credentialsCacheKey,
    })
  }

  return {
    credentials: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetchCredentials,
  }
} 