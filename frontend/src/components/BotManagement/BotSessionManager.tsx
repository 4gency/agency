import { useState, useEffect } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Card,
  CardBody,
  CardHeader,
  Stack,
  useToast,
  Icon,
  HStack,
  VStack,
  Spinner,
  Badge,
  Grid,
  GridItem,
  Tooltip,
  IconButton,
  Divider,
  Progress,
  RadioGroup,
  Radio,
} from "@chakra-ui/react";
import { 
  FiPlay, 
  FiPause, 
  FiSquare, 
  FiPlus, 
  FiInfo, 
  FiActivity, 
  FiList,
  FiAlertCircle,
  FiTrash2,
  FiChevronRight
} from "react-icons/fi";
import { BotsService, type SessionCreate, type BotSession, type BotSessionStatus, type BotStyleChoice, type CredentialsPublic, CredentialsService } from "../../client";
import DeleteAlert from "../Common/DeleteAlert";

type SessionStatusBadgeProps = {
  status: BotSessionStatus;
};

const SessionStatusBadge = ({ status }: SessionStatusBadgeProps) => {
  let color: string;
  let label: string;

  switch (status) {
    case "running":
      color = "green";
      label = "Running";
      break;
    case "paused":
      color = "yellow";
      label = "Paused";
      break;
    case "starting":
      color = "blue";
      label = "Starting";
      break;
    case "stopping":
      color = "orange";
      label = "Stopping";
      break;
    case "stopped":
      color = "gray";
      label = "Stopped";
      break;
    case "failed":
      color = "red";
      label = "Failed";
      break;
    case "completed":
      color = "teal";
      label = "Completed";
      break;
    case "waiting":
      color = "purple";
      label = "Waiting for Input";
      break;
    default:
      color = "gray";
      label = "Unknown";
  }

  return <Badge colorScheme={color}>{label}</Badge>;
};

const BotSessionManager = () => {
  const [sessions, setSessions] = useState<BotSession[]>([]);
  const [credentials, setCredentials] = useState<CredentialsPublic[]>([]);
  const [selectedCredentialId, setSelectedCredentialId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingAction, setIsLoadingAction] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [formData, setFormData] = useState<SessionCreate>({
    credentials_id: "",
    applies_limit: 100,
    style: "Modern Blue",
  });

  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  
  const toast = useToast();

  // Fetch sessions and credentials on component mount
  useEffect(() => {
    fetchSessions();
    fetchCredentials();
  }, []);

  // Fetch sessions from API
  const fetchSessions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await BotsService.getBotSessions();
      setSessions(response.items || []);
    } catch (err) {
      console.error("Error fetching sessions:", err);
      setError("Failed to load sessions. Please try again.");
      toast({
        title: "Error",
        description: "Failed to load bot sessions",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch credentials from API
  const fetchCredentials = async () => {
    try {
      const response = await CredentialsService.getUserCredentials();
      setCredentials(response.items || []);
      
      // If there's at least one credential, set it as selected by default
      if (response.items && response.items.length > 0 && !formData.credentials_id) {
        setFormData(prev => ({
          ...prev,
          credentials_id: response.items[0].id
        }));
        setSelectedCredentialId(response.items[0].id);
      }
    } catch (err) {
      console.error("Error fetching credentials:", err);
      toast({
        title: "Error",
        description: "Failed to load credentials",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Handle input changes for create form
  const handleInputChange = (name: string, value: any) => {
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  // Handle credential selection
  const handleCredentialSelect = (credentialId: string) => {
    setSelectedCredentialId(credentialId);
    setFormData({
      ...formData,
      credentials_id: credentialId,
    });
  };

  // Handle session creation
  const handleCreateSession = async () => {
    try {
      await BotsService.createBotSession({
        requestBody: formData,
      });
      toast({
        title: "Success",
        description: "Bot session created successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      onCreateClose();
      setFormData({
        ...formData,
        applies_limit: 100,
        style: "Modern Blue",
      });
      fetchSessions();
    } catch (err) {
      console.error("Error creating session:", err);
      toast({
        title: "Error",
        description: "Failed to create bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Handle session start
  const handleStartSession = async (sessionId: string) => {
    setIsLoadingAction(true);
    try {
      await BotsService.startBotSession({ sessionId });
      toast({
        title: "Success",
        description: "Bot session started",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      fetchSessions();
    } catch (err) {
      console.error("Error starting session:", err);
      toast({
        title: "Error",
        description: "Failed to start bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoadingAction(false);
    }
  };

  // Handle session pause
  const handlePauseSession = async (sessionId: string) => {
    setIsLoadingAction(true);
    try {
      await BotsService.pauseBotSession({ sessionId });
      toast({
        title: "Success",
        description: "Bot session paused",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      fetchSessions();
    } catch (err) {
      console.error("Error pausing session:", err);
      toast({
        title: "Error",
        description: "Failed to pause bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoadingAction(false);
    }
  };

  // Handle session resume
  const handleResumeSession = async (sessionId: string) => {
    setIsLoadingAction(true);
    try {
      await BotsService.resumeBotSession({ sessionId });
      toast({
        title: "Success",
        description: "Bot session resumed",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      fetchSessions();
    } catch (err) {
      console.error("Error resuming session:", err);
      toast({
        title: "Error",
        description: "Failed to resume bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoadingAction(false);
    }
  };

  // Handle session stop
  const handleStopSession = async (sessionId: string) => {
    setIsLoadingAction(true);
    try {
      await BotsService.stopBotSession({ sessionId });
      toast({
        title: "Success",
        description: "Bot session stopped",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      fetchSessions();
    } catch (err) {
      console.error("Error stopping session:", err);
      toast({
        title: "Error",
        description: "Failed to stop bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoadingAction(false);
    }
  };

  // Open delete confirmation modal
  const handleDeleteClick = (sessionId: string) => {
    setSessionToDelete(sessionId);
    onDeleteOpen();
  };

  // Handle session deletion
  const handleDeleteSession = async () => {
    if (!sessionToDelete) return;
    
    try {
      await BotsService.deleteBotSession({
        sessionId: sessionToDelete,
      });
      toast({
        title: "Success",
        description: "Bot session deleted successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      onDeleteClose();
      setSessionToDelete(null);
      fetchSessions();
    } catch (err) {
      console.error("Error deleting session:", err);
      toast({
        title: "Error",
        description: "Failed to delete bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Format date function
  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString();
  };

  // Calculate success rate
  const calculateSuccessRate = (session: BotSession) => {
    if (!session.total_applied || session.total_applied === 0) return 0;
    return Math.round((session.total_success || 0) / session.total_applied * 100);
  };

  // Render action buttons based on session status
  const renderActionButtons = (session: BotSession) => {
    switch (session.status) {
      case "running":
        return (
          <HStack spacing={2}>
            <Tooltip label="Pause Session">
              <IconButton
                aria-label="Pause Session"
                icon={<FiPause />}
                size="sm"
                isLoading={isLoadingAction}
                onClick={() => handlePauseSession(session.id!)}
              />
            </Tooltip>
            <Tooltip label="Stop Session">
              <IconButton
                aria-label="Stop Session"
                icon={<FiSquare />}
                size="sm"
                colorScheme="red"
                isLoading={isLoadingAction}
                onClick={() => handleStopSession(session.id!)}
              />
            </Tooltip>
          </HStack>
        );
      case "paused":
        return (
          <HStack spacing={2}>
            <Tooltip label="Resume Session">
              <IconButton
                aria-label="Resume Session"
                icon={<FiPlay />}
                size="sm"
                colorScheme="green"
                isLoading={isLoadingAction}
                onClick={() => handleResumeSession(session.id!)}
              />
            </Tooltip>
            <Tooltip label="Stop Session">
              <IconButton
                aria-label="Stop Session"
                icon={<FiSquare />}
                size="sm"
                colorScheme="red"
                isLoading={isLoadingAction}
                onClick={() => handleStopSession(session.id!)}
              />
            </Tooltip>
          </HStack>
        );
      case "starting":
      case "stopping":
        return (
          <Spinner size="sm" />
        );
      case "stopped":
      case "failed":
        return (
          <HStack spacing={2}>
            <Tooltip label="Start Session">
              <IconButton
                aria-label="Start Session"
                icon={<FiPlay />}
                size="sm"
                colorScheme="green"
                isLoading={isLoadingAction}
                onClick={() => handleStartSession(session.id!)}
              />
            </Tooltip>
            <Tooltip label="Delete Session">
              <IconButton
                aria-label="Delete Session"
                icon={<FiTrash2 />}
                size="sm"
                colorScheme="red"
                onClick={() => handleDeleteClick(session.id!)}
              />
            </Tooltip>
          </HStack>
        );
      default:
        return (
          <HStack spacing={2}>
            <Tooltip label="Delete Session">
              <IconButton
                aria-label="Delete Session"
                icon={<FiTrash2 />}
                size="sm"
                colorScheme="red"
                onClick={() => handleDeleteClick(session.id!)}
              />
            </Tooltip>
          </HStack>
        );
    }
  };

  return (
    <Box>
      <Flex justifyContent="space-between" alignItems="center" mb={4}>
        <Heading size="md">Bot Sessions</Heading>
        <Button 
          leftIcon={<FiPlus />} 
          colorScheme="teal"
          onClick={onCreateOpen}
          isDisabled={credentials.length === 0}
        >
          New Session
        </Button>
      </Flex>

      {credentials.length === 0 && (
        <Card mb={4} bg="yellow.50">
          <CardBody>
            <Flex align="center">
              <Icon as={FiAlertCircle} color="yellow.500" mr={2} />
              <Text>You need to add LinkedIn credentials before creating a bot session.</Text>
            </Flex>
          </CardBody>
        </Card>
      )}

      {isLoading ? (
        <Flex justifyContent="center" py={8}>
          <Spinner size="lg" />
        </Flex>
      ) : error ? (
        <Text color="red.500">{error}</Text>
      ) : sessions.length === 0 ? (
        <Card>
          <CardBody>
            <Text textAlign="center">No bot sessions found. Create a new session to start automating job applications.</Text>
          </CardBody>
        </Card>
      ) : (
        <VStack spacing={4} align="stretch">
          {sessions.map((session) => (
            <Card key={session.id} variant="outline" shadow="md">
              <CardHeader pb={0}>
                <Flex justify="space-between" align="center">
                  <HStack>
                    <SessionStatusBadge status={session.status!} />
                    <Text fontWeight="bold">
                      {session.kubernetes_pod_name?.split('-').pop()}
                    </Text>
                  </HStack>
                  <HStack>
                    {renderActionButtons(session)}
                    <Tooltip label="View Details">
                      <IconButton
                        aria-label="View Details"
                        icon={<FiChevronRight />}
                        size="sm"
                        variant="ghost"
                      />
                    </Tooltip>
                  </HStack>
                </Flex>
              </CardHeader>
              <CardBody>
                <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                  <GridItem>
                    <Text fontSize="sm" color="gray.500">Created</Text>
                    <Text>{formatDate(session.created_at)}</Text>
                  </GridItem>
                  <GridItem>
                    <Text fontSize="sm" color="gray.500">Last Activity</Text>
                    <Text>{formatDate(session.last_heartbeat_at)}</Text>
                  </GridItem>
                </Grid>
                
                <Divider my={3} />
                
                <Box mb={3}>
                  <Flex justify="space-between" mb={1}>
                    <Text fontSize="sm">Progress: {session.total_applied || 0} / {session.applies_limit}</Text>
                    <Text fontSize="sm">{Math.min(Math.round(((session.total_applied || 0) / (session.applies_limit || 1)) * 100), 100)}%</Text>
                  </Flex>
                  <Progress 
                    value={Math.min(((session.total_applied || 0) / (session.applies_limit || 1)) * 100, 100)} 
                    size="sm" 
                    colorScheme="teal" 
                    borderRadius="full"
                  />
                </Box>
                
                <Grid templateColumns="repeat(3, 1fr)" gap={2}>
                  <GridItem>
                    <HStack>
                      <Icon as={FiActivity} color="green.500" />
                      <Text fontSize="sm">{session.total_success || 0} Successful</Text>
                    </HStack>
                  </GridItem>
                  <GridItem>
                    <HStack>
                      <Icon as={FiAlertCircle} color="red.500" />
                      <Text fontSize="sm">{session.total_failed || 0} Failed</Text>
                    </HStack>
                  </GridItem>
                  <GridItem>
                    <HStack>
                      <Icon as={FiInfo} color="blue.500" />
                      <Text fontSize="sm">{calculateSuccessRate(session)}% Success Rate</Text>
                    </HStack>
                  </GridItem>
                </Grid>
              </CardBody>
            </Card>
          ))}
        </VStack>
      )}

      {/* Create Session Modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="md">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create Bot Session</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack spacing={4}>
              <FormControl isRequired>
                <FormLabel>LinkedIn Credential</FormLabel>
                <Select 
                  value={formData.credentials_id} 
                  onChange={(e) => handleInputChange("credentials_id", e.target.value)}
                >
                  {credentials.map((cred) => (
                    <option key={cred.id} value={cred.id}>
                      {cred.email}
                    </option>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel>Applications Limit</FormLabel>
                <NumberInput 
                  min={1} 
                  max={500} 
                  value={formData.applies_limit} 
                  onChange={(value) => handleInputChange("applies_limit", parseInt(value))}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Maximum number of job applications the bot will submit
                </Text>
              </FormControl>
              
              <FormControl>
                <FormLabel>Bot Style</FormLabel>
                <RadioGroup 
                  value={formData.style} 
                  onChange={(value) => handleInputChange("style", value)}
                >
                  <Stack spacing={2}>
                    <Radio value="Cloyola Grey">Cloyola Grey</Radio>
                    <Radio value="Modern Blue">Modern Blue</Radio>
                    <Radio value="Modern Grey">Modern Grey</Radio>
                    <Radio value="Default">Default</Radio>
                    <Radio value="Clean Blue">Clean Blue</Radio>
                  </Stack>
                </RadioGroup>
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Visual style of the bot interface
                </Text>
              </FormControl>
            </Stack>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" mr={3} onClick={onCreateClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="teal" 
              onClick={handleCreateSession}
              isDisabled={!formData.credentials_id}
            >
              Create
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation */}
      <DeleteAlert
        isOpen={isDeleteOpen}
        onClose={onDeleteClose}
        onDelete={handleDeleteSession}
        title="Delete Bot Session"
        message="Are you sure you want to delete this bot session? This action cannot be undone."
      />
    </Box>
  );
};

export default BotSessionManager; 