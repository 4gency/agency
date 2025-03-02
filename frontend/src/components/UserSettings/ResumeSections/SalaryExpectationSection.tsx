import {
  FormControl,
  FormLabel,
  Input,
  Grid,
  GridItem,
  Select,
} from "@chakra-ui/react"
import { UseFormRegister, FieldErrors } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"

interface SalaryExpectationSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
}

const SalaryExpectationSection: React.FC<SalaryExpectationSectionProps> = ({
  register,
  errors,
}) => {
  const currencies = [
    "USD",
    "EUR",
    "GBP",
    "CAD",
    "AUD",
    "JPY",
    "CHF",
    "CNY",
    "INR",
    "BRL",
  ]

  return (
    <SectionContainer title="Salary Expectation">
      <Grid templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap={4}>
        <GridItem>
          <FormControl>
            <FormLabel>Minimum Expected Salary</FormLabel>
            <Input
              type="number"
              {...register("salary_expectation.minimum", {
                valueAsNumber: true,
              })}
              placeholder="e.g., 50000"
            />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>Maximum Expected Salary</FormLabel>
            <Input
              type="number"
              {...register("salary_expectation.maximum", {
                valueAsNumber: true,
              })}
              placeholder="e.g., 70000"
            />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>Currency</FormLabel>
            <Select
              {...register("salary_expectation.currency")}
              placeholder="Select currency"
            >
              {currencies.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </Select>
          </FormControl>
        </GridItem>
      </Grid>
    </SectionContainer>
  )
}

export default SalaryExpectationSection 