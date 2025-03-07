import { Checkbox, CheckboxGroup, FormControl, Stack } from "@chakra-ui/react"
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
    <SectionContainer title="Work Preferences">
      <FormControl>
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
    </SectionContainer>
  )
}

export default WorkPreferenceSection
