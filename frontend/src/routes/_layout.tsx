import { Flex, Spinner } from "@chakra-ui/react"
import { Outlet, createFileRoute } from "@tanstack/react-router"

import Sidebar from "../components/Common/Sidebar"
import UserMenu from "../components/Common/UserMenu"
import useAuth from "../hooks/useAuth"
import LandingPage from "../components/Pages/LandingPage"

export const Route = createFileRoute("/_layout")({
  component: Layout,
})

function Layout() {
  const { isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <Flex justify="center" align="center" height="100vh" width="full">
        <Spinner size="xl" color="ui.main" />
      </Flex>
    )
  }

  if (!user) {
    return (
      <div style={{ all: "unset" }}>
        <LandingPage />
      </div>
    )
  }

  return (
    <Flex maxW="large" h="auto" position="relative">
      <Sidebar />
      <Outlet />      
      <UserMenu />
    </Flex>
  )
}
