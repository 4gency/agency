import { useColorModeValue } from "@chakra-ui/react"
import { UseFormRegister, FieldErrors, UseFormSetValue, UseFormGetValues } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import ArrayInputField from "./ArrayInputField"
import { ResumeForm } from "../types"

interface SkillsSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  setValue: UseFormSetValue<ResumeForm>
  getValues: UseFormGetValues<ResumeForm>
}

const SkillsSection: React.FC<SkillsSectionProps> = ({
  register,
  errors,
  setValue,
  getValues,
}) => {
  const handleSkillsChange = (skills: string[]) => {
    setValue("skills", skills)
  }

  return (
    <SectionContainer title="Skills">
      <ArrayInputField
        label="Skills"
        items={getValues("skills") || []}
        onChange={handleSkillsChange}
        placeholder="Add a skill and press Enter or click Add"
        onBlur={() => register("skills")}
      />
    </SectionContainer>
  )
}

export default SkillsSection 