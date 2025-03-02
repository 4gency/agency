import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  Button,
  Card,
  Container,
  Flex,
  Heading,
  Icon,
  Text,
  useColorModeValue,
  VStack,
  Box,
} from "@chakra-ui/react"
import { CloseIcon } from "@chakra-ui/icons"
import { useState, useEffect } from "react"

// Define search params
interface CheckoutFailedSearchParams {
  sessionId?: string
}

export const Route = createFileRoute("/checkout-failed")({
  component: CheckoutFailed,
  validateSearch: (search: Record<string, unknown>): CheckoutFailedSearchParams => {
    return {
      sessionId: search.sessionId as string | undefined,
    }
  },
})

function CheckoutFailed() {
  const navigate = useNavigate()
  
  // Colors for theming
  const cardBgColor = useColorModeValue("white", "#2D3748")
  const buttonBgColor = useColorModeValue("black", "#00766c")
  const errorBgColor = useColorModeValue("red.500", "red.600")
  const textColor = useColorModeValue("gray.800", "white")

  // Animation for card
  const [animate, setAnimate] = useState(false)

  useEffect(() => {
    // Start animation after a short delay
    setTimeout(() => {
      setAnimate(true)
    }, 200)
  }, [])

  return (
    <Container 
      maxW="100%" 
      height="100vh" 
      display="flex" 
      alignItems="center" 
      justifyContent="center"
    >
      <Box
        width="100%"
        maxW="md"
        position="relative"
      >
        <Card
          width="100%"
          p={8}
          borderRadius="lg"
          bg={cardBgColor}
          boxShadow="lg"
          transform={animate ? "scale(1)" : "scale(0.95)"}
          opacity={animate ? 1 : 0}
          transition="all 0.5s ease-in-out"
        >
          <VStack spacing={4} align="flex-start">
            <Flex
              bg={errorBgColor}
              w="45px"
              h="45px"
              borderRadius="full"
              justifyContent="center"
              alignItems="center"
              mb={1}
            >
              <Icon as={CloseIcon} w={4} h={4} color="white" />
            </Flex>
            
            <Heading as="h2" size="xl" color={textColor} fontWeight="bold">
              Payment Failed
            </Heading>
            
            <Text color={textColor}>
              Unfortunately, we were unable to activate your subscription.
            </Text>
            
            <Button
              mt={4}
              bg={buttonBgColor}
              color="white"
              fontWeight="bold"
              _hover={{
                opacity: 0.9,
              }}
              onClick={() => navigate({ to: "/" })}
            >
              Return to Dashboard
            </Button>
          </VStack>
        </Card>
      </Box>
    </Container>
  )
} 