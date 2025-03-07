import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router"
import ReactDOM from "react-dom/client"
import { routeTree } from "./routeTree.gen"

import { StrictMode } from "react"
import { OpenAPI } from "./client"
import theme from "./theme"

OpenAPI.BASE = import.meta.env.VITE_API_URL
OpenAPI.TOKEN = async () => {
  return localStorage.getItem("access_token") || ""
}

// Adiciona interceptor para lidar com erros de autenticação
OpenAPI.interceptors.response.use(async (response) => {
  // Se o status for 4xx (erro do cliente), mas não for uma rota pública como /login ou /register
  if (response.status >= 400 && response.status < 500) {
    const publicRoutes = [
      '/login/access-token',
      '/login',
      '/register',
      '/password-reset',
      '/docs',
      '/redoc',
      '/openapi.json'
    ]
    
    // Verifica se não é uma rota pública
    const isPublicRoute = publicRoutes.some(route => response.config.url?.includes(route))
    
    if (!isPublicRoute && localStorage.getItem("access_token")) {
      console.log(`Erro ${response.status}: Usuário desconectado automaticamente`)
      localStorage.removeItem("access_token")
      window.location.href = "/login"
    }
  }
  
  return response
})

const queryClient = new QueryClient()

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ChakraProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ChakraProvider>
  </StrictMode>,
)
