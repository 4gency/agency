import {
  Alert,
  AlertIcon,
  AlertDescription,
  Box,
  Button,
  ButtonGroup,
  Container,
  Heading,
  Skeleton,
  SkeletonText,
  Stack,
  Card,
} from "@chakra-ui/react"
import { useMutation, useQuery } from "@tanstack/react-query"
import type React from "react"
import { useEffect, useLayoutEffect, useState, useMemo, forwardRef, useImperativeHandle, useRef } from "react"
import { useForm } from "react-hook-form"
import { type ApiError, type ConfigPublic, ConfigsService, SubscriptionsService } from "../../client"

import useCustomToast from "../../hooks/useCustomToast"

// Definindo um tipo estendido para incluir as propriedades específicas
type ExtendedConfigPublic = ConfigPublic;

// Função para converter ConfigPublic para ExtendedConfigPublic
function toExtendedConfig(config: ConfigPublic): ExtendedConfigPublic {
  return config;
}

// Função para converter ExtendedConfigPublic para ConfigPublic
function toApiConfig(extConfig: ExtendedConfigPublic): ConfigPublic {
  return extConfig;
}

// Importando os componentes de seção
import WorkLocationSection from "./JobPreferenceSections/WorkLocationSection"
import ExperienceLevelSection from "./JobPreferenceSections/ExperienceLevelSection"
import JobTypeSection from "./JobPreferenceSections/JobTypeSection"
import PostingDateSection from "./JobPreferenceSections/PostingDateSection"
import ApplyOnceSection from "./JobPreferenceSections/ApplyOnceSection"
import DistanceSection from "./JobPreferenceSections/DistanceSection"
import FilterListSection from "./JobPreferenceSections/FilterListSection"
import BlacklistsSection from "./JobPreferenceSections/BlacklistsSection"

/* ----------------------------- TYPES & UTILS ----------------------------- */

/** The shape we'll use internally for form data (more user-friendly). */
type JobPreferencesForm = {
  remote: boolean
  experience_levels: string[]
  job_types: string[]
  posting_date: string
  apply_once_at_company: boolean
  distance: number
  positions: string[]
  locations: string[]
  company_blacklist: string[]
  title_blacklist: string[]
  location_blacklist: string[]
}

/**
 * Transform API data (ConfigPublic) --> Form data (JobPreferencesForm)
 */
function transformToForm(config: ExtendedConfigPublic): JobPreferencesForm {
  const experience_levels: string[] = []
  if (config.experience_level?.intership) experience_levels.push("internship")
  if (config.experience_level?.entry) experience_levels.push("entry")
  if (config.experience_level?.associate) experience_levels.push("associate")
  if (config.experience_level?.mid_senior_level)
    experience_levels.push("mid_senior_level")
  if (config.experience_level?.director) experience_levels.push("director")
  if (config.experience_level?.executive) experience_levels.push("executive")

  const job_types: string[] = []
  if (config.job_types?.full_time) job_types.push("full_time")
  if (config.job_types?.contract) job_types.push("contract")
  if (config.job_types?.part_time) job_types.push("part_time")
  if (config.job_types?.temporary) job_types.push("temporary")
  if (config.job_types?.internship) job_types.push("internship")
  if (config.job_types?.other) job_types.push("other")
  if (config.job_types?.volunteer) job_types.push("volunteer")

  let posting_date = "all_time"
  if (config.date?.month) posting_date = "month"
  if (config.date?.week) posting_date = "week"
  if (config.date?.hours) posting_date = "hours"

  return {
    remote: config.remote ?? false,
    experience_levels,
    job_types,
    posting_date,
    apply_once_at_company: config.apply_once_at_company ?? false,
    distance: config.distance ?? DEFAULT_DISTANCE,
    positions: config.positions || [],
    locations: config.locations || [],
    company_blacklist: config.company_blacklist || [],
    title_blacklist: config.title_blacklist || [],
    location_blacklist: config.location_blacklist || [],
  }
}

/**
 * Transform Form data (JobPreferencesForm) --> API data (ConfigPublic)
 */
function transformFromForm(formData: JobPreferencesForm): ExtendedConfigPublic {
  return {
    remote: formData.remote,
    experience_level: {
      intership: formData.experience_levels.includes("internship"),
      entry: formData.experience_levels.includes("entry"),
      associate: formData.experience_levels.includes("associate"),
      mid_senior_level: formData.experience_levels.includes("mid_senior_level"),
      director: formData.experience_levels.includes("director"),
      executive: formData.experience_levels.includes("executive"),
    },
    job_types: {
      full_time: formData.job_types.includes("full_time"),
      contract: formData.job_types.includes("contract"),
      part_time: formData.job_types.includes("part_time"),
      temporary: formData.job_types.includes("temporary"),
      internship: formData.job_types.includes("internship"),
      other: formData.job_types.includes("other"),
      volunteer: formData.job_types.includes("volunteer"),
    },
    date: {
      all_time: formData.posting_date === "all_time",
      month: formData.posting_date === "month",
      week: formData.posting_date === "week",
      hours: formData.posting_date === "hours",
    },
    apply_once_at_company: formData.apply_once_at_company,
    distance: formData.distance,
    positions: formData.positions,
    locations: formData.locations,
    company_blacklist: formData.company_blacklist,
    title_blacklist: formData.title_blacklist,
    location_blacklist: formData.location_blacklist,
  }
}

// Definir o valor padrão para distance
const DEFAULT_DISTANCE = 25;

/* --------------------------- LOADING SKELETON COMPONENT --------------------------- */
const LoadingSkeleton = () => {
  return (
    <Box p={4}>
      <Skeleton height="40px" width="150px" mb={6} />
      <SkeletonText mt="4" noOfLines={4} spacing="4" />
      <SkeletonText mt="6" noOfLines={3} spacing="4" />
      <SkeletonText mt="6" noOfLines={5} spacing="4" />
      <SkeletonText mt="6" noOfLines={2} spacing="4" />
    </Box>
  )
}

/* --------------------------- MAIN COMPONENT --------------------------- */

const JobPreferencesPage: React.FC = () => {
  const { data: subscriptions, isLoading: isLoadingSubscriptions } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: async () => {
      return await SubscriptionsService.getUserSubscriptions({
        onlyActive: true,
      })
    },
  })

  const hasActiveSubscription = useMemo(() => {
    const hasSubscription = subscriptions && subscriptions.length > 0;
    return hasSubscription;
  }, [subscriptions]);

  const [scrollPosition, setScrollPosition] = useState<number>(0)
  const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false)
  const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false)
  const showToast = useCustomToast()
  const isInitialMount = useRef(true)

  // Default form data for first render
  const defaultFormValues: JobPreferencesForm = {
    remote: true,
    experience_levels: [],
    job_types: [],
    posting_date: "all_time",
    apply_once_at_company: true,
    distance: DEFAULT_DISTANCE,
    positions: ["Developer"],
    locations: ["USA"],
    company_blacklist: [],
    title_blacklist: [],
    location_blacklist: [],
  }

  // Form setup with React Hook Form
  const {
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { isSubmitting },
  } = useForm<JobPreferencesForm>({
    defaultValues: defaultFormValues,
  })

  // Adicionar um useLayoutEffect para garantir que a página não role após o carregamento dos dados
  useLayoutEffect(() => {
    if (isDataLoaded && scrollPosition > 0) {
      // Forçar a restauração da posição do scroll após o React terminar de renderizar
      window.scrollTo({
        top: scrollPosition,
        behavior: "auto",
      })
    }
  }, [isDataLoaded, scrollPosition])

  // Fetch config using React Query directly for better consistency
  const { refetch: refetchConfig } = useQuery({
    queryKey: ["jobPreferences"],
    queryFn: async () => {
      try {
        setIsDataLoaded(false);
        
        // Capturar a posição atual de scroll para restaurar depois
        setScrollPosition(window.scrollY)
        
        const config = await ConfigsService.getConfig();
        
        try {
          // Transform API config -> form shape
          // Converter para o formato estendido primeiro
          const extendedConfig = toExtendedConfig(config);
          const transformed = transformToForm(extendedConfig);

          // Use reset with callback para garantir conclusão da atualização
          reset(transformed, {
            keepDirty: false,
            keepErrors: false,
            keepDefaultValues: false,
            keepValues: false,
            keepIsSubmitted: false,
            keepTouched: false,
            keepIsValid: false,
            keepSubmitCount: false,
          })

          // Marcar que os dados foram carregados e não estamos criando novos
          setIsCreatingNew(false)
          setIsDataLoaded(true)

          // Usar múltiplos timeouts para garantir que o DOM seja atualizado completamente
          setTimeout(() => {
            window.scrollTo({
              top: window.scrollY,
              behavior: "auto",
            })
          }, 100)

          setTimeout(() => {
            window.scrollTo({
              top: window.scrollY,
              behavior: "auto",
            })
            setIsDataLoaded(true)
          }, 300)
        } catch (error) {
          console.error("Error processing config data:", error)
          setIsDataLoaded(true)
          showToast(
            "Error processing preferences",
            "There was an error processing your preference data.",
            "error"
          )
        }
        
        return config;
      } catch (err) {
        const apiError = err as ApiError;
        
        // Em caso de 404, não é erro - apenas não existe config ainda
        if (apiError.status === 404) {
          setIsDataLoaded(true)
          if (!isCreatingNew) {
            setIsCreatingNew(true)
            showToast(
              "Job preferences not found",
              "Please fill out the form to create your job preferences.",
              "success"
            )
          }
        } else {
          console.error("Error fetching preferences:", apiError)
          const detail = (apiError.body as any)?.detail || apiError.message
          showToast("Error fetching preferences", String(detail), "error")
          setIsDataLoaded(true)
        }
        
        throw apiError;
      }
    },
    enabled: true,
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
  });

  // Effect para recarregar os dados quando solicitado externamente
  useEffect(() => {
    if (!isInitialMount.current) {
      refetchConfig();
    } else {
      isInitialMount.current = false;
    }
  }, [refetchConfig]);

  /** Save preferences with better error handling */
  const mutation = useMutation({
    mutationFn: (data: ExtendedConfigPublic) => {
      try {
        // Converter de volta para o formato da API
        const apiConfig = toApiConfig(data);
        return ConfigsService.updateConfig({
          requestBody: apiConfig,
        })
      } catch (error) {
        console.error("Error in mutation:", error)
        throw error
      }
    },
    onSuccess: () => {
      showToast(
        isCreatingNew ? "Preferences created" : "Preferences updated", 
        isCreatingNew 
          ? "Your preferences have been successfully created." 
          : "Your preferences have been successfully updated.", 
        "success"
      )
      
      // If we were creating, we're now editing
      if (isCreatingNew) {
        setIsCreatingNew(false)
      }
    },
    onError: (err: ApiError) => {
      console.error("Mutation error:", err)
      const detail = (err.body as any)?.detail || err.message
      showToast("Error saving preferences", String(detail), "error")
    },
  })

  /** Handle form submit with better error handling */
  const onSubmit = (data: JobPreferencesForm) => {
    try {
      if (!hasActiveSubscription) {
        showToast("Attention", "No active subscription available.", "error")
        return
      }
      
      // Convert form data -> API shape
      const extendedConfig = transformFromForm(data)
      mutation.mutate(extendedConfig)
    } catch (error) {
      console.error("Form submission error:", error)
      showToast(
        "Submission error", 
        "An error occurred while processing your form submission.", 
        "error"
      )
    }
  }

  // Ensure all form fields correctly mark the form as dirty
  const updateField = (field: any, value: any) => {
    setValue(field, value, { 
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true 
    });
  }

  if (isLoadingSubscriptions) {
    return (
      <Container maxW="full">
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
          Job Preferences
        </Heading>
      </Container>
    )
  }

  /** Watch local state for array-based fields to keep form in sync. */
  const remote = watch("remote")
  const positions = watch("positions")
  const locations = watch("locations")
  const companyBlacklist = watch("company_blacklist")
  const titleBlacklist = watch("title_blacklist")
  const locationBlacklist = watch("location_blacklist")
  const experienceLevels = watch("experience_levels")
  const jobTypes = watch("job_types")
  const postingDate = watch("posting_date")
  const applyOnce = watch("apply_once_at_company")
  const distance = watch("distance")

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Job Preferences
      </Heading>
      {!hasActiveSubscription && (
        <Alert status="warning" mb={4}>
          <AlertIcon />
          <AlertDescription>
            You need an active subscription to configure job preferences
          </AlertDescription>
        </Alert>
      )}

      {!isDataLoaded ? (
        <LoadingSkeleton />
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} style={{ marginBottom: '3rem' }}>
          <Stack spacing={6}>
            {/* Work Location Section */}
            <WorkLocationSection 
              remote={remote}
              onUpdate={(field, value) => updateField(field, value)}
            />

            {/* Experience Levels Section */}
            <ExperienceLevelSection 
              selected={experienceLevels}
              onChange={(values) => updateField("experience_levels", values)}
            />

            {/* Job Types Section */}
            <JobTypeSection 
              selected={jobTypes}
              onChange={(values) => updateField("job_types", values)}
            />

            {/* Posting Date Section */}
            <PostingDateSection 
              value={postingDate}
              onChange={(val) => updateField("posting_date", val)}
            />

            {/* Apply Once Section */}
            <ApplyOnceSection 
              value={applyOnce}
              onChange={(val) => updateField("apply_once_at_company", val)}
            />

            {/* Distance Section */}
            <DistanceSection 
              value={distance}
              onChange={(val) => updateField("distance", val)}
            />

            {/* Positions Section */}
            <FilterListSection
              title="Positions"
              infoTooltip="List job titles you're interested in, such as 'Developer' or 'Frontend Engineer'. Enter specific keywords."
              label="Positions"
              items={positions}
              onChange={(newItems) => updateField("positions", newItems)}
              placeholder="e.g. Developer, Frontend"
            />

            {/* Locations Section */}
            <FilterListSection
              title="Locations"
              infoTooltip="Specify locations where you're looking for jobs. Can be countries, states, or cities."
              label="Locations"
              items={locations}
              onChange={(newItems) => updateField("locations", newItems)}
              placeholder="e.g. USA, Canada"
            />

            {/* Blacklists Section */}
            <BlacklistsSection 
              companyBlacklist={companyBlacklist}
              titleBlacklist={titleBlacklist}
              locationBlacklist={locationBlacklist}
              onCompanyChange={(newItems) => updateField("company_blacklist", newItems)}
              onTitleChange={(newItems) => updateField("title_blacklist", newItems)}
              onLocationChange={(newItems) => updateField("location_blacklist", newItems)}
            />
          </Stack>
          <ButtonGroup justifyContent="flex-end" mt={4}>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              isDisabled={!hasActiveSubscription}
            >
              {isCreatingNew ? "Create Preferences" : "Save Preferences"}
            </Button>
          </ButtonGroup>
        </form>
      )}
    </Container>
  )
}

// Forwardable version for use in onboarding
interface JobPreferencesComponentProps {
  onComplete?: () => void
  isOnboarding?: boolean
  hideSubmitButton?: boolean
}

const JobPreferences = forwardRef<{ submit: () => Promise<boolean> }, JobPreferencesComponentProps>(
  ({ onComplete, isOnboarding = false, hideSubmitButton = false }, ref) => {
    const { data: subscriptions, isLoading: isLoadingSubscriptions } = useQuery({
      queryKey: ["subscriptions"],
      queryFn: async () => {
        return await SubscriptionsService.getUserSubscriptions({
          onlyActive: true,
        })
      },
    })

    const hasActiveSubscription = useMemo(() => {
      const hasSubscription = subscriptions && subscriptions.length > 0;
      return hasSubscription;
    }, [subscriptions]);

    const [scrollPosition, setScrollPosition] = useState<number>(0)
    const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false)
    const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false)
    const showToast = useCustomToast()
    const isInitialMount = useRef(true)

    // Default form data for first render
    const defaultFormValues: JobPreferencesForm = {
      remote: true,
      experience_levels: [],
      job_types: [],
      posting_date: "all_time",
      apply_once_at_company: true,
      distance: DEFAULT_DISTANCE,
      positions: ["Developer"],
      locations: ["USA"],
      company_blacklist: [],
      title_blacklist: [],
      location_blacklist: [],
    }

    // Form setup with React Hook Form
    const {
      handleSubmit,
      watch,
      setValue,
      reset,
      formState: { isSubmitting },
    } = useForm<JobPreferencesForm>({
      defaultValues: defaultFormValues,
    })

    // Adicionar um useLayoutEffect para garantir que a página não role após o carregamento dos dados
    useLayoutEffect(() => {
      if (isDataLoaded && scrollPosition > 0) {
        // Forçar a restauração da posição do scroll após o React terminar de renderizar
        window.scrollTo({
          top: scrollPosition,
          behavior: "auto",
        })
      }
    }, [isDataLoaded, scrollPosition])

    // Fetch config using React Query directly for better consistency
    const { refetch: refetchConfig } = useQuery({
      queryKey: ["jobPreferences"],
      queryFn: async () => {
        try {
          setIsDataLoaded(false);
          
          // Capturar a posição atual de scroll para restaurar depois
          setScrollPosition(window.scrollY)
          
          const config = await ConfigsService.getConfig();
          
          try {
            // Transform API config -> form shape
            // Converter para o formato estendido primeiro
            const extendedConfig = toExtendedConfig(config);
            const transformed = transformToForm(extendedConfig);

            // Use reset with callback para garantir conclusão da atualização
            reset(transformed, {
              keepDirty: false,
              keepErrors: false,
              keepDefaultValues: false,
              keepValues: false,
              keepIsSubmitted: false,
              keepTouched: false,
              keepIsValid: false,
              keepSubmitCount: false,
            })

            // Marcar que os dados foram carregados e não estamos criando novos
            setIsCreatingNew(false)
            setIsDataLoaded(true)
            
            return config
          } catch (error) {
            console.error("Error transforming config:", error)
            
            // Reset para valores padrão
            reset(defaultFormValues)
            setIsCreatingNew(true)
            setIsDataLoaded(true)
            throw error
          }
        } catch (error) {
          const apiError = error as ApiError
          
          if (apiError.status === 404) {
            // Silenciosamente lidar com o caso de não haver configuração ainda
            console.log("No existing config, creating new preferences...")
            reset(defaultFormValues)
            setIsCreatingNew(true)
            setIsDataLoaded(true)
            return null
          }
          
          // Outros erros de API devem ser relatados
          console.error("Error fetching job preferences:", error)
          setIsDataLoaded(true)
          
          // Não mostrar toast se estiver no modo de onboarding
          if (!isOnboarding) {
            showToast(
              "Error loading preferences", 
              apiError.message || "Failed to load job preferences", 
              "error"
            )
          }
          
          throw error
        }
      },
      enabled: true,
      retry: false,
      refetchOnWindowFocus: false,
    });

    // Effect para recarregar os dados quando solicitado externamente
    useEffect(() => {
      if (!isInitialMount.current) {
        refetchConfig();
      } else {
        isInitialMount.current = false;
      }
    }, [refetchConfig]);

    // Setup mutations with better error handling
    const mutation = useMutation({
      mutationFn: async (extendedConfig: ExtendedConfigPublic) => {
        if (!hasActiveSubscription) {
          throw new Error("No active subscription available")
        }
        
        const apiConfig = toApiConfig(extendedConfig)
        
        // Use ConfigsService to update
        await ConfigsService.updateConfig({
          requestBody: apiConfig, 
        })
        
        // Return the transformed config
        return extendedConfig
      },
      onSuccess: () => {
        // Only show success toast if not in onboarding mode
        if (!isOnboarding) {
          showToast(
            isCreatingNew ? "Preferences created" : "Preferences updated", 
            isCreatingNew 
              ? "Your preferences have been successfully created." 
              : "Your preferences have been successfully updated.", 
            "success"
          )
        }
        
        // Call onComplete callback if provided
        if (onComplete) {
          onComplete()
        }
        
        // If we were creating, we're now editing
        if (isCreatingNew) {
          setIsCreatingNew(false)
        }
      },
      onError: (err: ApiError) => {
        console.error("Mutation error:", err)
        
        // Melhor tratamento para garantir que o erro seja sempre uma string
        let errorMessage = "An unexpected error occurred."
        
        // Tenta extrair detalhes do erro em diferentes formatos
        try {
          if (err.body) {
            const errorBody = err.body as any
            
            if (errorBody.detail) {
              // Se detail for um objeto (validation_error), extrair apenas as mensagens
              if (typeof errorBody.detail === 'object') {
                if (Array.isArray(errorBody.detail)) {
                  // Se for um array de erros
                  errorMessage = errorBody.detail
                    .map((e: any) => {
                      if (typeof e === 'object' && e.msg) {
                        return String(e.msg)
                      }
                      return String(e)
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
          } else if (err.message) {
            errorMessage = String(err.message)
          }
        } catch (formatError) {
          console.error("Error formatting error message:", formatError)
          // Manter a mensagem padrão em caso de erro ao extrair detalhes
        }
        
        showToast("Error saving preferences", errorMessage, "error")
      },
    })

    // Function to save job preferences
    const saveJobPreferences = async (data: JobPreferencesForm): Promise<boolean> => {
      try {
        if (!hasActiveSubscription) {
          showToast("Attention", "No active subscription available.", "error")
          return false
        }
        
        // Convert form data -> API shape
        const extendedConfig = transformFromForm(data)
        await mutation.mutateAsync(extendedConfig)
        return true
      } catch (error) {
        console.error("Form submission error:", error)
        showToast(
          "Submission error", 
          "An error occurred while processing your form submission.", 
          "error"
        )
        return false
      }
    }

    // Expose the submit method to parent components through ref
    useImperativeHandle(ref, () => ({
      submit: async () => {
        try {
          // Trigger form validation and submission
          return await new Promise<boolean>((resolve, reject) => {
            handleSubmit(async (data) => {
              try {
                // Validar se temos pelo menos uma posição e localização
                if (!data.positions || data.positions.length === 0) {
                  throw new Error("Job position is required");
                }
                if (!data.locations || data.locations.length === 0) {
                  throw new Error("Job location is required");
                }
                
                const success = await saveJobPreferences(data);
                resolve(success);
              } catch (error) {
                console.error("Error in JobPreferences submission:", error);
                
                // Garantir que o erro seja uma instância de Error
                if (error instanceof Error) {
                  reject(error);
                } else {
                  reject(new Error("Error submitting job preferences"));
                }
              }
            }, (validationErrors) => {
              // Este callback é chamado quando a validação do react-hook-form falha
              console.error("Form validation failed:", validationErrors);
              const errorMessage = "Please fill all required fields in the job preferences form";
              reject(new Error(errorMessage));
              return;
            })();
          });
        } catch (error) {
          console.error("Error submitting job preferences form:", error);
          
          // Garantir que o erro seja uma instância de Error
          if (error instanceof Error) {
            throw error;
          } else {
            throw new Error("Error submitting job preferences form");
          }
        }
      }
    }));

    /** Handle form submit with better error handling */
    const onSubmit = (data: JobPreferencesForm) => {
      saveJobPreferences(data)
    }

    // Ensure all form fields correctly mark the form as dirty
    const updateField = (field: any, value: any) => {
      setValue(field, value, { 
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true 
      })
    }

    if (isLoadingSubscriptions) {
      return (
        <Container maxW="full">
          {!isOnboarding && (
            <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
              Job Preferences
            </Heading>
          )}
        </Container>
      )
    }

    /** Watch local state for array-based fields to keep form in sync. */
    const remote = watch("remote")
    const positions = watch("positions")
    const locations = watch("locations")
    const companyBlacklist = watch("company_blacklist")
    const titleBlacklist = watch("title_blacklist")
    const locationBlacklist = watch("location_blacklist")
    const experienceLevels = watch("experience_levels")
    const jobTypes = watch("job_types")
    const postingDate = watch("posting_date")
    const applyOnce = watch("apply_once_at_company")
    const distance = watch("distance")

    return (
      <Container maxW="full">
        {!isOnboarding && (
          <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
            Job Preferences
          </Heading>
        )}
        
        {!hasActiveSubscription && !isOnboarding && (
          <Alert status="warning" mb={4}>
            <AlertIcon />
            <AlertDescription>
              You need an active subscription to configure job preferences
            </AlertDescription>
          </Alert>
        )}

        {!isDataLoaded ? (
          <LoadingSkeleton />
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} style={{ marginBottom: '3rem' }}>
            <Stack spacing={6}>
              {/* Work Location Section */}
              <WorkLocationSection 
                remote={remote}
                onUpdate={(field, value) => updateField(field, value)}
              />

              {/* Experience Levels Section */}
              <ExperienceLevelSection 
                selected={experienceLevels}
                onChange={(values) => updateField("experience_levels", values)}
              />

              {/* Job Types Section */}
              <JobTypeSection 
                selected={jobTypes}
                onChange={(values) => updateField("job_types", values)}
              />

              {/* Posting Date Section */}
              <PostingDateSection 
                value={postingDate}
                onChange={(val) => updateField("posting_date", val)}
              />

              {/* Apply Once Section */}
              <ApplyOnceSection 
                value={applyOnce}
                onChange={(val) => updateField("apply_once_at_company", val)}
              />

              {/* Distance Section */}
              <DistanceSection 
                value={distance}
                onChange={(val) => updateField("distance", val)}
              />

              {/* Positions Section */}
              <FilterListSection
                title="Positions"
                infoTooltip="List job titles you're interested in, such as 'Developer' or 'Frontend Engineer'. Enter specific keywords."
                label="Positions"
                items={positions}
                onChange={(newItems) => updateField("positions", newItems)}
                placeholder="e.g. Developer, Frontend"
              />

              {/* Locations Section */}
              <FilterListSection
                title="Locations"
                infoTooltip="Specify locations where you're looking for jobs. Can be countries, states, or cities."
                label="Locations"
                items={locations}
                onChange={(newItems) => updateField("locations", newItems)}
                placeholder="e.g. USA, Canada"
              />

              {/* Blacklist Sections */}
              <Card variant="outline" p={4}>
                <Heading size="md" mb={4}>Blacklists</Heading>
                <Stack spacing={4}>
                  <BlacklistsSection 
                    companyBlacklist={companyBlacklist}
                    titleBlacklist={titleBlacklist}
                    locationBlacklist={locationBlacklist}
                    onCompanyChange={(val) => updateField("company_blacklist", val)}
                    onTitleChange={(val) => updateField("title_blacklist", val)}
                    onLocationChange={(val) => updateField("location_blacklist", val)}
                  />
                </Stack>
              </Card>

              {/* Submit Button */}
              {!hideSubmitButton && (
                <Button 
                  type="submit" 
                  colorScheme="blue" 
                  size="lg"
                  isLoading={isSubmitting || mutation.isPending}
                  isDisabled={!hasActiveSubscription}
                >
                  {isCreatingNew ? "Create Preferences" : "Save Preferences"}
                </Button>
              )}
            </Stack>
          </form>
        )}
      </Container>
    )
  }
)

// Display name for debugging
JobPreferences.displayName = "JobPreferences"

export default JobPreferencesPage
export { JobPreferences }
