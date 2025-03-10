import {
  FormControl,
  FormLabel,
  Input,
  SimpleGrid,
  Text,
} from "@chakra-ui/react"
import type { UseFormRegister } from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface SalaryExpectationSectionProps {
  register: UseFormRegister<ResumeForm>
}

const SalaryExpectationSection: React.FC<SalaryExpectationSectionProps> = ({
  register,
}) => {
  return (
    <SectionContainer 
      title="Salary Expectation" 
      infoTooltip="Provide a realistic range based on your research. It helps match you with opportunities aligned with your expectations."
    >
      <Text fontSize="sm" color="gray.500" mb={3}>
        Please provide your expected annual salary range in USD.
      </Text>
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
        <FormControl>
          <FormLabel>Minimum (USD/year)</FormLabel>
          <Input
            type="number"
            placeholder="Minimum salary"
            {...register("salary_expectation.minimum", {
              valueAsNumber: true,
            })}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Maximum (USD/year)</FormLabel>
          <Input
            type="number"
            placeholder="Maximum salary"
            {...register("salary_expectation.maximum", {
              valueAsNumber: true,
            })}
          />
        </FormControl>
      </SimpleGrid>
    </SectionContainer>
  )
}

export default SalaryExpectationSection
