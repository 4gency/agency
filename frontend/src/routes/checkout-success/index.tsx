import {
  Box,
  Button,
  Heading,
  Text,
  VStack,
  Icon,
  useColorModeValue,
} from "@chakra-ui/react"
import { useNavigate, createFileRoute } from "@tanstack/react-router"
import { FiArrowRight, FiCheckCircle } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"

// Constante para armazenar a chave do localStorage usada no onboarding
const ONBOARDING_COMPLETED_KEY_PREFIX = "user_onboarding_completed_"

// Componente de animação de sucesso
const SuccessAnimation = () => {
  return (
    <Box 
      width="100px" 
      height="100px" 
      borderRadius="full" 
      bg="green.100" 
      display="flex" 
      alignItems="center" 
      justifyContent="center"
      animation="pulse 2s infinite"
      sx={{
        "@keyframes pulse": {
          "0%": { transform: "scale(0.95)", boxShadow: "0 0 0 0 rgba(72, 187, 120, 0.7)" },
          "70%": { transform: "scale(1)", boxShadow: "0 0 0 10px rgba(72, 187, 120, 0)" },
          "100%": { transform: "scale(0.95)", boxShadow: "0 0 0 0 rgba(72, 187, 120, 0)" }
        }
      }}
    >
      <Icon as={FiCheckCircle} boxSize={14} color="green.500" />
    </Box>
  )
}

function CheckoutSuccess() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const bgColor = useColorModeValue("white", "gray.800")

  const handleCompleteSetup = () => {
    // Limpar o cache do onboarding para permitir que o usuário acesse novamente
    if (user) {
      const userOnboardingKey = `${ONBOARDING_COMPLETED_KEY_PREFIX}${user.id}`
      localStorage.removeItem(userOnboardingKey)
    }
    navigate({ to: "/onboarding" })
  }

  return (
    <Box py={16} px={4} textAlign="center">
      <VStack spacing={8} maxW="container.md" mx="auto">
        <SuccessAnimation />
        
        <Heading as="h1" size="xl" color="green.500">
          Payment Successful!
        </Heading>
        
        <Text fontSize="lg">
          Thank you for subscribing to our service. Your subscription is now active and you can start
          setting up your account to automate your job applications.
        </Text>
        
        <Box 
          border="1px" 
          borderColor="gray.200" 
          p={6} 
          borderRadius="md"
          boxShadow="md"
          bg={bgColor}
          w="full"
          maxW="md"
        >
          <VStack spacing={4}>
            <Box bg="green.50" p={3} borderRadius="full">
              <Icon as={FiCheckCircle} boxSize={12} color="green.500" />
            </Box>
            
            <Heading as="h2" size="md">
              Subscription Details
            </Heading>
            
            <Text fontSize="sm" color="gray.600">
              Your subscription is now active. You can now complete your account setup to start automating your job search.
            </Text>
            
            <Button 
              colorScheme="blue" 
              size="lg" 
              width="full"
              onClick={handleCompleteSetup}
              rightIcon={<FiArrowRight />}
            >
              Complete Account Setup
            </Button>
          </VStack>
        </Box>
        
        <Text fontSize="sm" color="gray.500">
          If you have any questions or need assistance, please contact our support team.
        </Text>
      </VStack>
    </Box>
  )
}

export default CheckoutSuccess

export const Route = createFileRoute("/checkout-success/")({
  component: CheckoutSuccess
}) 