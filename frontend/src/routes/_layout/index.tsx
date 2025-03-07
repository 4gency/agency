import { useState, useEffect } from "react";
import { 
  Box, 
  Container, 
  Text, 
  Heading, 
  Card, 
  CardBody, 
  SimpleGrid, 
  Stat, 
  StatLabel, 
  StatNumber, 
  StatHelpText, 
  Icon, 
  Flex, 
  Tabs, 
  TabList, 
  TabPanels, 
  Tab, 
  TabPanel,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Button,
  VStack,
  useColorModeValue,
  Badge,
  List,
  ListItem,
  ListIcon,
  HStack,
  Center,
  Spinner,
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { FiUsers, FiActivity, FiBriefcase, FiAlertTriangle, FiLock } from "react-icons/fi";
import { CheckIcon } from "@chakra-ui/icons";

import useAuth from "../../hooks/useAuth";
import CredentialsManager from "../../components/BotManagement/CredentialsManager";
import BotSessionManager from "../../components/BotManagement/BotSessionManager";
import SessionDetails from "../../components/BotManagement/SessionDetails";
import useSubscriptions from "../../hooks/userSubscriptions";
import { SubscriptionPlansService, type SubscriptionPlanPublic } from "../../client";

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
});

function Dashboard() {
  const { user: currentUser } = useAuth();
  const { data: subscriptions } = useSubscriptions();
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedCredentialId, setSelectedCredentialId] = useState<string | null>(null);
  const [subscriptionPlans, setSubscriptionPlans] = useState<SubscriptionPlanPublic[]>([]);
  const [loadingPlans, setLoadingPlans] = useState<boolean>(true);
  
  const { 
    isOpen: isSessionDetailsOpen, 
    onOpen: onSessionDetailsOpen, 
    onClose: onSessionDetailsClose 
  } = useDisclosure();

  const isSubscriber = subscriptions && subscriptions.length > 0;

  // Fetch subscription plans on component mount
  useEffect(() => {
    if (!isSubscriber) {
      fetchSubscriptionPlans();
    }
  }, [isSubscriber]);

  const fetchSubscriptionPlans = async () => {
    setLoadingPlans(true);
    try {
      const response = await SubscriptionPlansService.readSubscriptionPlans({ onlyActive: true });
      if (response.plans) {
        setSubscriptionPlans(response.plans);
      }
    } catch (error) {
      console.error("Error fetching subscription plans:", error);
    } finally {
      setLoadingPlans(false);
    }
  };

  // Mock stats for demo
  const stats = {
    totalApplications: 256,
    successfulApplications: 178,
    failedApplications: 35,
    pendingApplications: 43,
    successRate: 69.5
  };

  const handleViewSessionDetails = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    onSessionDetailsOpen();
  };

  const handleCredentialSelect = (credentialId: string) => {
    setSelectedCredentialId(credentialId);
  };
  
  // Subscription card styling
  const cardBg = useColorModeValue('white', 'gray.800');
  const cardBorder = useColorModeValue('gray.200', 'gray.700');
  const highlightColor = useColorModeValue('teal.500', 'teal.300');
  const planBg = useColorModeValue('gray.50', 'gray.700');
  const planBorder = useColorModeValue('gray.200', 'gray.600');
  const accentColor = useColorModeValue('teal.500', 'teal.300');

  // Mini plan card component for subscription overlay
  const MiniPlanCard = ({ plan }: { plan: SubscriptionPlanPublic }) => {
    // Format the price correctly (assuming price is in cents)
    const formattedPrice = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: plan.currency || 'USD',
      minimumFractionDigits: 0,
    }).format(plan.price / 100);

    // Determine metric display
    const metricDisplay = () => {
      switch (plan.metric_type) {
        case "applies":
          return `${plan.metric_value} Applications`;
        case "day":
          return `${plan.metric_value} Days`;
        case "week":
          return `${plan.metric_value} Weeks`;
        case "month":
          return `${plan.metric_value} Months`;
        case "year":
          return `${plan.metric_value} Years`;
        default:
          return "Unlimited";
      }
    };

    return (
      <VStack 
        p={4} 
        bg={planBg}
        borderRadius="md" 
        borderWidth="1px" 
        borderColor={planBorder}
        align="flex-start"
        spacing={2}
        height="full"
      >
        {plan.has_badge && plan.badge_text && (
          <Badge colorScheme="teal">{plan.badge_text}</Badge>
        )}
        <Text fontWeight="bold">{plan.name}</Text>
        <HStack>
          <Text fontWeight="bold" fontSize="xl">{formattedPrice}</Text>
          {plan.metric_type && (
            <Text fontSize="sm" color="gray.500">/ {plan.metric_type}</Text>
          )}
        </HStack>
        <Text fontSize="sm">{metricDisplay()}</Text>
        
        {plan.benefits && plan.benefits.length > 0 && (
          <List spacing={1} mt={2} fontSize="sm" width="full">
            {plan.benefits.slice(0, 2).map((benefit, index) => (
              <ListItem key={index}>
                <Flex align="center">
                  <ListIcon as={CheckIcon} color={accentColor} />
                  <Text noOfLines={1}>{benefit.name}</Text>
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
    );
  };

  // Dashboard content - to be blurred if not subscribed
  const DashboardContent = () => (
    <>
      {/* Stats Overview Section */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card>
          <CardBody>
            <Stat>
              <Flex justify="space-between">
                <Box>
                  <StatLabel>Total Applications</StatLabel>
                  <StatNumber>{stats.totalApplications}</StatNumber>
                  <StatHelpText>Across all sessions</StatHelpText>
                </Box>
                <Box>
                  <Icon as={FiBriefcase} boxSize={10} color="teal.400" />
                </Box>
              </Flex>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <Flex justify="space-between">
                <Box>
                  <StatLabel>Successful</StatLabel>
                  <StatNumber>{stats.successfulApplications}</StatNumber>
                  <StatHelpText>Success Rate: {stats.successRate}%</StatHelpText>
                </Box>
                <Box>
                  <Icon as={FiActivity} boxSize={10} color="green.400" />
                </Box>
              </Flex>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <Flex justify="space-between">
                <Box>
                  <StatLabel>Failed</StatLabel>
                  <StatNumber>{stats.failedApplications}</StatNumber>
                  <StatHelpText>Failure Rate: {100 - stats.successRate}%</StatHelpText>
                </Box>
                <Box>
                  <Icon as={FiAlertTriangle} boxSize={10} color="red.400" />
                </Box>
              </Flex>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <Flex justify="space-between">
                <Box>
                  <StatLabel>Pending</StatLabel>
                  <StatNumber>{stats.pendingApplications}</StatNumber>
                  <StatHelpText>Awaiting Responses</StatHelpText>
                </Box>
                <Box>
                  <Icon as={FiUsers} boxSize={10} color="blue.400" />
                </Box>
              </Flex>
            </Stat>
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
            <BotSessionManager />
          </TabPanel>
          <TabPanel px={0}>
            <CredentialsManager 
              onCredentialSelect={handleCredentialSelect}
              selectedCredentialId={selectedCredentialId || undefined}
            />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </>
  );

  // Render subscription plans based on count
  const renderPlans = () => {
    if (loadingPlans) {
      return (
        <Center p={6}>
          <Spinner size="xl" color="teal.500" />
        </Center>
      );
    }

    if (subscriptionPlans.length === 0) {
      return (
        <Box p={4} textAlign="center">
          <Text>No subscription plans available at the moment.</Text>
        </Box>
      );
    }

    if (subscriptionPlans.length === 1) {
      // For a single plan, display it centered
      return (
        <Box width="full" px={4}>
          <MiniPlanCard plan={subscriptionPlans[0]} />
        </Box>
      );
    }

    // For 2 or more plans, display up to 2 plans in a grid
    return (
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} width="full">
        {subscriptionPlans.slice(0, 2).map((plan, index) => (
          <MiniPlanCard key={plan.id} plan={plan} />
        ))}
      </SimpleGrid>
    );
  };

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
              filter="blur(6px)" 
              pointerEvents="none" 
              opacity={0.7}
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
                bg={cardBg} 
                borderColor={cardBorder} 
                borderWidth="1px" 
                borderRadius="xl" 
                boxShadow="lg" 
                overflow="hidden"
              >
                <Box bg="teal.500" h="8px" w="full" />
                <CardBody p={8}>
                  <VStack spacing={6} align="center">
                    <Icon as={FiLock} boxSize={16} color={highlightColor} />
                    
                    <VStack spacing={2}>
                      <Heading size="lg" textAlign="center">Unlock Bot Features</Heading>
                      <Text textAlign="center" fontSize="md" color="gray.500">
                        To access the automated job application bot and all dashboard features, 
                        you need an active subscription plan.
                      </Text>
                    </VStack>
                    
                    <Box w="full" pt={4}>
                      {renderPlans()}
                    </Box>
                    
                    <Button 
                      colorScheme="teal" 
                      size="lg"
                      width={{ base: "full", md: "auto" }}
                      onClick={() => window.location.href = "/pricing"}
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
          <ModalContent>
            <ModalHeader>Session Details</ModalHeader>
            <ModalCloseButton />
            <ModalBody pb={6}>
              <SessionDetails 
                sessionId={selectedSessionId}
                onClose={onSessionDetailsClose}
              />
            </ModalBody>
          </ModalContent>
        </Modal>
      )}
    </Container>
  );
}

export default Dashboard;
