import {
  Flex,
  FormControl,
  Radio,
  RadioGroup,
} from "@chakra-ui/react"
import type React from "react"
import JobSectionContainer from "./JobSectionContainer"

interface PostingDateSectionProps {
  value: string
  onChange: (value: string) => void
}

const PostingDateSection: React.FC<PostingDateSectionProps> = ({
  value,
  onChange
}) => {
  return (
    <JobSectionContainer 
      title="Posting Date" 
      infoTooltip="Filter jobs by how recently they were posted. Newer listings often have less competition."
    >
      <FormControl mb={4}>
        <RadioGroup
          value={value}
          onChange={onChange}
        >
          <Flex direction="column" gap={2}>
            <Radio value="all_time">All Time</Radio>
            <Radio value="month">Past Month</Radio>
            <Radio value="week">Past Week</Radio>
            <Radio value="hours">Past 24 Hours</Radio>
          </Flex>
        </RadioGroup>
      </FormControl>
    </JobSectionContainer>
  )
}

export default PostingDateSection 