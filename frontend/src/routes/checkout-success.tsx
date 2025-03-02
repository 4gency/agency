import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  Button,
  Container,
  Heading,
  Text,
  useColorModeValue,
  VStack,
  Box,
} from "@chakra-ui/react"
import { CheckIcon } from "@chakra-ui/icons"
import useAuth from "../hooks/useAuth"
import { AnimatedCard } from "../components/Common/AnimatedCard"
import { CircleIcon } from "../components/Common/CircleIcon"
import { useProcessSuccessCheckout } from "../hooks/useProcessSuccessCheckout"

// Define search params
interface CheckoutSuccessSearchParams {
  sessionId?: string
}

export const Route = createFileRoute("/checkout-success")({
  component: CheckoutSuccess,
  validateSearch: (search: Record<string, unknown>): CheckoutSuccessSearchParams => {
    return {
      sessionId: search.sessionId as string | undefined,
    }
  },
})

function CheckoutSuccess() {
  const { sessionId } = Route.useSearch()
  const { user: authUser, isLoading } = useAuth()
  const navigate = useNavigate()
  
  // Use our custom hook for checkout processing
  const { shouldShowCard } = useProcessSuccessCheckout({
    authUser,
    isLoading,
    sessionId
  })

  // Colors for theming
  const cardBgColor = useColorModeValue("white", "#2D3748")
  const buttonBgColor = useColorModeValue("black", "#00766c")
  const checkBgColor = useColorModeValue("green.500", "green.600")
  const textColor = useColorModeValue("gray.800", "white")

  if (!shouldShowCard) {
    return (
      <Container 
        maxW="100%" 
        height="100vh" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
      />
    )
  }

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
        zIndex={1} // Garante que a modal fique na frente do confete
      >
        <AnimatedCard
          width="100%"
          p={8}
          borderRadius="lg"
          bg={cardBgColor}
          boxShadow="lg"
        >
          <VStack spacing={4} align="flex-start">
            <CircleIcon 
              icon={CheckIcon} 
              bgColor={checkBgColor}
              iconSize={5}
            />
            
            <Heading as="h2" size="xl" color={textColor} fontWeight="bold">
              Payment succeeded!
            </Heading>
            
            <Box>
              <Text color={textColor} mb={2}>
                Thank you for processing your most recent payment.
              </Text>
              
              <Text color={textColor}>
                Your premium subscription will expire on June 2, 2025.
              </Text>
            </Box>
            
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
              Your dashboard
            </Button>
          </VStack>
        </AnimatedCard>
      </Box>
    </Container>
  )
} 