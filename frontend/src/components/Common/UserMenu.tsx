import {
  Box,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  useColorMode,
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
  
  // Alterna o tema sem fechar o menu
  const handleToggleColorMode = (e: React.MouseEvent) => {
    // Impede o comportamento padrão que fecharia o menu
    e.stopPropagation();
    toggleColorMode();
  }

  return (
    <>
      {/* Desktop */}
      <Box
        display={{ base: "none", md: "block" }}
        position="fixed"
        top={4}
        right={4}
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
          <MenuList>
            <MenuItem 
              icon={<FiUser fontSize="18px" />} 
              onClick={handleNavigateToSettings}
              closeOnSelect={true}
            >
              My profile
            </MenuItem>
            <MenuItem
              icon={colorMode === 'dark' ? <FiSun fontSize="18px" /> : <FiMoon fontSize="18px" />}
              onClick={handleToggleColorMode}
              closeOnSelect={false}
            >
              {colorMode === 'dark' ? 'Light mode' : 'Dark mode'}
            </MenuItem>
            <MenuItem
              icon={<FiLogOut fontSize="18px" />}
              onClick={handleLogout}
              color="ui.danger"
              fontWeight="bold"
              closeOnSelect={true}
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
