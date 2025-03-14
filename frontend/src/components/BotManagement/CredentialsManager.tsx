import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  HStack,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spinner,
  Stack,
  Text,
  useDisclosure,
  useToast,
  VStack,
  useColorModeValue,
  Icon,
} from "@chakra-ui/react"
import { useState, useRef } from "react"
import { FiEdit, FiPlus, FiTrash2, FiLinkedin, FiUser, FiLock } from "react-icons/fi"
import {
  type CredentialsPublic,
  CredentialsService,
  type CredentialsUpdate,
} from "../../client"
import DeleteAlert from "../Common/DeleteAlert"
import useCredentialsData from "../../hooks/useCredentialsData"
import LinkedInCredentialsForm, { LinkedInCredentialsFormRef } from "../LinkedIn/LinkedInCredentialsForm"

export type CredentialsManagerProps = {
  onCredentialSelect?: (credentialId: string) => void
  selectedCredentialId?: string
  onCredentialsUpdate?: () => void
}

const CredentialsManager = ({
  onCredentialSelect,
  selectedCredentialId,
  onCredentialsUpdate,
}: CredentialsManagerProps) => {
  const { 
    credentials, 
    isLoading, 
    error: credentialsError, 
    refetchCredentials 
  } = useCredentialsData()
  const [credentialToDelete, setCredentialToDelete] = useState<string | null>(
    null,
  )
  const [credentialToEdit, setCredentialToEdit] =
    useState<CredentialsPublic | null>(null)
  const [formData, setFormData] = useState<{
    email: string
    password: string
  }>({
    email: "",
    password: "",
  })

  const {
    isOpen: isCreateOpen,
    onOpen: onCreateOpen,
    onClose: onCreateClose,
  } = useDisclosure()
  const {
    isOpen: isEditOpen,
    onOpen: onEditOpen,
    onClose: onEditClose,
  } = useDisclosure()
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure()

  const toast = useToast()

  // Handle input changes for create/edit forms
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value,
    })
  }

  // Open edit modal and set form data
  const handleEditClick = (credential: CredentialsPublic) => {
    setCredentialToEdit(credential)
    setFormData({
      email: credential.email,
      password: "", // Password is not returned from the API for security reasons
    })
    onEditOpen()
  }

  // Handle credential update
  const handleUpdateCredential = async () => {
    try {
      if (!credentialToEdit) return
      
      // Verificar se a senha foi preenchida
      if (!formData.password || formData.password.trim() === "") {
        toast({
          title: "Validation Error",
          description: "Password is required. Please enter a new password.",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
        return;
      }

      // Garantir que a senha não seja enviada como nula ou vazia
      const password = formData.password.trim();
      
      // Enviar apenas a senha para atualização, não o email
      await CredentialsService.updateCredentials({
        credentialsId: credentialToEdit.id,
        requestBody: { 
          password: password 
        } as CredentialsUpdate,
      })
      toast({
        title: "Success",
        description: "Password updated successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      onEditClose()
      setFormData({ email: "", password: "" })
      await refetchCredentials()

      // Notify parent component that credentials have been updated
      if (onCredentialsUpdate) {
        onCredentialsUpdate()
      }
    } catch (err) {
      console.error("Error updating credential:", err)
      toast({
        title: "Error",
        description: "Failed to update password",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    }
  }

  // Open delete confirmation modal
  const handleDeleteClick = (id: string) => {
    setCredentialToDelete(id)
    onDeleteOpen()
  }

  // Handle credential deletion
  const handleDeleteCredential = async () => {
    try {
      if (!credentialToDelete) return

      await CredentialsService.deleteCredentials({
        credentialsId: credentialToDelete,
      })
      toast({
        title: "Success",
        description: "Credential deleted successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      onDeleteClose()
      setCredentialToDelete(null)
      await refetchCredentials()

      // Notify parent component that credentials have been updated
      if (onCredentialsUpdate) {
        onCredentialsUpdate()
      }
    } catch (err) {
      console.error("Error deleting credential:", err)
      toast({
        title: "Error",
        description: "Failed to delete credential",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    }
  }

  // Reset form data when closing modals
  const handleCreateClose = () => {
    setFormData({ email: "", password: "" })
    onCreateClose()
  }

  const handleEditClose = () => {
    setCredentialToEdit(null)
    setFormData({ email: "", password: "" })
    onEditClose()
  }

  // Ref para o formulário do LinkedIn
  const linkedInFormRef = useRef<LinkedInCredentialsFormRef | null>(null)

  // Cores para temas claros/escuros
  const bgColor = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.700")
  const textColor = useColorModeValue("gray.700", "gray.200")
  const secondaryTextColor = useColorModeValue("gray.600", "gray.400")

  // Handler para sucesso ao salvar credencial do LinkedIn
  const handleLinkedInSuccess = async () => {
    toast({
      title: "Success",
      description: "Credential created successfully",
      status: "success",
      duration: 3000,
      isClosable: true,
    })
    onCreateClose()
    await refetchCredentials()

    // Notify parent component that credentials have been updated
    if (onCredentialsUpdate) {
      onCredentialsUpdate()
    }
  }

  // Handler para salvar credencial com o novo formulário
  const handleSaveLinkedIn = async () => {
    try {
      if (linkedInFormRef.current) {
        await linkedInFormRef.current.submit()
      }
    } catch (error) {
      console.error("Error saving LinkedIn credential:", error)
    }
  }

  return (
    <Box>
      <Flex justifyContent="space-between" alignItems="center" mb={4}>
        <Heading size="md">LinkedIn Credentials</Heading>
        <Button leftIcon={<FiPlus />} variant="primary" onClick={onCreateOpen}>
          Add Credential
        </Button>
      </Flex>

      {isLoading ? (
        <Flex justifyContent="center" py={8}>
          <Spinner size="lg" />
        </Flex>
      ) : credentialsError ? (
        <Text color="red.500">Erro ao carregar credenciais</Text>
      ) : credentials.length === 0 ? (
        <Card>
          <CardBody>
            <Text textAlign="center">
              No credentials found. Add your LinkedIn credentials to start using
              the bot.
            </Text>
          </CardBody>
        </Card>
      ) : (
        <VStack spacing={3} align="stretch">
          {credentials.map((credential) => (
            <Card
              key={credential.id}
              cursor="pointer"
              borderColor={
                selectedCredentialId === credential.id
                  ? "ui.main"
                  : "transparent"
              }
              borderWidth={2}
              onClick={() => onCredentialSelect?.(credential.id)}
              _hover={{ shadow: "md" }}
              transition="all 0.2s"
            >
              <CardBody>
                <Flex justify="space-between" align="center">
                  <Box>
                    <HStack mb={1}>
                      <Text fontWeight="bold">{credential.email}</Text>
                      {selectedCredentialId === credential.id && (
                        <Badge colorScheme="teal">Selected</Badge>
                      )}
                    </HStack>
                    <Text color="gray.500">●●●●●●●●●●●●</Text>
                  </Box>
                  <HStack spacing={2}>
                    <IconButton
                      aria-label="Edit credential"
                      icon={<FiEdit />}
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEditClick(credential)
                      }}
                    />
                    <IconButton
                      aria-label="Delete credential"
                      icon={<FiTrash2 />}
                      size="sm"
                      variant="ghost"
                      colorScheme="red"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteClick(credential.id)
                      }}
                    />
                  </HStack>
                </Flex>
              </CardBody>
            </Card>
          ))}
        </VStack>
      )}

      {/* Create Credential Modal */}
      <Modal isOpen={isCreateOpen} onClose={handleCreateClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Connect LinkedIn Account</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Box borderWidth="1px" borderRadius="lg" borderColor={borderColor} bg={bgColor} p={6}>
              <VStack spacing={6} align="stretch">
                <Text color={textColor}>
                  To enable automated job applications, you need to connect your LinkedIn account.
                  This allows our system to apply to jobs on your behalf.
                </Text>
                
                <HStack spacing={4} mt={4}>
                  <Box 
                    bg="linkedin.500" 
                    color="white" 
                    borderRadius="md" 
                    p={2} 
                    width="50px" 
                    height="50px" 
                    display="flex" 
                    alignItems="center" 
                    justifyContent="center"
                  >
                    <Icon as={FiLinkedin} boxSize={6} />
                  </Box>
                  <VStack align="start" spacing={1}>
                    <Text fontWeight="bold">LinkedIn Integration</Text>
                    <Text fontSize="sm" color={secondaryTextColor}>
                      Securely connect to automate your job search
                    </Text>
                  </VStack>
                </HStack>
                
                <LinkedInCredentialsForm 
                  ref={linkedInFormRef}
                  onSuccess={handleLinkedInSuccess}
                  hideSubmitButton={true}
                />
              </VStack>
            </Box>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" mr={3} onClick={handleCreateClose}>
              Cancel
            </Button>
            <Button
              colorScheme="linkedin"
              onClick={handleSaveLinkedIn}
            >
              Save LinkedIn Credentials
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Credential Modal */}
      <Modal isOpen={isEditOpen} onClose={handleEditClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Update LinkedIn Password</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Box borderWidth="1px" borderRadius="lg" borderColor={borderColor} bg={bgColor} p={6}>
              <VStack spacing={6} align="stretch">
                <Text color={textColor}>
                  You can update your LinkedIn password here. The email address cannot be modified.
                </Text>
                
                <HStack spacing={4} mt={4}>
                  <Box 
                    bg="linkedin.500" 
                    color="white" 
                    borderRadius="md" 
                    p={2} 
                    width="50px" 
                    height="50px" 
                    display="flex" 
                    alignItems="center" 
                    justifyContent="center"
                  >
                    <Icon as={FiLinkedin} boxSize={6} />
                  </Box>
                  <VStack align="start" spacing={1}>
                    <Text fontWeight="bold">LinkedIn Integration</Text>
                    <Text fontSize="sm" color={secondaryTextColor}>
                      Securely update your password
                    </Text>
                  </VStack>
                </HStack>

                <Stack spacing={4}>
                  <FormControl>
                    <FormLabel>Email</FormLabel>
                    <InputGroup>
                      <InputLeftElement pointerEvents="none">
                        <Icon as={FiUser} color="gray.500" />
                      </InputLeftElement>
                      <Input
                        name="email"
                        value={formData.email || ""}
                        isReadOnly
                        isDisabled
                        bg={useColorModeValue("gray.100", "gray.700")}
                        cursor="not-allowed"
                      />
                    </InputGroup>
                    <Text fontSize="sm" color="gray.500" mt={1}>
                      Email cannot be changed. If needed, delete this credential and create a new one.
                    </Text>
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>New Password</FormLabel>
                    <InputGroup>
                      <InputLeftElement pointerEvents="none">
                        <Icon as={FiLock} color="gray.500" />
                      </InputLeftElement>
                      <Input
                        name="password"
                        type="password"
                        value={formData.password || ""}
                        onChange={handleInputChange}
                        placeholder="Enter new password"
                        required
                      />
                    </InputGroup>
                    <Text fontSize="sm" color="gray.500" mt={1}>
                      Enter your new LinkedIn password
                    </Text>
                  </FormControl>
                </Stack>
              </VStack>
            </Box>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" mr={3} onClick={handleEditClose}>
              Cancel
            </Button>
            <Button
              colorScheme="linkedin"
              onClick={handleUpdateCredential}
              isDisabled={!formData.password || formData.password.trim() === ""}
            >
              Update Password
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation */}
      <DeleteAlert
        isOpen={isDeleteOpen}
        onClose={onDeleteClose}
        onDelete={handleDeleteCredential}
        title="Delete Credential"
        message="Are you sure you want to delete this credential? This action cannot be undone."
      />
    </Box>
  )
}

export default CredentialsManager
