import { Box, Flex, Icon, Text, useColorModeValue } from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { FiBriefcase, FiHome, FiSettings, FiUsers } from "react-icons/fi"
import { SlCalender } from "react-icons/sl"
import { HiOutlineDocumentText } from "react-icons/hi"

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

  const listItems = finalItems.map(({ icon, title, path }) => (
    <Flex
      as={Link}
      to={path}
      w="100%"
      p={2}
      key={title}
      activeProps={{
        style: {
          background: bgActive,
          borderRadius: "12px",
        },
      }}
      color={textColor}
      onClick={onClose}
    >
      <Icon as={icon} alignSelf="center" />
      <Text ml={2}>{title}</Text>
    </Flex>
  ))

  return (
    <>
      <Box>{listItems}</Box>
    </>
  )
}

export default SidebarItems
