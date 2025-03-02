import {
  FormControl,
  FormLabel,
  Input,
} from "@chakra-ui/react"
import { UseFormRegister, FieldErrors } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"

interface AvailabilitySectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
}

const AvailabilitySection: React.FC<AvailabilitySectionProps> = ({
  register,
  errors,
}) => {
  return (
    <SectionContainer title="Availability">
      <FormControl>
        <FormLabel>When are you available to start working?</FormLabel>
        <Input
          placeholder="e.g., Immediately, 2 weeks notice, From DD/MM/YYYY, etc."
          {...register("availability")}
        />
      </FormControl>
    </SectionContainer>
  )
}

export default AvailabilitySection 