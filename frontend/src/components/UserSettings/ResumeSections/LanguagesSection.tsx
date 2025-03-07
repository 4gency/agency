import { AddIcon, DeleteIcon } from "@chakra-ui/icons"
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Grid,
  GridItem,
  Input,
  Select,
  useColorModeValue,
} from "@chakra-ui/react"
import {
  type Control,
  type FieldErrors,
  type UseFormRegister,
  useFieldArray,
} from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface LanguagesSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
}

const LanguagesSection: React.FC<LanguagesSectionProps> = ({
  register,
  errors,
  control,
}) => {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "languages",
  })

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")

  const languageLevels = [
    "A1 - Beginner",
    "A2 - Elementary",
    "B1 - Intermediate",
    "B2 - Upper Intermediate",
    "C1 - Advanced",
    "C2 - Proficient",
    "Native",
  ]

  return (
    <SectionContainer
      title="Languages"
      actionButton={
        <Button
          leftIcon={<AddIcon />}
          size="sm"
          onClick={() =>
            append({
              name: "",
              level: "",
            })
          }
          bg={buttonBg}
          color={buttonColor}
          _hover={{ bg: buttonHoverBg }}
        >
          Add Language
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
            <GridItem>
              <FormControl isInvalid={!!errors.languages?.[index]?.name} mb={4}>
                <FormLabel>Language</FormLabel>
                <Input
                  {...register(`languages.${index}.name` as const, {
                    required: "Language name is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.languages?.[index]?.name?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl
                isInvalid={!!errors.languages?.[index]?.level}
                mb={4}
              >
                <FormLabel>Level</FormLabel>
                <Select
                  {...register(`languages.${index}.level` as const, {
                    required: "Level is required",
                  })}
                  placeholder="Select level"
                >
                  {languageLevels.map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
                </Select>
                <FormErrorMessage>
                  {errors.languages?.[index]?.level?.message}
                </FormErrorMessage>
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
                level: "",
              })
            }
            bg={buttonBg}
            color={buttonColor}
            _hover={{ bg: buttonHoverBg }}
          >
            Add Language
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default LanguagesSection
