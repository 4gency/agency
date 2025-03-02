import type React from "react"
import {
  Box,
  Text,
  VStack,
  List,
  ListItem,
  ListIcon,
  Button,
  Badge,
} from "@chakra-ui/react"
import { CheckIcon } from "@chakra-ui/icons"
import { useBadgePricingCardTheme } from "./hooks/useBadgePricingCardTheme"

interface BadgePricingCardProps {
  title: string
  badgeText: string
  price: number
  benefits: string[]
  buttonText: string
  buttonEnabled?: boolean
  buttonLink: string
  hasDiscount?: boolean
  priceWithoutDiscount?: number
  recurrence: string
  isLandingPage?: boolean
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
      p={{ base: 5, md: 6 }}
      display="flex"
      flexDirection="column"
      justifyContent="space-between"
      position="relative"
      transition="all 0.3s"
      mx="auto"
      _hover={{ transform: "translateY(-5px)", boxShadow: "lg" }}
    >
      {/* Badge */}
      <Badge
        position="absolute"
        top="-3"
        right="-3"
        bg={badgeBg}
        color={badgeColor}
        px={3}
        py={1}
        borderRadius="md"
        fontSize="sm"
        fontWeight="bold"
        boxShadow="sm"
      >
        {badgeText}
      </Badge>

      <VStack align="start" spacing={0.1} height="100%">
        <Text fontSize="2xl" fontWeight="bold" color={highlightColor}>
          {title}
        </Text>
        
        {hasDiscount && priceWithoutDiscount !== undefined && (
          <Text fontSize="md" color={discountColor} textDecoration="line-through">
            ${priceWithoutDiscount.toFixed(2)}
          </Text>
        )}
        
        <Text fontSize="3xl" fontWeight="bold" color={priceColor}>
          ${price.toFixed(2)}/{recurrence}
        </Text>
        
        <List spacing={1} w="100%" mt={2} flex="1" overflow="auto" maxH="180px">
          {benefits.map((benefit, index) => (
            <ListItem key={index} display="flex" alignItems="flex-start" py={1}>
              <ListIcon as={CheckIcon} color={highlightColor} boxSize={4} mt="5px" />
              <Text color={textColor}>
                {benefit}
              </Text>
            </ListItem>
          ))}
        </List>
      </VStack>
      
      <Button
        as="a"
        href={buttonEnabled ? buttonLink : undefined}
        onClick={buttonEnabled ? undefined : (e) => e.preventDefault()}
        variant="primary"
        size="md"
        h="55px"
        w="100%"
        mt={6}
        isDisabled={!buttonEnabled}
      >
        {buttonText}
      </Button>
    </Box>
  )
}

export default BadgePricingCard
