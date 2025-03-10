import { 
  Button,
  FormControl,
  useColorModeValue,
  Box,
  Text
} from "@chakra-ui/react"
import type React from "react"
import JobSectionContainer from "./JobSectionContainer"

interface WorkLocationSectionProps {
  remote: boolean
  onUpdate: (field: string, value: boolean) => void
}

const WorkLocationSection: React.FC<WorkLocationSectionProps> = ({
  remote,
  onUpdate
}) => {
  const bgColor = useColorModeValue("gray.100", "gray.700");
  const textColor = useColorModeValue("gray.800", "white");

  return (
    <JobSectionContainer 
      title="Work Location" 
      infoTooltip="Toggle to include remote jobs in your search. Remote jobs allow you to work from anywhere."
    >
      <Box bg={bgColor} p={4} borderRadius="md" mb={4}>
        <Text fontSize="sm" color={textColor}>
          This setting controls whether you want to see remote job opportunities in your search results.
          Remote jobs allow you to work from anywhere, regardless of your physical location.
        </Text>
      </Box>

      <FormControl mb={4}>
        <Button
          bg={remote ? "#00766C" : useColorModeValue("white", "gray.800")}
          color={remote ? "white" : useColorModeValue("black", "white")}
          border="1px solid #00766C"
          _hover={{
            bg: remote ? "#00655D" : useColorModeValue("gray.100", "gray.700"),
          }}
          onClick={() => onUpdate("remote", !remote)}
          width="100%"
          height="50px"
          fontSize="md"
        >
          {remote ? "Remote Jobs Included ✓" : "Remote Jobs Excluded"}
        </Button>
      </FormControl>
    </JobSectionContainer>
  )
}

export default WorkLocationSection 