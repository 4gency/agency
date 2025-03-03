import { Box, Flex, Icon, Text, useColorModeValue } from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate } from "@tanstack/react-router"
import { FiBriefcase, FiHome, FiSettings, FiUsers } from "react-icons/fi"
import { SlCalender } from "react-icons/sl"
import { HiOutlineDocumentText } from "react-icons/hi"
import { useEffect, useState } from "react"

import type { UserPublic } from "../../client"
import useSubscriptions from "../../hooks/userSubscriptions"

// Base items without subscriber-only items
const baseItems = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: SlCalender, title: "Pricing", path: "/pricing" },
  { icon: FiSettings, title: "Settings", path: "/settings" },
]

// Subscriber-only items
const jobPreferencesItem = { icon: FiBriefcase, title: "Job Preferences", path: "/job-preferences" }
const resumeItem = { icon: HiOutlineDocumentText, title: "Resume", path: "/resume" }

interface SidebarItemsProps {
  onClose?: () => void
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const queryClient = useQueryClient()
  const textColor = useColorModeValue("ui.main", "ui.light")
  const bgActive = useColorModeValue("#E2E8F0", "#4A5568")
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const { data: subscriptions } = useSubscriptions()
  const navigate = useNavigate()
  const [isSettingsActive, setIsSettingsActive] = useState(false)
  
  // Verificar se estamos na página de configurações quando o componente monta
  // e quando a URL muda
  useEffect(() => {
    const checkIfSettingsActive = () => {
      const path = window.location.pathname;
      setIsSettingsActive(path === "/settings" || path === "/settings/");
    };
    
    // Verificar na montagem do componente
    checkIfSettingsActive();
    
    // Adicionar um listener para mudanças de URL
    window.addEventListener('popstate', checkIfSettingsActive);
    
    return () => {
      window.removeEventListener('popstate', checkIfSettingsActive);
    };
  }, []);
  
  // Adicionar mais um listener para clicks
  useEffect(() => {
    const handleNavigationChanges = () => {
      const path = window.location.pathname;
      setIsSettingsActive(path === "/settings" || path === "/settings/");
    };
    
    // Verificar periodicamente se a URL mudou (solução mais robusta)
    const interval = setInterval(handleNavigationChanges, 300);
    
    return () => {
      clearInterval(interval);
    };
  }, []);
  
  // Check if user is a subscriber
  const isSubscriber = subscriptions && subscriptions.length > 0

  // Build the items array based on user state
  let items = [...baseItems]
  
  // Add subscriber-only items
  if (isSubscriber) {
    items = [
      baseItems[0], 
      jobPreferencesItem,
      resumeItem,
      ...baseItems.slice(1)
    ]
  }
  
  // Add admin link for superusers
  const finalItems = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items

  const handleClick = (path: string) => {
    if (onClose) onClose();
    
    // Para o item Settings, usamos navegação direta com window.location
    if (path === '/settings') {
      window.location.href = path;
      return;
    }
    
    // Para outros itens, usamos a navegação normal
    navigate({ to: path });
  };

  const listItems = finalItems.map(({ icon, title, path }) => {
    // Se for o item Settings, renderizamos de forma diferente
    if (path === '/settings') {
      return (
        <Flex
          as="div"
          w="100%"
          p={2}
          key={title}
          color={textColor}
          cursor="pointer"
          onClick={() => handleClick(path)}
          bg={isSettingsActive ? bgActive : undefined}
          borderRadius={isSettingsActive ? "12px" : undefined}
        >
          <Icon as={icon} alignSelf="center" />
          <Text ml={2}>{title}</Text>
        </Flex>
      );
    }
    
    // Para outros itens, usamos o componente Link
    return (
      <Flex
        as={Link}
        to={path}
        w="100%"
        p={2}
        key={title}
        color={textColor}
        activeProps={{
          style: {
            background: bgActive,
            borderRadius: "12px",
          },
        }}
        onClick={onClose}
      >
        <Icon as={icon} alignSelf="center" />
        <Text ml={2}>{title}</Text>
      </Flex>
    );
  });

  return (
    <>
      <Box>{listItems}</Box>
    </>
  )
}

export default SidebarItems
