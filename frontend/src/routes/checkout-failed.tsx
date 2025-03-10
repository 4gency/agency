import { CloseIcon } from "@chakra-ui/icons"
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
import { useProcessFailedCheckout } from "../hooks/useProcessFailedCheckout"

// Define search params
interface CheckoutFailedSearchParams {
  sessionId?: string
}

export const Route = createFileRoute("/checkout-failed")({
  component: CheckoutFailed,
  validateSearch: (
    search: Record<string, unknown>,
  ): CheckoutFailedSearchParams => {
    return {
      sessionId: search.sessionId as string | undefined,
    }
  },
})

function CheckoutFailed() {
  const { sessionId } = Route.useSearch()
  const { user: authUser, isLoading } = useAuth()

  // Use our custom hook for failed checkout processing
  const { shouldShowCard } = useProcessFailedCheckout({
    authUser,
    isLoading,
    sessionId,
  })

  // Colors for theming
  const cardBgColor = useColorModeValue("white", "#2D3748")
  const buttonBgColor = useColorModeValue("black", "#00766c")
  const errorBgColor = useColorModeValue("red.500", "red.600")
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
      <Box width="100%" maxW="md" position="relative">
        <AnimatedCard
          width="100%"
          p={8}
          borderRadius="lg"
          bg={cardBgColor}
          boxShadow="lg"
        >
          <VStack spacing={4} align="flex-start">
            <CircleIcon icon={CloseIcon} bgColor={errorBgColor} iconSize={4} />

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
              onClick={() => {
                // Use window.location para forçar um recarregamento completo
                window.location.href = "/";
              }}
            >
              Return to Dashboard
            </Button>
          </VStack>
        </AnimatedCard>
      </Box>
    </Container>
  )
}
