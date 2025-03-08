import { useColorModeValue } from "@chakra-ui/react"

export const useBadgePricingCardTheme = (isLandingPage: boolean) => {
  const bgColor = isLandingPage
    ? "white"
    : useColorModeValue("white", "gray.800")
  const textColor = isLandingPage
    ? "gray.700"
    : useColorModeValue("gray.700", "white")
  const borderColor = isLandingPage
    ? "teal.100"
    : useColorModeValue("#99D5CF", "teal.900")
  const priceColor = isLandingPage
    ? "ui.main"
    : useColorModeValue("ui.main", "ui.main")
  const discountColor = isLandingPage
    ? "gray.400"
    : useColorModeValue("gray.400", "gray.500")
  const highlightColor = isLandingPage
    ? "ui.main"
    : useColorModeValue("ui.main", "ui.main")
  const badgeBg = isLandingPage
    ? "ui.main"
    : useColorModeValue("ui.main", "teal")
  const badgeColor = isLandingPage
    ? "white"
    : useColorModeValue("white", "white")

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
