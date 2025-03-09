import { CheckIcon } from "@chakra-ui/icons"
import {
  Badge,
  Box,
  Button,
  List,
  ListIcon,
  ListItem,
  Text,
  VStack,
  useBreakpointValue,
} from "@chakra-ui/react"
import type React from "react"
import { useBadgePricingCardTheme } from "./hooks/useBadgePricingCardTheme"

interface BadgePricingCardProps {
  title: string
  badgeText: string
  price: number
  benefits: string[]
  buttonText: string
  buttonEnabled?: boolean
  buttonLink?: string
  hasDiscount?: boolean
  priceWithoutDiscount?: number
  recurrence: string
  isLandingPage?: boolean
  onButtonClick?: () => void
}

const BadgePricingCard: React.FC<BadgePricingCardProps> = ({
  title,
  badgeText,
  price,
  benefits,
  buttonText,
  buttonEnabled,
  buttonLink,
  hasDiscount = false,
  priceWithoutDiscount,
  recurrence,
  isLandingPage = false,
  onButtonClick,
}) => {
  const {
    bgColor,
    textColor,
    borderColor,
    priceColor,
    discountColor,
    highlightColor,
    badgeBg,
    badgeColor,
  } = useBadgePricingCardTheme(isLandingPage)

  const handleClick = buttonEnabled && onButtonClick ? onButtonClick : undefined

  // Check if button is in loading state
  const isLoading = buttonEnabled && buttonText === "Loading..."

  // Responsividade extrema para a largura do card
  const minWidth = useBreakpointValue({
    base: "240px",
    xs: "260px",
    sm: "280px",
    md: "320px",
  })

  // Padding responsivo para dispositivos muito pequenos
  const horizontalPadding = useBreakpointValue({
    base: 3,
    sm: 4,
    md: 6,
  })

  // Ajustar tamanho de fonte para dispositivos muito pequenos
  const titleFontSize = useBreakpointValue({ base: "xl", sm: "2xl" })
  const priceFontSize = useBreakpointValue({ base: "2xl", sm: "3xl" })
  const benefitFontSize = useBreakpointValue({ base: "sm", sm: "md" })
  const badgeFontSize = useBreakpointValue({ base: "xs", sm: "sm" })

  return (
    <Box
      bg={bgColor}
      borderRadius="xl"
      borderWidth="2px"
      borderColor={borderColor}
      boxShadow="md"
      width="100%"
      minW="320px"
      height="100%"
      maxHeight="450px"
      minHeight="390px"
      p={{ base: horizontalPadding, md: 6 }}
      display="flex"
      flexDirection="column"
      justifyContent="space-between"
      position="relative"
      transition="all 0.3s"
      mx="auto"
      _hover={
        { transform: "translateY(-5px)", boxShadow: "lg" }
      }
    >
      {/* Badge */}
      <Badge
        position="absolute"
        top="-3"
        right="-3"
        bg={badgeBg}
        color={badgeColor}
        px={3.5}
        py={4.5}
        borderRadius="md"
        fontSize={badgeFontSize}
        fontWeight="bold"
        boxShadow="sm"
      >
        {badgeText}
      </Badge>

      <VStack align="start" spacing={0.1} height="100%">
        <Text fontSize={titleFontSize} fontWeight="bold" color={highlightColor}>
          {title}
        </Text>

        {hasDiscount && priceWithoutDiscount !== undefined && (
          <Text
            fontSize={benefitFontSize}
            color={discountColor}
            textDecoration="line-through"
          >
            ${priceWithoutDiscount.toFixed(2)}
          </Text>
        )}

        <Text fontSize={priceFontSize} fontWeight="bold" color={priceColor}>
          ${price.toFixed(2)}/{recurrence}
        </Text>

        <List spacing={1} w="100%" mt={2} flex="1" overflow="auto" maxH="180px">
          {benefits.map((benefit, index) => (
            <ListItem key={index} display="flex" alignItems="flex-start" py={1}>
              <ListIcon
                as={CheckIcon}
                color={highlightColor}
                boxSize={4}
                mt="5px"
              />
              <Text color={textColor} fontSize={benefitFontSize}>
                {benefit}
              </Text>
            </ListItem>
          ))}
        </List>
      </VStack>

      {onButtonClick ? (
        <Button
          variant="primary"
          size="md"
          h={{ base: "45px", sm: "55px" }}
          w="100%"
          mt={4}
          isDisabled={!buttonEnabled}
          onClick={handleClick}
          isLoading={isLoading}
          loadingText="Loading..."
          fontSize={benefitFontSize}
        >
          {buttonText}
        </Button>
      ) : (
        <Button
          as="a"
          href={buttonEnabled ? buttonLink : undefined}
          variant="primary"
          size="md"
          h={{ base: "45px", sm: "55px" }}
          w="100%"
          mt={4}
          isDisabled={!buttonEnabled}
          fontSize={benefitFontSize}
        >
          {buttonText}
        </Button>
      )}
    </Box>
  )
}

export default BadgePricingCard
