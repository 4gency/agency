import { FormControl, FormLabel, Input } from "@chakra-ui/react"
import type { UseFormRegister } from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface AvailabilitySectionProps {
  register: UseFormRegister<ResumeForm>
}

const AvailabilitySection: React.FC<AvailabilitySectionProps> = ({
  register,
}) => {
  return (
    <SectionContainer 
      title="Availability" 
      infoTooltip="Specify when you can start working and your notice period. This helps match you with time-sensitive opportunities."
    >
      <FormControl>
        <FormLabel>Notice Period</FormLabel>
        <Input
          {...register("availability")}
          placeholder="How quickly can you start (e.g., 2 weeks, immediately)"
        />
      </FormControl>
    </SectionContainer>
  )
}

export default AvailabilitySection
