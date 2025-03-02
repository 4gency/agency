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
} from "@chakra-ui/react"
import { CheckIcon } from "@chakra-ui/icons"

interface NormalPricingCardProps {
  title: string
  price: number
  recurrence: string
  benefits: string[]
  buttonText: string
  buttonEnabled?: boolean
  buttonLink: string
  disabled?: boolean
  hasDiscount?: boolean
  priceWithoutDiscount?: number
  isLandingPage?: boolean
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
}) => {
  // Quando está na landing page, sempre usa o tema claro
  // Quando não está, respeita o tema do usuário
  const bgColor = isLandingPage ? "white" : useColorModeValue("white", "gray.800")
  const textColor = isLandingPage ? "gray.700" : useColorModeValue("gray.700", "white")
  const borderColor = isLandingPage ? "gray.200" : useColorModeValue("gray.200", "gray.700")
  const priceColor = isLandingPage ? "gray.700" : useColorModeValue("gray.700", "gray.200")
  const discountColor = isLandingPage ? "gray.400" : useColorModeValue("gray.400", "gray.500")
  const iconColor = isLandingPage ? "ui.main" : useColorModeValue("ui.main", "teal.300")

  return (
    <Box
      bg={bgColor}
      borderRadius="xl"
      borderWidth="1px"
      borderColor={borderColor}
      boxShadow={disabled ? "md" : "sm"}
      minW="350px"
      maxW="350px"
      height="auto"
      minH="400px"
      p={6}
      display="flex"
      flexDirection="column"
      justifyContent="space-between"
      filter={disabled ? "blur(5px)" : "none"}
      pointerEvents={disabled ? "none" : "auto"}
      transition="all 0.3s"
      _hover={!disabled ? { transform: "translateY(-5px)", boxShadow: "md" } : {}}
    >
      <VStack align="start" spacing={4} height="100%">
        <Text fontSize="2xl" fontWeight="bold" color={textColor}>
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
              <ListIcon as={CheckIcon} color={iconColor} boxSize={4} />
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

export default NormalPricingCard
