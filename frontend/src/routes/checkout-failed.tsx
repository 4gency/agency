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
import { CloseIcon } from "@chakra-ui/icons"
import { AnimatedCard } from "../components/Common/AnimatedCard"
import { CircleIcon } from "../components/Common/CircleIcon"
import { useEffect, useState } from "react"
import { CheckoutService } from "../client/sdk.gen"
import useAuth from "../hooks/useAuth"
import useCustomToast from "../hooks/useCustomToast"

// Define search params
interface CheckoutFailedSearchParams {
  sessionId?: string
}

// Define error interface for proper typing
interface ApiError {
  response?: {
    status: number
  }
  status?: number
  name?: string
  message?: string
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
  const { sessionId } = Route.useSearch()
  const { user: authUser, isLoading } = useAuth()
  const showToast = useCustomToast()
  const navigate = useNavigate()
  const [shouldShowCard, setShouldShowCard] = useState(false)
  
  // Colors for theming
  const cardBgColor = useColorModeValue("white", "#2D3748")
  const buttonBgColor = useColorModeValue("black", "#00766c")
  const errorBgColor = useColorModeValue("red.500", "red.600")
  const textColor = useColorModeValue("gray.800", "white")

  useEffect(() => {
    if (!isLoading && !authUser) {
      navigate({ to: "/login" })
      return
    }

    if (!sessionId) {
      navigate({ to: "/" })
      return
    }

    const processFailedCheckout = async () => {
      try {
        // Process the failed checkout with stripeCancel
        await CheckoutService.stripeCancel({ sessionId })
        // If the stripeCancel call succeeds, show the failure card
        setShouldShowCard(true)
      } catch (error: unknown) {
        console.error("Error processing failed checkout:", error)
        
        // More robust error checking for 404 responses
        const apiError = error as ApiError
        
        // Check different possible ways a 404 might be represented
        const is404 = 
          (apiError.response && apiError.response.status === 404) || 
          apiError.status === 404 || 
          (apiError.message && apiError.message.includes("404")) ||
          (apiError.name && apiError.name.includes("NotFound"));
          
        if (is404) {
          console.log("404 error detected, redirecting to dashboard");
          // If 404, redirect directly to dashboard without showing any modal
          navigate({ to: "/" })
        } else {
          // For other errors, still show the failure screen to give feedback
          setShouldShowCard(true)
        }
      }
    }

    if (authUser && sessionId) {
      processFailedCheckout()
    }
  }, [authUser, sessionId, isLoading, navigate, showToast])

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
              icon={CloseIcon} 
              bgColor={errorBgColor}
              iconSize={4}
            />
            
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
        </AnimatedCard>
      </Box>
    </Container>
  )
} 