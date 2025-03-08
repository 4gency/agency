import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  HStack,
  Heading,
  IconButton,
  Input,
  Radio,
  RadioGroup,
  Skeleton,
  SkeletonText,
  Slider,
  SliderFilledTrack,
  SliderThumb,
  SliderTrack,
  Tag,
  TagCloseButton,
  TagLabel,
  Text,
  useColorModeValue, // <--- importamos esse hook
} from "@chakra-ui/react"
import { useMutation, useQuery } from "@tanstack/react-query"
import type React from "react"
import { useEffect, useLayoutEffect, useRef, useState, useMemo } from "react"
import { useForm } from "react-hook-form"
import { type ApiError, type ConfigPublic, ConfigsService, SubscriptionsService } from "../../client"

import { AddIcon } from "@chakra-ui/icons"
import useCustomToast from "../../hooks/useCustomToast"

/* ----------------------------- TYPES & UTILS ----------------------------- */

/** The shape we'll use internally for form data (more user-friendly). */
type JobPreferencesForm = {
  remote: boolean
  hybrid: boolean
  onsite: boolean
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
function transformToForm(config: ConfigPublic): JobPreferencesForm {
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
    hybrid: config.hybrid ?? false,
    onsite: config.onsite ?? false,
    experience_levels,
    job_types,
    posting_date,
    apply_once_at_company: config.apply_once_at_company ?? false,
    distance: config.distance ?? 0,
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
function transformFromForm(formData: JobPreferencesForm): ConfigPublic {
  return {
    remote: formData.remote,
    hybrid: formData.hybrid,
    onsite: formData.onsite,
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

/* ----------------------- MULTI-SELECT TOGGLE COMPONENT ---------------------- */

type Option = {
  label: string
  value: string
}

type MultiSelectToggleProps = {
  options: Option[]
  selected: string[]
  onChange: (selected: string[]) => void
}

const MultiSelectToggle: React.FC<MultiSelectToggleProps> = ({
  options,
  selected,
  onChange,
}) => {
  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  return (
    <Flex wrap="wrap" gap={2}>
      {options.map((option) => {
        const isSelected = selected.includes(option.value)
        return (
          <Button
            key={option.value}
            // MUDANÇA AQUI: Usamos a mesma lógica do "Remote" p/ cor
            bg={
              isSelected ? "#00766C" : useColorModeValue("white", "gray.800") // claro/escuro
            }
            color={
              isSelected ? "white" : useColorModeValue("black", "white") // claro/escuro
            }
            border="1px solid #00766C"
            _hover={{
              bg: isSelected
                ? "#00655D"
                : useColorModeValue("gray.100", "gray.700"),
            }}
            onClick={() => handleToggle(option.value)}
          >
            {option.label}
          </Button>
        )
      })}
    </Flex>
  )
}

/* --------------------------- ARRAY INPUT COMPONENT --------------------------- */
/**
 * A small reusable component to manage an array of strings
 * with an input field and an "Add" button.
 */
type ArrayInputProps = {
  label: string
  items: string[]
  onChange: (newItems: string[]) => void
  placeholder?: string
}

const ArrayInput: React.FC<ArrayInputProps> = ({
  label,
  items,
  onChange,
  placeholder,
}) => {
  const [inputValue, setInputValue] = useState("")

  const handleAdd = () => {
    const trimmed = inputValue.trim()
    if (!trimmed) return
    if (!items.includes(trimmed)) {
      onChange([...items, trimmed])
    }
    setInputValue("")
  }

  const handleRemove = (item: string) => {
    const filtered = items.filter((i) => i !== item)
    onChange(filtered)
  }

  return (
    <FormControl mb={4}>
      <FormLabel>{label}</FormLabel>
      <Flex gap={2} mb={2}>
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={placeholder}
        />
        <IconButton
          aria-label="Add item"
          icon={<AddIcon />}
          onClick={handleAdd}
        />
      </Flex>
      <HStack wrap="wrap">
        {items.map((item) => (
          <Tag key={item} m="2px" variant="subtle">
            <TagLabel>{item}</TagLabel>
            <TagCloseButton onClick={() => handleRemove(item)} />
          </Tag>
        ))}
      </HStack>
    </FormControl>
  )
}

/* --------------------------- LOADING SKELETON --------------------------- */

const LoadingSkeleton = () => {
  return (
    <Box width="full">
      <SkeletonText
        mt="4"
        noOfLines={1}
        spacing="4"
        skeletonHeight="10"
        width="200px"
      />

      <Skeleton height="40px" mt="8" width="150px" />

      <Flex wrap="wrap" gap={2} mt="6">
        <Skeleton height="35px" width="100px" />
        <Skeleton height="35px" width="90px" />
        <Skeleton height="35px" width="120px" />
      </Flex>

      <Skeleton height="40px" mt="8" width="150px" />

      <Flex wrap="wrap" gap={2} mt="6">
        <Skeleton height="35px" width="100px" />
        <Skeleton height="35px" width="110px" />
        <Skeleton height="35px" width="90px" />
      </Flex>

      <Skeleton height="140px" mt="8" />
      <Skeleton height="140px" mt="8" />

      <Skeleton height="40px" mt="8" width="150px" />
    </Box>
  )
}

/* --------------------------- MAIN COMPONENT --------------------------- */

const JobPreferencesPage: React.FC = () => {
  const { data: subscriptions, isLoading: isLoadingSubscriptions } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: async () => {
      console.log("Fetching subscriptions for preferences...");
      return await SubscriptionsService.getUserSubscriptions({
        onlyActive: true,
      })
    },
  })

  // Check if user has an active subscription
  const hasActiveSubscription = useMemo(() => {
    const hasSubscription = subscriptions && subscriptions.length > 0;
    console.log("Has active subscription for preferences:", hasSubscription);
    return hasSubscription;
  }, [subscriptions]);

  const [scrollPosition, setScrollPosition] = useState<number>(0)
  const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false)
  const [containerHeight, setContainerHeight] = useState<number | null>(null)
  const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false)
  const [formKey, setFormKey] = useState<number>(0) // Add a key to force re-render when needed
  const pageContainerRef = useRef<HTMLDivElement>(null)
  const showToast = useCustomToast()

  // Default form data for first render
  const defaultFormValues: JobPreferencesForm = {
    remote: true,
    hybrid: true,
    onsite: true,
    experience_levels: [],
    job_types: [],
    posting_date: "all_time",
    apply_once_at_company: true,
    distance: 0,
    positions: ["Developer"],
    locations: ["USA"],
    company_blacklist: [],
    title_blacklist: [],
    location_blacklist: [],
  }

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { isSubmitting, isDirty },
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
      console.log("Executing job preferences fetch...");
      try {
        setIsDataLoaded(false);
        
        // Captura a altura atual do container antes de buscar os dados
        if (pageContainerRef.current) {
          setContainerHeight(
            pageContainerRef.current.getBoundingClientRect().height,
          )
        }

        // Store current scroll position before updating form
        const currentScrollPosition = window.scrollY
        setScrollPosition(currentScrollPosition)
        
        const config = await ConfigsService.getConfig();
        console.log("Job preferences fetch successful");
        
        try {
          // Transform API config -> form shape
          const transformed = transformToForm(config)

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

          // Reset creating new flag if we successfully loaded config
          if (isCreatingNew) {
            setIsCreatingNew(false)
          }

          // Usar múltiplos timeouts para garantir que o DOM seja atualizado completamente
          setTimeout(() => {
            window.scrollTo({
              top: currentScrollPosition,
              behavior: "auto",
            })
          }, 100)

          setTimeout(() => {
            window.scrollTo({
              top: currentScrollPosition,
              behavior: "auto",
            })
            setIsDataLoaded(true)
            setContainerHeight(null) // Remover a altura fixa após o carregamento
          }, 300)
        } catch (error) {
          console.error("Error processing config data:", error)
          setIsDataLoaded(true)
          setContainerHeight(null)
          showToast(
            "Error processing preferences",
            "There was an error processing your preference data.",
            "error"
          )
        }
        
        return config;
      } catch (err) {
        const apiError = err as ApiError;
        console.log("Job preferences fetch error:", apiError.status, apiError.message);
        
        // Em caso de 404, não é erro - apenas não existe config ainda
        if (apiError.status === 404) {
          setIsDataLoaded(true)
          setContainerHeight(null)
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
          setContainerHeight(null) // Remover a altura fixa em caso de erro
        }
        
        throw apiError;
      }
    },
    enabled: true,
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
  });

  // Ensure we fetch data when component mounts
  useEffect(() => {
    // Force a refetch on component mount to ensure data is loaded
    refetchConfig();
  }, [refetchConfig]);

  /** Save preferences with better error handling */
  const mutation = useMutation({
    mutationFn: (data: ConfigPublic) => {
      try {
        return ConfigsService.updateConfig({
          requestBody: data,
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
      
      // Force a re-render of the form
      setFormKey(prevKey => prevKey + 1)
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
      const payload = transformFromForm(data)
      mutation.mutate(payload)
    } catch (error) {
      console.error("Form submission error:", error)
      showToast(
        "Submission error", 
        "An error occurred while processing your form submission.", 
        "error"
      )
    }
  }

  /** Watch local state for array-based fields to keep form in sync. */
  const positions = watch("positions")
  const locations = watch("locations")
  const companyBlacklist = watch("company_blacklist")
  const titleBlacklist = watch("title_blacklist")
  const locationBlacklist = watch("location_blacklist")
  const experienceLevels = watch("experience_levels")
  const jobTypes = watch("job_types")

  // Options for the MultiSelectToggle components
  const experienceOptions: Option[] = [
    { value: "internship", label: "Internship" },
    { value: "entry", label: "Entry" },
    { value: "associate", label: "Associate" },
    { value: "mid_senior_level", label: "Mid-Senior Level" },
    { value: "director", label: "Director" },
    { value: "executive", label: "Executive" },
  ]

  const jobTypeOptions: Option[] = [
    { value: "full_time", label: "Full-time" },
    { value: "contract", label: "Contract" },
    { value: "part_time", label: "Part-time" },
    { value: "temporary", label: "Temporary" },
    { value: "internship", label: "Internship" },
    { value: "other", label: "Other" },
    { value: "volunteer", label: "Volunteer" },
  ]

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
      <Container maxW={{ base: "full", md: "60%" }} ml={{ base: 0, md: 0 }}>
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
          Job Preferences
        </Heading>
        <LoadingSkeleton />
      </Container>
    )
  }

  return (
    <Container
      maxW={{ base: "container.md", lg: "container.lg" }}
      p={4}
      position="relative"
      h={containerHeight ? `${containerHeight}px` : "auto"}
      ref={pageContainerRef}
      key={formKey}
    >
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Job Preferences
      </Heading>

      {!hasActiveSubscription ? (
        <Text>No active subscription available.</Text>
      ) : (
        <Box as="form" onSubmit={handleSubmit(onSubmit)}>
          {/* Remote */}
          <FormControl mb={4}>
            <FormLabel>Remote</FormLabel>
            <Input type="hidden" {...register("remote")} />
            <Button
              bg={
                watch("remote")
                  ? "#00766C"
                  : useColorModeValue("white", "gray.800")
              }
              color={
                watch("remote") ? "white" : useColorModeValue("black", "white")
              }
              border="1px solid #00766C"
              _hover={{
                bg: watch("remote")
                  ? "#00655D"
                  : useColorModeValue("gray.100", "gray.700"),
              }}
              onClick={() => updateField("remote", !watch("remote"))}
            >
              {watch("remote") ? "Remote Allowed" : "Remote Not Allowed"}
            </Button>
          </FormControl>

          {/* Hybrid */}
          <FormControl mb={4}>
            <FormLabel>Hybrid</FormLabel>
            <Input type="hidden" {...register("hybrid")} />
            <Button
              bg={
                watch("hybrid")
                  ? "#00766C"
                  : useColorModeValue("white", "gray.800")
              }
              color={
                watch("hybrid") ? "white" : useColorModeValue("black", "white")
              }
              border="1px solid #00766C"
              _hover={{
                bg: watch("hybrid")
                  ? "#00655D"
                  : useColorModeValue("gray.100", "gray.700"),
              }}
              onClick={() => updateField("hybrid", !watch("hybrid"))}
            >
              {watch("hybrid") ? "Hybrid Allowed" : "Hybrid Not Allowed"}
            </Button>
          </FormControl>

          {/* Onsite */}
          <FormControl mb={4}>
            <FormLabel>Onsite</FormLabel>
            <Input type="hidden" {...register("onsite")} />
            <Button
              bg={
                watch("onsite")
                  ? "#00766C"
                  : useColorModeValue("white", "gray.800")
              }
              color={
                watch("onsite") ? "white" : useColorModeValue("black", "white")
              }
              border="1px solid #00766C"
              _hover={{
                bg: watch("onsite")
                  ? "#00655D"
                  : useColorModeValue("gray.100", "gray.700"),
              }}
              onClick={() => updateField("onsite", !watch("onsite"))}
            >
              {watch("onsite") ? "Onsite Allowed" : "Onsite Not Allowed"}
            </Button>
          </FormControl>

          {/* EXPERIENCE LEVELS (custom multi-select toggle) */}
          <FormControl mb={4}>
            <FormLabel>Experience Levels</FormLabel>
            <MultiSelectToggle
              options={experienceOptions}
              selected={experienceLevels}
              onChange={(values) => updateField("experience_levels", values)}
            />
          </FormControl>

          {/* JOB TYPES (custom multi-select toggle) */}
          <FormControl mb={4}>
            <FormLabel>Job Types</FormLabel>
            <MultiSelectToggle
              options={jobTypeOptions}
              selected={jobTypes}
              onChange={(values) => updateField("job_types", values)}
            />
          </FormControl>

          {/* POSTING DATE (single select) */}
          <FormControl mb={4}>
            <FormLabel>Posting Date</FormLabel>
            <RadioGroup
              value={watch("posting_date")}
              onChange={(val) => updateField("posting_date", val)}
            >
              <Flex direction="column" gap={2}>
                <Radio value="all_time">All time</Radio>
                <Radio value="month">Last Month</Radio>
                <Radio value="week">Last Week</Radio>
                <Radio value="hours">Last 24 Hours</Radio>
              </Flex>
            </RadioGroup>
          </FormControl>

          {/* APPLY ONCE AT COMPANY */}
          <FormControl mb={4}>
            <FormLabel>Apply Once Per Company</FormLabel>
            <Input type="hidden" {...register("apply_once_at_company")} />
            <Button
              bg={
                watch("apply_once_at_company")
                  ? "#00766C"
                  : useColorModeValue("white", "gray.800")
              }
              color={
                watch("apply_once_at_company")
                  ? "white"
                  : useColorModeValue("black", "white")
              }
              border="1px solid #00766C"
              _hover={{
                bg: watch("apply_once_at_company")
                  ? "#00655D"
                  : useColorModeValue("gray.100", "gray.700"),
              }}
              onClick={() =>
                updateField(
                  "apply_once_at_company",
                  !watch("apply_once_at_company"),
                )
              }
            >
              {watch("apply_once_at_company")
                ? "Apply Once Per Company"
                : "Apply Multiple Times"}
            </Button>
          </FormControl>

          {/* DISTANCE SLIDER */}
          <FormControl mb={4}>
            <FormLabel>Distance (miles)</FormLabel>
            <Slider
              min={0}
              max={200}
              step={10}
              value={watch("distance")}
              onChange={(val) => updateField("distance", val)}
            >
              <SliderTrack>
                <SliderFilledTrack />
              </SliderTrack>
              <SliderThumb />
            </Slider>
            <Text mt={2}>Selected Distance: {watch("distance")}</Text>
          </FormControl>

          {/* POSITIONS */}
          <ArrayInput
            label="Positions"
            items={positions}
            onChange={(newItems) => updateField("positions", newItems)}
            placeholder="e.g. Developer, Frontend"
          />

          {/* LOCATIONS */}
          <ArrayInput
            label="Locations"
            items={locations}
            onChange={(newItems) => updateField("locations", newItems)}
            placeholder="e.g. USA, Canada"
          />

          {/* COMPANY BLACKLIST */}
          <ArrayInput
            label="Company Blacklist"
            items={companyBlacklist}
            onChange={(newItems) => updateField("company_blacklist", newItems)}
            placeholder="e.g. Gupy, Lever"
          />

          {/* TITLE BLACKLIST */}
          <ArrayInput
            label="Title Blacklist"
            items={titleBlacklist}
            onChange={(newItems) => updateField("title_blacklist", newItems)}
            placeholder="e.g. Senior, Jr"
          />

          {/* LOCATION BLACKLIST */}
          <ArrayInput
            label="Location Blacklist"
            items={locationBlacklist}
            onChange={(newItems) => updateField("location_blacklist", newItems)}
            placeholder="e.g. Brazil, Mexico"
          />

          <Button
            type="submit"
            colorScheme="blue"
            isLoading={isSubmitting}
            isDisabled={!hasActiveSubscription}
            mt={4}
            width="100%"
          >
            {isCreatingNew ? "Create Preferences" : "Save Preferences"}
          </Button>
        </Box>
      )}
    </Container>
  )
}

export default JobPreferencesPage
