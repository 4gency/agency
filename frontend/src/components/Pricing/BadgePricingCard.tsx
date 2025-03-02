import type React from "react"
import {
  Box,
  Text,
  VStack,
  List,
  ListItem,
  ListIcon,
  Button,
  useColorModeValue,
  Badge,
} from "@chakra-ui/react"
import { CheckIcon } from "@chakra-ui/icons"

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
  // Quando está na landing page, sempre usa o tema claro
  // Quando não está, respeita o tema do usuário
  const bgColor = isLandingPage ? "white" : useColorModeValue("white", "gray.800")
  const textColor = isLandingPage ? "gray.700" : useColorModeValue("gray.700", "white")
  const borderColor = isLandingPage ? "teal.100" : useColorModeValue("teal.100", "teal.800")
  const priceColor = isLandingPage ? "teal.700" : useColorModeValue("teal.700", "teal.200")
  const discountColor = isLandingPage ? "gray.400" : useColorModeValue("gray.400", "gray.500")
  const highlightColor = isLandingPage ? "ui.main" : useColorModeValue("ui.main", "teal.300")
  const badgeBg = isLandingPage ? "ui.main" : useColorModeValue("ui.main", "teal.300")
  const badgeColor = isLandingPage ? "white" : useColorModeValue("white", "gray.800")

  return (
    <Box
      bg={bgColor}
      borderRadius="xl"
      borderWidth="2px"
      borderColor={borderColor}
      boxShadow="md"
      width="300px"
      minW="350px"
      maxW="350px"
      height="auto"
      minH="400px"
      p={6}
      display="flex"
      flexDirection="column"
      justifyContent="space-between"
      position="relative"
      transition="all 0.3s"
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

      <VStack align="start" spacing={4} height="100%">
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
        
        <List spacing={4} w="100%" mt={2} flex="1">
          {benefits.map((benefit, index) => (
            <ListItem key={index} display="flex" alignItems="center">
              <ListIcon as={CheckIcon} color={highlightColor} boxSize={4} />
              <Text color={textColor}>{benefit}</Text>
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
