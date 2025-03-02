import { useEffect, useState } from "react"
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
import { CheckIcon } from "@chakra-ui/icons"
import { CheckoutService } from "../client/sdk.gen"
import useAuth from "../hooks/useAuth"
import useCustomToast from "../hooks/useCustomToast"
import confetti from "canvas-confetti"

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
  const showToast = useCustomToast()
  const navigate = useNavigate()

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

  // Animation for card - animação mais rápida
  const [animate, setAnimate] = useState(false)

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
        
        // Start animations faster
        setTimeout(() => {
          setAnimate(true)
          triggerConfetti()
        }, 200) // Reduzido de 300ms para 200ms
      } catch (error) {
        console.error("Failed to process checkout:", error)
        navigate({ to: "/checkout-failed", search: { sessionId } })
        showToast("Payment Processing Failed", "We were unable to process your payment.", "error")
      }
    }

    if (authUser && sessionId) {
      processCheckout()
    }
  }, [authUser, sessionId, isLoading, navigate, showToast])

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
        <Card
          width="100%"
          p={8}
          borderRadius="lg"
          bg={cardBgColor}
          boxShadow="lg"
          transform={animate ? "scale(1)" : "scale(0.95)"}
          opacity={animate ? 1 : 0}
          transition="all 0.5s ease-in-out" // Animação mais rápida (0.5s em vez de 1s)
        >
          <VStack spacing={4} align="flex-start"> {/* Alinhamento à esquerda e espaçamento reduzido */}
            <Flex
              bg={checkBgColor}
              w="45px" // Reduzido de 60px para 45px
              h="45px" // Reduzido de 60px para 45px
              borderRadius="full"
              justifyContent="center"
              alignItems="center"
              mb={1}
            >
              <Icon as={CheckIcon} w={5} h={5} color="white" /> {/* Reduzido de w={6} h={6} para w={5} h={5} */}
            </Flex>
            
            <Heading as="h2" size="xl" color={textColor} fontWeight="bold">
              Payment succeeded!
            </Heading>
            
            <Box>
              <Text color={textColor} mb={2}> {/* Espaçamento reduzido entre os textos */}
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
        </Card>
      </Box>
    </Container>
  )
} 