import { AddIcon, DeleteIcon } from "@chakra-ui/icons"
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
import {
  type Control,
  type FieldErrors,
  type UseFormRegister,
  type UseFormWatch,
  useFieldArray,
} from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface WorkExperienceSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
  watch?: UseFormWatch<ResumeForm>
}

const WorkExperienceSection: React.FC<WorkExperienceSectionProps> = ({
  register,
  errors,
  control,
  watch,
}) => {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "work_experience",
  })

  // Função para verificar se é um trabalho atual
  const isCurrentJob = (index: number): boolean => {
    if (watch) {
      return !!watch(`work_experience.${index}.current`)
    }
    // Fallback para comportamento anterior se watch não estiver disponível
    return !!control._formValues?.work_experience?.[index]?.current
  }

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")

  return (
    <SectionContainer
      title="Work Experience"
      actionButton={
        <Button
          leftIcon={<AddIcon />}
          size="sm"
          onClick={() =>
            append({
              company: "",
              position: "",
              start_date: "",
              end_date: "",
              current: false,
              description: "",
              location: "",
            })
          }
          bg={buttonBg}
          color={buttonColor}
          _hover={{ bg: buttonHoverBg }}
        >
          Add Experience
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
            zIndex={10}
          >
            <DeleteIcon />
          </Button>

          <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4}>
            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl
                isInvalid={!!errors.work_experience?.[index]?.company}
                mb={4}
              >
                <FormLabel>Company</FormLabel>
                <Input
                  {...register(`work_experience.${index}.company` as const, {
                    required: "Company is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.work_experience?.[index]?.company?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl
                isInvalid={!!errors.work_experience?.[index]?.position}
                mb={4}
              >
                <FormLabel>Position</FormLabel>
                <Input
                  {...register(`work_experience.${index}.position` as const, {
                    required: "Position is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.work_experience?.[index]?.position?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl mb={4}>
                <FormLabel>Location</FormLabel>
                <Input
                  {...register(`work_experience.${index}.location` as const)}
                />
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl
                isInvalid={!!errors.work_experience?.[index]?.start_date}
                mb={4}
              >
                <FormLabel>Start Date</FormLabel>
                <Input
                  type="date"
                  {...register(`work_experience.${index}.start_date` as const, {
                    required: "Start date is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.work_experience?.[index]?.start_date?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl mb={4}>
                <FormLabel>End Date</FormLabel>
                <Input
                  type="date"
                  {...register(`work_experience.${index}.end_date` as const)}
                  isDisabled={isCurrentJob(index)}
                />
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl display="flex" alignItems="center" mb={4}>
                <Checkbox
                  {...register(`work_experience.${index}.current` as const)}
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
                  {...register(`work_experience.${index}.description` as const)}
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
                company: "",
                position: "",
                start_date: "",
                end_date: "",
                current: false,
                description: "",
                location: "",
              })
            }
            bg={buttonBg}
            color={buttonColor}
            _hover={{ bg: buttonHoverBg }}
          >
            Add Experience
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default WorkExperienceSection
