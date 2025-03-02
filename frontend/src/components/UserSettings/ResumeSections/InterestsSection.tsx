import { UseFormRegister, FieldErrors, UseFormSetValue, UseFormGetValues } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import ArrayInputField from "./ArrayInputField"
import { ResumeForm } from "../types"

interface InterestsSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  setValue: UseFormSetValue<ResumeForm>
  getValues: UseFormGetValues<ResumeForm>
}

const InterestsSection: React.FC<InterestsSectionProps> = ({
  register,
  errors,
  setValue,
  getValues,
}) => {
  const handleInterestsChange = (interests: string[]) => {
    setValue("interests", interests)
  }

  return (
    <SectionContainer title="Interests">
      <ArrayInputField
        label="Interests"
        items={getValues("interests") || []}
        onChange={handleInterestsChange}
        placeholder="Add an interest and press Enter or click Add"
        onBlur={() => register("interests")}
      />
    </SectionContainer>
  )
}

export default InterestsSection 