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
import { createFileRoute, redirect } from "@tanstack/react-router"
import type { UserPublic } from "../../client"
import Appearance from "../../components/UserSettings/Appearance"
import ChangePassword from "../../components/UserSettings/ChangePassword"
import DeleteAccount from "../../components/UserSettings/DeleteAccount"
import Payments from "../../components/UserSettings/Payments"
import Subscriptions from "../../components/UserSettings/Subscriptions"
import UserInformation from "../../components/UserSettings/UserInformation"
import { isLoggedIn } from "../../hooks/useAuth"

const tabsConfig = [
  { title: "My profile", component: UserInformation },
  { title: "Password", component: ChangePassword },
  { title: "Appearance", component: Appearance },
  { title: "Subscriptions", component: Subscriptions },
  { title: "Payments", component: Payments },
  { title: "Danger zone", component: DeleteAccount },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
})

function UserSettings() {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const finalTabs = currentUser?.is_superuser
    ? tabsConfig.filter(tab => tab.title !== "Danger zone")
    : tabsConfig

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
