import {
  Button,
  Container,
  Divider,
  Flex,
  Heading,
  Skeleton,
  Stack,
} from "@chakra-ui/react"
import { useMutation, useQuery } from "@tanstack/react-query"
import type React from "react"
import { useEffect, useState, useMemo } from "react"
import { useForm } from "react-hook-form"
import { ConfigsService, SubscriptionsService } from "../../client/sdk.gen"
import type { GetPlainTextResumeResponse } from "../../client/types.gen"
import { ApiError } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import type { ResumeForm } from "./types"

import AvailabilitySection from "./ResumeSections/AvailabilitySection"
import EducationSection from "./ResumeSections/EducationSection"
import InterestsSection from "./ResumeSections/InterestsSection"
import LanguagesSection from "./ResumeSections/LanguagesSection"
// Import all section components
import PersonalInformationSection from "./ResumeSections/PersonalInformationSection"
import ProjectsSection from "./ResumeSections/ProjectsSection"
import SalaryExpectationSection from "./ResumeSections/SalaryExpectationSection"
import SkillsSection from "./ResumeSections/SkillsSection"
import WorkExperienceSection from "./ResumeSections/WorkExperienceSection"
import WorkPreferenceSection from "./ResumeSections/WorkPreferenceSection"

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
const transformApiResponseToFormData = (
  apiData: GetPlainTextResumeResponse,
): ResumeForm => {
  try {
    // Check if apiData is null or undefined
    if (!apiData) {
      console.warn("API data is null or undefined, using default values")
      return defaultValues
    }

    // Check if we received a JSON string and parse it
    if (typeof apiData === "string") {
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
      // Extract skills from experience details
      let skills: string[] = []

      // Collect skills from experience details
      if (Array.isArray(apiData.experience_details)) {
        const skillsFromExperience = apiData.experience_details
          .flatMap((exp) => exp.skills_acquired || [])
          .filter((skill: string) => skill && skill.trim() !== "")

        skills = [...skills, ...skillsFromExperience]
      }

      // Add direct skills if available in any custom properties
      const apiDataAny = apiData as any
      if (Array.isArray(apiDataAny.skills)) {
        const directSkills = apiDataAny.skills.filter(
          (skill: string) => skill && skill.trim() !== "",
        )
        skills = [...skills, ...directSkills]
      }

      // Remove duplicates
      skills = Array.from(new Set(skills))

      // Ensure we always have an array for interests
      let interests: string[] = []
      if (Array.isArray(apiData.interests)) {
        interests = apiData.interests.filter(
          (interest: string) =>
            interest && typeof interest === "string" && interest.trim() !== "",
        )
      }

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
        education: Array.isArray(apiData.education_details)
          ? apiData.education_details.map((edu) => ({
              institution: edu.institution || "",
              degree: edu.education_level || "",
              field_of_study: edu.field_of_study || "",
              start_date: edu.start_date || "",
              end_date: edu.year_of_completion || "",
              current: false,
              description: "",
            }))
          : [],
        work_experience: Array.isArray(apiData.experience_details)
          ? apiData.experience_details.map((exp) => ({
              company: exp.company || "",
              position: exp.position || "",
              start_date: exp.employment_period
                ? exp.employment_period.split("-")[0]?.trim() || ""
                : "",
              end_date: exp.employment_period
                ? exp.employment_period.split("-")[1]?.trim() || ""
                : "",
              current: false,
              description: (exp.key_responsibilities || []).join("\n"),
              location: exp.location || "",
            }))
          : [],
        projects: Array.isArray(apiData.projects)
          ? apiData.projects.map((proj) => ({
              name: proj.name || "",
              description: proj.description || "",
              url: proj.link || "",
              start_date: "",
              end_date: "",
              current: false,
            }))
          : [],
        skills: skills,
        languages: Array.isArray(apiData.languages)
          ? apiData.languages.map((lang) => ({
              name: lang.language || "",
              level: lang.proficiency || "",
            }))
          : [],
        availability: apiData.availability?.notice_period || "",
        salary_expectation: {
          minimum: apiData.salary_expectations?.salary_range_usd
            ? Number.parseInt(
                apiData.salary_expectations.salary_range_usd
                  .split("-")[0]
                  ?.replace(/\D/g, ""),
              ) || undefined
            : undefined,
          maximum: apiData.salary_expectations?.salary_range_usd
            ? Number.parseInt(
                apiData.salary_expectations.salary_range_usd
                  .split("-")[1]
                  ?.replace(/\D/g, ""),
              ) || undefined
            : undefined,
          currency: "USD",
        },
        work_preference: {
          remote: apiData.work_preferences?.remote_work || false,
          hybrid: false, // API doesn't have hybrid option
          on_site: apiData.work_preferences?.in_person_work || false,
          relocation: apiData.work_preferences?.open_to_relocation || false,
        },
        interests: interests,
      }
    }

    return defaultValues
  } catch (error) {
    console.error("Error transforming API response:", error)
    // Log the structure of apiData to help with debugging
    if (apiData) {
      console.error(
        "Failed to transform API data structure:",
        typeof apiData === "object"
          ? JSON.stringify(apiData, null, 2)
          : typeof apiData,
      )
    }

    // Always return defaultValues as fallback to prevent application crashes
    return defaultValues
  }
}

// Function to transform form data to API model
const transformFormToApiData = (
  data: ResumeForm,
): GetPlainTextResumeResponse => {
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
      education_details: data.education.map((edu) => ({
        institution: edu.institution,
        education_level: edu.degree,
        field_of_study: edu.field_of_study,
        start_date: edu.start_date,
        year_of_completion: edu.end_date,
      })),
      experience_details: data.work_experience.map((exp) => ({
        company: exp.company,
        position: exp.position,
        employment_period:
          exp.start_date && exp.end_date
            ? `${exp.start_date} - ${exp.end_date}`
            : exp.start_date || "",
        location: exp.location,
        key_responsibilities: exp.description ? [exp.description] : [],
        skills_acquired: [],
      })),
      projects: data.projects.map((proj) => ({
        name: proj.name,
        description: proj.description,
        link: proj.url,
      })),
      languages: data.languages.map((lang) => ({
        language: lang.name,
        proficiency: lang.level,
      })),
      interests: data.interests,
      availability: {
        notice_period: data.availability,
      },
      salary_expectations: {
        salary_range_usd:
          data.salary_expectation.minimum && data.salary_expectation.maximum
            ? `${data.salary_expectation.minimum} - ${data.salary_expectation.maximum}`
            : undefined,
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
  const showToast = useCustomToast()
  const [_scrollPosition, setScrollPosition] = useState<number>(0)
  const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false)
  const [formKey, setFormKey] = useState<number>(0) // Add a key to force re-render when needed

  // Form setup
  const {
    register,
    handleSubmit,
    control,
    setValue,
    getValues,
    reset,
    formState: { errors, isDirty, isSubmitting },
    watch,
  } = useForm<ResumeForm>({
    defaultValues,
  })

  // Fetch user subscriptions
  const { data: subscriptions, isLoading: isLoadingSubscriptions } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: async () => {
      console.log("Fetching subscriptions...");
      return await SubscriptionsService.getUserSubscriptions({
        onlyActive: true,
      })
    },
  })

  // Check if user has an active subscription
  const hasActiveSubscription = useMemo(() => {
    const hasSubscription = subscriptions && subscriptions.length > 0;
    console.log("Has active subscription:", hasSubscription);
    return hasSubscription;
  }, [subscriptions]);

  // Fetch resume data with better initialization and error handling
  const { data: resumeData, isLoading: isLoadingResume, error: resumeError, refetch: refetchResume } = useQuery({
    queryKey: ["plainTextResume"],
    queryFn: async () => {
      console.log("Executing resume fetch...");
      try {
        const result = await ConfigsService.getPlainTextResume();
        console.log("Resume fetch successful");
        return result;
      } catch (error) {
        const apiError = error as ApiError;
        console.log("Resume fetch error:", apiError.status, apiError.message);
        if (apiError.status === 404) {
          setIsCreatingNew(true);
        }
        throw error;
      }
    },
    // Don't condition the query on subscription status to avoid race conditions
    enabled: true,
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
  });

  // When component mounts, ensure a fetch attempt is made
  useEffect(() => {
    // Force a refetch on component mount to ensure data is loaded
    refetchResume();
  }, [refetchResume]);

  // Handle resume fetch error - only show actual errors, not 404
  useEffect(() => {
    // If loading or data exists, do nothing
    if (isLoadingResume || resumeData) return;
    
    // If we have an active subscription but no resume data
    if (hasActiveSubscription && !resumeData) {
      const apiError = resumeError as ApiError;
      
      // Only show a message for 404 if we haven't shown it already
      if (apiError && apiError.status === 404) {
        if (!isCreatingNew) {
          setIsCreatingNew(true);
          showToast(
            "Resume not found",
            "Please fill out the form to create your resume.",
            "success",
          )
        }
      } else if (apiError) {
        // Real errors
        console.error("Resume fetch error:", apiError);
        showToast(
          "Error fetching resume",
          "There was an error loading your resume data.",
          "error",
        )
      }
    }
  }, [isLoadingResume, resumeData, hasActiveSubscription, resumeError, showToast, isCreatingNew])

  // Update resume mutation with better error handling
  const updateResumeMutation = useMutation({
    mutationFn: async (data: ResumeForm) => {
      if (!hasActiveSubscription) {
        throw new Error("No active subscription available")
      }
      
      try {
        const apiData = transformFormToApiData(data)
        const result = await ConfigsService.updatePlainTextResume({
          requestBody: apiData,
        })
        
        // If we were creating a new resume, we're now editing
        if (isCreatingNew) {
          setIsCreatingNew(false)
        }
        
        return result
      } catch (error) {
        console.error("Error saving resume:", error)
        throw error
      }
    },
    onSuccess: () => {
      showToast(
        isCreatingNew ? "Resume created" : "Resume updated",
        isCreatingNew 
          ? "Your resume has been successfully created." 
          : "Your resume has been successfully updated.",
        "success",
      )
      
      // Force a re-render of the form with the current data
      setFormKey(prevKey => prevKey + 1)
    },
    onError: (error: Error) => {
      console.error("Resume mutation error:", error)
      const apiError = error as ApiError
      const errorDetail = apiError.body ? 
        (apiError.body as any).detail || apiError.message : 
        "An unexpected error occurred."
      
      showToast(
        "Error saving resume",
        errorDetail,
        "error",
      )
    },
  })

  // Parse and set form data when API response is received
  useEffect(() => {
    if (resumeData) {
      try {
        // Store current scroll position before form data is set
        const currentScrollPosition = window.scrollY
        setScrollPosition(currentScrollPosition)

        const formData = transformApiResponseToFormData(resumeData)

        // Reset form with fetched data
        reset(formData, {
          keepDirty: false,
          keepErrors: false,
          keepDefaultValues: false,
          keepValues: false,
          keepIsSubmitted: false,
          keepTouched: false,
          keepIsValid: false,
          keepSubmitCount: false,
        })

        // Restore scroll position
        setTimeout(() => {
          window.scrollTo({
            top: currentScrollPosition,
            behavior: "auto",
          })
        }, 100)
      } catch (error) {
        console.error("Error processing resume data:", error)
        showToast(
          "Error processing data",
          "There was an error processing your resume data.",
          "error",
        )
      }
    }
  }, [resumeData, reset, showToast])

  // Form submission handler with better error handling
  const onSubmit = (data: ResumeForm) => {
    try {
      updateResumeMutation.mutate(data)
    } catch (error) {
      console.error("Form submission error:", error)
      showToast(
        "Submission error",
        "There was an error submitting the form.",
        "error",
      )
    }
  }

  const isLoading = isLoadingSubscriptions || isLoadingResume

  // Ensure all form fields correctly mark the form as dirty
  const updateField = (field: any, value: any) => {
    setValue(field, value, { 
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true 
    });
  }

  // Return with the form key to force re-renders when needed
  return (
    <Container
      maxW={{ base: "full", md: "60%" }}
      ml={{ base: 0, md: 0 }}
      pb="100px"
      key={formKey}
    >
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
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
              watch={watch}
            />

            <Divider />

            <WorkExperienceSection
              register={register}
              errors={errors}
              control={control}
              watch={watch}
            />

            <Divider />

            <ProjectsSection
              register={register}
              errors={errors}
              control={control}
              watch={watch}
            />

            <Divider />

            <SkillsSection
              setValue={updateField}
              getValues={getValues}
              watch={watch}
            />

            <Divider />

            <LanguagesSection
              register={register}
              errors={errors}
              control={control}
            />

            <Divider />

            <AvailabilitySection register={register} />

            <Divider />

            <SalaryExpectationSection register={register} />

            <Divider />

            <WorkPreferenceSection register={register} />

            <Divider />

            <InterestsSection
              setValue={updateField}
              getValues={getValues}
              watch={watch}
            />

            <Flex justify="flex-end" mt={6}>
              <Button
                type="submit"
                isLoading={isSubmitting || updateResumeMutation.isPending}
                isDisabled={!hasActiveSubscription}
              >
                {isCreatingNew ? "Create Resume" : "Save Resume"}
              </Button>
            </Flex>
          </Stack>
        </form>
      )}
    </Container>
  )
}

export default ResumePage
