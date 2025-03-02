import { Flex, Spinner } from "@chakra-ui/react"
import { Outlet, createFileRoute } from "@tanstack/react-router"
import { useEffect } from "react"

import Sidebar from "../components/Common/Sidebar"
import UserMenu from "../components/Common/UserMenu"
import LandingPage from "../components/Pages/LandingPage"
import useAuth from "../hooks/useAuth"
import { useCheckoutHandler } from "../hooks/useCheckoutHandler"

export const Route = createFileRoute("/_layout")({
  component: Layout,
})

function Layout() {
  const { isLoading, user } = useAuth()
  const { checkForSelectedPlan } = useCheckoutHandler()

  // Effect to check for saved subscription plan after login
  useEffect(() => {
    if (user && !isLoading) {
      // Only run once when user is logged in and not loading
      checkForSelectedPlan()
    }
  }, [user, isLoading])

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
