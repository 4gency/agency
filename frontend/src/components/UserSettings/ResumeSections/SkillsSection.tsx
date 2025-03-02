import { 
  FormControl,
  FormLabel,
} from "@chakra-ui/react"
import { UseFormGetValues, UseFormWatch } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"
import ArrayInputField from "./ArrayInputField"
import { useEffect } from "react"

interface SkillsSectionProps {
  setValue: (field: "skills", value: string[], options?: {shouldDirty?: boolean}) => void
  getValues: UseFormGetValues<ResumeForm>
  watch?: UseFormWatch<ResumeForm>
}

const SkillsSection: React.FC<SkillsSectionProps> = ({
  setValue,
  getValues,
  watch
}) => {
  // Garantir que skills sempre seja um array válido
  useEffect(() => {
    const currentSkills = getValues("skills")
    if (!Array.isArray(currentSkills) || currentSkills === undefined) {
      setValue("skills", [])
    }
  }, [getValues, setValue])

  // Obter skills do formulário utilizando watch se disponível, caso contrário usar getValues
  // Isso garante reatividade quando o hook watch está disponível
  const skills = watch ? watch("skills") : getValues("skills") || []
  
  // Sempre garantir que temos um array válido para exibição
  const displaySkills = Array.isArray(skills) ? skills : []

  return (
    <SectionContainer title="Skills">
      <FormControl>
        <FormLabel>Skills</FormLabel>
        <ArrayInputField
          label="Skill"
          items={displaySkills}
          onChange={(newItems) => setValue("skills", newItems)}
          placeholder="Add a skill (e.g., JavaScript, Project Management, Leadership)"
          onBlur={() => {}}
        />
      </FormControl>
    </SectionContainer>
  )
}

export default SkillsSection 