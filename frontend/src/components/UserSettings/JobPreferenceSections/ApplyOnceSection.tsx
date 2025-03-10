import {
  Button,
  FormControl,
  useColorModeValue
} from "@chakra-ui/react"
import type React from "react"
import JobSectionContainer from "./JobSectionContainer"

interface ApplyOnceSectionProps {
  value: boolean
  onChange: (value: boolean) => void
}

const ApplyOnceSection: React.FC<ApplyOnceSectionProps> = ({
  value,
  onChange
}) => {
  return (
    <JobSectionContainer 
      title="Apply Once at Company" 
      infoTooltip="When enabled, you'll only be matched with one job per company, avoiding duplicate applications."
    >
      <FormControl mb={4}>
        <Button
          bg={
            value ? "#00766C" : useColorModeValue("white", "gray.800")
          }
          color={
            value ? "white" : useColorModeValue("black", "white")
          }
          border="1px solid #00766C"
          _hover={{
            bg: value
              ? "#00655D"
              : useColorModeValue("gray.100", "gray.700"),
          }}
          onClick={() => onChange(!value)}
        >
          {value
            ? "Apply Once at Company"
            : "Apply Multiple Times at Company"}
        </Button>
      </FormControl>
    </JobSectionContainer>
  )
}

export default ApplyOnceSection 