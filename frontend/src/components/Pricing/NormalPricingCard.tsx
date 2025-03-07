import { CheckIcon } from "@chakra-ui/icons"
import {
  Box,
  Button,
  List,
  ListIcon,
  ListItem,
  Text,
  VStack,
} from "@chakra-ui/react"
import type React from "react"
import { useNormalPricingCardTheme } from "./hooks/useNormalPricingCardTheme"

interface NormalPricingCardProps {
  title: string
  price: number
  recurrence: string
  benefits: string[]
  buttonText: string
  buttonEnabled?: boolean
  buttonLink?: string
  disabled?: boolean
  hasDiscount?: boolean
  priceWithoutDiscount?: number
  isLandingPage?: boolean
  onButtonClick?: () => void
}

const NormalPricingCard: React.FC<NormalPricingCardProps> = ({
  title,
  price,
  recurrence,
  benefits,
  buttonText,
  buttonEnabled,
  buttonLink,
  disabled = false,
  hasDiscount = false,
  priceWithoutDiscount,
  isLandingPage = false,
  onButtonClick,
}) => {
  const {
    bgColor,
    textColor,
    borderColor,
    priceColor,
    discountColor,
    iconColor,
  } = useNormalPricingCardTheme(isLandingPage)

  // Define the handler for click event
  const handleClick = buttonEnabled && onButtonClick ? onButtonClick : undefined

  // Check if button is in loading state
  const isLoading = buttonEnabled && buttonText === "Loading..."

  return (
    <Box
      bg={bgColor}
      borderRadius="xl"
      borderWidth="1px"
      borderColor={borderColor}
      boxShadow={disabled ? "md" : "sm"}
      width="100%"
      minW="320px"
      height="100%"
      maxHeight="450px"
      minHeight="390px"
      p={{ base: 5, md: 6 }}
      display="flex"
      flexDirection="column"
      justifyContent="space-between"
      filter={disabled ? "blur(5px)" : "none"}
      pointerEvents={disabled ? "none" : "auto"}
      transition="all 0.3s"
      mx="auto"
      _hover={
        !disabled ? { transform: "translateY(-5px)", boxShadow: "md" } : {}
      }
    >
      <VStack align="start" spacing={0.1} height="100%">
        <Text fontSize="2xl" fontWeight="bold" color={textColor}>
          {title}
        </Text>

        {hasDiscount && priceWithoutDiscount !== undefined && (
          <Text
            fontSize="md"
            color={discountColor}
            textDecoration="line-through"
          >
            ${priceWithoutDiscount.toFixed(2)}
          </Text>
        )}

        <Text fontSize="3xl" fontWeight="bold" color={priceColor}>
          ${price.toFixed(2)}/{recurrence}
        </Text>

        <List spacing={1} w="100%" mt={2} flex="1" overflow="auto" maxH="180px">
          {benefits.map((benefit, index) => (
            <ListItem key={index} display="flex" alignItems="flex-start" py={1}>
              <ListIcon as={CheckIcon} color={iconColor} boxSize={4} mt="5px" />
              <Text color={textColor}>{benefit}</Text>
            </ListItem>
          ))}
        </List>
      </VStack>

      {onButtonClick ? (
        <Button
          variant="primary"
          size="md"
          h="55px"
          w="100%"
          mt={6}
          isDisabled={!buttonEnabled}
          onClick={handleClick}
          isLoading={isLoading}
          loadingText="Loading..."
        >
          {buttonText}
        </Button>
      ) : (
        <Button
          as="a"
          href={buttonEnabled ? buttonLink : undefined}
          variant="primary"
          size="md"
          h="55px"
          w="100%"
          mt={6}
          isDisabled={!buttonEnabled}
        >
          {buttonText}
        </Button>
      )}
    </Box>
  )
}

export default NormalPricingCard
