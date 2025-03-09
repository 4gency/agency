import { createFileRoute } from "@tanstack/react-router"

// Simplificando a rota de índice para não interferir
export const Route = createFileRoute("/_layout/settings/subscription/")({
  component: SubscriptionIndexPage,
  beforeLoad: () => {
  },
})

function SubscriptionIndexPage() {

  // Esta página agora apenas retorna um componente vazio
  // Ela existe apenas para satisfazer a estrutura de rotas
  return null
}
