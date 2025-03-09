import {
  Box,
  Button,
  Card,
  CardBody,
  Center,
  Container,
  Flex,
  HStack,
  Heading,
  Icon,
  List,
  ListIcon,
  ListItem,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Spinner,
  Stat,
  StatHelpText,
  StatLabel,
  StatNumber,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  Tooltip,
  VStack,
  useColorModeValue,
  useDisclosure,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import {
  FiActivity,
  FiAlertTriangle,
  FiBriefcase,
  FiLock,
  FiRefreshCw,
  FiUsers,
} from "react-icons/fi"
import { CheckIcon } from "@chakra-ui/icons"

import {
  type SubscriptionPlanPublic,
} from "../../client"
import {
  BotSessionManager,
  CredentialsManager,
  SessionDetails,
} from "../../components/BotManagement"
import useAuth from "../../hooks/useAuth"
import useDashboardStats from "../../hooks/useDashboardStats"
import useSubscriptionPlans from "../../hooks/useSubscriptionPlans"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  // Usando apenas o hook useAuth para obter o usuário atual que já contém a propriedade is_subscriber
  const { user: currentUser, isLoading: isLoadingUser } = useAuth()
  
  // Usando o hook de estatísticas do dashboard (com cache e compartilhamento)
  const { 
    stats: dashboardStats, 
    isLoading: loadingStats, 
    refreshStats: refreshDashboardStats 
  } = useDashboardStats()
  
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  )
  const [selectedCredentialId, setSelectedCredentialId] = useState<
    string | null
  >(null)
  const [credentialsUpdated, setCredentialsUpdated] = useState<number>(0)
  
  // Estado para controlar a visibilidade do overlay
  const [showSubscriptionOverlay, setShowSubscriptionOverlay] = useState<boolean>(false)
  
  // Estado para controlar quando é seguro carregar componentes pesados
  const [canLoadHeavyComponents, setCanLoadHeavyComponents] = useState<boolean>(false)

  const {
    isOpen: isSessionDetailsOpen,
    onOpen: onSessionDetailsOpen,
    onClose: onSessionDetailsClose,
  } = useDisclosure()

  // Uso direto da propriedade is_subscriber do usuário atual
  const isSubscriber = currentUser?.is_subscriber || false
  
  // Apenas verificamos o status de assinatura baseado nas informações do usuário atual
  // Não carregamos nada até sabermos se o usuário é assinante
  useEffect(() => {
    if (!isLoadingUser && currentUser) {
      if (!isSubscriber) {
        // Se não for assinante, mostra o overlay e carrega os planos
        setShowSubscriptionOverlay(true)
        // Não carrega componentes pesados para não-assinantes
        setCanLoadHeavyComponents(false)
      } else {
        // Se for assinante, mantém o overlay oculto e permite carregar componentes pesados
        setShowSubscriptionOverlay(false)
        setCanLoadHeavyComponents(true)
      }
    }
  }, [isLoadingUser, currentUser, isSubscriber])

  // Usando o hook de planos de assinatura (com cache e compartilhamento)
  const { 
    plans: subscriptionPlans, 
    isLoading: loadingPlans 
  } = useSubscriptionPlans(true) // true para mostrar apenas planos ativos

  // Use real stats from API if available, otherwise use empty values
  const stats = dashboardStats

  const handleViewSessionDetails = (sessionId: string) => {
    setSelectedSessionId(sessionId)
    onSessionDetailsOpen()
  }

  const handleCredentialSelect = (credentialId: string) => {
    setSelectedCredentialId(credentialId)
  }

  const handleCredentialsUpdate = () => {
    setCredentialsUpdated((prev) => prev + 1)
  }

  const MiniPlanCard = ({ plan }: { plan: SubscriptionPlanPublic }) => {
    const highlightColor = useColorModeValue("teal.500", "teal.300")
    const cardBg = useColorModeValue(
      "rgba(255, 255, 255, 0.9)",
      "rgba(26, 32, 44, 0.6)",
    )

    const metricDisplay = () => {
      switch (plan.metric_type) {
        case "day":
          return `${plan.metric_value} days`
        case "week":
          return `${plan.metric_value} weeks`  
        case "month":
          return `${plan.metric_value} months`
        case "year":
          return `${plan.metric_value} years`
        default:
          return "subscription"
      }
    }

    return (
      <Card
        bg={cardBg}
        borderWidth="1px"
        borderColor={useColorModeValue(
          "rgba(209, 213, 219, 0.4)",
          "rgba(255, 255, 255, 0.1)",
        )}
        borderRadius="lg"
        overflow="hidden"
        transition="all 0.2s"
        _hover={{ transform: "translateY(-2px)", boxShadow: "md" }}
      >
        <CardBody p={4}>
          <VStack spacing={2} align="start">
            <Heading size="md" color={highlightColor}>
              {plan.name}
            </Heading>
            <Flex align="baseline">
              <Text fontSize="2xl" fontWeight="bold">
                ${plan.price}
              </Text>
              <Text fontSize="sm" color="gray.500" ml={1}>
                /{metricDisplay()}
              </Text>
            </Flex>
            <List spacing={1} w="full" mt={2}>
              {plan.benefits && plan.benefits.length > 0 && 
                plan.benefits.slice(0, 2).map((benefit, idx) => (
                  <ListItem key={idx} fontSize="sm">
                    <ListIcon as={CheckIcon} color={highlightColor} />
                    {benefit.name}
                  </ListItem>
                ))}
              {plan.benefits && plan.benefits.length > 2 && (
                <Text fontSize="xs" color="gray.500" ml={6}>
                  +{plan.benefits.length - 2} more benefits
                </Text>
              )}
            </List>
          </VStack>
        </CardBody>
      </Card>
    )
  }

  const highlightColor = useColorModeValue("teal.500", "teal.300")

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString()
    } catch (e) {
      return "Unknown"
    }
  }

  const DashboardContent = () => (
    <>
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontWeight="bold" fontSize="xl">
          Dashboard Overview
        </Text>
        <HStack>
          {loadingStats ? (
            <Spinner size="sm" color="teal.500" />
          ) : (
            <>
              <Tooltip
                label={`Last updated: ${formatTimestamp(stats.timestamp)}`}
              >
                <Text
                  fontSize="xs"
                  color="gray.500"
                  display={{ base: "none", md: "block" }}
                >
                  Last updated: {formatTimestamp(stats.timestamp)}
                </Text>
              </Tooltip>
              <Button
                size="sm"
                leftIcon={<FiRefreshCw />}
                onClick={refreshDashboardStats}
                isLoading={loadingStats}
                minW={{ base: "80px", md: "auto" }}
                display={{ base: "flex", md: "flex" }}
                variant="primary"
              >
                <Text display={{ base: "none", md: "block" }}>Refresh</Text>
                <Text display={{ base: "block", md: "none" }}>Sync</Text>
              </Button>
            </>
          )}
        </HStack>
      </Flex>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={6}>
        <Card>
          <CardBody>
            {loadingStats ? (
              <Center p={4}>
                <Spinner color="teal.500" />
              </Center>
            ) : (
              <Stat>
                <Flex justify="space-between">
                  <Box>
                    <StatLabel>Total Applications</StatLabel>
                    <StatNumber>{stats.total_applications}</StatNumber>
                    <StatHelpText>Across all sessions</StatHelpText>
                  </Box>
                  <Box>
                    <Icon as={FiActivity} boxSize={10} color="teal.400" />
                  </Box>
                </Flex>
              </Stat>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            {loadingStats ? (
              <Center p={4}>
                <Spinner color="teal.500" />
              </Center>
            ) : (
              <Stat>
                <Flex justify="space-between">
                  <Box>
                    <StatLabel>Success Rate</StatLabel>
                    <StatNumber>{stats.success_rate}%</StatNumber>
                    <StatHelpText>
                      {stats.successful_applications} successful
                    </StatHelpText>
                  </Box>
                  <Box>
                    <Icon as={FiBriefcase} boxSize={10} color="green.400" />
                  </Box>
                </Flex>
              </Stat>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            {loadingStats ? (
              <Center p={4}>
                <Spinner color="teal.500" />
              </Center>
            ) : (
              <Stat>
                <Flex justify="space-between">
                  <Box>
                    <StatLabel>Failed</StatLabel>
                    <StatNumber>{stats.failure_rate}%</StatNumber>
                    <StatHelpText>
                      {stats.failed_applications} applications
                    </StatHelpText>
                  </Box>
                  <Box>
                    <Icon
                      as={FiAlertTriangle}
                      boxSize={10}
                      color="red.400"
                    />
                  </Box>
                </Flex>
              </Stat>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            {loadingStats ? (
              <Center p={4}>
                <Spinner color="teal.500" />
              </Center>
            ) : (
              <Stat>
                <Flex justify="space-between">
                  <Box>
                    <StatLabel>Pending</StatLabel>
                    <StatNumber>{stats.pending_applications}</StatNumber>
                    <StatHelpText>Awaiting Responses</StatHelpText>
                  </Box>
                  <Box>
                    <Icon as={FiUsers} boxSize={10} color="blue.400" />
                  </Box>
                </Flex>
              </Stat>
            )}
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Main Bot Management Tabs - Carregados apenas se o usuário for assinante */}
      {canLoadHeavyComponents ? (
        <Tabs variant="enclosed" colorScheme="teal" mb={4}>
          <TabList>
            <Tab>Bot Sessions</Tab>
            <Tab>Credentials</Tab>
          </TabList>

          <TabPanels>
            <TabPanel px={0}>
              <BotSessionManager
                onViewSessionDetails={handleViewSessionDetails}
                onCredentialsUpdate={credentialsUpdated > 0 ? () => {} : undefined}
              />
            </TabPanel>
            <TabPanel px={0}>
              <CredentialsManager
                onCredentialSelect={handleCredentialSelect}
                selectedCredentialId={selectedCredentialId || undefined}
                onCredentialsUpdate={handleCredentialsUpdate}
              />
            </TabPanel>
          </TabPanels>
        </Tabs>
      ) : (
        /* Placeholder para quando os componentes pesados não estiverem carregados */
        <Box 
          p={4} 
          textAlign="center" 
          borderWidth="1px" 
          borderRadius="md" 
          bg={useColorModeValue("gray.50", "gray.700")}
        >
          <Spinner size="sm" mr={2} />
          <Text>Loading...</Text>
        </Box>
      )}
    </>
  )

  // Render subscription plans based on count
  const renderPlans = () => {
    if (loadingPlans) {
      return (
        <Center p={6}>
          <Spinner size="xl" color="teal.500" />
        </Center>
      )
    }

    if (subscriptionPlans.length === 0) {
      return (
        <Box p={4} textAlign="center">
          <Text>No subscription plans available at the moment.</Text>
        </Box>
      )
    }

    if (subscriptionPlans.length === 1) {
      // For a single plan, display it centered
      return (
        <Box width="full" px={4}>
          <MiniPlanCard plan={subscriptionPlans[0]} />
        </Box>
      )
    }

    // For 2 or more plans, display up to 2 plans in a grid
    return (
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} width="full">
        {subscriptionPlans.slice(0, 2).map((plan) => (
          <MiniPlanCard key={plan.id} plan={plan} />
        ))}
      </SimpleGrid>
    )
  }

  // Efeito para impedir scroll do body quando o modal estiver aberto
  useEffect(() => {
    if (showSubscriptionOverlay) {
      // Impedir scroll no body
      document.body.style.overflow = 'hidden';
    } else {
      // Restaurar scroll
      document.body.style.overflow = '';
    }
    
    // Cleanup function
    return () => {
      document.body.style.overflow = '';
    };
  }, [showSubscriptionOverlay]);

  return (
    <Container maxW="full">
      <Box pt={12}>
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Heading fontSize="2xl">
              Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
            </Heading>
            <Text>Welcome back, nice to see you again!</Text>
          </Box>
        </Flex>

        {/* Começamos mostrando o dashboard, e apenas se não for um assinante mostramos o overlay */}
        <Box position="relative">
          {/* O dashboard é sempre renderizado */}
          <Box 
            filter={showSubscriptionOverlay ? "blur(5px)" : "none"}
            pointerEvents={showSubscriptionOverlay ? "none" : "auto"}
            opacity={showSubscriptionOverlay ? 0.6 : 1}
            transition="all 0.3s ease"
            overflow={showSubscriptionOverlay ? "hidden" : "auto"}
            userSelect={showSubscriptionOverlay ? "none" : "auto"}
            height={showSubscriptionOverlay ? "100vh" : "auto"}
          >
            <DashboardContent />
          </Box>

          {/* Overlay de assinatura apenas se for mostrado */}
          {showSubscriptionOverlay && (
            <Box
              position="fixed"
              top="0"
              left={{ base: "0", md: "250px" }}
              right="0"
              bottom="0"
              zIndex={5}
              pointerEvents="none"
              display="flex"
              alignItems="center"
              justifyContent="center"
              overflow="auto"
              sx={{
                '&::-webkit-scrollbar': {
                  display: 'none',
                },
                scrollbarWidth: 'none',
                msOverflowStyle: 'none',
              }}
            >
              <Box
                width={["90%", "550px"]}
                maxWidth="90vw"
                margin="auto"
                pt={{ base: "80px", md: 0 }}
                pb={{ base: "50px", md: 0 }}
                pointerEvents="auto"
                overflowY="auto"
                maxHeight="100%"
                sx={{
                  '&::-webkit-scrollbar': {
                    display: 'none',
                  },
                  scrollbarWidth: 'none',
                  msOverflowStyle: 'none',
                }}
              >
                <Card
                  bg={useColorModeValue(
                    "rgba(255, 255, 255, 0.01)",
                    "rgba(26, 32, 44, 0.2)",
                  )}
                  backdropFilter="blur(25px)"
                  borderColor={useColorModeValue(
                    "rgba(209, 213, 219, 0.15)",
                    "rgba(255, 255, 255, 0.1)",
                  )}
                  borderWidth="1px"
                  borderRadius="xl"
                  boxShadow="xl"
                  overflow="hidden"
                  style={{ WebkitBackdropFilter: "blur(25px)" }}
                >
                  <Box bg="teal.500" h="8px" w="full" />
                  <CardBody
                    p={8}
                    bg={useColorModeValue(
                      "rgba(255, 255, 255, 0.05)",
                      "rgba(26, 32, 44, 0.3)",
                    )}
                  >
                    <VStack spacing={6} align="center">
                      <Icon as={FiLock} boxSize={16} color={highlightColor} />

                      <VStack spacing={2}>
                        <Heading
                          size="lg"
                          textAlign="center"
                          color={useColorModeValue("gray.800", "white")}
                        >
                          Unlock Bot Features
                        </Heading>
                        <Text
                          textAlign="center"
                          fontSize="md"
                          fontWeight="medium"
                          color={useColorModeValue("gray.800", "gray.100")}
                        >
                          To access the automated job application bot and all
                          dashboard features, you need an active subscription
                          plan.
                        </Text>
                      </VStack>

                      <Box w="full" pt={4}>
                        {renderPlans()}
                      </Box>

                      <Button
                        variant="primary"
                        size="lg"
                        width={{ base: "full", md: "auto" }}
                        onClick={() => (window.location.href = "/pricing")}
                        isLoading={loadingPlans}
                      >
                        View All Plans
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              </Box>
            </Box>
          )}
        </Box>
      </Box>

      {/* Session Details Modal */}
      {selectedSessionId && (
        <Modal
          isOpen={isSessionDetailsOpen}
          onClose={onSessionDetailsClose}
          size="full"
        >
          <ModalOverlay />
          <ModalContent maxW={{ base: "100%", lg: "90%" }} maxH="90vh">
            <ModalHeader
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              borderBottomWidth="1px"
              pb={4}
            >
              <Text>Bot Session Details</Text>
              <ModalCloseButton position="static" />
            </ModalHeader>
            <ModalBody pb={6} overflow="auto">
              <SessionDetails
                sessionId={selectedSessionId}
                onClose={onSessionDetailsClose}
              />
            </ModalBody>
          </ModalContent>
        </Modal>
      )}
    </Container>
  )
}

export default Dashboard
