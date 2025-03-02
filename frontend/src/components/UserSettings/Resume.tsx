import {
  Button,
  Container,
  Divider,
  Flex,
  Heading,
  Skeleton,
  Stack,
  useColorModeValue,
  useToast,
} from "@chakra-ui/react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { 
  ConfigsService, 
  SubscriptionsService 
} from "../../client/sdk.gen"
import { 
  GetPlainTextResumeResponse
} from "../../client/types.gen"
import React, { useEffect, useState } from "react"
import { ResumeForm } from "./types"

// Import all section components
import PersonalInformationSection from "./ResumeSections/PersonalInformationSection"
import EducationSection from "./ResumeSections/EducationSection"
import WorkExperienceSection from "./ResumeSections/WorkExperienceSection"
import ProjectsSection from "./ResumeSections/ProjectsSection"
import SkillsSection from "./ResumeSections/SkillsSection"
import LanguagesSection from "./ResumeSections/LanguagesSection"
import AvailabilitySection from "./ResumeSections/AvailabilitySection"
import SalaryExpectationSection from "./ResumeSections/SalaryExpectationSection"
import WorkPreferenceSection from "./ResumeSections/WorkPreferenceSection"
import InterestsSection from "./ResumeSections/InterestsSection"

// Default empty form values
const defaultValues: ResumeForm = {
  personal_information: {
    name: "",
    surname: "",
    email: "",
  },
  education: [],
  work_experience: [],
  projects: [],
  skills: [],
  languages: [],
  salary_expectation: {
    minimum: undefined,
    maximum: undefined,
    currency: "",
  },
  work_preference: {
    remote: false,
    hybrid: false,
    on_site: false,
    relocation: false,
  },
  interests: [],
}

// Function to transform API response to our form model
const transformApiResponseToFormData = (apiData: GetPlainTextResumeResponse): ResumeForm => {
  try {
    // Check if we received a JSON string and parse it
    if (typeof apiData === 'string') {
      try {
        const parsed = JSON.parse(apiData)
        return {
          ...defaultValues,
          ...parsed,
        }
      } catch (e) {
        console.error("Error parsing resume JSON string:", e)
        return defaultValues
      }
    }
    
    // Handle case where we have plain text resume in the actual structure
    if (apiData.personal_information) {
      return {
        personal_information: {
          name: apiData.personal_information.name || "",
          surname: apiData.personal_information.surname || "",
          email: apiData.personal_information.email || "",
          date_of_birth: apiData.personal_information.date_of_birth,
          country: apiData.personal_information.country,
          city: apiData.personal_information.city,
          address: apiData.personal_information.address,
          zip_code: apiData.personal_information.zip_code,
          phone_prefix: apiData.personal_information.phone_prefix,
          phone: apiData.personal_information.phone,
          linkedin: apiData.personal_information.linkedin,
          github: apiData.personal_information.github,
        },
        education: [],
        work_experience: [],
        projects: [],
        skills: [],
        languages: [],
        availability: apiData.availability?.notice_period || "",
        salary_expectation: {
          minimum: undefined,
          maximum: undefined,
          currency: "",
        },
        work_preference: {
          remote: apiData.work_preferences?.remote_work || false,
          hybrid: false,
          on_site: apiData.work_preferences?.in_person_work || false,
          relocation: apiData.work_preferences?.open_to_relocation || false,
        },
        interests: apiData.interests || [],
      }
    }
    
    return defaultValues
  } catch (error) {
    console.error("Error transforming API response:", error)
    return defaultValues
  }
}

// Function to transform form data to API model
const transformFormToApiData = (data: ResumeForm): GetPlainTextResumeResponse => {
  try {
    return {
      personal_information: {
        name: data.personal_information.name,
        surname: data.personal_information.surname,
        email: data.personal_information.email,
        date_of_birth: data.personal_information.date_of_birth,
        country: data.personal_information.country,
        city: data.personal_information.city,
        address: data.personal_information.address,
        zip_code: data.personal_information.zip_code,
        phone_prefix: data.personal_information.phone_prefix,
        phone: data.personal_information.phone,
        linkedin: data.personal_information.linkedin,
        github: data.personal_information.github,
      },
      interests: data.interests,
      availability: {
        notice_period: data.availability,
      },
      work_preferences: {
        remote_work: data.work_preference.remote,
        in_person_work: data.work_preference.on_site,
        open_to_relocation: data.work_preference.relocation,
        willing_to_complete_assessments: false,
        willing_to_undergo_drug_tests: false,
        willing_to_undergo_background_checks: false,
      },
    }
  } catch (error) {
    console.error("Error transforming form data to API model:", error)
    return {}
  }
}

// Loading skeleton component
const LoadingSkeleton: React.FC = () => (
  <Stack spacing={6} width="100%">
    <Skeleton height="40px" width="200px" />
    <Skeleton height="100px" />
    <Skeleton height="200px" />
    <Skeleton height="150px" />
    <Skeleton height="100px" />
  </Stack>
)

// Main component
export const ResumePage: React.FC = () => {
  const toast = useToast()
  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")
  const [subscriptionId, setSubscriptionId] = useState<string>("")
  const [isLoadingSubscription, setIsLoadingSubscription] = useState<boolean>(true)

  // Form setup
  const {
    register,
    handleSubmit,
    control,
    setValue,
    getValues,
    reset,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<ResumeForm>({
    defaultValues,
  })

  // Fetch user subscriptions
  const { data: subscriptions, isLoading: isLoadingSubscriptions } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: async () => {
      return await SubscriptionsService.getUserSubscriptions({ onlyActive: true })
    },
  })

  // Set subscription ID when data is available
  useEffect(() => {
    if (subscriptions && subscriptions.length > 0) {
      setSubscriptionId(subscriptions[0].id)
      setIsLoadingSubscription(false)
    }
  }, [subscriptions])

  // Fetch resume data
  const { data: resumeData, isLoading: isLoadingResume } = useQuery({
    queryKey: ["plainTextResume", subscriptionId],
    queryFn: async () => {
      if (!subscriptionId) return null
      return await ConfigsService.getPlainTextResume({ subscriptionId })
    },
    enabled: !!subscriptionId && !isLoadingSubscription,
    retry: false,
  })

  // Handle resume fetch error
  useEffect(() => {
    if (!isLoadingResume && !resumeData && subscriptionId) {
      toast({
        title: "Error fetching resume",
        description: "There was an error loading your resume data.",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }, [isLoadingResume, resumeData, subscriptionId, toast])

  // Update resume mutation
  const updateResumeMutation = useMutation({
    mutationFn: async (data: ResumeForm) => {
      if (!subscriptionId) throw new Error("No subscription ID available")
      const apiData = transformFormToApiData(data)
      return await ConfigsService.updatePlainTextResume({
        subscriptionId,
        requestBody: apiData
      })
    },
    onSuccess: () => {
      toast({
        title: "Resume updated",
        description: "Your resume has been successfully updated.",
        status: "success",
        duration: 5000,
        isClosable: true,
      })
    },
    onError: (error: Error) => {
      console.error("Error updating resume:", error)
      toast({
        title: "Error updating resume",
        description: "There was an error saving your resume data.",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    },
  })

  // Parse and set form data when API response is received
  useEffect(() => {
    if (resumeData) {
      const formData = transformApiResponseToFormData(resumeData)
      reset(formData)
    }
  }, [resumeData, reset])

  // Form submission handler
  const onSubmit = (data: ResumeForm) => {
    updateResumeMutation.mutate(data)
  }

  const isLoading = isLoadingSubscriptions || isLoadingSubscription || isLoadingResume

  return (
    <Container maxW="6xl" py={8}>
      <Heading as="h1" mb={8} fontSize="2xl" fontWeight="bold">
        Resume
      </Heading>

      {isLoading ? (
        <LoadingSkeleton />
      ) : (
        <form onSubmit={handleSubmit(onSubmit)}>
          <Stack spacing={8}>
            <PersonalInformationSection register={register} errors={errors} />
            
            <Divider />
            
            <EducationSection 
              register={register} 
              errors={errors} 
              control={control} 
            />
            
            <Divider />
            
            <WorkExperienceSection 
              register={register} 
              errors={errors} 
              control={control} 
            />
            
            <Divider />
            
            <ProjectsSection 
              register={register} 
              errors={errors} 
              control={control} 
            />
            
            <Divider />
            
            <SkillsSection 
              register={register} 
              errors={errors} 
              setValue={setValue} 
              getValues={getValues} 
            />
            
            <Divider />
            
            <LanguagesSection 
              register={register} 
              errors={errors} 
              control={control} 
            />
            
            <Divider />
            
            <AvailabilitySection register={register} errors={errors} />
            
            <Divider />
            
            <SalaryExpectationSection register={register} errors={errors} />
            
            <Divider />
            
            <WorkPreferenceSection register={register} errors={errors} />
            
            <Divider />
            
            <InterestsSection 
              register={register} 
              errors={errors} 
              setValue={setValue} 
              getValues={getValues} 
            />
            
            <Flex justify="flex-end" mt={6}>
              <Button
                type="submit"
                isLoading={isSubmitting || updateResumeMutation.isPending}
                bg={buttonBg}
                color={buttonColor}
                _hover={{ bg: buttonHoverBg }}
                isDisabled={!isDirty || !subscriptionId}
              >
                Save Resume
              </Button>
            </Flex>
          </Stack>
        </form>
      )}
    </Container>
  )
}

export default ResumePage 