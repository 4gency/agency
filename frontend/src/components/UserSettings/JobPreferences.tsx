import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Select,
  Text,
  RadioGroup,
  Radio,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  RangeSlider,
  RangeSliderTrack,
  RangeSliderFilledTrack,
  RangeSliderThumb,
  IconButton,
  Tag,
  TagLabel,
  TagCloseButton,
  HStack,
  useColorModeValue, // <--- importamos esse hook
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { ApiError, ConfigsService, type ConfigPublic } from "../../client";

import useCustomToast from "../../hooks/useCustomToast";
import useSubscriptions from "../../hooks/userSubscriptions";
import { AddIcon } from "@chakra-ui/icons";

/* ----------------------------- TYPES & UTILS ----------------------------- */

/** The shape we'll use internally for form data (more user-friendly). */
type JobPreferencesForm = {
  remote: boolean;
  experience_levels: string[];
  job_types: string[];
  posting_date: string;
  apply_once_at_company: boolean;
  distance: number;
  positions: string[];
  locations: string[];
  company_blacklist: string[];
  title_blacklist: string[];
  applicants_range: [number, number];
};

/**
 * Transform API data (ConfigPublic) --> Form data (JobPreferencesForm)
 */
function transformToForm(config: ConfigPublic): JobPreferencesForm {
  const experience_levels: string[] = [];
  if (config.experience_level?.intership) experience_levels.push("internship");
  if (config.experience_level?.entry) experience_levels.push("entry");
  if (config.experience_level?.associate) experience_levels.push("associate");
  if (config.experience_level?.mid_senior_level)
    experience_levels.push("mid_senior_level");
  if (config.experience_level?.director) experience_levels.push("director");
  if (config.experience_level?.executive) experience_levels.push("executive");

  const job_types: string[] = [];
  if (config.job_types?.full_time) job_types.push("full_time");
  if (config.job_types?.contract) job_types.push("contract");
  if (config.job_types?.part_time) job_types.push("part_time");
  if (config.job_types?.temporary) job_types.push("temporary");
  if (config.job_types?.internship) job_types.push("internship");
  if (config.job_types?.other) job_types.push("other");
  if (config.job_types?.volunteer) job_types.push("volunteer");

  let posting_date = "all_time";
  if (config.date?.month) posting_date = "month";
  if (config.date?.week) posting_date = "week";
  if (config.date?.hours) posting_date = "hours";

  return {
    remote: config.remote ?? false,
    experience_levels,
    job_types,
    posting_date,
    apply_once_at_company: config.apply_once_at_company ?? false,
    distance: config.distance ?? 0,
    positions: config.positions || [],
    locations: config.locations || [],
    company_blacklist: config.company_blacklist || [],
    title_blacklist: config.title_blacklist || [],
    applicants_range: [
      config.job_applicants_threshold?.min_applicants ?? 0,
      config.job_applicants_threshold?.max_applicants ?? 10000,
    ],
  };
}

/**
 * Transform Form data (JobPreferencesForm) --> API data (ConfigPublic)
 */
function transformFromForm(formData: JobPreferencesForm): ConfigPublic {
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
    job_applicants_threshold: {
      min_applicants: formData.applicants_range[0],
      max_applicants: formData.applicants_range[1],
    },
  };
}

/* ----------------------- MULTI-SELECT TOGGLE COMPONENT ---------------------- */

type Option = {
  label: string;
  value: string;
};

type MultiSelectToggleProps = {
  options: Option[];
  selected: string[];
  onChange: (selected: string[]) => void;
};

const MultiSelectToggle: React.FC<MultiSelectToggleProps> = ({
  options,
  selected,
  onChange,
}) => {
  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <Flex wrap="wrap" gap={2}>
      {options.map((option) => {
        const isSelected = selected.includes(option.value);
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
        );
      })}
    </Flex>
  );
};

/* --------------------------- ARRAY INPUT COMPONENT --------------------------- */
/**
 * A small reusable component to manage an array of strings
 * with an input field and an "Add" button.
 */
type ArrayInputProps = {
  label: string;
  items: string[];
  onChange: (newItems: string[]) => void;
  placeholder?: string;
};

const ArrayInput: React.FC<ArrayInputProps> = ({
  label,
  items,
  onChange,
  placeholder,
}) => {
  const [inputValue, setInputValue] = useState("");

  const handleAdd = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    if (!items.includes(trimmed)) {
      onChange([...items, trimmed]);
    }
    setInputValue("");
  };

  const handleRemove = (item: string) => {
    const filtered = items.filter((i) => i !== item);
    onChange(filtered);
  };

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
  );
};

/* --------------------------- MAIN COMPONENT --------------------------- */

const JobPreferencesPage: React.FC = () => {
  const { data: subscriptions, isLoading } = useSubscriptions();
  const [selectedSubId, setSelectedSubId] = useState<string>("");
  const showToast = useCustomToast();

  // Default form data for first render
  const defaultFormValues: JobPreferencesForm = {
    remote: true,
    experience_levels: [],
    job_types: [],
    posting_date: "all_time",
    apply_once_at_company: true,
    distance: 0,
    positions: ["Developer"],
    locations: ["USA"],
    company_blacklist: [],
    title_blacklist: [],
    applicants_range: [0, 10000],
  };

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { isSubmitting },
  } = useForm<JobPreferencesForm>({
    defaultValues: defaultFormValues,
  });

  /** When a subscription is selected, fetch the config and populate the form. */
  useEffect(() => {
    if (selectedSubId) {
      ConfigsService.getConfig({ subscriptionId: selectedSubId })
        .then((config) => {
          // Transform API config -> form shape
          const transformed = transformToForm(config);
          reset(transformed);
        })
        .catch((err: ApiError) => {
          const detail = (err.body as any)?.detail || err.message;
          showToast("Error fetching preferences", String(detail), "error");
        });
    }
  }, [selectedSubId, reset, showToast]);

  /** Save preferences (PUT) */
  const mutation = useMutation({
    mutationFn: (data: ConfigPublic) =>
      ConfigsService.updateConfig({
        subscriptionId: selectedSubId,
        requestBody: data,
      }),
    onSuccess: () => {
      showToast("Success", "Preferences updated!", "success");
    },
    onError: (err: ApiError) => {
      const detail = (err.body as any)?.detail || err.message;
      showToast("Error updating preferences", String(detail), "error");
    },
  });

  /** Handle form submit */
  const onSubmit = (data: JobPreferencesForm) => {
    if (!selectedSubId) {
      showToast("Attention", "Select a subscription before saving.", "error");
      return;
    }
    // Convert form data -> API shape
    const payload = transformFromForm(data);
    mutation.mutate(payload);
  };

  /** Watch local state for array-based fields to keep form in sync. */
  const positions = watch("positions");
  const locations = watch("locations");
  const companyBlacklist = watch("company_blacklist");
  const titleBlacklist = watch("title_blacklist");
  const applicantsRange = watch("applicants_range");
  const experienceLevels = watch("experience_levels");
  const jobTypes = watch("job_types");

  // Options for the MultiSelectToggle components
  const experienceOptions: Option[] = [
    { value: "internship", label: "Internship" },
    { value: "entry", label: "Entry" },
    { value: "associate", label: "Associate" },
    { value: "mid_senior_level", label: "Mid-Senior Level" },
    { value: "director", label: "Director" },
    { value: "executive", label: "Executive" },
  ];

  const jobTypeOptions: Option[] = [
    { value: "full_time", label: "Full-time" },
    { value: "contract", label: "Contract" },
    { value: "part_time", label: "Part-time" },
    { value: "temporary", label: "Temporary" },
    { value: "internship", label: "Internship" },
    { value: "other", label: "Other" },
    { value: "volunteer", label: "Volunteer" },
  ];

  if (isLoading) {
    return <Text>Loading subscriptions...</Text>;
  }

  const hasSubscriptions = subscriptions && subscriptions.length > 0;

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Job Preferences
      </Heading>

      {!hasSubscriptions ? (
        <Text>No subscriptions available.</Text>
      ) : (
        <FormControl mb={4} width="300px">
          <FormLabel>Select your subscription</FormLabel>
          <Select
            placeholder="Choose a subscription"
            value={selectedSubId}
            onChange={(e) => setSelectedSubId(e.target.value)}
          >
            {subscriptions.map((sub) => (
              <option key={sub.id} value={sub.id}>
                {sub.id}
              </option>
            ))}
          </Select>
        </FormControl>
      )}

      <Box as="form" onSubmit={handleSubmit(onSubmit)}>
        {/* Remote */}
        <FormControl mb={4}>
          <FormLabel>Remote</FormLabel>
          <Input type="hidden" {...register("remote")} />
          <Button
            // MUDANÇA AQUI
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
            onClick={() => setValue("remote", !watch("remote"))}
          >
            {watch("remote") ? "Remote Allowed" : "Remote Not Allowed"}
          </Button>
        </FormControl>

        {/* EXPERIENCE LEVELS (custom multi-select toggle) */}
        <FormControl mb={4}>
          <FormLabel>Experience Levels</FormLabel>
          <MultiSelectToggle
            options={experienceOptions}
            selected={experienceLevels}
            onChange={(values) => setValue("experience_levels", values)}
          />
        </FormControl>

        {/* JOB TYPES (custom multi-select toggle) */}
        <FormControl mb={4}>
          <FormLabel>Job Types</FormLabel>
          <MultiSelectToggle
            options={jobTypeOptions}
            selected={jobTypes}
            onChange={(values) => setValue("job_types", values)}
          />
        </FormControl>

        {/* POSTING DATE (single select) */}
        <FormControl mb={4}>
          <FormLabel>Posting Date</FormLabel>
          <RadioGroup
            value={watch("posting_date")}
            onChange={(val) => setValue("posting_date", val)}
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
          <Input type="hidden" {...register("apply_once_at_company")} />
          <Button
            // MUDANÇA AQUI
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
              setValue("apply_once_at_company", !watch("apply_once_at_company"))
            }
          >
            {watch("apply_once_at_company")
              ? "Apply Once Per Company"
              : "Apply Multiple Times"}
          </Button>
        </FormControl>

        {/* DISTANCE SLIDER */}
        <FormControl mb={4}>
          <FormLabel>Distance (miles or km?)</FormLabel>
          <Slider
            min={0}
            max={200}
            step={10}
            value={watch("distance")}
            onChange={(val) => setValue("distance", val)}
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
          onChange={(newItems) => setValue("positions", newItems)}
          placeholder="e.g. Developer, Frontend"
        />

        {/* LOCATIONS */}
        <ArrayInput
          label="Locations"
          items={locations}
          onChange={(newItems) => setValue("locations", newItems)}
          placeholder="e.g. USA, Canada"
        />

        {/* COMPANY BLACKLIST */}
        <ArrayInput
          label="Company Blacklist"
          items={companyBlacklist}
          onChange={(newItems) => setValue("company_blacklist", newItems)}
          placeholder="e.g. Gupy, Lever"
        />

        {/* TITLE BLACKLIST */}
        <ArrayInput
          label="Title Blacklist"
          items={titleBlacklist}
          onChange={(newItems) => setValue("title_blacklist", newItems)}
          placeholder="e.g. Senior, Jr"
        />

        {/* APPLICANT RANGE (range slider) */}
        <FormControl mb={4}>
          <FormLabel>Number of Applicants Range</FormLabel>
          <RangeSlider
            min={0}
            max={10000}
            step={50}
            value={applicantsRange}
            onChange={(val) =>
              setValue("applicants_range", val as [number, number])
            }
          >
            <RangeSliderTrack>
              <RangeSliderFilledTrack />
            </RangeSliderTrack>
            <RangeSliderThumb index={0} />
            <RangeSliderThumb index={1} />
          </RangeSlider>
          <Flex justify="space-between">
            <Text>Min: {applicantsRange[0]}</Text>
            <Text>Max: {applicantsRange[1]}</Text>
          </Flex>
        </FormControl>

        <Button
          mt={6}
          type="submit"
          isDisabled={!hasSubscriptions}
          isLoading={isSubmitting || mutation.status === "pending"}
        >
          Save Preferences
        </Button>
      </Box>
    </Container>
  );
};

export default JobPreferencesPage;
