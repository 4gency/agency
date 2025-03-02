import {
  Box,
  Button,
  Checkbox,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Grid,
  GridItem,
  Input,
  Textarea,
  useColorModeValue,
} from "@chakra-ui/react"
import { AddIcon, DeleteIcon } from "@chakra-ui/icons"
import { Control, FieldErrors, UseFormRegister, useFieldArray } from "react-hook-form"
import SectionContainer from "./SectionContainer"
import { ResumeForm } from "../types"

interface EducationSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
}

const EducationSection: React.FC<EducationSectionProps> = ({
  register,
  errors,
  control,
}) => {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "education",
  })

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")

  return (
    <SectionContainer
      title="Education"
      actionButton={
        <Button
          leftIcon={<AddIcon />}
          size="sm"
          onClick={() =>
            append({
              institution: "",
              degree: "",
              field_of_study: "",
              start_date: "",
              end_date: "",
              current: false,
              description: "",
            })
          }
          bg={buttonBg}
          color={buttonColor}
          _hover={{ bg: buttonHoverBg }}
        >
          Add Education
        </Button>
      }
    >
      {fields.map((field, index) => (
        <Box
          key={field.id}
          p={4}
          mb={4}
          borderWidth="1px"
          borderRadius="md"
          position="relative"
        >
          <Button
            size="sm"
            position="absolute"
            top={2}
            right={2}
            colorScheme="red"
            onClick={() => remove(index)}
          >
            <DeleteIcon />
          </Button>

          <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4}>
            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl
                isInvalid={!!errors.education?.[index]?.institution}
                mb={4}
              >
                <FormLabel>Institution</FormLabel>
                <Input
                  {...register(`education.${index}.institution` as const, {
                    required: "Institution is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.education?.[index]?.institution?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl
                isInvalid={!!errors.education?.[index]?.degree}
                mb={4}
              >
                <FormLabel>Degree</FormLabel>
                <Input
                  {...register(`education.${index}.degree` as const, {
                    required: "Degree is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.education?.[index]?.degree?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl mb={4}>
                <FormLabel>Field of Study</FormLabel>
                <Input
                  {...register(`education.${index}.field_of_study` as const)}
                />
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl
                isInvalid={!!errors.education?.[index]?.start_date}
                mb={4}
              >
                <FormLabel>Start Date</FormLabel>
                <Input
                  type="date"
                  {...register(`education.${index}.start_date` as const, {
                    required: "Start date is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.education?.[index]?.start_date?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl mb={4}>
                <FormLabel>End Date</FormLabel>
                <Input
                  type="date"
                  {...register(`education.${index}.end_date` as const)}
                  isDisabled={!!control._formValues.education[index]?.current}
                />
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl display="flex" alignItems="center" mb={4}>
                <Checkbox
                  {...register(`education.${index}.current` as const)}
                  colorScheme="teal"
                >
                  Current
                </Checkbox>
              </FormControl>
            </GridItem>

            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl mb={4}>
                <FormLabel>Description</FormLabel>
                <Textarea
                  {...register(`education.${index}.description` as const)}
                  rows={3}
                />
              </FormControl>
            </GridItem>
          </Grid>
        </Box>
      ))}

      {fields.length === 0 && (
        <Flex justifyContent="center" my={4}>
          <Button
            leftIcon={<AddIcon />}
            onClick={() =>
              append({
                institution: "",
                degree: "",
                field_of_study: "",
                start_date: "",
                end_date: "",
                current: false,
                description: "",
              })
            }
            bg={buttonBg}
            color={buttonColor}
            _hover={{ bg: buttonHoverBg }}
          >
            Add Education
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default EducationSection 