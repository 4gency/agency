import {
  FormControl,
  FormLabel,
} from "@chakra-ui/react"
import { UseFormSetValue, UseFormGetValues } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"
import ArrayInputField from "./ArrayInputField"

interface InterestsSectionProps {
  setValue: UseFormSetValue<ResumeForm>
  getValues: UseFormGetValues<ResumeForm>
}

const InterestsSection: React.FC<InterestsSectionProps> = ({
  setValue,
  getValues,
}) => {
  return (
    <SectionContainer title="Interests">
      <FormControl>
        <FormLabel>Interests</FormLabel>
        <ArrayInputField
          label="Interest"
          items={getValues("interests")}
          onChange={(newItems) => setValue("interests", newItems)}
          placeholder="Add an interest (e.g., Photography, Hiking, Machine Learning)"
          onBlur={() => {}}
        />
      </FormControl>
    </SectionContainer>
  )
}

export default InterestsSection 