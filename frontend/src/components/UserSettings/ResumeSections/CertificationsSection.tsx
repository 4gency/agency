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

interface CertificationsSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
}

const CertificationsSection: React.FC<CertificationsSectionProps> = ({
  register,
  errors,
  control,
}) => {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "certifications",
  })

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")

  return (
    <SectionContainer
      title="Certifications"
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
          Add Certification
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
              <FormControl isInvalid={!!errors.certifications?.[index]?.name} mb={4}>
                <FormLabel>Certification Name</FormLabel>
                <Input
                  {...register(`certifications.${index}.name` as const, {
                    required: "Certification name is required",
                  })}
                />
                <FormErrorMessage>
                  {errors.certifications?.[index]?.name?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl mb={4}>
                <FormLabel>Description</FormLabel>
                <Textarea
                  {...register(`certifications.${index}.description` as const, {
                    required: "Description is required",
                  })}
                  rows={3}
                />
                <FormErrorMessage>
                  {errors.certifications?.[index]?.description?.message}
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
            Add Certification
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default CertificationsSection 