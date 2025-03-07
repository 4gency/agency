import { createFileRoute } from "@tanstack/react-router"

// Simplificando a rota de índice para não interferir
export const Route = createFileRoute("/_layout/settings/subscription/")({
  component: SubscriptionIndexPage,
  beforeLoad: () => {
    console.log("Carregando rota de índice de assinatura")
  },
})

function SubscriptionIndexPage() {
  console.log("Renderizando página de índice de assinatura")

  // Esta página agora apenas retorna um componente vazio
  // Ela existe apenas para satisfazer a estrutura de rotas
  return null
}
