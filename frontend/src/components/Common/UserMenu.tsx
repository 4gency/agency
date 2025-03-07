import {
  Box,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  useColorMode,
  useColorModeValue,
} from "@chakra-ui/react"
import { FaUserAstronaut } from "react-icons/fa"
import { FiLogOut, FiUser, FiMoon, FiSun } from "react-icons/fi"

import useAuth from "../../hooks/useAuth"

const UserMenu = () => {
  const { logout } = useAuth()
  const { colorMode, toggleColorMode } = useColorMode()

  const handleLogout = async () => {
    logout()
  }
  
  const handleNavigateToSettings = () => {
    window.location.href = "/settings";
  }
  
  // Alterna o tema e fecha o menu
  const handleToggleColorMode = (e: React.MouseEvent) => {
    toggleColorMode();
    // Não precisamos mais impedir o comportamento padrão
    // para permitir que o menu feche após o clique
  }

  return (
    <>
      {/* Desktop */}
      <Box
        display={{ base: "none", md: "block" }}
        position="fixed"
        top={4}
        right={4}
        zIndex={100}
      >
        <Menu closeOnSelect={false}>
          <MenuButton
            as={IconButton}
            aria-label="Options"
            icon={<FaUserAstronaut color="white" fontSize="18px" />}
            bg="ui.main"
            isRound
            data-testid="user-menu"
          />
          <MenuList
            bg={useColorModeValue('rgba(255, 255, 255, 0.3)', 'rgba(26, 32, 44, 0.3)')}
            backdropFilter="blur(12px)"
            borderColor={useColorModeValue('rgba(209, 213, 219, 0.4)', 'rgba(255, 255, 255, 0.1)')}
            borderWidth="1px"
            borderRadius="xl"
            boxShadow="md"
            p={2}
            style={{ WebkitBackdropFilter: "blur(12px)" }}
          >
            <MenuItem 
              icon={<FiUser fontSize="18px" />} 
              onClick={handleNavigateToSettings}
              closeOnSelect={true}
              bg="transparent"
              borderRadius="md"
              mb={2}
              color={useColorModeValue('gray.800', 'white')}
              fontWeight="medium"
              _hover={{
                bg: useColorModeValue('rgba(255, 255, 255, 0.4)', 'rgba(45, 55, 72, 0.4)'),
                boxShadow: "sm"
              }}
            >
              My profile
            </MenuItem>
            <MenuItem
              icon={colorMode === 'dark' ? <FiSun fontSize="18px" /> : <FiMoon fontSize="18px" />}
              onClick={handleToggleColorMode}
              closeOnSelect={true}
              bg="transparent"
              borderRadius="md"
              mb={2}
              color={useColorModeValue('gray.800', 'white')}
              fontWeight="medium"
              _hover={{
                bg: useColorModeValue('rgba(255, 255, 255, 0.4)', 'rgba(45, 55, 72, 0.4)'),
                boxShadow: "sm"
              }}
              _active={{
                bg: 'transparent', 
                boxShadow: 'none'
              }}
            >
              {colorMode === 'dark' ? 'Light mode' : 'Dark mode'}
            </MenuItem>
            <MenuItem
              icon={<FiLogOut fontSize="18px" />}
              onClick={handleLogout}
              color="ui.danger"
              fontWeight="bold"
              closeOnSelect={true}
              bg="transparent"
              borderRadius="md"
              _hover={{
                bg: useColorModeValue('rgba(255, 255, 255, 0.4)', 'rgba(45, 55, 72, 0.4)'),
                boxShadow: "sm"
              }}
            >
              Log out
            </MenuItem>
          </MenuList>
        </Menu>
      </Box>
    </>
  )
}

export default UserMenu
