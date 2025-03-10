import { FormControl } from "@chakra-ui/react"
import { useEffect } from "react"
import type { UseFormGetValues, UseFormWatch } from "react-hook-form"
import type { ResumeForm } from "../types"
import ArrayInputField from "./ArrayInputField"
import SectionContainer from "./SectionContainer"

interface InterestsSectionProps {
  setValue: (
    field: "interests",
    value: string[],
    options?: { shouldDirty?: boolean },
  ) => void
  getValues: UseFormGetValues<ResumeForm>
  watch?: UseFormWatch<ResumeForm>
}

const InterestsSection: React.FC<InterestsSectionProps> = ({
  setValue,
  getValues,
  watch,
}) => {
  // Garantir que interests sempre seja um array válido
  useEffect(() => {
    const currentInterests = getValues("interests")
    if (!Array.isArray(currentInterests) || currentInterests === undefined) {
      setValue("interests", [])
    }
  }, [getValues, setValue])

  // Obter interests do formulário utilizando watch se disponível, caso contrário usar getValues
  // Isso garante reatividade quando o hook watch está disponível
  const interests = watch ? watch("interests") : getValues("interests") || []

  // Sempre garantir que temos um array válido para exibição
  const displayInterests = Array.isArray(interests) ? interests : []

  return (
    <SectionContainer 
      title="Interests" 
      infoTooltip="Share relevant hobbies and interests that reveal your personality and complement your professional profile."
    >
      <FormControl>
        <ArrayInputField
          label="Add interest"
          items={displayInterests}
          onChange={(newItems) => setValue("interests", newItems)}
          placeholder="Add an interest (e.g., Photography, Hiking, Machine Learning)"
          onBlur={() => {}}
        />
      </FormControl>
    </SectionContainer>
  )
}

export default InterestsSection
