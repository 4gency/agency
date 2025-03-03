import {
  Container,
  Heading,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Box,
} from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import type { UserPublic } from "../../client"
import Appearance from "../../components/UserSettings/Appearance"
import ChangePassword from "../../components/UserSettings/ChangePassword"
import Payments from "../../components/UserSettings/Payments"
import Subscriptions from "../../components/UserSettings/Subscriptions"
import UserInformation from "../../components/UserSettings/UserInformation"
import { isLoggedIn } from "../../hooks/useAuth"
import { useEffect } from "react"

const tabsConfig = [
  { title: "My profile", component: UserInformation },
  { title: "Password", component: ChangePassword },
  { title: "Appearance", component: Appearance },
  { title: "Subscriptions", component: Subscriptions },
  { title: "Payments", component: Payments },
]

export const Route = createFileRoute("/_layout/settings")({
  component: SettingsLayout,
  beforeLoad: async ({ location }) => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }

    // Permitir que o redirecionamento não aconteça para subrotas
    if (location.pathname !== "/settings" && 
        location.pathname !== "/settings/") {
      return;
    }
  },
})

// Layout que renderiza o UserSettings ou um Outlet para subrotas
function SettingsLayout() {
  // Usando a verificação baseada na URL atual (não o pathname do router)
  const currentUrl = window.location.pathname;
  
  useEffect(() => {
    console.log("SettingsLayout renderizado, URL atual:", currentUrl);
    
    // Se estiver exatamente em /settings ou /settings/ e a página estiver em branco
    // Vamos forçar um refresh para garantir que o conteúdo seja carregado
    if (currentUrl === "/settings" || currentUrl === "/settings/") {
      console.log("Na rota principal de settings, verificando conteúdo");
    }
  }, [currentUrl]);
  
  // Se estiver na subrota de subscription, renderiza o Outlet
  if (currentUrl.includes('/settings/subscription/')) {
    console.log("Renderizando subrota de subscription:", currentUrl);
    return <Outlet />;
  }
  
  // Caso contrário, renderiza o componente UserSettings
  console.log("Renderizando UserSettings para URL:", currentUrl);
  return <UserSettings />;
}

// Componente UserSettings deve ser acessado diretamente via link do menu
export function UserSettings() {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const finalTabs = currentUser?.is_superuser
    ? tabsConfig.filter(tab => tab.title !== "Danger zone")
    : tabsConfig

  // Log para debug
  useEffect(() => {
    console.log("UserSettings renderizado");
  }, []);

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        User Settings
      </Heading>
      <Tabs variant="enclosed" maxWidth="100%">
        <Box overflowX="auto" overflowY="hidden" pb={2} sx={{
          scrollbarWidth: 'thin',
          '::-webkit-scrollbar': { height: '6px' },
          '::-webkit-scrollbar-thumb': { backgroundColor: 'gray.300', borderRadius: 'full' },
        }}>
          <TabList width="max-content" minWidth="100%">
            {finalTabs.map((tab, index) => (
              <Tab key={index}>{tab.title}</Tab>
            ))}
          </TabList>
        </Box>
        <TabPanels>
          {finalTabs.map((tab, index) => (
            <TabPanel key={index}>
              <tab.component />
            </TabPanel>
          ))}
        </TabPanels>
      </Tabs>
    </Container>
  )
}
