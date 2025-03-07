import {
  FormControl,
  FormErrorMessage,
  FormLabel,
  Grid,
  GridItem,
  Input,
} from "@chakra-ui/react"
import type { FieldErrors, UseFormRegister } from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface PersonalInformationSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
}

const PersonalInformationSection: React.FC<PersonalInformationSectionProps> = ({
  register,
  errors,
}) => {
  return (
    <SectionContainer title="Personal Information">
      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={6}>
        <GridItem>
          <FormControl isInvalid={!!errors.personal_information?.name}>
            <FormLabel>First Name</FormLabel>
            <Input
              {...register("personal_information.name", {
                required: "First name is required",
              })}
            />
            <FormErrorMessage>
              {errors.personal_information?.name?.message}
            </FormErrorMessage>
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl isInvalid={!!errors.personal_information?.surname}>
            <FormLabel>Last Name</FormLabel>
            <Input
              {...register("personal_information.surname", {
                required: "Last name is required",
              })}
            />
            <FormErrorMessage>
              {errors.personal_information?.surname?.message}
            </FormErrorMessage>
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>Date of Birth</FormLabel>
            <Input
              type="date"
              {...register("personal_information.date_of_birth")}
            />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl isInvalid={!!errors.personal_information?.email}>
            <FormLabel>Email</FormLabel>
            <Input
              type="email"
              {...register("personal_information.email", {
                required: "Email is required",
                pattern: {
                  value: /^\S+@\S+\.\S+$/,
                  message: "Invalid email format",
                },
              })}
            />
            <FormErrorMessage>
              {errors.personal_information?.email?.message}
            </FormErrorMessage>
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>Country</FormLabel>
            <Input {...register("personal_information.country")} />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>City</FormLabel>
            <Input {...register("personal_information.city")} />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>Address</FormLabel>
            <Input {...register("personal_information.address")} />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>ZIP/Postal Code</FormLabel>
            <Input {...register("personal_information.zip_code")} />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>Phone Prefix</FormLabel>
            <Input {...register("personal_information.phone_prefix")} />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>Phone Number</FormLabel>
            <Input {...register("personal_information.phone")} />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>LinkedIn</FormLabel>
            <Input {...register("personal_information.linkedin")} />
          </FormControl>
        </GridItem>

        <GridItem>
          <FormControl>
            <FormLabel>GitHub</FormLabel>
            <Input {...register("personal_information.github")} />
          </FormControl>
        </GridItem>
      </Grid>
    </SectionContainer>
  )
}

export default PersonalInformationSection
