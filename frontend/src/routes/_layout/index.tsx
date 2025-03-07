import { useState } from "react";
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
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { FiUsers, FiActivity, FiBriefcase, FiAlertTriangle, FiLock } from "react-icons/fi";

import useAuth from "../../hooks/useAuth";
import CredentialsManager from "../../components/BotManagement/CredentialsManager";
import BotSessionManager from "../../components/BotManagement/BotSessionManager";
import SessionDetails from "../../components/BotManagement/SessionDetails";
import useSubscriptions from "../../hooks/userSubscriptions";

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
});

function Dashboard() {
  const { user: currentUser } = useAuth();
  const { data: subscriptions } = useSubscriptions();
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedCredentialId, setSelectedCredentialId] = useState<string | null>(null);
  
  const { 
    isOpen: isSessionDetailsOpen, 
    onOpen: onSessionDetailsOpen, 
    onClose: onSessionDetailsClose 
  } = useDisclosure();

  const isSubscriber = subscriptions && subscriptions.length > 0;

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
              width={{ base: "90%", md: "500px" }}
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
                      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} width="full">
                        <VStack 
                          p={4} 
                          bg={planBg}
                          borderRadius="md" 
                          borderWidth="1px" 
                          borderColor={planBorder}
                          align="flex-start"
                          spacing={2}
                        >
                          <Badge colorScheme="teal">Basic Plan</Badge>
                          <Text fontWeight="bold">100 Applications</Text>
                          <Text fontSize="sm">Perfect for casual job seekers</Text>
                        </VStack>
                        
                        <VStack 
                          p={4} 
                          bg={planBg}
                          borderRadius="md" 
                          borderWidth="1px" 
                          borderColor={planBorder}
                          align="flex-start"
                          spacing={2}
                        >
                          <Badge colorScheme="purple">Pro Plan</Badge>
                          <Text fontWeight="bold">Unlimited Applications</Text>
                          <Text fontSize="sm">Ideal for active job seekers</Text>
                        </VStack>
                      </SimpleGrid>
                    </Box>
                    
                    <Button 
                      colorScheme="teal" 
                      size="lg"
                      width={{ base: "full", md: "auto" }}
                      onClick={() => window.location.href = "/pricing"}
                    >
                      View Pricing Plans
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
