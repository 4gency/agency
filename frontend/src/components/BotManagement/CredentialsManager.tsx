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
} from "@chakra-ui/react"
import { useState } from "react"
import { FiEdit, FiPlus, FiTrash2 } from "react-icons/fi"
import {
  type CredentialsCreate,
  type CredentialsPublic,
  CredentialsService,
  type CredentialsUpdate,
} from "../../client"
import DeleteAlert from "../Common/DeleteAlert"
import useCredentialsData from "../../hooks/useCredentialsData"

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

  // Handle credential creation
  const handleCreateCredential = async () => {
    try {
      await CredentialsService.createCredentials({
        requestBody: formData as CredentialsCreate,
      })
      toast({
        title: "Success",
        description: "Credential created successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      onCreateClose()
      setFormData({ email: "", password: "" })
      await refetchCredentials()

      // Notify parent component that credentials have been updated
      if (onCredentialsUpdate) {
        onCredentialsUpdate()
      }
    } catch (err) {
      console.error("Error creating credential:", err)
      toast({
        title: "Error",
        description: "Failed to create credential",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    }
  }

  // Handle credential update
  const handleUpdateCredential = async () => {
    try {
      if (!credentialToEdit) return

      await CredentialsService.updateCredentials({
        credentialsId: credentialToEdit.id,
        requestBody: formData as CredentialsUpdate,
      })
      toast({
        title: "Success",
        description: "Credential updated successfully",
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
        description: "Failed to update credential",
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
      <Modal isOpen={isCreateOpen} onClose={handleCreateClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add LinkedIn Credential</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  name="email"
                  value={formData.email || ""}
                  onChange={handleInputChange}
                  placeholder="example@linkedin.com"
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Password</FormLabel>
                <Input
                  name="password"
                  type="password"
                  value={formData.password || ""}
                  onChange={handleInputChange}
                  placeholder="LinkedIn password"
                />
              </FormControl>
            </Stack>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" mr={3} onClick={handleCreateClose}>
              Cancel
            </Button>
            <Button
              colorScheme="teal"
              onClick={handleCreateCredential}
              isDisabled={!formData.email || !formData.password}
            >
              Save
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Credential Modal */}
      <Modal isOpen={isEditOpen} onClose={handleEditClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit LinkedIn Credential</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  name="email"
                  value={formData.email || ""}
                  onChange={handleInputChange}
                  placeholder="example@linkedin.com"
                />
              </FormControl>
              <FormControl>
                <FormLabel>Password</FormLabel>
                <Input
                  name="password"
                  type="password"
                  value={formData.password || ""}
                  onChange={handleInputChange}
                  placeholder="Optional"
                />
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Leave blank to keep your current password
                </Text>
              </FormControl>
            </Stack>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" mr={3} onClick={handleEditClose}>
              Cancel
            </Button>
            <Button
              colorScheme="teal"
              onClick={handleUpdateCredential}
              isDisabled={!formData.email}
            >
              Update
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
