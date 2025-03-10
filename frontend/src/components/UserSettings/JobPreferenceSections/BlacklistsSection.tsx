import { VStack } from "@chakra-ui/react"
import type React from "react"
import JobSectionContainer from "./JobSectionContainer"
import ArrayInputField from "./ArrayInputField"

interface BlacklistsSectionProps {
  companyBlacklist: string[]
  titleBlacklist: string[]
  locationBlacklist: string[]
  onCompanyChange: (items: string[]) => void
  onTitleChange: (items: string[]) => void
  onLocationChange: (items: string[]) => void
}

const BlacklistsSection: React.FC<BlacklistsSectionProps> = ({
  companyBlacklist,
  titleBlacklist,
  locationBlacklist,
  onCompanyChange,
  onTitleChange,
  onLocationChange
}) => {
  return (
    <JobSectionContainer 
      title="Blacklists" 
      infoTooltip="Exclude specific companies, job titles, or locations from your search. Useful to filter out irrelevant opportunities."
    >
      <VStack align="stretch" spacing={4}>
        <ArrayInputField
          label="Company Blacklist"
          items={companyBlacklist}
          onChange={onCompanyChange}
          placeholder="e.g. Gupy, Lever"
        />

        <ArrayInputField
          label="Title Blacklist"
          items={titleBlacklist}
          onChange={onTitleChange}
          placeholder="e.g. Senior, Jr"
        />

        <ArrayInputField
          label="Location Blacklist"
          items={locationBlacklist}
          onChange={onLocationChange}
          placeholder="e.g. Brazil, Mexico"
        />
      </VStack>
    </JobSectionContainer>
  )
}

export default BlacklistsSection 