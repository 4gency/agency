import {
  FormControl,
  FormLabel,
  Grid,
  GridItem,
  Checkbox,
  Text,
} from "@chakra-ui/react"
import { UseFormRegister, FieldErrors } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"

interface WorkPreferenceSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
}

const WorkPreferenceSection: React.FC<WorkPreferenceSectionProps> = ({
  register,
  errors,
}) => {
  return (
    <SectionContainer title="Work Preferences">
      <Text mb={4}>Select all work arrangements you are open to:</Text>
      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4}>
        <GridItem>
          <FormControl display="flex" alignItems="center">
            <Checkbox
              {...register("work_preference.remote")}
              colorScheme="teal"
            >
              Remote
            </Checkbox>
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl display="flex" alignItems="center">
            <Checkbox
              {...register("work_preference.hybrid")}
              colorScheme="teal"
            >
              Hybrid
            </Checkbox>
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl display="flex" alignItems="center">
            <Checkbox
              {...register("work_preference.on_site")}
              colorScheme="teal"
            >
              On-site
            </Checkbox>
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl display="flex" alignItems="center">
            <Checkbox
              {...register("work_preference.relocation")}
              colorScheme="teal"
            >
              Willing to relocate
            </Checkbox>
          </FormControl>
        </GridItem>
      </Grid>
    </SectionContainer>
  )
}

export default WorkPreferenceSection 