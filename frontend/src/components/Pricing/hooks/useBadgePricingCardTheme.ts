import { useColorModeValue } from "@chakra-ui/react"

export const useBadgePricingCardTheme = (isLandingPage: boolean) => {
  const bgColor = isLandingPage ? "white" : useColorModeValue("white", "gray.800")
  const textColor = isLandingPage ? "gray.700" : useColorModeValue("gray.700", "white")
  const borderColor = isLandingPage ? "teal.100" : useColorModeValue("teal.100", "teal.800")
  const priceColor = isLandingPage ? "teal.700" : useColorModeValue("teal.700", "teal.200")
  const discountColor = isLandingPage ? "gray.400" : useColorModeValue("gray.400", "gray.500")
  const highlightColor = isLandingPage ? "ui.main" : useColorModeValue("ui.main", "teal.300")
  const badgeBg = isLandingPage ? "ui.main" : useColorModeValue("ui.main", "teal.300")
  const badgeColor = isLandingPage ? "white" : useColorModeValue("white", "gray.800")

  return {
    bgColor,
    textColor,
    borderColor,
    priceColor,
    discountColor,
    highlightColor,
    badgeBg,
    badgeColor,
  }
} 