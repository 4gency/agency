import {
  Box,
  Checkbox,
  FormControl,
  FormLabel,
  Grid,
  GridItem,
  Input,
  Select,
} from "@chakra-ui/react"
import { type FieldErrors, type UseFormRegister } from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface SelfIdentificationSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
}

const SelfIdentificationSection: React.FC<SelfIdentificationSectionProps> = ({
  register,
  errors,
}) => {
  const genderOptions = [
    { value: "", label: "Select gender" },
    { value: "Male", label: "Male" },
    { value: "Female", label: "Female" },
    { value: "Non-binary", label: "Non-binary" },
    { value: "Prefer not to say", label: "Prefer not to say" },
    { value: "Other", label: "Other" },
  ]

  const ethnicityOptions = [
    { value: "", label: "Select ethnicity" },
    { value: "Asian", label: "Asian" },
    { value: "Black or African American", label: "Black or African American" },
    { value: "Hispanic or Latino", label: "Hispanic or Latino" },
    { value: "Indigenous", label: "Indigenous" },
    { value: "Middle Eastern", label: "Middle Eastern" },
    { value: "Pacific Islander", label: "Pacific Islander" },
    { value: "White", label: "White" },
    { value: "Mixed", label: "Mixed" },
    { value: "Prefer not to say", label: "Prefer not to say" },
    { value: "Other", label: "Other" },
  ]

  return (
    <SectionContainer 
      title="Self Identification" 
      infoTooltip="Optional information used for diversity tracking. All responses are confidential and won't affect your application."
    >
      <Box p={4}>
        <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4}>
          <GridItem>
            <FormControl mb={4}>
              <FormLabel>Gender</FormLabel>
              <Select {...register("self_identification.gender")}>
                {genderOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </FormControl>
          </GridItem>

          <GridItem>
            <FormControl mb={4}>
              <FormLabel>Pronouns</FormLabel>
              <Input
                {...register("self_identification.pronouns")}
                placeholder="e.g., He/Him, She/Her, They/Them"
              />
            </FormControl>
          </GridItem>

          <GridItem>
            <FormControl mb={4}>
              <FormLabel>Ethnicity</FormLabel>
              <Select {...register("self_identification.ethnicity")}>
                {ethnicityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </FormControl>
          </GridItem>

          <GridItem display="flex" alignItems="flex-end">
            <FormControl display="flex" alignItems="center" mb={4}>
              <Checkbox
                {...register("self_identification.veteran")}
                colorScheme="teal"
                mr={4}
              >
                Veteran Status
              </Checkbox>
              
              <Checkbox
                {...register("self_identification.disability")}
                colorScheme="teal"
              >
                Disability Status
              </Checkbox>
            </FormControl>
          </GridItem>
        </Grid>
      </Box>
    </SectionContainer>
  )
}

export default SelfIdentificationSection 