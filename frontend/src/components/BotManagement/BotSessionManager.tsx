import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Center,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  GridItem,
  HStack,
  Heading,
  Icon,
  IconButton,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Progress,
  Radio,
  RadioGroup,
  Select,
  Spinner,
  Stack,
  Text,
  Tooltip,
  VStack,
  useDisclosure,
  useToast,
} from "@chakra-ui/react"
import { useEffect, useState } from "react"
import {
  FiActivity,
  FiAlertCircle,
  FiChevronRight,
  FiInfo,
  FiPause,
  FiPlay,
  FiPlus,
  FiRefreshCw,
  FiStopCircle,
  FiTrash2,
} from "react-icons/fi"
import {
  type BotSessionStatus,
  type BotStyleChoice,
  BotsService,
  type CredentialsPublic,
  CredentialsService,
  type SessionCreate,
  type SessionPublic,
} from "../../client"
import DeleteAlert from "../Common/DeleteAlert"
import useSessionsData from "../../hooks/useSessionsData"
import useCredentialsData from "../../hooks/useCredentialsData"

type SessionStatusBadgeProps = {
  status: string
}

type SessionProgressProps = {
  session: SessionPublic
}

export type BotSessionManagerProps = {
  onViewDetails: (sessionId: string) => void
  credentialsUpdated?: number
}

// Define a simplified type for the create session form
interface SessionFormData {
  credentials_id: string
  applies_limit: number
  style?: string
}

const SessionStatusBadge = ({ status }: SessionStatusBadgeProps) => {
  let color: string
  let label: string

  switch (status) {
    case "running":
      color = "green"
      label = "Running"
      break
    case "paused":
      color = "yellow"
      label = "Paused"
      break
    case "starting":
      color = "blue"
      label = "Starting"
      break
    case "stopping":
      color = "orange"
      label = "Stopping"
      break
    case "stopped":
      color = "gray"
      label = "Stopped"
      break
    case "failed":
      color = "red"
      label = "Failed"
      break
    case "completed":
      color = "teal"
      label = "Completed"
      break
    case "waiting":
      color = "purple"
      label = "Waiting for Input"
      break
    default:
      color = "gray"
      label = "Unknown"
  }

  return <Badge colorScheme={color}>{label}</Badge>
}

const BotSessionManager = ({
  onViewDetails,
  credentialsUpdated = 0,
}: BotSessionManagerProps) => {
  const { 
    sessions, 
    isLoading: isLoadingSessions, 
    isError: isSessionsError, 
    error: sessionsError, 
    refetchSessions 
  } = useSessionsData()
  const { 
    credentials, 
    refetchCredentials 
  } = useCredentialsData()

  const {
    isOpen: isCreateOpen,
    onOpen: onCreateOpen,
    onClose: onCreateClose,
  } = useDisclosure()
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure()

  const toast = useToast()

  const [isLoadingAction, setIsLoadingAction] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null)
  const [formData, setFormData] = useState<SessionFormData>({
    credentials_id: "",
    applies_limit: 200,
  })

  // Fetch sessions and credentials on component mount
  useEffect(() => {
    // Não precisamos mais chamar nada aqui, os hooks já carregam automaticamente
  }, [])

  // React to credentials updates
  useEffect(() => {
    if (credentialsUpdated > 0) {
      refetchCredentials()
    }
  }, [credentialsUpdated, refetchCredentials])

  const getCredentialName = (credentialsId: string) => {
    const credential = credentials.find((c) => c.id === credentialsId)
    return credential ? credential.name : "Unknown"
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]:
        e.target.type === "number" ? Number(e.target.value) : e.target.value,
    })
  }

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleRadioChange = (value: string) => {
    setFormData({
      ...formData,
      style: value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoadingAction(true)

    try {
      await BotsService.createBotSession({
        requestBody: formData as any, // Type cast to avoid issues
      })
      onCreateClose()
      setFormData({
        credentials_id: credentials.length > 0 ? credentials[0].id : "",
        applies_limit: 200,
      })
      toast({
        title: "Success",
        description: "Bot session created successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      refetchSessions()
    } catch (err) {
      console.error("Error creating session:", err)
      toast({
        title: "Error",
        description: "Failed to create bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsLoadingAction(false)
    }
  }

  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return

    setIsLoadingAction(true)
    try {
      await BotsService.deleteBotSession({
        sessionId: sessionToDelete,
      })
      setSessionToDelete(null)
      onDeleteClose()
      toast({
        title: "Success",
        description: "Bot session deleted successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      refetchSessions()
    } catch (err) {
      console.error("Error deleting session:", err)
      toast({
        title: "Error",
        description: "Failed to delete bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsLoadingAction(false)
    }
  }

  const handleStartSession = async (sessionId: string) => {
    setIsLoadingAction(true)
    try {
      await BotsService.startBotSession({
        sessionId,
      })
      toast({
        title: "Success",
        description: "Bot session started successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      refetchSessions()
    } catch (err) {
      console.error("Error starting session:", err)
      toast({
        title: "Error",
        description: "Failed to start bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsLoadingAction(false)
    }
  }

  const handleStopSession = async (sessionId: string) => {
    setIsLoadingAction(true)
    try {
      await BotsService.stopBotSession({
        sessionId,
      })
      toast({
        title: "Success",
        description: "Bot session stopped successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      refetchSessions()
    } catch (err) {
      console.error("Error stopping session:", err)
      toast({
        title: "Error",
        description: "Failed to stop bot session",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsLoadingAction(false)
    }
  }

  // Para evitar erros, vamos definir versões temporárias das funções faltantes
  const handlePauseSession = handleStopSession; // Usando handleStopSession como substituto
  const handleResumeSession = handleStartSession; // Usando handleStartSession como substituto

  const handleOpenDeleteModal = (sessionId: string) => {
    setSessionToDelete(sessionId)
    onDeleteOpen()
  }

  // Format date function
  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "N/A"
    return new Date(dateString).toLocaleString()
  }

  // Calculate success rate
  const calculateSuccessRate = (session: SessionPublic) => {
    if (!session.total_applied || session.total_applied === 0) return 0
    return Math.round(
      ((session.total_success || 0) / session.total_applied) * 100,
    )
  }

  // Handle view details
  const handleViewDetails = (sessionId: string) => {
    if (onViewDetails) {
      onViewDetails(sessionId)
    }
  }

  // Render action buttons based on session status
  const renderActionButtons = (session: SessionPublic) => {
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
                icon={<FiStopCircle />}
                size="sm"
                colorScheme="red"
                isLoading={isLoadingAction}
                onClick={() => handleStopSession(session.id!)}
              />
            </Tooltip>
          </HStack>
        )
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
                icon={<FiStopCircle />}
                size="sm"
                colorScheme="red"
                isLoading={isLoadingAction}
                onClick={() => handleStopSession(session.id!)}
              />
            </Tooltip>
          </HStack>
        )
      case "starting":
      case "stopping":
        return <Spinner size="sm" />
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
                onClick={() => handleOpenDeleteModal(session.id!)}
              />
            </Tooltip>
          </HStack>
        )
      default:
        return (
          <HStack spacing={2}>
            <Tooltip label="Delete Session">
              <IconButton
                aria-label="Delete Session"
                icon={<FiTrash2 />}
                size="sm"
                colorScheme="red"
                onClick={() => handleOpenDeleteModal(session.id!)}
              />
            </Tooltip>
          </HStack>
        )
    }
  }

  return (
    <Box>
      <Flex justifyContent="space-between" alignItems="center" mb={4}>
        <Heading size="md">Bot Sessions</Heading>
        <Button
          leftIcon={<FiPlus />}
          variant="primary"
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
              <Text>
                You need to add LinkedIn credentials before creating a bot
                session.
              </Text>
            </Flex>
          </CardBody>
        </Card>
      )}

      {isLoadingSessions ? (
        <Flex justifyContent="center" py={8}>
          <Spinner size="lg" />
        </Flex>
      ) : sessionsError ? (
        <Text color="red.500">{sessionsError}</Text>
      ) : sessions.length === 0 ? (
        <Card>
          <CardBody>
            <Text textAlign="center">
              No bot sessions found. Create a new session to start automating
              job applications.
            </Text>
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
                      {session.id?.substring(0, 8) || "Session"}
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
                        onClick={() => handleViewDetails(session.id!)}
                      />
                    </Tooltip>
                  </HStack>
                </Flex>
              </CardHeader>
              <CardBody>
                <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                  <GridItem>
                    <Text fontSize="sm" color="gray.500">
                      Created
                    </Text>
                    <Text>{formatDate(session.created_at)}</Text>
                  </GridItem>
                  <GridItem>
                    <Text fontSize="sm" color="gray.500">
                      Last Activity
                    </Text>
                    <Text>{formatDate(session.last_heartbeat_at)}</Text>
                  </GridItem>
                </Grid>

                <Divider my={3} />

                <Box mb={3}>
                  <Flex justify="space-between" mb={1}>
                    <Text fontSize="sm">
                      Progress: {session.total_applied || 0} /{" "}
                      {session.applies_limit}
                    </Text>
                    <Text fontSize="sm">
                      {Math.min(
                        Math.round(
                          ((session.total_applied || 0) /
                            (session.applies_limit || 1)) *
                            100,
                        ),
                        100,
                      )}
                      %
                    </Text>
                  </Flex>
                  <Progress
                    value={Math.min(
                      ((session.total_applied || 0) /
                        (session.applies_limit || 1)) *
                        100,
                      100,
                    )}
                    size="sm"
                    colorScheme="teal"
                    borderRadius="full"
                  />
                </Box>

                <Grid templateColumns="repeat(3, 1fr)" gap={2}>
                  <GridItem>
                    <HStack>
                      <Icon as={FiActivity} color="green.500" />
                      <Text fontSize="sm">
                        {session.total_success || 0} Successful
                      </Text>
                    </HStack>
                  </GridItem>
                  <GridItem>
                    <HStack>
                      <Icon as={FiAlertCircle} color="red.500" />
                      <Text fontSize="sm">
                        {session.total_failed || 0} Failed
                      </Text>
                    </HStack>
                  </GridItem>
                  <GridItem>
                    <HStack>
                      <Icon as={FiInfo} color="blue.500" />
                      <Text fontSize="sm">
                        {calculateSuccessRate(session)}% Success Rate
                      </Text>
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
                  onChange={(e) =>
                    handleInputChange("credentials_id", e.target.value)
                  }
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
                  onChange={(value) =>
                    handleInputChange("applies_limit", Number.parseInt(value))
                  }
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
                  onChange={(value) => handleRadioChange(value)}
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
              onClick={handleSubmit}
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
        onDelete={handleConfirmDelete}
        title="Delete Bot Session"
        message="Are you sure you want to delete this bot session? This action cannot be undone."
      />
    </Box>
  )
}

export default BotSessionManager
