import { useEffect, useState } from "react"
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
import { CheckoutService } from "../client/sdk.gen"
import useAuth from "../hooks/useAuth"
import useCustomToast from "../hooks/useCustomToast"
import confetti from "canvas-confetti"
import { AnimatedCard } from "../components/Common/AnimatedCard"
import { CircleIcon } from "../components/Common/CircleIcon"

// Define search params
interface CheckoutSuccessSearchParams {
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
  const showToast = useCustomToast()
  const navigate = useNavigate()
  const [shouldShowCard, setShouldShowCard] = useState(false)

  // Colors for theming - usar uma cor mais escura para o tema escuro
  const cardBgColor = useColorModeValue("white", "#2D3748") // Cores mais escuras para o tema escuro
  const buttonBgColor = useColorModeValue("black", "#00766c")
  const checkBgColor = useColorModeValue("green.500", "green.600")
  const textColor = useColorModeValue("gray.800", "white")

  // Confetti effect - maior e centralizado
  const triggerConfetti = () => {
    const duration = 1000
    const animationEnd = Date.now() + duration
    const defaults = { 
      startVelocity: 40, 
      spread: 100, 
      ticks: 80, 
      zIndex: -1, // Coloca o confete atrás do modal
      particleCount: 80,
      scalar: 1.5, // Faz os confetes maiores
    }

    const interval = setInterval(() => {
      const timeLeft = animationEnd - Date.now()

      if (timeLeft <= 0) {
        return clearInterval(interval)
      }

      const particleCount = 50 * (timeLeft / duration)
      
      // Confetes emanando do centro
      confetti({
        ...defaults,
        particleCount,
        origin: { x: 0.5, y: 0.5 }, // Centro da tela
        gravity: 0.8, // Um pouco mais de gravidade para que os confetes não subam muito
        disableForReducedMotion: true
      })
    }, 200)
  }

  useEffect(() => {
    if (!isLoading && !authUser) {
      navigate({ to: "/login" })
      return
    }

    if (!sessionId) {
      navigate({ to: "/" })
      showToast("Missing Information", "Session ID is required for checkout verification", "error")
      return
    }

    const processCheckout = async () => {
      try {
        // Call the API with sessionId
        await CheckoutService.stripeSuccess({ sessionId })
        
        // Trigger confetti and show card
        triggerConfetti()
        setShouldShowCard(true)
      } catch (error: unknown) {
        console.error("Failed to process checkout:", error)
        
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
          // For other errors, redirect to the failed page
          navigate({ to: "/checkout-failed", search: { sessionId } })
          showToast("Payment Processing Failed", "We were unable to process your payment.", "error")
        }
      }
    }

    if (authUser && sessionId) {
      processCheckout()
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