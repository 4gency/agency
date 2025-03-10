import type React from "react"
import JobSectionContainer from "./JobSectionContainer"
import MultiSelectToggleField, { type Option } from "./MultiSelectToggleField"

interface JobTypeSectionProps {
  selected: string[]
  onChange: (selected: string[]) => void
}

// Opções de tipos de trabalho
const jobTypeOptions: Option[] = [
  { value: "full_time", label: "Full-Time" },
  { value: "contract", label: "Contract" },
  { value: "part_time", label: "Part-Time" },
  { value: "temporary", label: "Temporary" },
  { value: "internship", label: "Internship" },
  { value: "other", label: "Other" },
  { value: "volunteer", label: "Volunteer" },
]

const JobTypeSection: React.FC<JobTypeSectionProps> = ({
  selected,
  onChange
}) => {
  return (
    <JobSectionContainer 
      title="Job Types" 
      infoTooltip="Choose the employment types you're interested in. Consider including contract work to expand opportunities."
    >
      <MultiSelectToggleField
        label="Select Job Types"
        options={jobTypeOptions}
        selected={selected}
        onChange={onChange}
      />
    </JobSectionContainer>
  )
}

export default JobTypeSection 