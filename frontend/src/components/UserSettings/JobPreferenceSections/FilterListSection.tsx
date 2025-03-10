import type React from "react"
import JobSectionContainer from "./JobSectionContainer"
import ArrayInputField from "./ArrayInputField"

interface FilterListSectionProps {
  title: string
  infoTooltip: string
  label: string
  items: string[]
  onChange: (items: string[]) => void
  placeholder?: string
}

const FilterListSection: React.FC<FilterListSectionProps> = ({
  title,
  infoTooltip,
  label,
  items,
  onChange,
  placeholder = "Add new item"
}) => {
  return (
    <JobSectionContainer 
      title={title}
      infoTooltip={infoTooltip}
    >
      <ArrayInputField
        label={label}
        items={items}
        onChange={onChange}
        placeholder={placeholder}
      />
    </JobSectionContainer>
  )
}

export default FilterListSection 