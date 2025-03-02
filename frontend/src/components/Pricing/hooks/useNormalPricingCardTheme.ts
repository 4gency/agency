import { useColorModeValue } from "@chakra-ui/react"

export const useNormalPricingCardTheme = (isLandingPage: boolean) => {
  const bgColor = isLandingPage ? "white" : useColorModeValue("white", "gray.800")
  const textColor = isLandingPage ? "gray.700" : useColorModeValue("gray.700", "white")
  const borderColor = isLandingPage ? "gray.200" : useColorModeValue("gray.200", "gray.700")
  const priceColor = isLandingPage ? "gray.700" : useColorModeValue("gray.700", "gray.200")
  const discountColor = isLandingPage ? "gray.400" : useColorModeValue("gray.400", "gray.500")
  const iconColor = isLandingPage ? "ui.main" : useColorModeValue("ui.main", "teal.300")

  return {
    bgColor,
    textColor,
    borderColor,
    priceColor,
    discountColor,
    iconColor,
  }
} 