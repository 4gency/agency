import {
  FormControl,
  FormLabel,
  Input,
} from "@chakra-ui/react"
import { UseFormRegister } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"

interface AvailabilitySectionProps {
  register: UseFormRegister<ResumeForm>
}

const AvailabilitySection: React.FC<AvailabilitySectionProps> = ({
  register,
}) => {
  return (
    <SectionContainer title="Availability">
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