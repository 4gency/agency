import { Box, Flex, Icon, Text, useColorModeValue } from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { Link, useMatchRoute, useNavigate, useRouterState } from "@tanstack/react-router"
import { useEffect, useState, useRef } from "react"
import { FiBriefcase, FiHome, FiSettings, FiUsers } from "react-icons/fi"
import { HiOutlineDocumentText } from "react-icons/hi"
import { SlCalender } from "react-icons/sl"

import type { UserPublic } from "../../client"
import useSubscriptions from "../../hooks/userSubscriptions"

// Tipo para os itens do menu
type MenuItem = {
  icon: any
  title: string
  path: string
}

// Base items without subscriber-only items
const baseItems: MenuItem[] = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: SlCalender, title: "Pricing", path: "/pricing" },
  { icon: FiSettings, title: "Settings", path: "/settings" },
]

// Subscriber-only items
const jobPreferencesItem: MenuItem = {
  icon: FiBriefcase,
  title: "Job Preferences",
  path: "/job-preferences",
}
const resumeItem: MenuItem = {
  icon: HiOutlineDocumentText,
  title: "Resume",
  path: "/resume",
}

interface SidebarItemsProps {
  onClose?: () => void
}

// Chave para armazenar os itens do menu na sessionStorage
const MENU_ITEMS_CACHE_KEY = 'sidebarMenuItems'
const USER_SUBSCRIBER_STATUS_KEY = 'userIsSubscriber'

// Função para carregar os itens do menu a partir do cache
const loadMenuItemsFromCache = (): MenuItem[] | null => {
  try {
    const cachedItems = sessionStorage.getItem(MENU_ITEMS_CACHE_KEY)
    if (cachedItems) {
      // Precisamos reconstruir os objetos de ícones, pois eles não são serializáveis
      const parsedItems = JSON.parse(cachedItems) as Array<Omit<MenuItem, 'icon'> & { iconName: string }>
      
      // Mapa para converter nomes de ícones de volta para componentes
      const iconMap: Record<string, any> = {
        FiHome,
        FiBriefcase,
        FiSettings,
        FiUsers,
        SlCalender,
        HiOutlineDocumentText
      }
      
      // Reconstruir os itens com os ícones corretos
      return parsedItems.map(item => ({
        ...item,
        icon: iconMap[item.iconName]
      }))
    }
  } catch (error) {
    console.error("Error loading menu items from cache:", error)
  }
  return null
}

// Função para salvar os itens do menu no cache
const saveMenuItemsToCache = (items: MenuItem[]) => {
  try {
    // Precisamos transformar os ícones em strings antes de salvar
    const serializableItems = items.map(item => {
      // Obter o nome do ícone
      let iconName = ''
      if (item.icon === FiHome) iconName = 'FiHome'
      else if (item.icon === FiBriefcase) iconName = 'FiBriefcase'
      else if (item.icon === FiSettings) iconName = 'FiSettings'
      else if (item.icon === FiUsers) iconName = 'FiUsers'
      else if (item.icon === SlCalender) iconName = 'SlCalender'
      else if (item.icon === HiOutlineDocumentText) iconName = 'HiOutlineDocumentText'
      
      return {
        title: item.title,
        path: item.path,
        iconName
      }
    })
    
    sessionStorage.setItem(MENU_ITEMS_CACHE_KEY, JSON.stringify(serializableItems))
  } catch (error) {
    console.error("Error saving menu items to cache:", error)
  }
}

// Função para salvar o status de assinante do usuário
const saveSubscriberStatusToCache = (isSubscriber: boolean) => {
  try {
    sessionStorage.setItem(USER_SUBSCRIBER_STATUS_KEY, String(isSubscriber))
  } catch (error) {
    console.error("Error saving subscriber status to cache:", error)
  }
}

// Função para carregar o status de assinante do usuário
const loadSubscriberStatusFromCache = (): boolean | null => {
  try {
    const status = sessionStorage.getItem(USER_SUBSCRIBER_STATUS_KEY)
    if (status !== null) {
      return status === 'true'
    }
  } catch (error) {
    console.error("Error loading subscriber status from cache:", error)
  }
  return null
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const queryClient = useQueryClient()
  const textColor = useColorModeValue("gray.800", "white")
  const bgActive = useColorModeValue(
    "rgba(255, 255, 255, 0.7)",
    "rgba(66, 75, 95, 0.5)",
  )
  const hoverBg = useColorModeValue(
    "rgba(255, 255, 255, 0.5)",
    "rgba(45, 55, 72, 0.4)",
  )
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const { data: subscriptions, isLoading: isLoadingSubscriptions } = useSubscriptions()
  const navigate = useNavigate()
  const matchRoute = useMatchRoute()
  
  // Referência para controlar se já verificamos a rota anterior
  const hasCheckedPrevRoute = useRef(false)
  // Obter o estado do router para verificar a rota anterior
  const routerState = useRouterState()

  // Estado para armazenar os itens do menu
  const [menuItems, setMenuItems] = useState<MenuItem[]>(() => {
    // Tentar carregar do cache inicialmente
    return loadMenuItemsFromCache() || baseItems
  })

  // Verificar se estamos na página de configurações usando o router
  const isSettingsActive =
    matchRoute({
      to: "/settings",
      fuzzy: false,
    }) ||
    matchRoute({
      to: "/settings/",
      fuzzy: false,
    })

  // Efeito para verificar se o usuário veio de uma página de checkout
  useEffect(() => {
    // Verificamos apenas uma vez ao montar o componente
    if (hasCheckedPrevRoute.current) return
    
    // Obter o histórico de navegação do browser
    const currentPath = window.location.pathname
    const fromCheckout = 
      sessionStorage.getItem('came_from_checkout') === 'true' || 
      document.referrer.includes('checkout-success') || 
      document.referrer.includes('checkout-failed')
    
    // Se o usuário veio de uma página de checkout e está na dashboard
    if (fromCheckout && (currentPath === '/' || currentPath === '/dashboard')) {
      console.log('User came from checkout page, invalidating subscriptions cache')
      
      // Limpar os caches de itens do menu e status de assinante
      sessionStorage.removeItem(MENU_ITEMS_CACHE_KEY)
      sessionStorage.removeItem(USER_SUBSCRIBER_STATUS_KEY)
      
      // Invalidar a consulta de assinaturas para forçar uma nova consulta
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      
      // Limpar o flag de checkout
      sessionStorage.removeItem('came_from_checkout')
    }
    
    hasCheckedPrevRoute.current = true
  }, [queryClient])

  // Atualizar os itens do menu quando os dados de assinatura mudam
  useEffect(() => {
    if (isLoadingSubscriptions) return
    
    // Check if user is a subscriber
    const isSubscriber = subscriptions && subscriptions.length > 0
    
    // Verificar se o status de assinante mudou
    const cachedStatus = loadSubscriberStatusFromCache()
    
    // Se o status não mudou e temos itens em cache, não fazemos nada
    if (cachedStatus === isSubscriber && loadMenuItemsFromCache() !== null) {
      return
    }
    
    // Se o status mudou ou não havia cache, atualizamos os itens
    // Build the items array based on user state
    let items = [...baseItems]

    // Add subscriber-only items
    if (isSubscriber) {
      items = [
        baseItems[0],
        jobPreferencesItem,
        resumeItem,
        ...baseItems.slice(1),
      ]
    }

    // Add admin link for superusers
    const finalItems = currentUser?.is_superuser
      ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
      : items
    
    // Atualizar o estado local
    setMenuItems(finalItems)
    
    // Salvar no cache
    saveMenuItemsToCache(finalItems)
    saveSubscriberStatusToCache(isSubscriber || false) // Garantir que não seja undefined
    
  }, [isLoadingSubscriptions, subscriptions, currentUser])

  const handleClick = (path: string) => {
    if (onClose) {
      onClose()
    }

    // Para o item Settings, usamos navegação direta com window.location
    if (path === "/settings") {
      window.location.href = path
      return
    }

    // Para outros itens, usamos a navegação normal
    navigate({ to: path })
  }

  const listItems = menuItems.map(({ icon, title, path }) => {
    // Se for o item Settings, renderizamos de forma diferente
    if (path === "/settings") {
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
          borderRadius="md"
          mb={2}
          fontWeight="medium"
          _hover={{ bg: hoverBg }}
          transition="all 0.2s"
        >
          <Icon as={icon} alignSelf="center" />
          <Text ml={2}>{title}</Text>
        </Flex>
      )
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
        borderRadius="md"
        mb={2}
        fontWeight="medium"
        transition="all 0.2s"
        _hover={{ bg: hoverBg }}
        activeProps={{
          style: {
            background: bgActive,
            borderRadius: "8px",
            boxShadow: "sm",
          },
        }}
        onClick={onClose}
      >
        <Icon as={icon} alignSelf="center" />
        <Text ml={2}>{title}</Text>
      </Flex>
    )
  })

  return <Box mb={4}>{listItems}</Box>
}

export default SidebarItems
