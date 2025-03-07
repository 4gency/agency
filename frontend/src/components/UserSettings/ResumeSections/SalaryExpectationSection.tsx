import {
  FormControl,
  FormLabel,
  Input,
  Select,
  SimpleGrid,
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
    <SectionContainer title="Salary Expectation">
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <FormControl>
          <FormLabel>Minimum</FormLabel>
          <Input
            type="number"
            placeholder="Minimum salary"
            {...register("salary_expectation.minimum", {
              valueAsNumber: true,
            })}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Maximum</FormLabel>
          <Input
            type="number"
            placeholder="Maximum salary"
            {...register("salary_expectation.maximum", {
              valueAsNumber: true,
            })}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Currency</FormLabel>
          <Select
            placeholder="Select currency"
            {...register("salary_expectation.currency")}
          >
            <option value="USD">USD - United States Dollar</option>
            <option value="EUR">EUR - Euro</option>
            <option value="GBP">GBP - British Pound</option>
            <option value="CAD">CAD - Canadian Dollar</option>
            <option value="AUD">AUD - Australian Dollar</option>
            <option value="JPY">JPY - Japanese Yen</option>
            <option value="CHF">CHF - Swiss Franc</option>
            <option value="CNY">CNY - Chinese Yuan</option>
            <option value="INR">INR - Indian Rupee</option>
            <option value="BRL">BRL - Brazilian Real</option>
          </Select>
        </FormControl>
      </SimpleGrid>
    </SectionContainer>
  )
}

export default SalaryExpectationSection
