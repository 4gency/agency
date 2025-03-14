import { Box, FormControl } from "@chakra-ui/react"
import { useEffect } from "react"
import type { UseFormGetValues, UseFormWatch } from "react-hook-form"
import type { ResumeForm } from "../types"
import ArrayInputField from "./ArrayInputField"
import SectionContainer from "./SectionContainer"

interface SkillsSectionProps {
  setValue: (
    field: "skills",
    value: string[],
    options?: { shouldDirty?: boolean },
  ) => void
  getValues: UseFormGetValues<ResumeForm>
  watch?: UseFormWatch<ResumeForm>
}

const SkillsSection: React.FC<SkillsSectionProps> = ({
  setValue,
  getValues,
  watch,
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
    <SectionContainer 
      title="Skills" 
      infoTooltip="Add as many skills as possible - technical and soft skills. This helps our AI provide more accurate answers about your expertise."
    >
      <Box mb={4}>
        <Box fontSize="sm" color="gray.600">
          Add as many skills as possible - technical and soft skills. This helps our AI provide more accurate answers about your expertise.
        </Box>
      </Box>
      <FormControl>
        <ArrayInputField
          label="Add skill"
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
