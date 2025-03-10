import type React from "react"
import JobSectionContainer from "./JobSectionContainer"
import MultiSelectToggleField, { type Option } from "./MultiSelectToggleField"

interface ExperienceLevelSectionProps {
  selected: string[]
  onChange: (selected: string[]) => void
}

// Opções de níveis de experiência
const experienceOptions: Option[] = [
  { value: "internship", label: "Internship" },
  { value: "entry", label: "Entry Level" },
  { value: "associate", label: "Associate" },
  { value: "mid_senior_level", label: "Mid-Senior Level" },
  { value: "director", label: "Director" },
  { value: "executive", label: "Executive" },
]

const ExperienceLevelSection: React.FC<ExperienceLevelSectionProps> = ({
  selected,
  onChange
}) => {
  return (
    <JobSectionContainer 
      title="Experience Levels" 
      infoTooltip="Select the experience levels you're qualified for. Choosing multiple levels increases your matching opportunities."
    >
      <MultiSelectToggleField
        label="Select Experience Levels"
        options={experienceOptions}
        selected={selected}
        onChange={onChange}
      />
    </JobSectionContainer>
  )
}

export default ExperienceLevelSection 