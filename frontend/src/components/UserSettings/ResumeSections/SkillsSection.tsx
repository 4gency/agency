import { 
  FormControl,
  FormLabel,
} from "@chakra-ui/react"
import { UseFormSetValue, UseFormGetValues } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"
import ArrayInputField from "./ArrayInputField"

interface SkillsSectionProps {
  setValue: UseFormSetValue<ResumeForm>
  getValues: UseFormGetValues<ResumeForm>
}

const SkillsSection: React.FC<SkillsSectionProps> = ({
  setValue,
  getValues,
}) => {
  return (
    <SectionContainer title="Skills">
      <FormControl>
        <FormLabel>Skills</FormLabel>
        <ArrayInputField
          label="Skill"
          items={getValues("skills")}
          onChange={(newItems) => setValue("skills", newItems)}
          placeholder="Add a skill (e.g., JavaScript, Project Management, Leadership)"
          onBlur={() => {}}
        />
      </FormControl>
    </SectionContainer>
  )
}

export default SkillsSection 