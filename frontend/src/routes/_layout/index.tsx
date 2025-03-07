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
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { FiUsers, FiActivity, FiBriefcase, FiAlertTriangle } from "react-icons/fi";

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
          <Card mb={6}>
            <CardBody>
              <Text fontSize="lg" fontWeight="medium">
                You don't have an active subscription. Please subscribe to use the bot features.
              </Text>
              <Button 
                colorScheme="teal" 
                mt={4} 
                onClick={() => window.location.href = "/pricing"}
              >
                View Pricing
              </Button>
            </CardBody>
          </Card>
        ) : (
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
