// hooks/useSubscriptions.ts
import { useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { type SubscriptionPublic, type UserPublic, UsersService } from "../client"

export default function useSubscriptions() {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  
  // Definimos como o hook deve comportar-se:
  // 1. Se o usuário não estiver logado ou não tivermos os dados do usuário, o hook não faz nada
  // 2. Se o usuário estiver logado e não for assinante (is_subscriber = false), retornamos array vazio sem fazer chamada API
  // 3. Se o usuário for assinante, fazemos a chamada API para obter os detalhes da assinatura

  const query = useQuery<SubscriptionPublic[], AxiosError>({
    queryKey: ["subscriptions"],
    queryFn: () => {
      // Se o usuário não for assinante, retornamos um array vazio sem fazer chamada API
      if (currentUser && currentUser.is_subscriber === false) {
        return Promise.resolve([])
      }
      
      // Se for assinante, buscamos os detalhes da assinatura
      return UsersService.getUserSubscriptions()
    },
    // Só habilitamos a query se o usuário estiver logado
    enabled: !!currentUser,
    // Maior tempo de cache para evitar chamadas repetidas
    staleTime: 5 * 60 * 1000, // 5 minutos
    // Se ocorrer erro 404 (nenhuma assinatura), retornamos array vazio
    retry: (failureCount, error: any) => {
      if (error?.status === 404) {
        return false // Não tenta novamente em caso de 404
      }
      return failureCount < 2 // Tenta no máximo 2 vezes para outros erros
    },
  })

  return query
}
