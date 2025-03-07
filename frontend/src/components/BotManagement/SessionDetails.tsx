import { useState, useEffect } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Card,
  CardBody,
  Stack,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatGroup,
  useToast,
  HStack,
  VStack,
  Spinner,
  Badge,
  IconButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Input,
  FormControl,
  FormLabel,
  Progress,
  Divider,
} from "@chakra-ui/react";
import { 
  FiAlertCircle, 
  FiCheckCircle, 
  FiClock, 
  FiInfo,
  FiRefreshCw,
  FiExternalLink
} from "react-icons/fi";

import { 
  BotsService, 
  EventsService, 
  ActionsService, 
  AppliesService,
  type BotSession, 
  type EventPublic, 
  type UserActionPublic,
  type ApplyPublic,
  type EventSummary,
  type ApplySummary,
  type ActionResponse
} from "../../client";

type SessionDetailsProps = {
  sessionId: string;
  onClose?: () => void;
};

const SessionDetails = ({ sessionId, onClose }: SessionDetailsProps) => {
  const [session, setSession] = useState<BotSession | null>(null);
  const [events, setEvents] = useState<EventPublic[]>([]);
  const [eventSummary, setEventSummary] = useState<EventSummary | null>(null);
  const [actions, setActions] = useState<UserActionPublic[]>([]);
  const [applies, setApplies] = useState<ApplyPublic[]>([]);
  const [applySummary, setApplySummary] = useState<ApplySummary | null>(null);
  const [selectedAction, setSelectedAction] = useState<UserActionPublic | null>(null);
  const [actionResponse, setActionResponse] = useState<string>("");
  
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [isLoadingEvents, setIsLoadingEvents] = useState(true);
  const [isLoadingActions, setIsLoadingActions] = useState(true);
  const [isLoadingApplies, setIsLoadingApplies] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { isOpen: isActionOpen, onOpen: onActionOpen, onClose: onActionClose } = useDisclosure();
  
  const toast = useToast();

  // Fetch session details on component mount
  useEffect(() => {
    fetchSessionData();
  }, [sessionId]);

  // Fetch all session data
  const fetchSessionData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        fetchSession(),
        fetchEvents(),
        fetchEventSummary(),
        fetchActions(),
        fetchApplies(),
        fetchApplySummary()
      ]);
    } catch (err) {
      console.error("Error fetching session data:", err);
      setError("Failed to load session data. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh all data
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetchSessionData();
      toast({
        title: "Refreshed",
        description: "Session data has been refreshed",
        status: "success",
        duration: 2000,
        isClosable: true,
      });
    } catch (err) {
      console.error("Error refreshing data:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Fetch session details
  const fetchSession = async () => {
    setIsLoadingSession(true);
    try {
      const data = await BotsService.getBotSession({ sessionId });
      setSession(data);
    } catch (err) {
      console.error("Error fetching session:", err);
      toast({
        title: "Error",
        description: "Failed to load session details",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoadingSession(false);
    }
  };

  // Fetch session events
  const fetchEvents = async () => {
    setIsLoadingEvents(true);
    try {
      const data = await EventsService.getSessionEvents({ sessionId, limit: 50 });
      setEvents(data.items || []);
    } catch (err) {
      console.error("Error fetching events:", err);
    } finally {
      setIsLoadingEvents(false);
    }
  };

  // Fetch event summary
  const fetchEventSummary = async () => {
    try {
      const data = await EventsService.getSessionEventsSummary({ sessionId });
      setEventSummary(data);
    } catch (err) {
      console.error("Error fetching event summary:", err);
    }
  };

  // Fetch user actions
  const fetchActions = async () => {
    setIsLoadingActions(true);
    try {
      const data = await ActionsService.getSessionActions({ 
        sessionId, 
        limit: 20,
        includeCompleted: true 
      });
      setActions(data.items || []);
    } catch (err) {
      console.error("Error fetching actions:", err);
    } finally {
      setIsLoadingActions(false);
    }
  };

  // Fetch session applies
  const fetchApplies = async () => {
    setIsLoadingApplies(true);
    try {
      const data = await AppliesService.getSessionApplies({ sessionId, limit: 50 });
      setApplies(data.items || []);
    } catch (err) {
      console.error("Error fetching applies:", err);
    } finally {
      setIsLoadingApplies(false);
    }
  };

  // Fetch apply summary
  const fetchApplySummary = async () => {
    try {
      const data = await AppliesService.getAppliesSummary({ sessionId });
      setApplySummary(data);
    } catch (err) {
      console.error("Error fetching apply summary:", err);
    }
  };

  // Handle action modal open
  const handleActionClick = (action: UserActionPublic) => {
    setSelectedAction(action);
    setActionResponse("");
    onActionOpen();
  };

  // Complete a user action
  const handleCompleteAction = async () => {
    if (!selectedAction) return;
    
    try {
      await ActionsService.completeAction({
        sessionId,
        actionId: selectedAction.id,
        requestBody: {
          user_input: actionResponse
        }
      });
      
      toast({
        title: "Success",
        description: "Action completed successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      
      onActionClose();
      setSelectedAction(null);
      setActionResponse("");
      fetchActions();
      fetchSession();
    } catch (err) {
      console.error("Error completing action:", err);
      toast({
        title: "Error",
        description: "Failed to complete action",
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
  
  // Format seconds to HH:MM:SS
  const formatDuration = (seconds?: number) => {
    if (!seconds) return "0:00";
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Get event severity color
  const getEventSeverityColor = (severity?: string) => {
    switch (severity) {
      case "error":
        return "red.500";
      case "warning":
        return "yellow.500";
      case "info":
        return "blue.500";
      default:
        return "gray.500";
    }
  };
  
  // Get apply status color
  const getApplyStatusColor = (status?: string) => {
    switch (status) {
      case "success":
        return "green";
      case "failed":
        return "red";
      default:
        return "gray";
    }
  };

  // Get action type display name
  const getActionTypeDisplay = (type: string) => {
    switch (type) {
      case "provide_2fa":
        return "2FA Verification";
      case "solve_captcha":
        return "CAPTCHA Challenge";
      case "answer_question":
        return "Answer Question";
      case "confirm_action":
        return "Confirmation Required";
      default:
        return type;
    }
  };

  // Calculate running time
  const calculateRunningTime = () => {
    if (!session) return "N/A";
    
    if (session.finished_at) {
      const startTime = session.started_at ? new Date(session.started_at).getTime() : 0;
      const endTime = new Date(session.finished_at).getTime();
      const pausedTime = session.total_paused_time || 0;
      
      const totalSeconds = Math.round((endTime - startTime) / 1000) - pausedTime;
      return formatDuration(totalSeconds);
    }
    
    if (session.started_at) {
      const startTime = new Date(session.started_at).getTime();
      const currentTime = new Date().getTime();
      const pausedTime = session.total_paused_time || 0;
      
      // If currently paused, don't count time since paused
      const pauseOffset = session.status === "paused" && session.paused_at
        ? (currentTime - new Date(session.paused_at).getTime()) / 1000
        : 0;
      
      const totalSeconds = Math.round((currentTime - startTime) / 1000) - pausedTime - pauseOffset;
      return formatDuration(totalSeconds);
    }
    
    return "Not started";
  };
  
  // Get session status badge
  const getStatusBadge = (status?: string) => {
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

  return (
    <Box>
      <Flex justifyContent="space-between" alignItems="center" mb={4}>
        <HStack>
          <Heading size="md">Session Details</Heading>
          {session && getStatusBadge(session.status)}
        </HStack>
        <HStack>
          <IconButton
            aria-label="Refresh"
            icon={<FiRefreshCw />}
            size="sm"
            onClick={handleRefresh}
            isLoading={isRefreshing}
          />
          {onClose && (
            <Button size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </HStack>
      </Flex>

      {isLoading ? (
        <Flex justifyContent="center" py={8}>
          <Spinner size="lg" />
        </Flex>
      ) : error ? (
        <Text color="red.500">{error}</Text>
      ) : !session ? (
        <Card>
          <CardBody>
            <Text>Session not found or you don't have access to this session.</Text>
          </CardBody>
        </Card>
      ) : (
        <Box>
          {/* Session Overview Section */}
          <Card mb={6} variant="outline">
            <CardBody>
              <StatGroup mb={4}>
                <Stat>
                  <StatLabel>Applications</StatLabel>
                  <StatNumber>{session.total_applied || 0} / {session.applies_limit}</StatNumber>
                  <StatHelpText>
                    {Math.min(Math.round(((session.total_applied || 0) / (session.applies_limit || 1)) * 100), 100)}% Complete
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>Successful</StatLabel>
                  <StatNumber>{session.total_success || 0}</StatNumber>
                  <StatHelpText>
                    {session.total_applied && session.total_applied > 0
                      ? `${Math.round((session.total_success || 0) / session.total_applied * 100)}%`
                      : "0%"}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>Failed</StatLabel>
                  <StatNumber>{session.total_failed || 0}</StatNumber>
                  <StatHelpText>
                    {session.total_applied && session.total_applied > 0
                      ? `${Math.round((session.total_failed || 0) / session.total_applied * 100)}%`
                      : "0%"}
                  </StatHelpText>
                </Stat>
                <Stat>
                  <StatLabel>Running Time</StatLabel>
                  <StatNumber>{calculateRunningTime()}</StatNumber>
                  <StatHelpText>
                    {session.paused_at && !session.resumed_at ? "Currently Paused" : ""}
                  </StatHelpText>
                </Stat>
              </StatGroup>
              
              <Progress 
                value={Math.min(((session.total_applied || 0) / (session.applies_limit || 1)) * 100, 100)} 
                size="sm" 
                colorScheme="teal" 
                borderRadius="full"
                mb={4}
              />
              
              <Divider mb={4} />
              
              <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4}>
                <GridItem>
                  <Text fontWeight="semibold">Session ID</Text>
                  <Text fontSize="sm" mb={2}>{session.id}</Text>
                  
                  <Text fontWeight="semibold">Pod Name</Text>
                  <Text fontSize="sm" mb={2}>{session.kubernetes_pod_name}</Text>
                  
                  <Text fontWeight="semibold">Status</Text>
                  <HStack mb={2}>
                    {getStatusBadge(session.status)}
                    <Text fontSize="sm">{session.last_status_message}</Text>
                  </HStack>
                  
                  {session.error_message && (
                    <>
                      <Text fontWeight="semibold" color="red.500">Error</Text>
                      <Text fontSize="sm" color="red.500" mb={2}>{session.error_message}</Text>
                    </>
                  )}
                </GridItem>
                
                <GridItem>
                  <Text fontWeight="semibold">Created</Text>
                  <Text fontSize="sm" mb={2}>{formatDate(session.created_at)}</Text>
                  
                  <Text fontWeight="semibold">Started</Text>
                  <Text fontSize="sm" mb={2}>{formatDate(session.started_at)}</Text>
                  
                  <Text fontWeight="semibold">Last Activity</Text>
                  <Text fontSize="sm" mb={2}>{formatDate(session.last_heartbeat_at)}</Text>
                  
                  <Text fontWeight="semibold">Finished</Text>
                  <Text fontSize="sm">{formatDate(session.finished_at)}</Text>
                </GridItem>
              </Grid>
            </CardBody>
          </Card>

          {/* Actions that require user input */}
          {actions.filter(a => !a.is_completed).length > 0 && (
            <Card mb={6} variant="outline" bg="purple.50">
              <CardBody>
                <Heading size="sm" mb={4}>Actions Requiring Your Input</Heading>
                <VStack spacing={3} align="stretch">
                  {actions
                    .filter(action => !action.is_completed)
                    .map(action => (
                      <Card key={action.id} variant="outline">
                        <CardBody>
                          <Flex justify="space-between" align="center">
                            <Box>
                              <HStack mb={1}>
                                <Badge colorScheme="purple">{getActionTypeDisplay(action.action_type)}</Badge>
                                <Text fontWeight="bold">{action.description}</Text>
                              </HStack>
                              <Text fontSize="sm" color="gray.600">Requested at {formatDate(action.requested_at)}</Text>
                            </Box>
                            <Button 
                              size="sm" 
                              colorScheme="purple" 
                              onClick={() => handleActionClick(action)}
                            >
                              Respond
                            </Button>
                          </Flex>
                        </CardBody>
                      </Card>
                    ))}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Tabs for Events, Actions, and Applies */}
          <Tabs variant="enclosed" colorScheme="teal">
            <TabList>
              <Tab>Events ({eventSummary?.total_events || events.length})</Tab>
              <Tab>Actions ({actions.length})</Tab>
              <Tab>Applications ({applySummary?.total_applies || applies.length})</Tab>
            </TabList>

            <TabPanels>
              {/* Events Tab */}
              <TabPanel>
                {isLoadingEvents ? (
                  <Flex justifyContent="center" py={4}>
                    <Spinner />
                  </Flex>
                ) : events.length === 0 ? (
                  <Text>No events found for this session.</Text>
                ) : (
                  <TableContainer>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Time</Th>
                          <Th>Type</Th>
                          <Th>Message</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {events.map(event => (
                          <Tr key={event.id}>
                            <Td whiteSpace="nowrap">{formatDate(event.created_at)}</Td>
                            <Td>
                              <Badge colorScheme={event.severity === "error" ? "red" : "blue"}>
                                {event.type}
                              </Badge>
                            </Td>
                            <Td>
                              <Text color={getEventSeverityColor(event.severity)}>{event.message}</Text>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </TableContainer>
                )}
              </TabPanel>

              {/* Actions Tab */}
              <TabPanel>
                {isLoadingActions ? (
                  <Flex justifyContent="center" py={4}>
                    <Spinner />
                  </Flex>
                ) : actions.length === 0 ? (
                  <Text>No actions found for this session.</Text>
                ) : (
                  <TableContainer>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Time</Th>
                          <Th>Type</Th>
                          <Th>Description</Th>
                          <Th>Status</Th>
                          <Th>Response</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {actions.map(action => (
                          <Tr key={action.id}>
                            <Td whiteSpace="nowrap">{formatDate(action.requested_at)}</Td>
                            <Td>
                              <Badge colorScheme="purple">
                                {getActionTypeDisplay(action.action_type)}
                              </Badge>
                            </Td>
                            <Td>{action.description}</Td>
                            <Td>
                              {action.is_completed ? (
                                <Badge colorScheme="green">Completed</Badge>
                              ) : (
                                <Badge colorScheme="yellow">Pending</Badge>
                              )}
                            </Td>
                            <Td>{action.user_input || "-"}</Td>
                            <Td>
                              {!action.is_completed && (
                                <Button 
                                  size="xs" 
                                  colorScheme="purple"
                                  onClick={() => handleActionClick(action)}
                                >
                                  Respond
                                </Button>
                              )}
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </TableContainer>
                )}
              </TabPanel>

              {/* Applications Tab */}
              <TabPanel>
                {isLoadingApplies ? (
                  <Flex justifyContent="center" py={4}>
                    <Spinner />
                  </Flex>
                ) : applies.length === 0 ? (
                  <Text>No applications found for this session.</Text>
                ) : (
                  <TableContainer>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Job Title</Th>
                          <Th>Company</Th>
                          <Th>Status</Th>
                          <Th>Time Taken</Th>
                          <Th>Link</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {applies.map(apply => (
                          <Tr key={apply.id}>
                            <Td>{apply.job_title || "Unknown Job"}</Td>
                            <Td>{apply.company_name || "Unknown Company"}</Td>
                            <Td>
                              <Badge colorScheme={getApplyStatusColor(apply.status)}>
                                {apply.status || "Unknown"}
                              </Badge>
                            </Td>
                            <Td>{formatDuration(apply.total_time)}</Td>
                            <Td>
                              {apply.job_url && (
                                <IconButton
                                  aria-label="Open job listing"
                                  icon={<FiExternalLink />}
                                  size="xs"
                                  variant="ghost"
                                  as="a"
                                  href={apply.job_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                />
                              )}
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </TableContainer>
                )}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>
      )}

      {/* Action Response Modal */}
      <Modal isOpen={isActionOpen} onClose={onActionClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {selectedAction && getActionTypeDisplay(selectedAction.action_type)}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedAction && (
              <VStack spacing={4} align="stretch">
                <Text>{selectedAction.description}</Text>
                <FormControl isRequired>
                  <FormLabel>Your Response</FormLabel>
                  <Input
                    value={actionResponse}
                    onChange={(e) => setActionResponse(e.target.value)}
                    placeholder="Enter your response here"
                  />
                </FormControl>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" mr={3} onClick={onActionClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="purple" 
              onClick={handleCompleteAction}
              isDisabled={!actionResponse.trim()}
            >
              Submit
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default SessionDetails;

// Helper Grid component for layout
const Grid = ({ 
  children, 
  templateColumns, 
  gap 
}: { 
  children: React.ReactNode;
  templateColumns: any;
  gap: number;
}) => {
  return (
    <Flex flexWrap="wrap" style={{ gap: `${gap * 4}px` }}>
      {React.Children.map(children, (child) => React.cloneElement(child as React.ReactElement, {
        style: {
          flexBasis: 
            typeof templateColumns === 'string' 
              ? undefined
              : `calc(${100 / Object.values(templateColumns)[0]}% - ${gap * 4 * (Object.values(templateColumns)[0] - 1) / Object.values(templateColumns)[0]}px)`,
          ...((child as React.ReactElement).props.style || {})
        }
      }))}
    </Flex>
  );
};

const GridItem = ({ children, ...rest }: { children: React.ReactNode; [key: string]: any }) => {
  return <Box {...rest}>{children}</Box>;
}; 