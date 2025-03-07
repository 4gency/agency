import { CheckIcon } from "@chakra-ui/icons"
import {
  Badge,
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

import {
  BotsService,
  type SubscriptionPlanPublic,
  SubscriptionPlansService,
  type UserDashboardStats,
} from "../../client"
import {
  BotSessionManager,
  CredentialsManager,
  SessionDetails,
} from "../../components/BotManagement"
import useAuth from "../../hooks/useAuth"
import useSubscriptions from "../../hooks/userSubscriptions"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const { data: subscriptions } = useSubscriptions()
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  )
  const [selectedCredentialId, setSelectedCredentialId] = useState<
    string | null
  >(null)
  const [subscriptionPlans, setSubscriptionPlans] = useState<
    SubscriptionPlanPublic[]
  >([])
  const [loadingPlans, setLoadingPlans] = useState<boolean>(true)
  const [dashboardStats, setDashboardStats] =
    useState<UserDashboardStats | null>(null)
  const [loadingStats, setLoadingStats] = useState<boolean>(true)
  const [credentialsUpdated, setCredentialsUpdated] = useState<number>(0)

  const {
    isOpen: isSessionDetailsOpen,
    onOpen: onSessionDetailsOpen,
    onClose: onSessionDetailsClose,
  } = useDisclosure()

  const isSubscriber = subscriptions && subscriptions.length > 0

  // Fetch subscription plans on component mount
  useEffect(() => {
    if (!isSubscriber) {
      fetchSubscriptionPlans()
    }
  }, [isSubscriber])

  // Fetch dashboard statistics
  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    setLoadingStats(true)
    try {
      const stats = await BotsService.getUserDashboardStats()
      setDashboardStats(stats)
    } catch (error) {
      console.error("Error fetching dashboard stats:", error)
    } finally {
      setLoadingStats(false)
    }
  }

  const fetchSubscriptionPlans = async () => {
    setLoadingPlans(true)
    try {
      const response = await SubscriptionPlansService.readSubscriptionPlans({
        onlyActive: true,
      })
      if (response.plans) {
        setSubscriptionPlans(response.plans)
      }
    } catch (error) {
      console.error("Error fetching subscription plans:", error)
    } finally {
      setLoadingPlans(false)
    }
  }

  // Use real stats from API if available, otherwise use empty values
  const stats = dashboardStats || {
    total_applications: 0,
    successful_applications: 0,
    failed_applications: 0,
    pending_applications: 0,
    success_rate: 0,
    failure_rate: 0,
    timestamp: "",
  }

  const handleViewSessionDetails = (sessionId: string) => {
    setSelectedSessionId(sessionId)
    onSessionDetailsOpen()
  }

  const handleCredentialSelect = (credentialId: string) => {
    setSelectedCredentialId(credentialId)
  }

  // Function to call when credentials are updated
  const handleCredentialsUpdate = () => {
    setCredentialsUpdated((prev) => prev + 1)
  }

  // Subscription card styling
  const highlightColor = useColorModeValue("teal.500", "teal.300")
  const accentColor = useColorModeValue("teal.500", "teal.300")

  // Mini plan card component for subscription overlay
  const MiniPlanCard = ({ plan }: { plan: SubscriptionPlanPublic }) => {
    // Format the price correctly (assuming price is in cents)
    const formattedPrice = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: plan.currency || "USD",
      minimumFractionDigits: 0,
    }).format(plan.price / 100)

    // Determine metric display
    const metricDisplay = () => {
      switch (plan.metric_type) {
        case "applies":
          return `${plan.metric_value} Applications`
        case "day":
          return `${plan.metric_value} Days`
        case "week":
          return `${plan.metric_value} Weeks`
        case "month":
          return `${plan.metric_value} Months`
        case "year":
          return `${plan.metric_value} Years`
        default:
          return "Unlimited"
      }
    }

    return (
      <VStack
        p={4}
        bg={useColorModeValue(
          "rgba(255, 255, 255, 0.01)",
          "rgba(45, 55, 72, 0.35)",
        )}
        backdropFilter="blur(25px)"
        style={{ WebkitBackdropFilter: "blur(25px)" }}
        borderRadius="md"
        borderWidth="1px"
        borderColor={useColorModeValue(
          "rgba(209, 213, 219, 0.15)",
          "rgba(255, 255, 255, 0.1)",
        )}
        align="flex-start"
        spacing={2}
        height="full"
        boxShadow="md"
        transition="all 0.2s"
        _hover={{
          transform: "translateY(-2px)",
          boxShadow: "lg",
        }}
      >
        {plan.has_badge && plan.badge_text && (
          <Badge colorScheme="teal" fontWeight="bold">
            {plan.badge_text}
          </Badge>
        )}
        <Text
          fontWeight="bold"
          fontSize="lg"
          color={useColorModeValue("gray.800", "white")}
        >
          {plan.name}
        </Text>
        <HStack>
          <Text fontWeight="bold" fontSize="xl" color={highlightColor}>
            {formattedPrice}
          </Text>
          {plan.metric_type && (
            <Text
              fontSize="sm"
              color={useColorModeValue("gray.600", "gray.300")}
            >
              / {plan.metric_type}
            </Text>
          )}
        </HStack>
        <Text fontSize="sm" color={useColorModeValue("gray.700", "gray.200")}>
          {metricDisplay()}
        </Text>

        {plan.benefits && plan.benefits.length > 0 && (
          <List spacing={1} mt={2} fontSize="sm" width="full">
            {plan.benefits.slice(0, 2).map((benefit, index) => (
              <ListItem key={index}>
                <Flex align="center">
                  <ListIcon as={CheckIcon} color={accentColor} />
                  <Text
                    noOfLines={1}
                    color={useColorModeValue("gray.700", "gray.200")}
                  >
                    {benefit.name}
                  </Text>
                </Flex>
              </ListItem>
            ))}
            {plan.benefits.length > 2 && (
              <ListItem>
                <Text ml={6} fontSize="xs" color="gray.500">
                  +{plan.benefits.length - 2} more benefits
                </Text>
              </ListItem>
            )}
          </List>
        )}
      </VStack>
    )
  }

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return ""
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  // Dashboard content - to be blurred if not subscribed
  const DashboardContent = () => (
    <>
      {/* Stats Overview Section */}
      <Flex justify="space-between" align="center" mb={4}>
        <Heading size="md">Your Application Stats</Heading>
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
                onClick={fetchDashboardStats}
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
                    <StatLabel>Successful</StatLabel>
                    <StatNumber>{stats.successful_applications}</StatNumber>
                    <StatHelpText>
                      Success Rate: {stats.success_rate}%
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
                    <StatNumber>{stats.failed_applications}</StatNumber>
                    <StatHelpText>
                      Failure Rate: {stats.failure_rate}%
                    </StatHelpText>
                  </Box>
                  <Box>
                    <Icon as={FiAlertTriangle} boxSize={10} color="red.400" />
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

      {/* Main Bot Management Tabs */}
      <Tabs variant="enclosed" colorScheme="teal" mb={4}>
        <TabList>
          <Tab>Bot Sessions</Tab>
          <Tab>Credentials</Tab>
        </TabList>

        <TabPanels>
          <TabPanel px={0}>
            <BotSessionManager
              onViewDetails={handleViewSessionDetails}
              credentialsUpdated={credentialsUpdated}
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

  return (
    <Container maxW="full">
      <Box pt={12} px={4}>
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Heading fontSize="2xl">
              Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
            </Heading>
            <Text>Welcome back, nice to see you again!</Text>
          </Box>
        </Flex>

        {!isSubscriber ? (
          <Box position="relative">
            {/* Blurred dashboard in background */}
            <Box
              filter="blur(5px)"
              pointerEvents="none"
              opacity={0.6}
              position="relative"
              zIndex={1}
            >
              <DashboardContent />
            </Box>

            {/* Subscription CTA overlay */}
            <Box
              position="absolute"
              top="50%"
              left="50%"
              transform="translate(-50%, -50%)"
              zIndex={2}
              width={{ base: "90%", md: "550px" }}
              maxWidth="90vw"
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
        ) : (
          <DashboardContent />
        )}
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
