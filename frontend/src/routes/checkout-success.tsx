import { CheckIcon } from "@chakra-ui/icons"
import {
  Box,
  Button,
  Container,
  Heading,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { AnimatedCard } from "../components/Common/AnimatedCard"
import { CircleIcon } from "../components/Common/CircleIcon"
import useAuth from "../hooks/useAuth"
import { useProcessSuccessCheckout } from "../hooks/useProcessSuccessCheckout"

// Define search params
interface CheckoutSuccessSearchParams {
  sessionId?: string
}

export const Route = createFileRoute("/checkout-success")({
  component: CheckoutSuccess,
  validateSearch: (
    search: Record<string, unknown>,
  ): CheckoutSuccessSearchParams => {
    return {
      sessionId: search.sessionId as string | undefined,
    }
  },
})

function CheckoutSuccess() {
  const { sessionId } = Route.useSearch()
  const { user: authUser, isLoading } = useAuth()

  // Use our custom hook for checkout processing
  const { shouldShowCard, successMessage } = useProcessSuccessCheckout({
    authUser,
    isLoading,
    sessionId,
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
            <CircleIcon icon={CheckIcon} bgColor={checkBgColor} iconSize={5} />

            <Heading as="h2" size="xl" color={textColor} fontWeight="bold">
              Payment succeeded!
            </Heading>

            <Box>
              <Text color={textColor} mb={2}>
                Thank you for processing your most recent payment.
              </Text>

              <Text color={textColor}>{successMessage}</Text>
            </Box>

            <Button
              mt={4}
              bg={buttonBgColor}
              color="white"
              fontWeight="bold"
              _hover={{
                opacity: 0.9,
              }}
              onClick={() => {
                // Redirect to onboarding flow instead of dashboard
                window.location.href = "/onboarding";
              }}
            >
              Complete Account Setup
            </Button>
          </VStack>
        </AnimatedCard>
      </Box>
    </Container>
  )
}
