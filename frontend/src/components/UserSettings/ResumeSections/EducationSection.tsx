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
  IconButton,
  Input,
  useColorModeValue,
  Tag,
  TagLabel,
  TagCloseButton,
  Wrap,
  WrapItem,
  HStack,
} from "@chakra-ui/react"
import {
  type Control,
  type FieldErrors,
  type UseFormRegister,
  type UseFormWatch,
  type UseFormSetValue,
  useFieldArray,
} from "react-hook-form"
import { useState, KeyboardEvent, useEffect } from "react"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface EducationSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
  watch: UseFormWatch<ResumeForm>
  setValue: UseFormSetValue<ResumeForm>
}

const EducationSection: React.FC<EducationSectionProps> = ({
  register,
  errors,
  control,
  watch,
  setValue
}) => {
  const { fields, append, remove, update } = useFieldArray({
    control,
    name: "education",
  })

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")
  
  const [examInputs, setExamInputs] = useState<{[key: number]: string}>({});

  // Função para verificar se é um item atual
  const isCurrentEducation = (index: number): boolean => {
    const currentValue = watch(`education.${index}.current`);    
    if (typeof currentValue === 'boolean') {
      return currentValue;
    }
    
    // Caso o valor não seja um booleano
    return !!currentValue;
  }

  // Handle current education checkbox change
  const handleCurrentChange = (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const isChecked = e.target.checked;
    // Definimos explicitamente como um booleano
    setValue(`education.${index}.current`, Boolean(isChecked), { 
      shouldValidate: true, 
      shouldDirty: true 
    });
    
    // Se marcar como atual, limpe a data de término
    if (isChecked) {
      setValue(`education.${index}.end_date`, "", { 
        shouldValidate: true,
        shouldDirty: true 
      });
    }
    
    // Se for desmarcado, exibe o campo end_date e força a validação
    // para garantir que o usuário preencha uma data válida
    if (!isChecked) {
      const endDate = watch(`education.${index}.end_date`);
      if (!endDate || endDate.trim() === "") {
        setTimeout(() => {
          setValue(`education.${index}.end_date`, "", { 
            shouldValidate: true,
            shouldDirty: true,
            shouldTouch: true
          });
        }, 100);
      }
    }
  };

  // Adicionar um exame para um item específico
  const addExam = (index: number) => {
    const currentEducation = watch(`education.${index}`);
    const currentExams = currentEducation.exam || [];
    const examToAdd = examInputs[index]?.trim();
    
    if (examToAdd && !currentExams.includes(examToAdd)) {
      const updatedExams = [...currentExams, examToAdd];
      
      update(index, {
        ...currentEducation,
        exam: updatedExams
      });
      
      // Limpar o input
      setExamInputs({...examInputs, [index]: ''});
    }
  };

  // Adicionar exame ao pressionar vírgula ou Enter
  const handleExamKeyDown = (e: KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addExam(index);
    }
  };

  // Lidar com paste de múltiplos itens separados por vírgula
  const handleExamPaste = (e: React.ClipboardEvent<HTMLInputElement>, index: number) => {
    const pasteData = e.clipboardData.getData('text');
    if (pasteData.includes(',')) {
      e.preventDefault();
      
      const items = pasteData.split(',').map(item => item.trim()).filter(item => item !== '');
      if (items.length === 0) return;
      
      const currentEducation = watch(`education.${index}`);
      const currentExams = [...(currentEducation.exam || [])];
      
      // Adicionar apenas itens que não existem ainda
      items.forEach(item => {
        if (!currentExams.includes(item)) {
          currentExams.push(item);
        }
      });
      
      update(index, {
        ...currentEducation,
        exam: currentExams
      });
      
      // Limpar o input
      setExamInputs({...examInputs, [index]: ''});
    }
  };

  // Remover um exame
  const removeExam = (educationIndex: number, examIndex: number) => {
    const currentEducation = watch(`education.${educationIndex}`);
    const currentExams = [...(currentEducation.exam || [])];
    currentExams.splice(examIndex, 1);
    
    update(educationIndex, {
      ...currentEducation,
      exam: currentExams
    });
  };

  // Adicione um efeito para monitorar as mudanças nos valores da educação
  useEffect(() => {
    fields.forEach((_, index) => {
      const isCurrent = watch(`education.${index}.current`);
      const endDate = watch(`education.${index}.end_date`);
      
      // Se current for true, certifique-se de que end_date está vazio
      if (isCurrent && endDate) {
        setValue(`education.${index}.end_date`, "");
      }
    });
  }, [watch, fields, setValue]);

  return (
    <SectionContainer
      title="Education"
      infoTooltip="Include all relevant degrees, certifications, and coursework. Mark ongoing education as current."
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
              final_evaluation_grade: "",
              exam: [],
            })
          }
          bg={buttonBg}
          color={buttonColor}
          _hover={{ 
            bg: buttonHoverBg,
            transform: "translateY(-2px)",
            shadow: "md" 
          }}
          shadow="sm"
          transition="all 0.2s"
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
            zIndex={10}
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
              <FormControl mb={4} isInvalid={!!errors.education?.[index]?.end_date}>
                <FormLabel>End Date</FormLabel>
                <Input
                  type="date"
                  {...register(`education.${index}.end_date` as const, {
                    validate: value => {
                      // Se não for current, então end_date é obrigatório
                      const isCurrent = isCurrentEducation(index);
                      
                      if (!isCurrent && (!value || value.trim() === "")) {
                        return "End date is required when not a current education";
                      }
                      return true;
                    }
                  })}
                  disabled={isCurrentEducation(index)}
                />
                <FormErrorMessage>
                  {errors.education?.[index]?.end_date?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl display="flex" alignItems="center" mb={4}>
                <Checkbox
                  id={`education-current-${index}`}
                  isChecked={isCurrentEducation(index)}
                  onChange={(e) => handleCurrentChange(index, e)}
                  colorScheme="teal"
                >
                  Current
                </Checkbox>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl mb={4}>
                <FormLabel>Final Grade/GPA</FormLabel>
                <Input
                  {...register(`education.${index}.final_evaluation_grade` as const)}
                  placeholder="e.g., 3.8/4.0, A, 85%"
                />
              </FormControl>
            </GridItem>
            
            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl mb={4}>
                <FormLabel>Standardized Tests</FormLabel>
                <HStack mb={2}>
                  <Input
                    placeholder="e.g., GRE, GMAT, TOEFL"
                    value={examInputs[index] || ''}
                    onChange={(e) => setExamInputs({...examInputs, [index]: e.target.value})}
                    onKeyDown={(e) => handleExamKeyDown(e, index)}
                    onPaste={(e) => handleExamPaste(e, index)}
                  />
                  <IconButton
                    aria-label="Add test"
                    icon={<AddIcon />}
                    onClick={() => addExam(index)}
                    colorScheme="gray"
                    shadow="sm"
                    _hover={{ 
                      transform: "translateY(-2px)",
                      shadow: "md" 
                    }}
                    transition="all 0.2s"
                  />
                </HStack>
                
                <Wrap spacing={2} mt={2}>
                  {watch(`education.${index}.exam`) && 
                    (watch(`education.${index}.exam`) || []).map((exam: string, examIndex: number) => (
                      <WrapItem key={examIndex}>
                        <Tag size="md" borderRadius="full" variant="solid" colorScheme="teal">
                          <TagLabel>{exam}</TagLabel>
                          <TagCloseButton 
                            onClick={() => removeExam(index, examIndex)} 
                          />
                        </Tag>
                      </WrapItem>
                    ))
                  }
                </Wrap>
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
                final_evaluation_grade: "",
                exam: [],
              })
            }
            bg={buttonBg}
            color={buttonColor}
            _hover={{ 
              bg: buttonHoverBg,
              transform: "translateY(-2px)",
              shadow: "md" 
            }}
            shadow="sm"
            transition="all 0.2s"
          >
            Add Education
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default EducationSection
