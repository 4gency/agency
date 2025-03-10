import { Box, Checkbox, CheckboxGroup, Divider, FormControl, FormLabel, Stack, Text } from "@chakra-ui/react"
import type { UseFormRegister } from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface WorkPreferenceSectionProps {
  register: UseFormRegister<ResumeForm>
}

const WorkPreferenceSection: React.FC<WorkPreferenceSectionProps> = ({
  register,
}) => {
  return (
    <SectionContainer 
      title="Work Preference" 
      infoTooltip="Be clear about your availability, preferred work modes, and relocation options to match with suitable opportunities."
    >
      <Box p={4}>
        <Text mb={4} fontSize="sm" color="gray.600">
          Please indicate your work preferences. This information helps employers find opportunities that match your preferences.
        </Text>
        
        <FormControl mb={6}>
          <FormLabel fontWeight="medium">Work Mode Preferences</FormLabel>
          <CheckboxGroup colorScheme="teal">
            <Stack spacing={[1, 5]} direction={{ base: "column", md: "row" }}>
              <Checkbox {...register("work_preference.remote")}>Remote</Checkbox>
              <Checkbox {...register("work_preference.hybrid")}>Hybrid</Checkbox>
              <Checkbox {...register("work_preference.on_site")}>
                On-site
              </Checkbox>
              <Checkbox {...register("work_preference.relocation")}>
                Open to relocation
              </Checkbox>
            </Stack>
          </CheckboxGroup>
        </FormControl>
        
        <Divider my={4} />
        
        <FormControl>
          <FormLabel fontWeight="medium">Additional Preferences</FormLabel>
          <CheckboxGroup colorScheme="teal">
            <Stack spacing={[1, 5]} direction={{ base: "column", md: "row" }}>
              <Checkbox {...register("work_preference.willing_to_complete_assessments")}>
                Willing to complete assessments
              </Checkbox>
              <Checkbox {...register("work_preference.willing_to_undergo_drug_tests")}>
                Willing to undergo drug tests
              </Checkbox>
              <Checkbox {...register("work_preference.willing_to_undergo_background_checks")}>
                Willing to undergo background checks
              </Checkbox>
            </Stack>
          </CheckboxGroup>
        </FormControl>
      </Box>
    </SectionContainer>
  )
}

export default WorkPreferenceSection
