import { createFileRoute, redirect } from "@tanstack/react-router"
import {
  Box,
  Container,
  Heading,
  Text,
  Spinner,
  Flex,
  Grid,
  GridItem,
  Badge,
  Button,
  Card,
  CardHeader,
  CardBody,
  Divider,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useColorModeValue,
  useToast,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useDisclosure,
} from "@chakra-ui/react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { UsersService } from "../../../../client"
import { useRef, useEffect } from "react"
import { isLoggedIn } from "../../../../hooks/useAuth"

// Definindo cores personalizadas para botões - serão usadas diretamente
const TEAL_COLOR = "#009688";
const TEAL_HOVER = "#00897B";
const TEAL_ACTIVE = "#00796B";
const RED_COLOR = "#F44336";
const RED_HOVER = "#E53935";
const RED_ACTIVE = "#D32F2F";

// Simplificando a rota para garantir que funcione corretamente
export const Route = createFileRoute("/_layout/settings/subscription/$subscriptionId")({
  component: SubscriptionDetailPage,
  beforeLoad: () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
    console.log("Carregando rota de detalhes da assinatura");
  },
})

function SubscriptionDetailPage() {
  // Capturando o parâmetro da URL diretamente para debug
  const urlParts = window.location.pathname.split("/")
  const subscriptionIdFromUrl = urlParts[urlParts.length - 1]
  
  // Também tentando obter o param da rota normal
  const params = Route.useParams()
  const subscriptionId = params.subscriptionId || subscriptionIdFromUrl
  
  // Logging para debug
  useEffect(() => {
    console.log("URL completa:", window.location.href)
    console.log("Path da URL:", window.location.pathname)
    console.log("Partes da URL:", urlParts)
    console.log("ID da assinatura da URL:", subscriptionIdFromUrl)
    console.log("Params da rota:", params)
    console.log("ID da assinatura usado:", subscriptionId)
  }, [])

  // Resto do componente
  const color = useColorModeValue("inherit", "ui.light")
  const bgCard = useColorModeValue("white", "gray.700")
  const toast = useToast()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const cancelRef = useRef<HTMLButtonElement>(null)
  const queryClient = useQueryClient()
  
  // Determinando se estamos no modo escuro
  const isDarkMode = !useColorModeValue(true, false);

  // Query subscription details
  const {
    data: subscription,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["subscription", subscriptionId],
    queryFn: () => UsersService.getUserSubscription({ subscriptionId }),
    enabled: !!subscriptionId, // só executa se tiver um ID
  })

  // Mutations for cancel/reactivate subscription
  const cancelMutation = useMutation({
    mutationFn: () => UsersService.cancelUserSubscription({ subscriptionId }),
    onSuccess: () => {
      toast({
        title: "Subscription cancelled",
        description: "Your subscription has been cancelled successfully",
        status: "success",
        duration: 5000,
        isClosable: true,
      })
      queryClient.invalidateQueries({ queryKey: ["subscription", subscriptionId] })
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] })
      onClose()
    },
    onError: (err: any) => {
      toast({
        title: "Error",
        description: err.message || "Failed to cancel subscription",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
      onClose()
    },
  })

  const reactivateMutation = useMutation({
    mutationFn: () => UsersService.reactivateUserSubscription({ subscriptionId }),
    onSuccess: () => {
      toast({
        title: "Subscription reactivated",
        description: "Your subscription has been reactivated successfully",
        status: "success",
        duration: 5000,
        isClosable: true,
      })
      queryClient.invalidateQueries({ queryKey: ["subscription", subscriptionId] })
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] })
    },
    onError: (err: any) => {
      toast({
        title: "Error",
        description: err.message || "Failed to reactivate subscription",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    },
  })

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  // Format currency
  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
    }).format(amount)
  }
  
  // Handler para voltar
  const handleBackToSettings = () => {
    window.location.href = "/settings"
  }

  if (!subscriptionId) {
    return (
      <Container maxW="full">
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
          Invalid Subscription ID
        </Heading>
        <Box maxW="container.lg" mx="auto">
          <Text mb={4}>The subscription ID is missing.</Text>
          <Button onClick={handleBackToSettings}>
            Go Back to Settings
          </Button>
        </Box>
      </Container>
    )
  }

  if (isLoading) {
    return (
      <Flex justify="center" align="center" minH="60vh">
        <Spinner size="xl" />
      </Flex>
    )
  }

  if (isError) {
    const statusCode = (error as any)?.response?.status
    console.error("Erro ao carregar assinatura:", error, "Status:", statusCode)
    
    if (statusCode === 404) {
      return (
        <Container maxW="full">
          <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
            Subscription Not Found
          </Heading>
          <Box maxW="container.lg" mx="auto">
            <Text mb={4}>The subscription you're looking for doesn't exist or you don't have access to it.</Text>
            <Button onClick={handleBackToSettings}>
              Go Back to Settings
            </Button>
          </Box>
        </Container>
      )
    }
    
    if (statusCode === 422) {
      return (
        <Container maxW="full">
          <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
            Invalid Subscription ID
          </Heading>
          <Box maxW="container.lg" mx="auto">
            <Text mb={4}>The subscription ID format is invalid.</Text>
            <Button onClick={handleBackToSettings}>
              Go Back to Settings
            </Button>
          </Box>
        </Container>
      )
    }

    return (
      <Container maxW="full">
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
          Error
        </Heading>
        <Box maxW="container.lg" mx="auto">
          <Text mb={4}>An error occurred while loading the subscription details. Please try again later.</Text>
          <Button onClick={handleBackToSettings}>
            Go Back to Settings
          </Button>
        </Box>
      </Container>
    )
  }

  if (!subscription) {
    return (
      <Container maxW="full">
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
          No Data Available
        </Heading>
        <Box maxW="container.lg" mx="auto">
          <Text mb={4}>Unable to load subscription details.</Text>
          <Button onClick={handleBackToSettings}>
            Go Back to Settings
          </Button>
        </Box>
      </Container>
    )
  }

  console.log("Dados da assinatura carregados:", subscription)

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Subscription Details
      </Heading>
      <Box position="absolute" top="2.5rem" right="1.5rem" display={{ base: "none", md: "block" }}>
        <Button
          variant="outline"
          onClick={handleBackToSettings}
          size="sm"
        >
          Back to Settings
        </Button>
      </Box>

      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={6} maxW="container.lg" mx="auto">
        {/* Subscription Info Card */}
        <GridItem colSpan={1}>
          <Card bg={bgCard} shadow="md" borderRadius="md">
            <CardHeader pb={2}>
              <Heading size="md">Plan Information</Heading>
            </CardHeader>
            <CardBody>
              <Box mb={4}>
                <Text fontWeight="bold">Plan Name:</Text>
                <Text fontSize="xl">{subscription.subscription_plan?.name || "Unknown Plan"}</Text>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="bold">Description:</Text>
                <Text>{subscription.subscription_plan?.description || "No description available"}</Text>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="bold">Price:</Text>
                <Text>
                  {subscription.subscription_plan?.price 
                    ? formatCurrency(subscription.subscription_plan.price, subscription.subscription_plan.currency || "USD")
                    : "N/A"}
                </Text>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="bold">Status:</Text>
                <Badge 
                  colorScheme={
                    subscription.payment_recurrence_status === "active"
                      ? "green"
                      : subscription.payment_recurrence_status === "pending_cancellation"
                      ? "yellow"
                      : "red"
                  }
                  fontSize="0.9em"
                  px={2}
                  py={1}
                  mt={1}
                >
                  {subscription.payment_recurrence_status}
                </Badge>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="bold">Period:</Text>
                <Text>
                  {formatDate(subscription.start_date)} to {formatDate(subscription.end_date)}
                </Text>
              </Box>

              <Box mb={4}>
                <Text fontWeight="bold">Usage:</Text>
                <Text>
                  {subscription.metric_type}: {subscription.metric_status} 
                  {subscription.subscription_plan?.metric_value ? ` / ${subscription.subscription_plan.metric_value}` : ""}
                </Text>
              </Box>

              <Divider my={4} />

              {subscription.payment_recurrence_status === "active" ? (
                <Button 
                  colorScheme="red"
                  width="full"
                  onClick={onOpen}
                  isLoading={cancelMutation.isPending}
                  bg={isDarkMode ? RED_COLOR : undefined}
                  _hover={{ bg: isDarkMode ? RED_HOVER : undefined }}
                  _active={{ bg: isDarkMode ? RED_ACTIVE : undefined }}
                >
                  Cancel Subscription
                </Button>
              ) : subscription.payment_recurrence_status === "pending_cancellation" ? (
                <Button 
                  colorScheme="green"
                  width="full"
                  onClick={() => reactivateMutation.mutate()}
                  isLoading={reactivateMutation.isPending}
                  bg={isDarkMode ? TEAL_COLOR : undefined}
                  color={isDarkMode ? "white" : undefined}
                  _hover={{ bg: isDarkMode ? TEAL_HOVER : undefined }}
                  _active={{ bg: isDarkMode ? TEAL_ACTIVE : undefined }}
                >
                  Reactivate Subscription
                </Button>
              ) : subscription.payment_recurrence_status === "canceled" && subscription.is_active ? (
                <Button 
                  colorScheme="green"
                  width="full"
                  onClick={() => reactivateMutation.mutate()}
                  isLoading={reactivateMutation.isPending}
                  bg={isDarkMode ? TEAL_COLOR : undefined}
                  color={isDarkMode ? "white" : undefined}
                  _hover={{ bg: isDarkMode ? TEAL_HOVER : undefined }}
                  _active={{ bg: isDarkMode ? TEAL_ACTIVE : undefined }}
                >
                  Reactivate Subscription
                </Button>
              ) : null}
            </CardBody>
          </Card>
        </GridItem>

        {/* Payment History Card */}
        <GridItem colSpan={1}>
          <Card bg={bgCard} shadow="md" borderRadius="md" height="100%">
            <CardHeader pb={2}>
              <Heading size="md">Payment History</Heading>
            </CardHeader>
            <CardBody>
              {subscription.payments && subscription.payments.length > 0 ? (
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead>
                      <Tr>
                        <Th color={color}>Date</Th>
                        <Th color={color}>Amount</Th>
                        <Th color={color}>Status</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {subscription.payments.map((payment) => (
                        <Tr key={payment.id}>
                          <Td>{formatDate(payment.payment_date)}</Td>
                          <Td>{formatCurrency(payment.amount, payment.currency)}</Td>
                          <Td>
                            <Badge
                              colorScheme={
                                payment.payment_status === "succeeded" || 
                                payment.payment_status === "paid"
                                  ? "green"
                                  : payment.payment_status === "pending"
                                  ? "yellow"
                                  : "red"
                              }
                              bg={
                                (payment.payment_status === "succeeded" || payment.payment_status === "paid") && 
                                isDarkMode
                                  ? TEAL_COLOR
                                  : undefined
                              }
                            >
                              {payment.payment_status}
                            </Badge>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              ) : (
                <Text>No payment history available</Text>
              )}
            </CardBody>
          </Card>
        </GridItem>
      </Grid>

      {/* Cancel Subscription Confirmation Dialog */}
      <AlertDialog
        isOpen={isOpen}
        leastDestructiveRef={cancelRef}
        onClose={onClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Cancel Subscription
            </AlertDialogHeader>

            <AlertDialogBody>
              Are you sure you want to cancel your subscription? You will still have access to your subscription benefits until the end date.
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onClose}>
                No, Keep It
              </Button>
              <Button 
                colorScheme="red"
                onClick={() => cancelMutation.mutate()} 
                ml={3}
                isLoading={cancelMutation.isPending}
                bg={isDarkMode ? RED_COLOR : undefined}
                _hover={{ bg: isDarkMode ? RED_HOVER : undefined }}
                _active={{ bg: isDarkMode ? RED_ACTIVE : undefined }}
              >
                Yes, Cancel It
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Container>
  )
} 