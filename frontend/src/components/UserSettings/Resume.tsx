import {
  Alert,
  AlertIcon,
  AlertDescription,
  Button,
  ButtonGroup,
  Card,
  Container,
  Heading,
  Skeleton,
  Stack,
} from "@chakra-ui/react"
import { useMutation, useQuery } from "@tanstack/react-query"
import type React from "react"
import { useEffect, useState, useMemo, forwardRef, useImperativeHandle } from "react"
import { useForm } from "react-hook-form"
import { ConfigsService, SubscriptionsService } from "../../client/sdk.gen"
import type { GetPlainTextResumeResponse } from "../../client/types.gen"
import { ApiError } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import type { ResumeForm } from "./types"

import AvailabilitySection from "./ResumeSections/AvailabilitySection"
import EducationSection from "./ResumeSections/EducationSection"
import InterestsSection from "./ResumeSections/InterestsSection"
import LanguagesSection from "./ResumeSections/LanguagesSection"
import PersonalInformationSection from "./ResumeSections/PersonalInformationSection"
import ProjectsSection from "./ResumeSections/ProjectsSection"
import SalaryExpectationSection from "./ResumeSections/SalaryExpectationSection"
import SkillsSection from "./ResumeSections/SkillsSection"
import WorkExperienceSection from "./ResumeSections/WorkExperienceSection"
import WorkPreferenceSection from "./ResumeSections/WorkPreferenceSection"
import AchievementsSection from "./ResumeSections/AchievementsSection"
import CertificationsSection from "./ResumeSections/CertificationsSection"
import SelfIdentificationSection from "./ResumeSections/SelfIdentificationSection"
import LegalAuthorizationSection from "./ResumeSections/LegalAuthorizationSection"

// Default empty form values
const defaultValues: ResumeForm = {
  personal_information: {
    name: "",
    surname: "",
    email: "",
    date_of_birth: "",
    country: "",
    city: "",
    address: "",
    zip_code: "",
    phone_prefix: "",
    phone: "",
    linkedin: "",
    github: "",
  },
  education: [],
  work_experience: [],
  projects: [],
  skills: [],
  languages: [],
  salary_expectation: {
    minimum: undefined,
    maximum: undefined,
  },
  work_preference: {
    remote: false,
    hybrid: false,
    on_site: false,
    relocation: false,
    willing_to_complete_assessments: false,
    willing_to_undergo_drug_tests: false,
    willing_to_undergo_background_checks: false,
  },
  interests: [],
  achievements: [],
  certifications: [],
  availability: "",
  self_identification: {
    gender: "",
    pronouns: "",
    veteran: false,
    disability: false,
    ethnicity: "",
  },
  legal_authorization: {
    eu_work_authorization: false,
    us_work_authorization: false,
    requires_us_visa: false,
    requires_us_sponsorship: false,
    requires_eu_visa: false,
    legally_allowed_to_work_in_eu: false,
    legally_allowed_to_work_in_us: false,
    requires_eu_sponsorship: false,
    canada_work_authorization: false,
    requires_canada_visa: false,
    legally_allowed_to_work_in_canada: false,
    requires_canada_sponsorship: false,
    uk_work_authorization: false,
    requires_uk_visa: false,
    legally_allowed_to_work_in_uk: false,
    requires_uk_sponsorship: false,
  },
}

// Função auxiliar para normalizar datas
const parseEmploymentPeriod = (period: string): { startDate: string; endDate: string; isCurrent: boolean } => {
  let startDate = "";
  let endDate = "";
  let isCurrent = false;
  
  // Log original
  
  if (!period) {
    return { startDate, endDate, isCurrent };
  }
  
  // Remover espaços extras e normalizar
  const normalizedPeriod = period.trim().replace(/\s+/g, ' ');
  
  // Verificar se contém a palavra "Present" em qualquer parte
  if (normalizedPeriod.toLowerCase().includes("present")) {
    isCurrent = true;
    
    // Procurar por um padrão comum: início "-" presente
    const presentPattern = /(.+?)\s*-\s*(?:present|atual|current)/i;
    const match = normalizedPeriod.match(presentPattern);
    
    if (match && match[1]) {
      startDate = match[1].trim();
    } else {
      // Último recurso se não conseguir extrair a data de início
      startDate = normalizedPeriod.replace(/\s*-\s*(?:present|atual|current)/i, "").trim();
    }
  } 
  // Verificar padrão de data específico: YYYY-MM-DD - YYYY-MM-DD
  else {
    const datePattern = /(\d{4}-\d{1,2}-\d{1,2})\s*-\s*(\d{4}-\d{1,2}-\d{1,2})/;
    const match = normalizedPeriod.match(datePattern);
    
    if (match) {
      startDate = match[1];
      endDate = match[2];
    } 
    // Tentar dividir por hífen com espaços
    else if (normalizedPeriod.includes(" - ")) {
      const parts = normalizedPeriod.split(" - ");
      if (parts.length === 2) {
        startDate = parts[0].trim();
        endDate = parts[1].trim();
      }
    } 
    // Tentar dividir apenas por hífen
    else if (normalizedPeriod.includes("-")) {
      // Se contém hífen nas datas (como 2020-01-01), precisamos ter cuidado
      // Use regex para encontrar os padrões de data
      const datesPattern = /(\d{4}-\d{1,2}-\d{1,2}).*?(\d{4}-\d{1,2}-\d{1,2})/;
      const datesMatch = normalizedPeriod.match(datesPattern);
      
      if (datesMatch) {
        startDate = datesMatch[1];
        endDate = datesMatch[2];
      } else {
        // Último recurso: dividir pelo primeiro hífen e tentar interpretar
        const parts = normalizedPeriod.split("-");
        startDate = parts[0].trim();
        
        // Se tiver mais de 2 partes, juntar o resto
        if (parts.length > 1) {
          endDate = parts.slice(1).join("-").trim();
        }
      }
    } 
    // Se não tiver hífen ou outros separadores, considerar como data única
    else {
      startDate = normalizedPeriod;
      isCurrent = true; // Assumir que é atual se só tem uma data
    }
  }
  
  // Verificar se temos uma data de fim
  isCurrent = isCurrent || !endDate || endDate.trim() === "";
  
  return { startDate, endDate, isCurrent };
};

// Function to transform API response to our form model
const transformApiResponseToFormData = (
  apiData: GetPlainTextResumeResponse,
): ResumeForm => {
  try {
    // Check if apiData is null or undefined
    if (!apiData) {
      console.warn("API data is null or undefined, using default values")
      return defaultValues
    }

    // Check if we received a JSON string and parse it
    if (typeof apiData === "string") {
      try {
        const parsed = JSON.parse(apiData)
        return {
          ...defaultValues,
          ...parsed,
        }
      } catch (e) {
        console.error("Error parsing resume JSON string:", e)
        return defaultValues
      }
    }

    // Handle case where we have plain text resume in the actual structure
    if (apiData.personal_information) {
      // Extract skills from experience details
      let skills: string[] = []

      // Collect skills from experience details
      if (Array.isArray(apiData.experience_details)) {
        const skillsFromExperience = apiData.experience_details
          .flatMap((exp) => exp.skills_acquired || [])
          .filter((skill: string) => skill && skill.trim() !== "")

        skills = [...skills, ...skillsFromExperience]
      }

      // Add direct skills if available in any custom properties
      const apiDataAny = apiData as any
      if (Array.isArray(apiDataAny.skills)) {
        const directSkills = apiDataAny.skills.filter(
          (skill: string) => skill && skill.trim() !== "",
        )
        skills = [...skills, ...directSkills]
      }

      // Remove duplicates
      skills = Array.from(new Set(skills))

      // Ensure we always have an array for interests
      let interests: string[] = []
      if (Array.isArray(apiData.interests)) {
        interests = apiData.interests.filter(
          (interest: string) =>
            interest && typeof interest === "string" && interest.trim() !== "",
        )
      }

      // Parse salary range from string to min/max numbers
      let minimum: number | undefined = undefined
      let maximum: number | undefined = undefined
      
      if (apiData.salary_expectations?.salary_range_usd) {
        const range = apiData.salary_expectations.salary_range_usd.split('-');
        if (range.length === 2) {
          minimum = parseInt(range[0].trim().replace(/\D/g, ''));
          maximum = parseInt(range[1].trim().replace(/\D/g, ''));
        }
      }

      // Map achievements
      const achievements = Array.isArray(apiData.achievements)
        ? apiData.achievements.map((ach) => ({
            name: ach.name || "",
            description: ach.description || "",
          }))
        : [];

      // Map certifications
      const certifications = Array.isArray(apiData.certifications)
        ? apiData.certifications.map((cert) => ({
            name: cert.name || "",
            description: cert.description || "",
          }))
        : [];

      // Extract self identification
      const selfId = apiData.self_identification || {};

      // Extract legal authorization
      const legalAuth = apiData.legal_authorization || {};

      return {
        personal_information: {
          name: apiData.personal_information.name || "",
          surname: apiData.personal_information.surname || "",
          email: apiData.personal_information.email || "",
          date_of_birth: apiData.personal_information.date_of_birth || "",
          country: apiData.personal_information.country || "",
          city: apiData.personal_information.city || "",
          address: apiData.personal_information.address || "",
          zip_code: apiData.personal_information.zip_code || "",
          phone_prefix: apiData.personal_information.phone_prefix || "",
          phone: apiData.personal_information.phone || "",
          linkedin: apiData.personal_information.linkedin || "",
          github: apiData.personal_information.github || "",
        },
        education: Array.isArray(apiData.education_details)
          ? apiData.education_details.map((edu) => {
              // Verificando se o campo year_of_completion está vazio para marcar como current
              const isCurrent = !edu.year_of_completion || edu.year_of_completion.trim() === "";
              
              return {
                institution: edu.institution || "",
                degree: edu.education_level || "",
                field_of_study: edu.field_of_study || "",
                start_date: edu.start_date || "",
                end_date: edu.year_of_completion || "",
                current: isCurrent,
                final_evaluation_grade: edu.final_evaluation_grade || "",
                exam: edu.exam || [],
              };
            })
          : [],
        work_experience: Array.isArray(apiData.experience_details)
          ? apiData.experience_details.map((exp) => {
              // Usar a função de parsing robusta
              const { startDate, endDate, isCurrent } = parseEmploymentPeriod(exp.employment_period);
              
              return {
                company: exp.company || "",
                position: exp.position || "",
                start_date: startDate,
                end_date: endDate,
                current: isCurrent,
                description: (exp.key_responsibilities || []).join("\n") || "",
                location: exp.location || "",
                industry: exp.industry || "",
                skills_acquired: exp.skills_acquired || [],
              };
            })
          : [],
        projects: Array.isArray(apiData.projects)
          ? apiData.projects.map((proj) => ({
              name: proj.name || "",
              description: proj.description || "",
              url: proj.link || "",
            }))
          : [],
        skills: skills,
        languages: Array.isArray(apiData.languages)
          ? apiData.languages.map((lang) => ({
              name: lang.language || "",
              level: lang.proficiency || "",
            }))
          : [],
        availability: apiData.availability?.notice_period || "",
        salary_expectation: {
          minimum: minimum,
          maximum: maximum,
        },
        work_preference: {
          remote: apiData.work_preferences?.remote_work || false,
          hybrid: false, // API doesn't have hybrid option
          on_site: apiData.work_preferences?.in_person_work || false,
          relocation: apiData.work_preferences?.open_to_relocation || false,
          willing_to_complete_assessments: apiData.work_preferences?.willing_to_complete_assessments || false,
          willing_to_undergo_drug_tests: apiData.work_preferences?.willing_to_undergo_drug_tests || false,
          willing_to_undergo_background_checks: apiData.work_preferences?.willing_to_undergo_background_checks || false,
        },
        interests: interests,
        achievements: achievements,
        certifications: certifications,
        self_identification: {
          gender: selfId.gender || "",
          pronouns: selfId.pronouns || "",
          veteran: selfId.veteran || false,
          disability: selfId.disability || false,
          ethnicity: selfId.ethnicity || "",
        },
        legal_authorization: {
          eu_work_authorization: legalAuth.eu_work_authorization || false,
          us_work_authorization: legalAuth.us_work_authorization || false,
          requires_us_visa: legalAuth.requires_us_visa || false,
          requires_us_sponsorship: legalAuth.requires_us_sponsorship || false,
          requires_eu_visa: legalAuth.requires_eu_visa || false,
          legally_allowed_to_work_in_eu: legalAuth.legally_allowed_to_work_in_eu || false,
          legally_allowed_to_work_in_us: legalAuth.legally_allowed_to_work_in_us || false,
          requires_eu_sponsorship: legalAuth.requires_eu_sponsorship || false,
          canada_work_authorization: legalAuth.canada_work_authorization || false,
          requires_canada_visa: legalAuth.requires_canada_visa || false,
          legally_allowed_to_work_in_canada: legalAuth.legally_allowed_to_work_in_canada || false,
          requires_canada_sponsorship: legalAuth.requires_canada_sponsorship || false,
          uk_work_authorization: legalAuth.uk_work_authorization || false,
          requires_uk_visa: legalAuth.requires_uk_visa || false,
          legally_allowed_to_work_in_uk: legalAuth.legally_allowed_to_work_in_uk || false,
          requires_uk_sponsorship: legalAuth.requires_uk_sponsorship || false,
        },
      }
    }

    return defaultValues
  } catch (error) {
    console.error("Error transforming API response:", error)
    if (apiData) {
      console.error(
        "Failed to transform API data structure:",
        typeof apiData === "object"
          ? JSON.stringify(apiData, null, 2)
          : typeof apiData,
      )
    }
    return defaultValues
  }
}

// Function to transform form data to API model
const transformFormToApiData = (
  data: ResumeForm,
): GetPlainTextResumeResponse => {
  try {
    return {
      personal_information: {
        name: data.personal_information.name,
        surname: data.personal_information.surname,
        email: data.personal_information.email,
        date_of_birth: data.personal_information.date_of_birth || "",
        country: data.personal_information.country || "",
        city: data.personal_information.city || "",
        address: data.personal_information.address || "",
        zip_code: data.personal_information.zip_code || "",
        phone_prefix: data.personal_information.phone_prefix || "",
        phone: data.personal_information.phone || "",
        linkedin: data.personal_information.linkedin || "",
        github: data.personal_information.github || "",
      },
      education_details: data.education.map((edu) => {        
        // Se for current, garantir que não enviamos year_of_completion
        const yearOfCompletion = edu.current ? "" : edu.end_date || "";
        
        return {
          institution: edu.institution,
          education_level: edu.degree,
          field_of_study: edu.field_of_study || "",
          start_date: edu.start_date,
          year_of_completion: yearOfCompletion,
          final_evaluation_grade: edu.final_evaluation_grade || "",
          exam: edu.exam || [],
        };
      }),
      experience_details: data.work_experience.map((exp) => {
        // Formatar employment_period de forma robusta
        let employmentPeriod = "";
        
        if (exp.start_date) {
          // Inicia com a data de início
          employmentPeriod = exp.start_date.trim();
          
          // Adiciona data de término apenas se não for um trabalho atual
          if (!exp.current) {
            // Verifica se existe uma data de término válida
            if (exp.end_date && exp.end_date.trim() !== "") {
              employmentPeriod += ` - ${exp.end_date.trim()}`;
            } else {
              console.warn("Work experience has current=false but no end_date:", exp);
            }
          } else {
            // Se for current, adicione explicitamente " - Present"
            employmentPeriod += " - Present";
          }
        }
        
        return {
          company: exp.company,
          position: exp.position,
          employment_period: employmentPeriod,
          location: exp.location || "",
          key_responsibilities: exp.description ? [exp.description] : [],
          skills_acquired: exp.skills_acquired || [],
          industry: exp.industry || "",
        };
      }),
      projects: data.projects.map((proj) => ({
        name: proj.name,
        description: proj.description || "",
        link: proj.url || "",
      })),
      languages: data.languages.map((lang) => ({
        language: lang.name,
        proficiency: lang.level,
      })),
      interests: data.interests,
      availability: {
        notice_period: data.availability || "",
      },
      salary_expectations: {
        salary_range_usd:
          data.salary_expectation.minimum && data.salary_expectation.maximum
            ? `${data.salary_expectation.minimum} - ${data.salary_expectation.maximum}`
            : "",
      },
      work_preferences: {
        remote_work: data.work_preference.remote || false,
        in_person_work: data.work_preference.on_site || false,
        open_to_relocation: data.work_preference.relocation || false,
        willing_to_complete_assessments: data.work_preference.willing_to_complete_assessments || false,
        willing_to_undergo_drug_tests: data.work_preference.willing_to_undergo_drug_tests || false,
        willing_to_undergo_background_checks: data.work_preference.willing_to_undergo_background_checks || false,
      },
      achievements: data.achievements.map(ach => ({
        name: ach.name,
        description: ach.description,
      })),
      certifications: data.certifications.map(cert => ({
        name: cert.name,
        description: cert.description,
      })),
      self_identification: {
        gender: data.self_identification.gender || "",
        pronouns: data.self_identification.pronouns || "",
        veteran: data.self_identification.veteran || false,
        disability: data.self_identification.disability || false,
        ethnicity: data.self_identification.ethnicity || "",
      },
      legal_authorization: {
        eu_work_authorization: data.legal_authorization.eu_work_authorization || false,
        us_work_authorization: data.legal_authorization.us_work_authorization || false,
        requires_us_visa: data.legal_authorization.requires_us_visa || false,
        requires_us_sponsorship: data.legal_authorization.requires_us_sponsorship || false,
        requires_eu_visa: data.legal_authorization.requires_eu_visa || false,
        legally_allowed_to_work_in_eu: data.legal_authorization.legally_allowed_to_work_in_eu || false,
        legally_allowed_to_work_in_us: data.legal_authorization.legally_allowed_to_work_in_us || false,
        requires_eu_sponsorship: data.legal_authorization.requires_eu_sponsorship || false,
        canada_work_authorization: data.legal_authorization.canada_work_authorization || false,
        requires_canada_visa: data.legal_authorization.requires_canada_visa || false,
        legally_allowed_to_work_in_canada: data.legal_authorization.legally_allowed_to_work_in_canada || false,
        requires_canada_sponsorship: data.legal_authorization.requires_canada_sponsorship || false,
        uk_work_authorization: data.legal_authorization.uk_work_authorization || false,
        requires_uk_visa: data.legal_authorization.requires_uk_visa || false,
        legally_allowed_to_work_in_uk: data.legal_authorization.legally_allowed_to_work_in_uk || false,
        requires_uk_sponsorship: data.legal_authorization.requires_uk_sponsorship || false,
      },
    }
  } catch (error) {
    console.error("Error transforming form data to API model:", error)
    throw error
  }
}

// Loading skeleton component
const LoadingSkeleton: React.FC = () => (
  <Stack spacing={6} width="100%">
    <Skeleton height="40px" width="200px" />
    <Skeleton height="100px" />
    <Skeleton height="200px" />
    <Skeleton height="150px" />
    <Skeleton height="100px" />
  </Stack>
)

// Main component
export const ResumePage: React.FC = () => {
  const showToast = useCustomToast()
  const [_scrollPosition, setScrollPosition] = useState<number>(0)
  const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false)
  const [hasShownNotFoundMessage, setHasShownNotFoundMessage] = useState<boolean>(false)

  // Form setup
  const {
    register,
    handleSubmit,
    control,
    setValue,
    getValues,
    reset,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<ResumeForm>({
    defaultValues,
  })

  // Fetch user subscriptions
  const { data: subscriptions, isLoading: isLoadingSubscriptions } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: async () => {
      return await SubscriptionsService.getUserSubscriptions({
        onlyActive: true,
      })
    }
  })

  // Check if user has an active subscription
  const hasActiveSubscription = useMemo(() => {
    const hasSubscription = subscriptions && subscriptions.length > 0;
    return hasSubscription;
  }, [subscriptions]);

  // Fetch resume data with better error handling
  const { data: resumeData, isLoading: isLoadingResume, error: resumeError } = useQuery({
    queryKey: ["plainTextResume"],
    queryFn: async () => {
      try {
        const result = await ConfigsService.getPlainTextResume();
        return result;
      } catch (error) {
        const apiError = error as ApiError;
        if (apiError.status === 404) {
          setIsCreatingNew(true);
          // Não mostrar toast aqui, deixar para o useEffect
        }
        throw error;
      }
    },
    // Don't condition the query on subscription status to avoid race conditions
    enabled: true,
    retry: false, // Não tentar novamente automaticamente
    refetchOnWindowFocus: false,
    staleTime: 60000, // 1 minuto
  });

  // Reset form data when resume data is loaded or cleared
  useEffect(() => {
    if (resumeData) {
      // If we successfully load data, we're editing an existing resume
      setIsCreatingNew(false);
      
      // Transform API data to form format
      const formData = transformApiResponseToFormData(resumeData);
      reset(formData);
    }
  }, [resumeData, reset]);

  // Handle resume fetch error - only show actual errors, not 404
  useEffect(() => {
    // If loading or data exists, do nothing
    if (isLoadingResume || resumeData) return;
    
    // If we have an active subscription but no resume data
    if (hasActiveSubscription && !resumeData) {
      const apiError = resumeError as ApiError;
      
      // Show message for 404 only if we haven't shown it already
      if (apiError && apiError.status === 404) {
        if (!hasShownNotFoundMessage) {
          setIsCreatingNew(true);
          setHasShownNotFoundMessage(true);
          showToast(
            "Resume not found",
            "Please fill out the form to create your resume.",
            "success"
          )
        }
      } else if (apiError) {
        // Real errors
        console.error("Resume fetch error:", apiError);
        showToast(
          "Error fetching resume",
          apiError.message || "An error occurred while fetching your resume.",
          "error"
        )
      }
    }
  }, [hasActiveSubscription, isLoadingResume, resumeData, resumeError, showToast, isCreatingNew, hasShownNotFoundMessage]);

  // Update resume mutation with better error handling
  const updateResumeMutation = useMutation({
    mutationFn: async (data: ResumeForm) => {
      if (!hasActiveSubscription) {
        throw new Error("No active subscription available")
      }
      
      try {
        const apiData = transformFormToApiData(data)
        const result = await ConfigsService.updatePlainTextResume({
          requestBody: apiData,
        })
        
        // If we were creating a new resume, we're now editing
        if (isCreatingNew) {
          setIsCreatingNew(false)
        }
        
        return result
      } catch (error) {
        console.error("Error saving resume:", error)
        throw error
      }
    },
    onSuccess: () => {
      showToast(
        isCreatingNew ? "Resume created" : "Resume updated",
        isCreatingNew 
          ? "Your resume has been successfully created." 
          : "Your resume has been successfully updated.",
        "success",
      )
    },
    onError: (error: Error) => {
      console.error("Resume mutation error:", error)
      
      // Melhor tratamento para garantir que o erro seja sempre uma string
      let errorMessage = "An unexpected error occurred."
      
      // Tenta extrair detalhes do erro em diferentes formatos
      try {
        const apiError = error as ApiError
        
        if (apiError.body) {
          const errorBody = apiError.body as any
          
          if (errorBody.detail) {
            // Se detail for um objeto (validation_error), extrair apenas as mensagens
            if (typeof errorBody.detail === 'object') {
              if (Array.isArray(errorBody.detail)) {
                // Se for um array de erros
                errorMessage = errorBody.detail
                  .map((err: any) => {
                    if (typeof err === 'object' && err.msg) {
                      return String(err.msg)
                    }
                    return String(err)
                  })
                  .join(", ")
              } else if (errorBody.detail.msg) {
                // Se for um único objeto de erro com a propriedade msg
                errorMessage = String(errorBody.detail.msg)
              } else {
                // Para outros objetos, tente obter uma representação de string
                errorMessage = JSON.stringify(errorBody.detail)
              }
            } else {
              // Se detail for uma string ou outro valor primitivo
              errorMessage = String(errorBody.detail)
            }
          } else if (errorBody.message) {
            errorMessage = String(errorBody.message)
          }
        } else if (apiError.message) {
          errorMessage = String(apiError.message)
        }
      } catch (formatError) {
        console.error("Error formatting error message:", formatError)
        // Manter a mensagem padrão em caso de erro ao extrair detalhes
      }
      
      showToast(
        "Error saving resume",
        errorMessage,
        "error",
      )
    },
  })

  // Parse and set form data when API response is received
  useEffect(() => {
    if (resumeData) {
      try {
        // Store current scroll position before form data is set
        const currentScrollPosition = window.scrollY
        setScrollPosition(currentScrollPosition)

        const formData = transformApiResponseToFormData(resumeData)

        // Reset form with fetched data
        reset(formData, {
          keepDirty: false,
          keepErrors: false,
          keepDefaultValues: false,
          keepValues: false,
          keepIsSubmitted: false,
          keepTouched: false,
          keepIsValid: false,
          keepSubmitCount: false,
        })

        // Forçar a atualização de cada campo current para garantir que a UI reflita os valores
        formData.education.forEach((edu, index) => {
          setValue(`education.${index}.current`, edu.current, { shouldDirty: false });
        });
        
        formData.work_experience.forEach((exp, index) => {
          setValue(`work_experience.${index}.current`, exp.current, { shouldDirty: false });
        });

        // Restore scroll position
        setTimeout(() => {
          window.scrollTo({
            top: currentScrollPosition,
            behavior: "auto",
          })
        }, 100)
      } catch (error) {
        console.error("Error processing resume data:", error)
        showToast(
          "Error processing data",
          "There was an error processing your resume data.",
          "error",
        )
      }
    }
  }, [resumeData, reset, showToast, setValue])

  // Form submission handler with better error handling
  const onSubmit = (data: ResumeForm) => {
    try {
      // Validação adicional para garantir que não há inconsistências
      let isValid = true;
      
      // Verificar se há experiências de trabalho com current false mas sem end_date
      data.work_experience.forEach((exp, index) => {
        if (exp.current === false && (!exp.end_date || exp.end_date.trim() === "")) {
          setValue(`work_experience.${index}.end_date`, "", { 
            shouldValidate: true,
            shouldDirty: true,
            shouldTouch: true
          });
          isValid = false;
        }
      });
      
      // Verificar se há educações com current false mas sem end_date
      data.education.forEach((edu, index) => {
        if (edu.current === false && (!edu.end_date || edu.end_date.trim() === "")) {
          setValue(`education.${index}.end_date`, "", { 
            shouldValidate: true,
            shouldDirty: true,
            shouldTouch: true
          });
          isValid = false;
        }
      });
      
      if (!isValid) {
        showToast(
          "Validation Error",
          "Please fill all required fields. End dates are required for non-current items.",
          "error"
        );
        return;
      }
      
      // Agora temos certeza que os dados estão válidos
      updateResumeMutation.mutate(data);
    } catch (error) {
      console.error("Form submission error:", error);
      showToast(
        "Submission error",
        "There was an error submitting the form.",
        "error",
      );
    }
  };

  const isLoading = isLoadingSubscriptions || isLoadingResume

  // Ensure all form fields correctly mark the form as dirty
  const updateField = (field: any, value: any) => {
    setValue(field, value, { 
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true 
    });
  }

  // Return with the form key to force re-renders when needed
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Resume
      </Heading>
      {!hasActiveSubscription ? (
        <Alert status="warning" mb={4}>
          <AlertIcon />
          <AlertDescription>
            You need an active subscription to create or edit your resume.
          </AlertDescription>
        </Alert>
      ) : null}

      {isLoading ? (
        <LoadingSkeleton />
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} style={{ marginBottom: '3rem' }}>
          <Stack spacing={8}>
            <Card variant="outline" p={4}>
              <PersonalInformationSection register={register} errors={errors} />
            </Card>

            <Card variant="outline" p={4}>
              <SelfIdentificationSection
                register={register}
              />
            </Card>

            <Card variant="outline" p={4}>
              <EducationSection
                register={register}
                errors={errors}
                control={control}
                watch={watch}
                setValue={setValue}
              />
            </Card>

            <Card variant="outline" p={4}>
              <WorkExperienceSection
                register={register}
                errors={errors}
                control={control}
                watch={watch}
                setValue={setValue}
              />
            </Card>

            <Card variant="outline" p={4}>
              <ProjectsSection
                register={register}
                errors={errors}
                control={control}
              />
            </Card>

            <Card variant="outline" p={4}>
              <SkillsSection
                setValue={updateField}
                getValues={getValues}
                watch={watch}
              />
            </Card>

            <Card variant="outline" p={4}>
              <LanguagesSection
                register={register}
                errors={errors}
                control={control}
              />
            </Card>

            <Card variant="outline" p={4}>
              <AvailabilitySection register={register} />
            </Card>

            <Card variant="outline" p={4}>
              <SalaryExpectationSection register={register} />
            </Card>

            <Card variant="outline" p={4}>
              <WorkPreferenceSection register={register} />
            </Card>

            <Card variant="outline" p={4}>
              <InterestsSection
                setValue={updateField}
                getValues={getValues}
                watch={watch}
              />
            </Card>

            <Card variant="outline" p={4}>
              <AchievementsSection
                register={register}
                errors={errors}
                control={control}
              />
            </Card>

            <Card variant="outline" p={4}>
              <CertificationsSection
                register={register}
                errors={errors}
                control={control}
              />
            </Card>

            <Card variant="outline" p={4}>
              <LegalAuthorizationSection
                register={register}
              />
            </Card>
          </Stack>
          <ButtonGroup spacing={4} mt={4}>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting || updateResumeMutation.isPending}
              isDisabled={!hasActiveSubscription}
            >
              {isCreatingNew ? "Create Resume" : "Save Resume"}
            </Button>
          </ButtonGroup>
        </form>
      )}
    </Container>
  )
}

// Forwardable version for use in Onboarding
interface ResumeSettingsProps {
  onComplete?: () => void
  isOnboarding?: boolean
  hideSubmitButton?: boolean
}

const ResumeSettings = forwardRef<{ submit: () => Promise<boolean> }, ResumeSettingsProps>(
  ({ onComplete, isOnboarding = false, hideSubmitButton = false }, ref) => {
    const showToast = useCustomToast()
    const [_scrollPosition] = useState<number>(0)
    const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false)
    const [hasShownNotFoundMessage, setHasShownNotFoundMessage] = useState<boolean>(false)

    // Form setup
    const {
      register,
      handleSubmit,
      control,
      setValue,
      getValues,
      reset,
      formState: { errors, isSubmitting },
      watch,
    } = useForm<ResumeForm>({
      defaultValues,
    })

    // Fetch user subscriptions
    const { data: subscriptions, isLoading: isLoadingSubscriptions } = useQuery({
      queryKey: ["subscriptions"],
      queryFn: async () => {
        return await SubscriptionsService.getUserSubscriptions({
          onlyActive: true,
        })
      }
    })

    // Check if user has an active subscription
    const hasActiveSubscription = useMemo(() => {
      const hasSubscription = subscriptions && subscriptions.length > 0;
      return hasSubscription;
    }, [subscriptions]);

    // Fetch resume data with better error handling
    const { data: resumeData, isLoading: isLoadingResume, error: resumeError } = useQuery({
      queryKey: ["plainTextResume"],
      queryFn: async () => {
        try {
          const result = await ConfigsService.getPlainTextResume();
          return result;
        } catch (error) {
          const apiError = error as ApiError;
          if (apiError.status === 404) {
            setIsCreatingNew(true);
            // Não mostrar toast aqui, deixar para o useEffect
          }
          throw error;
        }
      },
      // Don't condition the query on subscription status to avoid race conditions
      enabled: true,
      retry: false, // Não tentar novamente automaticamente
      refetchOnWindowFocus: false,
      staleTime: 60000, // 1 minuto
    });

    // Reset form data when resume data is loaded or cleared
    useEffect(() => {
      if (resumeData) {
        // If we successfully load data, we're editing an existing resume
        setIsCreatingNew(false);
        
        // Transform API data to form format
        const formData = transformApiResponseToFormData(resumeData);
        reset(formData);
      }
    }, [resumeData, reset]);

    // Handle resume fetch error - only show actual errors, not 404
    useEffect(() => {
      // If loading or data exists, do nothing
      if (isLoadingResume || resumeData) return;
      
      // If we have an active subscription but no resume data
      if (hasActiveSubscription && !resumeData) {
        const apiError = resumeError as ApiError;
        
        // Show message for 404 only if we haven't shown it already
        if (apiError && apiError.status === 404) {
          if (!hasShownNotFoundMessage) {
            setIsCreatingNew(true);
            setHasShownNotFoundMessage(true);
            
            // Only show toast if not in onboarding mode
            if (!isOnboarding) {
              showToast(
                "Resume not found",
                "Please fill out the form to create your resume.",
                "success"
              )
            }
          }
        } else if (apiError) {
          // Real errors
          console.error("Resume fetch error:", apiError);
          showToast(
            "Error fetching resume",
            apiError.message || "An error occurred while fetching your resume.",
            "error"
          )
        }
      }
    }, [hasActiveSubscription, isLoadingResume, resumeData, resumeError, showToast, isCreatingNew, hasShownNotFoundMessage, isOnboarding]);

    // Update resume mutation with better error handling
    const updateResumeMutation = useMutation({
      mutationFn: async (data: ResumeForm) => {
        if (!hasActiveSubscription) {
          throw new Error("No active subscription available")
        }
        
        try {
          const apiData = transformFormToApiData(data)
          const result = await ConfigsService.updatePlainTextResume({
            requestBody: apiData,
          })
          
          // If we were creating a new resume, we're now editing
          if (isCreatingNew) {
            setIsCreatingNew(false)
          }
          
          return result
        } catch (error) {
          console.error("Error saving resume:", error)
          throw error
        }
      },
      onSuccess: () => {
        // Show toast only if not in onboarding mode
        if (!isOnboarding) {
          showToast(
            isCreatingNew ? "Resume created" : "Resume updated",
            isCreatingNew 
              ? "Your resume has been successfully created." 
              : "Your resume has been successfully updated.",
            "success",
          )
        }
        
        // Call onComplete callback if provided
        if (onComplete) {
          onComplete()
        }
      },
      onError: (error: Error) => {
        console.error("Resume mutation error:", error)
        
        // Melhor tratamento para garantir que o erro seja sempre uma string
        let errorMessage = "An unexpected error occurred."
        
        // Tenta extrair detalhes do erro em diferentes formatos
        try {
          const apiError = error as ApiError
          
          if (apiError.body) {
            const errorBody = apiError.body as any
            
            if (errorBody.detail) {
              // Se detail for um objeto (validation_error), extrair apenas as mensagens
              if (typeof errorBody.detail === 'object') {
                if (Array.isArray(errorBody.detail)) {
                  // Se for um array de erros
                  errorMessage = errorBody.detail
                    .map((err: any) => {
                      if (typeof err === 'object' && err.msg) {
                        return String(err.msg)
                      }
                      return String(err)
                    })
                    .join(", ")
                } else if (errorBody.detail.msg) {
                  // Se for um único objeto de erro com a propriedade msg
                  errorMessage = String(errorBody.detail.msg)
                } else {
                  // Para outros objetos, tente obter uma representação de string
                  errorMessage = JSON.stringify(errorBody.detail)
                }
              } else {
                // Se detail for uma string ou outro valor primitivo
                errorMessage = String(errorBody.detail)
              }
            } else if (errorBody.message) {
              errorMessage = String(errorBody.message)
            }
          } else if (apiError.message) {
            errorMessage = String(apiError.message)
          }
        } catch (formatError) {
          console.error("Error formatting error message:", formatError)
          // Manter a mensagem padrão em caso de erro ao extrair detalhes
        }
        
        showToast(
          "Error saving resume",
          errorMessage,
          "error",
        )
      },
    })

    // Expose the submit method to parent components through ref
    useImperativeHandle(ref, () => ({
      submit: async () => {
        try {
          const formData = getValues();
          
          // Validar campos obrigatórios manualmente
          const formErrors = Object.keys(errors);
          const hasErrors = formErrors.length > 0;
          
          if (hasErrors) {
            // Identifique os campos com erro para mensagem mais específica
            const errorFields = formErrors.join(", ");
            console.error(`Form validation failed for fields: ${errorFields}`);
            
            // Throw a structured error to be caught by parent component
            throw new Error(`Resume form validation failed for fields: ${errorFields}`);
          }
          
          // Submit form if valid
          await updateResumeMutation.mutateAsync(formData);
          return true;
        } catch (error) {
          // Propagate the error to be handled by the parent component
          console.error("Error in ResumeSettings submit method:", error);
          
          // Certifique-se de que o erro seja tratável pelo componente pai
          if (error instanceof Error) {
            throw error;
          } else {
            throw new Error("Error submitting resume");
          }
        }
      }
    }))

    // Helper to update fields that don't work well with direct register
    const updateField = (field: string, value: any) => {
      setValue(field as any, value, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      })
    }

    // Submit handler
    const onSubmit = async (data: ResumeForm) => {
      try {
        await updateResumeMutation.mutateAsync(data)
      } catch (error) {
        // Error handling is done in mutation onError
        console.log("Submit handler caught error, already handled in mutation")
      }
    }

    // Compute loading state
    const isLoading = isLoadingSubscriptions || isLoadingResume

    // Return with the form key to force re-renders when needed
    return (
      <Container maxW="full">
        {!isOnboarding && (
          <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
            Resume
          </Heading>
        )}
        {!hasActiveSubscription && !isOnboarding ? (
          <Alert status="warning" mb={4}>
            <AlertIcon />
            <AlertDescription>
              You need an active subscription to create or edit your resume.
            </AlertDescription>
          </Alert>
        ) : null}

        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} style={{ marginBottom: '3rem' }}>
            <Stack spacing={8}>
              <Card variant="outline" p={4}>
                <PersonalInformationSection register={register} errors={errors} />
              </Card>

              <Card variant="outline" p={4}>
                <SelfIdentificationSection
                  register={register}
                />
              </Card>

              <Card variant="outline" p={4}>
                <EducationSection
                  register={register}
                  errors={errors}
                  control={control}
                  watch={watch}
                  setValue={setValue}
                />
              </Card>

              <Card variant="outline" p={4}>
                <WorkExperienceSection
                  register={register}
                  errors={errors}
                  control={control}
                  watch={watch}
                  setValue={setValue}
                />
              </Card>

              <Card variant="outline" p={4}>
                <ProjectsSection
                  register={register}
                  errors={errors}
                  control={control}
                />
              </Card>

              <Card variant="outline" p={4}>
                <SkillsSection
                  setValue={updateField}
                  getValues={getValues}
                  watch={watch}
                />
              </Card>

              <Card variant="outline" p={4}>
                <LanguagesSection
                  register={register}
                  errors={errors}
                  control={control}
                />
              </Card>

              <Card variant="outline" p={4}>
                <AvailabilitySection register={register} />
              </Card>

              <Card variant="outline" p={4}>
                <SalaryExpectationSection register={register} />
              </Card>

              <Card variant="outline" p={4}>
                <WorkPreferenceSection register={register} />
              </Card>

              <Card variant="outline" p={4}>
                <InterestsSection
                  setValue={updateField}
                  getValues={getValues}
                  watch={watch}
                />
              </Card>

              <Card variant="outline" p={4}>
                <AchievementsSection
                  register={register}
                  errors={errors}
                  control={control}
                />
              </Card>

              <Card variant="outline" p={4}>
                <CertificationsSection
                  register={register}
                  errors={errors}
                  control={control}
                />
              </Card>

              <Card variant="outline" p={4}>
                <LegalAuthorizationSection
                  register={register}
                />
              </Card>
            </Stack>
            
            {!hideSubmitButton && (
              <ButtonGroup spacing={4} mt={4}>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting || updateResumeMutation.isPending}
                  isDisabled={!hasActiveSubscription}
                >
                  {isCreatingNew ? "Create Resume" : "Save Resume"}
                </Button>
              </ButtonGroup>
            )}
          </form>
        )}
      </Container>
    )
  }
)

// Display name for debugging
ResumeSettings.displayName = "ResumeSettings"

export default ResumePage
export { ResumeSettings }
