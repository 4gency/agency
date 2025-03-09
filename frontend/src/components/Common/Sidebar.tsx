import {
  Box,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerOverlay,
  Flex,
  IconButton,
  Text,
  useColorMode,
  useColorModeValue,
  useDisclosure,
} from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { FiLogOut, FiMenu, FiMoon, FiSun } from "react-icons/fi"

import type { UserPublic } from "../../client"
import useAuth from "../../hooks/useAuth"
import Logo from "./Logo"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  const queryClient = useQueryClient()
  const bgColor = useColorModeValue("ui.light", "ui.dark")
  const textColor = useColorModeValue("ui.dark", "ui.light")
  const secBgColor = useColorModeValue("ui.secondary", "ui.darkSlate")
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const { isOpen, onOpen, onClose } = useDisclosure()
  const { logout } = useAuth()
  const { colorMode, toggleColorMode } = useColorMode()

  const handleLogout = async () => {
    logout()
  }

  return (
    <>
      {/* Mobile */}
      <IconButton
        onClick={onOpen}
        display={{ base: "flex", md: "none" }}
        aria-label="Open Menu"
        position="fixed"
        top={4}
        left={4}
        fontSize="20px"
        icon={<FiMenu />}
        zIndex="200"
      />
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay
          bg={useColorModeValue(
            "rgba(255, 255, 255, 0.5)",
            "rgba(0, 0, 0, 0.2)",
          )}
          backdropFilter="blur(8px)"
        />
        <DrawerContent
          maxW="250px"
          zIndex={20}
          bg={useColorModeValue(
            "rgba(255, 255, 255, 0.8)",
            "rgba(26, 32, 44, 0.3)",
          )}
          backdropFilter="blur(20px)"
          style={{ WebkitBackdropFilter: "blur(20px)" }}
          borderRight="1px solid"
          borderColor={useColorModeValue(
            "rgba(209, 213, 219, 0.4)",
            "rgba(255, 255, 255, 0.1)",
          )}
          boxShadow={useColorModeValue("lg", "xl")}
        >
          <DrawerCloseButton color={useColorModeValue("gray.800", "white")} />
          <DrawerBody py={8}>
            <Flex flexDir="column" justify="space-between">
              <Box>
                <Box p={6}>
                  <Logo alt="logo" />
                </Box>
                <SidebarItems onClose={onClose} />

                {/* Theme Toggle Button */}
                <Flex
                  as="button"
                  onClick={toggleColorMode}
                  p={2}
                  fontWeight="medium"
                  alignItems="center"
                  mt={4}
                  color={useColorModeValue("gray.800", "white")}
                  _hover={{
                    bg: useColorModeValue(
                      "rgba(255, 255, 255, 0.4)",
                      "rgba(45, 55, 72, 0.4)",
                    ),
                  }}
                  borderRadius="md"
                  mb={3}
                >
                  {colorMode === "dark" ? <FiSun /> : <FiMoon />}
                  <Text ml={2}>
                    {colorMode === "dark" ? "Light mode" : "Dark mode"}
                  </Text>
                </Flex>

                {/* Logout Button */}
                <Flex
                  as="button"
                  onClick={handleLogout}
                  p={2}
                  color="ui.danger"
                  fontWeight="bold"
                  alignItems="center"
                  _hover={{
                    bg: useColorModeValue(
                      "rgba(255, 255, 255, 0.4)",
                      "rgba(45, 55, 72, 0.4)",
                    ),
                  }}
                  borderRadius="md"
                >
                  <FiLogOut />
                  <Text ml={2}>Log out</Text>
                </Flex>
              </Box>
              {currentUser?.email && (
                <Text
                  color={useColorModeValue("gray.800", "white")}
                  noOfLines={2}
                  fontSize="sm"
                  p={2}
                >
                  Logged in as: {currentUser.email}
                </Text>
              )}
            </Flex>
          </DrawerBody>
        </DrawerContent>
      </Drawer>

      {/* Desktop */}
      <Box
        bg={bgColor}
        p={3}
        h="100vh"
        position="sticky"
        top="0"
        zIndex={20}
        display={{ base: "none", md: "flex" }}
      >
        <Flex
          flexDir="column"
          justify="space-between"
          bg={secBgColor}
          p={4}
          borderRadius={12}
        >
          <Box>
            <Box p={6}>
              <Logo width="180px" maxW="2xs" alt="Logo" />
            </Box>
            <SidebarItems />
          </Box>
          {currentUser?.email && (
            <Text
              color={textColor}
              noOfLines={2}
              fontSize="sm"
              p={2}
              maxW="180px"
            >
              Logged in as: {currentUser.email}
            </Text>
          )}
        </Flex>
      </Box>
    </>
  )
}

export default Sidebar
