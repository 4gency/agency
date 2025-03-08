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

interface ProjectsSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
  watch?: UseFormWatch<ResumeForm>
}

const ProjectsSection: React.FC<ProjectsSectionProps> = ({
  register,
  errors,
  control,
  watch,
}) => {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "projects",
  })

  // Função para verificar se é um projeto atual
  const isCurrentProject = (index: number): boolean => {
    if (watch) {
      return !!watch(`projects.${index}.current`)
    }
    // Fallback para comportamento anterior se watch não estiver disponível
    return !!control._formValues?.projects?.[index]?.current
  }

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")

  return (
    <SectionContainer
      title="Projects"
      actionButton={
        <Button
          leftIcon={<AddIcon />}
          size="sm"
          onClick={() =>
            append({
              name: "",
              description: "",
              url: "",
              start_date: "",
              end_date: "",
              current: false,
            })
          }
          bg={buttonBg}
          color={buttonColor}
          _hover={{ bg: buttonHoverBg }}
        >
          Add Project
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
              <FormControl isInvalid={!!errors.projects?.[index]?.name} mb={4}>
                <FormLabel>Project Name</FormLabel>
                <Input
                  {...register(`projects.${index}.name` as const, {
                    required: "Project name is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.projects?.[index]?.name?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl mb={4}>
                <FormLabel>URL</FormLabel>
                <Input
                  {...register(`projects.${index}.url` as const)}
                  placeholder="https://..."
                />
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl mb={4}>
                <FormLabel>Start Date</FormLabel>
                <Input
                  type="date"
                  {...register(`projects.${index}.start_date` as const)}
                />
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl mb={4}>
                <FormLabel>End Date</FormLabel>
                <Input
                  type="date"
                  {...register(`projects.${index}.end_date` as const)}
                  isDisabled={isCurrentProject(index)}
                />
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl display="flex" alignItems="center" mb={4}>
                <Checkbox
                  {...register(`projects.${index}.current` as const)}
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
                  {...register(`projects.${index}.description` as const)}
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
                name: "",
                description: "",
                url: "",
                start_date: "",
                end_date: "",
                current: false,
              })
            }
            bg={buttonBg}
            color={buttonColor}
            _hover={{ bg: buttonHoverBg }}
          >
            Add Project
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default ProjectsSection
