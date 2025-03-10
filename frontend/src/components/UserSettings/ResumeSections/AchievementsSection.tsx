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
  Textarea,
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

interface AchievementsSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
}

const AchievementsSection: React.FC<AchievementsSectionProps> = ({
  register,
  errors,
  control,
}) => {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "achievements",
  })

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")

  return (
    <SectionContainer
      title="Achievements"
      infoTooltip="Highlight notable accomplishments that set you apart. Include awards, recognition, and measurable successes."
      actionButton={
        <Button
          leftIcon={<AddIcon />}
          size="sm"
          onClick={() =>
            append({
              name: "",
              description: "",
            })
          }
          bg={buttonBg}
          color={buttonColor}
          _hover={{ bg: buttonHoverBg }}
        >
          Add Achievement
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
              <FormControl isInvalid={!!errors.achievements?.[index]?.name} mb={4}>
                <FormLabel>Achievement Title</FormLabel>
                <Input
                  {...register(`achievements.${index}.name` as const, {
                    required: "Achievement title is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.achievements?.[index]?.name?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl mb={4}>
                <FormLabel>Description</FormLabel>
                <Textarea
                  {...register(`achievements.${index}.description` as const, {
                    required: "Description is required",
                  })}
                  rows={3}
                />
                <FormErrorMessage>
                  {errors.achievements?.[index]?.description?.message}
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
                description: "",
              })
            }
            bg={buttonBg}
            color={buttonColor}
            _hover={{ bg: buttonHoverBg }}
          >
            Add Achievement
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default AchievementsSection 