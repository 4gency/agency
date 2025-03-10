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
  Textarea,
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

interface WorkExperienceSectionProps {
  register: UseFormRegister<ResumeForm>
  errors: FieldErrors<ResumeForm>
  control: Control<ResumeForm>
  watch?: UseFormWatch<ResumeForm>
  setValue: UseFormSetValue<ResumeForm>
}

const WorkExperienceSection: React.FC<WorkExperienceSectionProps> = ({
  register,
  errors,
  control,
  watch,
  setValue
}) => {
  const { fields, append, remove, update } = useFieldArray({
    control,
    name: "work_experience",
  })

  const [skillInputs, setSkillInputs] = useState<{[key: number]: string}>({});

  // Função para adicionar uma habilidade
  const addSkill = (index: number) => {
    if (!watch) return;
    
    const currentExperience = watch(`work_experience.${index}`);
    const currentSkills = currentExperience.skills_acquired || [];
    const skillToAdd = skillInputs[index]?.trim();
    
    if (skillToAdd && !currentSkills.includes(skillToAdd)) {
      const updatedSkills = [...currentSkills, skillToAdd];
      
      update(index, {
        ...currentExperience,
        skills_acquired: updatedSkills
      });
      
      // Limpar o input
      setSkillInputs({...skillInputs, [index]: ''});
    }
  };

  // Adicionar skill ao pressionar vírgula ou Enter
  const handleSkillKeyDown = (e: KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill(index);
    }
  };

  // Lidar com paste de múltiplos itens separados por vírgula
  const handleSkillPaste = (e: React.ClipboardEvent<HTMLInputElement>, index: number) => {
    if (!watch) return;
    
    const pasteData = e.clipboardData.getData('text');
    if (pasteData.includes(',')) {
      e.preventDefault();
      
      const items = pasteData.split(',').map(item => item.trim()).filter(item => item !== '');
      if (items.length === 0) return;
      
      const currentExperience = watch(`work_experience.${index}`);
      const currentSkills = [...(currentExperience.skills_acquired || [])];
      
      // Adicionar apenas itens que não existem ainda
      items.forEach(item => {
        if (!currentSkills.includes(item)) {
          currentSkills.push(item);
        }
      });
      
      update(index, {
        ...currentExperience,
        skills_acquired: currentSkills
      });
      
      // Limpar o input
      setSkillInputs({...skillInputs, [index]: ''});
    }
  };

  // Função para remover uma habilidade
  const removeSkill = (experienceIndex: number, skillIndex: number) => {
    if (!watch) return;
    
    const currentExperience = watch(`work_experience.${experienceIndex}`);
    const currentSkills = [...(currentExperience.skills_acquired || [])];
    currentSkills.splice(skillIndex, 1);
    
    update(experienceIndex, {
      ...currentExperience,
      skills_acquired: currentSkills
    });
  };

  // Função para verificar se é um trabalho atual
  const isCurrentJob = (index: number): boolean => {
    if (!watch) return false;
    
    // Obtenha o valor diretamente do campo current
    const currentValue = watch(`work_experience.${index}.current`);
    
    // Isso permitirá que vejamos o valor exato que está sendo usado
    console.log(`Work experience ${index} current value:`, currentValue, "type:", typeof currentValue);
    
    if (typeof currentValue === 'boolean') {
      return currentValue;
    }
    
    // Caso o valor não seja um booleano (pode ser undefined, null, string, etc.)
    return !!currentValue;
  }

  // Handle current job checkbox change
  const handleCurrentChange = (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const isChecked = e.target.checked;
    console.log(`Changing work experience ${index} current to:`, isChecked, "type:", typeof isChecked);
    
    // Definimos explicitamente como um booleano
    setValue(`work_experience.${index}.current`, Boolean(isChecked), { 
      shouldValidate: true, 
      shouldDirty: true 
    });
    
    // Se marcar como atual, limpe a data de término
    if (isChecked) {
      setValue(`work_experience.${index}.end_date`, "", { 
        shouldValidate: true,
        shouldDirty: true 
      });
    }
    
    // Se for desmarcado, exibe o campo end_date e força a validação
    // para garantir que o usuário preencha uma data válida
    if (!isChecked && watch) {
      const endDate = watch(`work_experience.${index}.end_date`);
      if (!endDate || endDate.trim() === "") {
        setTimeout(() => {
          setValue(`work_experience.${index}.end_date`, "", { 
            shouldValidate: true,
            shouldDirty: true,
            shouldTouch: true
          });
        }, 100);
      }
    }
  };

  // Adicione um efeito para monitorar as mudanças nos valores do trabalho
  useEffect(() => {
    if (!watch) return;
    
    // Para cada experiência de trabalho, monitore as alterações em current e end_date
    fields.forEach((field, index) => {
      const isCurrent = watch(`work_experience.${index}.current`);
      const endDate = watch(`work_experience.${index}.end_date`);
      
      console.log(`Work experience ${index} values:`, {
        company: watch(`work_experience.${index}.company`),
        current: isCurrent,
        end_date: endDate
      });
      
      // Se current for true, certifique-se de que end_date está vazio
      if (isCurrent && endDate) {
        setValue(`work_experience.${index}.end_date`, "");
      }
    });
  }, [watch, fields, setValue]);

  const buttonBg = useColorModeValue("#00766C", "#00766C")
  const buttonHoverBg = useColorModeValue("#005f57", "#005f57")
  const buttonColor = useColorModeValue("white", "white")

  return (
    <SectionContainer 
      title="Work Experience" 
      infoTooltip="Detail your job history, focusing on achievements and responsibilities. Quantify results where possible."
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
              industry: "",
              skills_acquired: [],
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
                <FormLabel>Industry</FormLabel>
                <Input
                  {...register(`work_experience.${index}.industry` as const)}
                  placeholder="e.g., Technology, Healthcare, Finance"
                />
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
              <FormControl mb={4} isInvalid={!!errors.work_experience?.[index]?.end_date}>
                <FormLabel>End Date</FormLabel>
                <Input
                  type="date"
                  {...register(`work_experience.${index}.end_date` as const, {
                    validate: value => {
                      // Se não for current, então end_date é obrigatório
                      const isCurrent = isCurrentJob(index);
                      
                      if (!isCurrent && (!value || value.trim() === "")) {
                        return "End date is required when not a current job";
                      }
                      return true;
                    }
                  })}
                  disabled={isCurrentJob(index)}
                />
                <FormErrorMessage>
                  {errors.work_experience?.[index]?.end_date?.message}
                </FormErrorMessage>
              </FormControl>
            </GridItem>

            <GridItem>
              <FormControl display="flex" alignItems="center" mb={4}>
                <Checkbox
                  id={`work-experience-current-${index}`}
                  isChecked={isCurrentJob(index)}
                  onChange={(e) => handleCurrentChange(index, e)}
                  colorScheme="teal"
                >
                  Current
                </Checkbox>
              </FormControl>
            </GridItem>

            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl mb={4}>
                <FormLabel>Job Description</FormLabel>
                <Textarea
                  {...register(`work_experience.${index}.description` as const)}
                  rows={3}
                  placeholder="Describe your key responsibilities and achievements"
                />
              </FormControl>
            </GridItem>

            <GridItem colSpan={{ base: 1, md: 2 }}>
              <FormControl mb={4}>
                <FormLabel>Skills Acquired</FormLabel>
                <HStack mb={2}>
                  <Input
                    placeholder="e.g., Project Management, Python, Public Speaking"
                    value={skillInputs[index] || ''}
                    onChange={(e) => setSkillInputs({...skillInputs, [index]: e.target.value})}
                    onKeyDown={(e) => handleSkillKeyDown(e, index)}
                    onPaste={(e) => handleSkillPaste(e, index)}
                  />
                  <IconButton
                    aria-label="Add skill"
                    icon={<AddIcon />}
                    onClick={() => addSkill(index)}
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
                  {watch && watch(`work_experience.${index}.skills_acquired`) && 
                    (watch(`work_experience.${index}.skills_acquired`) || []).map((skill: string, skillIndex: number) => (
                      <WrapItem key={skillIndex}>
                        <Tag size="md" borderRadius="full" variant="solid" colorScheme="teal">
                          <TagLabel>{skill}</TagLabel>
                          <TagCloseButton 
                            onClick={() => removeSkill(index, skillIndex)} 
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
                company: "",
                position: "",
                start_date: "",
                end_date: "",
                current: false,
                description: "",
                location: "",
                industry: "",
                skills_acquired: [],
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
            Add Experience
          </Button>
        </Flex>
      )}
    </SectionContainer>
  )
}

export default WorkExperienceSection
