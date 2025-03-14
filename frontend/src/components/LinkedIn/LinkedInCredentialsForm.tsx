import { useState, forwardRef, useImperativeHandle } from "react"
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  FormErrorMessage,
  VStack,
  useToast,
  Text,
  InputGroup,
  InputRightElement,
  InputLeftElement,
  Icon,
  Divider,
  Alert,
  AlertIcon,
  useColorModeValue,
} from "@chakra-ui/react"
import { FiEye, FiEyeOff, FiLock, FiUser } from "react-icons/fi"
import { CredentialsService } from "../../client"
import { ApiError } from "../../client"

interface LinkedInCredentialsFormProps {
  onSuccess?: () => void
  hideSubmitButton?: boolean
}

interface FormData {
  email: string
  password: string
}

// Define the ref type
export interface LinkedInCredentialsFormRef {
  submit: () => Promise<boolean>
}

const LinkedInCredentialsForm = forwardRef<LinkedInCredentialsFormRef, LinkedInCredentialsFormProps>(
  ({ onSuccess, hideSubmitButton = false }, ref) => {
    const [formData, setFormData] = useState<FormData>({
      email: "",
      password: "",
    })
    const [errors, setErrors] = useState<Record<string, string>>({})
    const [isLoading, setIsLoading] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    
    const toast = useToast()
    
    // Colors for theming
    const borderColor = useColorModeValue("gray.200", "gray.600")
    const alertBgColor = useColorModeValue("blue.50", "blue.900")
    
    // Expose the submit method to the parent component through ref
    useImperativeHandle(ref, () => ({
      submit: async () => {
        try {
          if (!validateForm()) {
            // Lança uma exceção com mensagem específica se a validação falhar
            throw new Error("LinkedIn credentials validation failed");
          }
          
          setIsLoading(true)
          
          // Call API to save LinkedIn credentials
          await CredentialsService.createCredentials({
            requestBody: {
              email: formData.email,
              password: formData.password,
            }
          })
          
          // Reset form
          setFormData({
            email: "",
            password: "",
          })
          
          // Call success callback if provided
          if (onSuccess) {
            onSuccess()
          }
          
          return true
        } catch (error) {
          console.error("Error saving LinkedIn credentials:", error)
          
          // Show error message apenas se não for um erro de validação
          if (!(error instanceof Error && error.message === "LinkedIn credentials validation failed")) {
            // Melhor tratamento para garantir que o erro seja sempre uma string
            let errorMessage = "Failed to save LinkedIn credentials. Please try again."
            
            // Tenta extrair detalhes do erro em diferentes formatos
            try {
              const apiError = error as ApiError
              
              if (apiError.body) {
                const errorBody = apiError.body as any
                
                if (errorBody.detail) {
                  // Se detail for um objeto (validation_error), extrair apenas as mensagens
                  if (typeof errorBody.detail === 'object') {
                    if (Array.isArray(errorBody.detail)) {
                      // Se for um array de erros
                      errorMessage = errorBody.detail
                        .map((err: any) => {
                          if (typeof err === 'object' && err.msg) {
                            return String(err.msg)
                          }
                          return String(err)
                        })
                        .join(", ")
                    } else if (errorBody.detail.msg) {
                      // Se for um único objeto de erro com a propriedade msg
                      errorMessage = String(errorBody.detail.msg)
                    } else {
                      // Para outros objetos, tente obter uma representação de string
                      errorMessage = JSON.stringify(errorBody.detail)
                    }
                  } else {
                    // Se detail for uma string ou outro valor primitivo
                    errorMessage = String(errorBody.detail)
                  }
                } else if (errorBody.message) {
                  errorMessage = String(errorBody.message)
                }
              } else if (apiError.message) {
                errorMessage = String(apiError.message)
              }
            } catch (formatError) {
              console.error("Error formatting error message:", formatError)
              // Manter a mensagem padrão em caso de erro ao extrair detalhes
            }
            
            toast({
              title: "Error",
              description: errorMessage,
              status: "error",
              duration: 5000,
              position: "bottom-right",
              isClosable: true,
            })
          }
          
          // Repropaga a exceção para ser tratada pelo componente pai
          if (error instanceof Error) {
            throw error;
          } else {
            throw new Error("Error saving LinkedIn credentials");
          }
        } finally {
          setIsLoading(false)
        }
      }
    }))
    
    const validateForm = (): boolean => {
      const newErrors: Record<string, string> = {}
      
      if (!formData.email) {
        newErrors.email = "LinkedIn email is required"
      } else if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(formData.email)) {
        newErrors.email = "Invalid email address"
      }
      
      if (!formData.password) {
        newErrors.password = "LinkedIn password is required"
      }
      
      setErrors(newErrors)
      return Object.keys(newErrors).length === 0
    }
    
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target
      setFormData(prev => ({
        ...prev,
        [name]: value
      }))
      
      // Clear error when typing
      if (errors[name]) {
        setErrors(prev => ({
          ...prev,
          [name]: ""
        }))
      }
    }
    
    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      
      // Use the ref's submit method
      await (ref as React.RefObject<LinkedInCredentialsFormRef>).current?.submit()
    }
    
    const toggleShowPassword = () => {
      setShowPassword(!showPassword)
    }
    
    return (
      <Box as="form" onSubmit={handleSubmit}>
        <VStack spacing={6} align="stretch">
          <Alert status="info" borderRadius="md" bg={alertBgColor}>
            <AlertIcon />
            <Text fontSize="sm">
            Your data is protected by end-to-end encryption and zero-knowledge security protocols. Only you and our automated job application system can access your credentials.
            </Text>
          </Alert>
          
          <FormControl isRequired isInvalid={!!errors.email}>
            <FormLabel>LinkedIn Email</FormLabel>
            <InputGroup>
              <InputLeftElement pointerEvents="none">
                <Icon as={FiUser} color="gray.500" />
              </InputLeftElement>
              <Input
                name="email"
                type="email"
                placeholder="your.email@example.com"
                value={formData.email}
                onChange={handleInputChange}
              />
            </InputGroup>
            <FormErrorMessage>{errors.email}</FormErrorMessage>
          </FormControl>
          
          <FormControl isRequired isInvalid={!!errors.password}>
            <FormLabel>LinkedIn Password</FormLabel>
            <InputGroup>
              <InputLeftElement pointerEvents="none">
                <Icon as={FiLock} color="gray.500" />
              </InputLeftElement>
              <Input
                name="password"
                type={showPassword ? "text" : "password"}
                placeholder="Your LinkedIn password"
                value={formData.password}
                onChange={handleInputChange}
              />
              <InputRightElement width="3rem">
                <Button 
                  h="1.5rem" 
                  size="sm" 
                  variant="ghost"
                  onClick={toggleShowPassword}
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  <Icon as={showPassword ? FiEyeOff : FiEye} />
                </Button>
              </InputRightElement>
            </InputGroup>
            <FormErrorMessage>{errors.password}</FormErrorMessage>
          </FormControl>
          
          <Divider borderColor={borderColor} />
          
          {!hideSubmitButton && (
            <Button
              type="submit"
              colorScheme="linkedin"
              isLoading={isLoading}
              loadingText="Saving"
              size="lg"
            >
              Save LinkedIn Credentials
            </Button>
          )}
        </VStack>
      </Box>
    )
  }
)

// Display name for debugging purposes
LinkedInCredentialsForm.displayName = "LinkedInCredentialsForm"

export default LinkedInCredentialsForm 