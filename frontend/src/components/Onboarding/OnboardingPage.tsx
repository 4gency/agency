import { useState, useEffect, useRef, useCallback } from "react"
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Progress,
  Step,
  StepDescription,
  StepIcon,
  StepIndicator,
  StepNumber,
  StepSeparator,
  StepStatus,
  StepTitle,
  Stepper,
  Text,
  useColorModeValue,
  useToast,
  HStack,
  Icon,
  VStack,
  useBreakpointValue,
} from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { ResumeSettings } from "../UserSettings/Resume"
import { JobPreferences } from "../UserSettings/JobPreferences"
import { FiUser, FiBriefcase, FiLinkedin, FiArrowRight, FiChevronLeft } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import ConfettiExplosion from "react-confetti-explosion"
import LinkedInCredentialsForm, { LinkedInCredentialsFormRef } from "../LinkedIn/LinkedInCredentialsForm"

// Define the steps for the onboarding process
const steps = [
  { title: "Resume", description: "Set up your resume", icon: FiUser },
  { title: "Job Preferences", description: "Define your job search criteria", icon: FiBriefcase },
  { title: "LinkedIn Account", description: "Connect your LinkedIn account", icon: FiLinkedin },
]

// Temporary property to track onboarding in localStorage until API is updated
const ONBOARDING_COMPLETED_KEY_PREFIX = "user_onboarding_completed_"

const OnboardingPage = () => {
  const [activeStep, setActiveStep] = useState(0)
  const [skipped, setSkipped] = useState(new Set<number>())
  const [isExploding, setIsExploding] = useState(false)
  const [stepComplete, setStepComplete] = useState([false, false, false])
  const [isUpdatingUser, setIsUpdatingUser] = useState(false)
  const [isProcessingStep, setIsProcessingStep] = useState(false)
  
  // Refs to form submission functions
  const resumeFormRef = useRef<{ submit: () => Promise<boolean> } | null>(null)
  const jobPreferencesFormRef = useRef<{ submit: () => Promise<boolean> } | null>(null)
  const linkedInFormRef = useRef<LinkedInCredentialsFormRef | null>(null)
  
  const navigate = useNavigate()
  const toast = useToast()
  const { user } = useAuth()
  
  // Get the user-specific key for localStorage
  const getUserOnboardingKey = useCallback(() => {
    if (!user) return null;
    return `${ONBOARDING_COMPLETED_KEY_PREFIX}${user.id}`
  }, [user]);

  // Colors for light/dark mode
  const bgColor = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.700")
  const stepperBgColor = useColorModeValue("gray.50", "gray.900")
  const textColor = useColorModeValue("gray.700", "gray.200")
  const secondaryTextColor = useColorModeValue("gray.600", "gray.400")

  // Responsive design adjustments
  const containerMaxW = useBreakpointValue({ base: "container.sm", md: "container.md", lg: "container.xl" })
  const stepperOrientation = useBreakpointValue({ base: "vertical", md: "horizontal" }) as "vertical" | "horizontal"
  const showStepDescription = useBreakpointValue({ 
    base: stepperOrientation === "vertical", 
    md: true 
  })

  // Check if onboarding is already completed using localStorage
  useEffect(() => {
    // If user is logged in, check if onboarding is completed for this specific user
    if (user) {
      const userOnboardingKey = getUserOnboardingKey();
      if (userOnboardingKey) {
        const isOnboardingCompleted = localStorage.getItem(userOnboardingKey) === "true";
        if (isOnboardingCompleted) {
          navigate({ to: "/" });
        }
      }
    }
  }, [user, navigate, getUserOnboardingKey]);
  
  // Function to register form refs
  const registerFormRef = (step: number, ref: any) => {
    if (step === 0) resumeFormRef.current = ref
    else if (step === 1) jobPreferencesFormRef.current = ref
    else if (step === 2) linkedInFormRef.current = ref
  }
  
  const markStepAsComplete = (step: number) => {
    const newStepComplete = [...stepComplete]
    newStepComplete[step] = true
    setStepComplete(newStepComplete)
    
    toast({
      title: `${steps[step].title} Settings Saved`,
      description: `Your ${steps[step].title.toLowerCase()} settings have been successfully saved.`,
      status: "success",
      duration: 3000,
      position: "bottom-right",
      isClosable: true,
    })
  }

  const handleNext = async () => {
    if (activeStep < steps.length - 1) {
      setIsProcessingStep(true)
      
      try {
        // Try to submit the current form
        let success = false
        
        if (activeStep === 0 && resumeFormRef.current) {
          try {
            success = await resumeFormRef.current.submit()
          } catch (formError) {
            console.error("Error submitting resume form:", formError)
            toast({
              title: "Validation Error",
              description: "Please fill all required fields in the resume form before proceeding.",
              status: "error",
              duration: 5000,
              position: "bottom-right",
              isClosable: true,
            })
            success = false
          }
        } else if (activeStep === 1 && jobPreferencesFormRef.current) {
          try {
            success = await jobPreferencesFormRef.current.submit()
          } catch (formError) {
            console.error("Error submitting job preferences form:", formError)
            toast({
              title: "Validation Error",
              description: "Please fill all required fields in the job preferences form before proceeding.",
              status: "error",
              duration: 5000,
              position: "bottom-right",
              isClosable: true,
            })
            success = false
          }
        } else if (activeStep === 2 && linkedInFormRef.current) {
          try {
            success = await linkedInFormRef.current.submit()
          } catch (formError) {
            console.error("Error submitting LinkedIn form:", formError)
            toast({
              title: "Validation Error",
              description: "Please provide valid LinkedIn credentials before proceeding.",
              status: "error",
              duration: 5000,
              position: "bottom-right",
              isClosable: true,
            })
            success = false
          }
        } else {
          // If no form ref is available, assume success
          success = true
        }
        
        if (success) {
          markStepAsComplete(activeStep)
          setActiveStep((prevStep) => prevStep + 1)
        }
      } catch (error) {
        console.error(`Error in handleNext for step ${activeStep}:`, error)
        toast({
          title: "Error",
          description: "There was a problem processing your information. Please try again.",
          status: "error",
          duration: 5000,
          position: "bottom-right",
          isClosable: true,
        })
      } finally {
        setIsProcessingStep(false)
      }
    } else {
      // All steps completed
      handleComplete()
    }
  }

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1)
  }

  const handleSkip = () => {
    // Skip the current step
    const newSkipped = new Set(skipped)
    newSkipped.add(activeStep)
    setSkipped(newSkipped)
    
    // Go to next step or complete if all steps are done
    if (activeStep < steps.length - 1) {
      setActiveStep((prevStep) => prevStep + 1)
    } else {
      const userOnboardingKey = getUserOnboardingKey();
      if (userOnboardingKey) {
        localStorage.setItem(userOnboardingKey, "true");
      }
      
      toast({
        title: "Setup Skipped",
        description: "You can complete your LinkedIn setup later from your profile settings.",
        status: "info",
        duration: 3000,
        position: "bottom-right",
        isClosable: true,
      })
      
      // Redirect to dashboard
      navigate({ to: "/" })
    }
  }

  const handleComplete = async () => {
    // Attempt to submit the last form if not already complete
    if (!stepComplete[activeStep]) {
      setIsProcessingStep(true)
      
      try {
        let success = false
        
        if (activeStep === 2 && linkedInFormRef.current) {
          try {
            success = await linkedInFormRef.current.submit()
          } catch (formError) {
            console.error("Error submitting LinkedIn form:", formError)
            toast({
              title: "Validation Error",
              description: "Please provide valid LinkedIn credentials before completing the onboarding.",
              status: "error",
              duration: 5000,
              position: "bottom-right",
              isClosable: true,
            })
            setIsProcessingStep(false)
            return
          }
        }
        
        if (!success) {
          setIsProcessingStep(false)
          return
        }
        
        markStepAsComplete(activeStep)
      } catch (error) {
        console.error(`Error in handleComplete for step ${activeStep}:`, error)
        toast({
          title: "Error",
          description: "There was a problem processing your information. Please try again.",
          status: "error",
          duration: 5000,
          position: "bottom-right",
          isClosable: true,
        })
        setIsProcessingStep(false)
        return
      }
    }
    
    setIsUpdatingUser(true)
    
    try {
      // Store onboarding completion in localStorage for this specific user
      const userOnboardingKey = getUserOnboardingKey();
      if (userOnboardingKey) {
        localStorage.setItem(userOnboardingKey, "true");
      }
      
      // We'll skip updating the user object until the API supports the onboarding_completed field
      // Instead, we'll just rely on localStorage to track completion status
      
      // Show confetti explosion
      setIsExploding(true)
      
      // Show success message
      toast({
        title: "Onboarding Completed!",
        description: "Your account is now set up and ready to use.",
        status: "success",
        duration: 5000,
        position: "bottom-right",
        isClosable: true,
      })
      
      // Wait a moment to show the celebration before redirecting
      setTimeout(() => {
        // Redirect to dashboard
        navigate({ to: "/" })
      }, 3000)
      
    } catch (error) {
      console.error("Failed to update user onboarding status:", error)
      toast({
        title: "Error",
        description: "Failed to complete onboarding. Please try again.",
        status: "error",
        duration: 5000,
        position: "bottom-right",
        isClosable: true,
      })
    } finally {
      setIsUpdatingUser(false)
      setIsProcessingStep(false)
    }
  }

  // Render the current step content
  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <ResumeSettings 
              ref={(ref) => registerFormRef(0, ref)}
              onComplete={() => markStepAsComplete(0)}
              isOnboarding={true}
              hideSubmitButton={true}
            />
          </Box>
        )
      case 1:
        return (
          <Box maxW={{ base: "100%", md: "container.md" }} mx="auto" px={{ base: 2, md: 0 }}>
            <JobPreferences 
              ref={(ref) => registerFormRef(1, ref)}
              onComplete={() => markStepAsComplete(1)}
              isOnboarding={true}
              hideSubmitButton={true}
            />
          </Box>
        )
      case 2:
        return (
          <Box borderWidth="1px" borderRadius="lg" borderColor={borderColor} bg={bgColor} maxW={{ base: "100%", md: "container.md" }} mx="auto" p={{ base: 4, md: 6 }} mb={10}>
            <VStack spacing={6} align="stretch">
              <Heading size="md">Connect Your LinkedIn Account</Heading>
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
                ref={(ref) => registerFormRef(2, ref)}
                onSuccess={() => markStepAsComplete(2)}
                hideSubmitButton={true}
              />
            </VStack>
          </Box>
        )
      default:
        return null
    }
  }

  // Welcome message for the first step
  const renderWelcomeHeader = () => {
    if (activeStep === 0) {
      return (
        <Box mb={8} textAlign="center">
          <Heading as="h1" size="xl" mb={3}>
            Welcome to Your Job Search Automation
          </Heading>
          <Text fontSize="lg" color={secondaryTextColor} maxW="container.md" mx="auto">
            Complete these three simple steps to set up your account and start automating your job search.
            Each step is essential to ensure you get the best results.
          </Text>
        </Box>
      )
    }
    return null
  }

  return (
    <Container maxW={containerMaxW} py={10} px={{ base: 3, md: 6 }}>
      {isExploding && (
        <Box position="fixed" top="50%" left="50%" zIndex={1000} transform="translate(-50%, -50%)">
          <ConfettiExplosion 
            force={0.8}
            duration={3000}
            particleCount={250}
            width={1600}
          />
        </Box>
      )}
      
      <VStack spacing={8}>
        {renderWelcomeHeader()}
        
        <Box w="100%" p={{ base: 3, md: 6 }} borderRadius="lg" bg={stepperBgColor} boxShadow="sm">
          <Stepper index={activeStep} orientation={stepperOrientation} colorScheme="teal" gap={{ base: 2, md: 4 }}>
            {steps.map((step, index) => (
              <Step key={index}>
                <StepIndicator>
                  <StepStatus
                    complete={<StepIcon />}
                    incomplete={<Icon as={step.icon} />}
                    active={<StepNumber />}
                  />
                </StepIndicator>
                <Box flexShrink="0">
                  <StepTitle>{step.title}</StepTitle>
                  {showStepDescription && (
                    <StepDescription>{step.description}</StepDescription>
                  )}
                </Box>
                <StepSeparator />
              </Step>
            ))}
          </Stepper>
        </Box>
        
        {/* Progress indicator */}
        <Box w="100%">
          <Flex justify="space-between" mb={2}>
            <Text fontSize="sm" color={secondaryTextColor}>
              Step {activeStep + 1} of {steps.length}
            </Text>
            <Text fontSize="sm" color={secondaryTextColor}>
              {Math.round(((activeStep + (stepComplete[activeStep] ? 1 : 0)) / steps.length) * 100)}% Complete
            </Text>
          </Flex>
          <Progress 
            value={((activeStep + (stepComplete[activeStep] ? 1 : 0)) / steps.length) * 100} 
            size="sm" 
            colorScheme="teal" 
            borderRadius="full" 
          />
        </Box>
        
        {/* Step content */}
        <Box w="100%" borderRadius="lg" boxShadow="md">
          {renderStepContent()}
        </Box>
        
        {/* Navigation buttons */}
        <HStack spacing={4} w="100%" justifyContent="space-between" mt={4}>
          <Button 
            onClick={handleBack} 
            isDisabled={activeStep === 0 || isProcessingStep || isUpdatingUser}
            variant="outline"
            size={{ base: "md", md: "md" }}
            aria-label="Go back"
            minW="40px"
          >
            <Icon as={FiChevronLeft} boxSize={5} />
          </Button>
          
          <HStack>
            <Button 
              onClick={handleSkip}
              variant="ghost"
              isDisabled={isProcessingStep || isUpdatingUser}
              size={{ base: "md", md: "md" }}
            >
              Skip for now
            </Button>
            
            <Button 
              onClick={handleNext} 
              colorScheme="teal"
              rightIcon={activeStep < steps.length - 1 ? <FiArrowRight /> : undefined}
              isLoading={isProcessingStep || isUpdatingUser}
              loadingText={activeStep === steps.length - 1 ? "Completing" : "Saving"}
              isDisabled={false}
              size={{ base: "md", md: "md" }}
            >
              {activeStep === steps.length - 1 ? "Complete Setup" : "Next Step"}
            </Button>
          </HStack>
        </HStack>
      </VStack>
    </Container>
  )
}

export default OnboardingPage 