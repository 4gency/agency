import React, { useEffect, useState } from "react"
import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Select,
  Switch,
  Text,
} from "@chakra-ui/react"
import { useMutation } from "@tanstack/react-query"
// import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { ApiError, ConfigsService, type ConfigPublic } from "../../client" 

import useCustomToast from "../../hooks/useCustomToast"
import useSubscriptions from "../../hooks/userSubscriptions"

type JobPreferences = ConfigPublic

const defaultPreferences: ConfigPublic = {
  remote: true,
  experience_level: {
    intership: true,
    entry: true,
    associate: true,
    mid_senior_level: true,
    director: true,
    executive: true,
  },
  job_types: {
    full_time: true,
    contract: true,
    part_time: true,
    temporary: true,
    internship: true,
    other: true,
    volunteer: true,
  },
  date: {
    all_time: true,
    month: false,
    week: false,
    hours: false,
  },
  positions: ["Developer"],
  locations: ["USA"],
  apply_once_at_company: true,
  distance: 0,
  company_blacklist: [],
  title_blacklist: [],
  job_applicants_threshold: {
    min_applicants: 0,
    max_applicants: 10000,
  },
}

const JobPreferencesPage: React.FC = () => {
  const { data: subscriptions, isLoading } = useSubscriptions()
  const [selectedSubId, setSelectedSubId] = useState<string>("")
  // const navigate = useNavigate()
  const showToast = useCustomToast()

  const {
    register,
    handleSubmit,
    reset, // adicionando o reset para receber do GET
    formState: { isSubmitting },
  } = useForm<JobPreferences>({
    defaultValues: defaultPreferences,
  })

  // GET das preferências no load do subscriptionId
  useEffect(() => {
    if (selectedSubId) {
      ConfigsService.getConfig({ subscriptionId: selectedSubId })
        .then((config) => {
          // Preenche o formulário com dados do backend
          reset(config)
        })
        .catch((err: ApiError) => {
          const detail = (err.body as any)?.detail || err.message
          showToast("Erro ao buscar preferências", String(detail), "error")
        })
    }
  }, [selectedSubId, reset, showToast])

  // PUT das preferências
  const mutation = useMutation({
    mutationFn: (data: JobPreferences) =>
      ConfigsService.updateConfig({
        subscriptionId: selectedSubId,
        requestBody: data,
      }),
    onSuccess: () => {
      showToast("Sucesso", "Preferências atualizadas!", "success")
    },
    onError: (err: ApiError) => {
      const detail = (err.body as any)?.detail || err.message
      showToast("Erro ao atualizar", String(detail), "error")
    },
  })

  const onSubmit = (data: JobPreferences) => {
    if (!selectedSubId) {
      showToast("Atenção", "Selecione uma assinatura antes de salvar.", "error")
      return
    }
    mutation.mutate(data)
  }

  if (isLoading) {
    return <Text>Carregando assinaturas...</Text>
  }

  return (
    <Container maxW="container.md" py={8}>
      <Heading mb={4}>Configurar Preferências de Vagas</Heading>

      <FormControl mb={4} width="300px">
        <FormLabel>Escolha sua assinatura</FormLabel>
        <Select
          value={selectedSubId}
          onChange={(e) => setSelectedSubId(e.target.value)}
        >
          {subscriptions?.map((sub) => (
            <option key={sub.id} value={sub.id}>
              {sub.id}
            </option>
          ))}
        </Select>
      </FormControl>

      <Box as="form" onSubmit={handleSubmit(onSubmit)}>
        <FormControl display="flex" alignItems="center" mb={4}>
          <FormLabel mb={0} mr={2}>
            Remote
          </FormLabel>
          <Switch {...register("remote")} />
        </FormControl>

        <Heading size="sm" mt={6} mb={2}>
          Nível de Experiência
        </Heading>
        <Flex gap={4} flexWrap="wrap">
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Intership</FormLabel>
            <Switch {...register("experience_level.intership")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Entry</FormLabel>
            <Switch {...register("experience_level.entry")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Associate</FormLabel>
            <Switch {...register("experience_level.associate")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Mid-Senior</FormLabel>
            <Switch {...register("experience_level.mid_senior_level")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Director</FormLabel>
            <Switch {...register("experience_level.director")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Executive</FormLabel>
            <Switch {...register("experience_level.executive")} />
          </FormControl>
        </Flex>

        <Heading size="sm" mt={6} mb={2}>
          Tipos de Vaga
        </Heading>
        <Flex gap={4} flexWrap="wrap">
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Full-time</FormLabel>
            <Switch {...register("job_types.full_time")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Contract</FormLabel>
            <Switch {...register("job_types.contract")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Part-time</FormLabel>
            <Switch {...register("job_types.part_time")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Temporary</FormLabel>
            <Switch {...register("job_types.temporary")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Internship</FormLabel>
            <Switch {...register("job_types.internship")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Other</FormLabel>
            <Switch {...register("job_types.other")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Volunteer</FormLabel>
            <Switch {...register("job_types.volunteer")} />
          </FormControl>
        </Flex>

        <Heading size="sm" mt={6} mb={2}>
          Data de Postagem
        </Heading>
        <Flex gap={4} flexWrap="wrap">
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>All time</FormLabel>
            <Switch {...register("date.all_time")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Month</FormLabel>
            <Switch {...register("date.month")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Week</FormLabel>
            <Switch {...register("date.week")} />
          </FormControl>
          <FormControl display="flex" alignItems="center">
            <FormLabel mb={0}>Hours</FormLabel>
            <Switch {...register("date.hours")} />
          </FormControl>
        </Flex>

        <FormControl display="flex" alignItems="center" mt={6} mb={4}>
          <FormLabel mb={0} mr={2}>
            Apply once at company
          </FormLabel>
          <Switch {...register("apply_once_at_company")} />
        </FormControl>

        <FormControl mb={4}>
          <FormLabel>Distance</FormLabel>
          <Input type="number" {...register("distance")} />
        </FormControl>

        <FormControl mb={4}>
          <FormLabel>Positions (separe por vírgula)</FormLabel>
          <Input
            {...register("positions")}
            placeholder="Developer, Frontend..."
          />
        </FormControl>

        <FormControl mb={4}>
          <FormLabel>Locations (separe por vírgula)</FormLabel>
          <Input
            {...register("locations")}
            placeholder="USA, Canada..."
          />
        </FormControl>

        <FormControl mb={4}>
          <FormLabel>Company Blacklist (separe por vírgula)</FormLabel>
          <Input
            {...register("company_blacklist")}
            placeholder="Empresa X..."
          />
        </FormControl>

        <FormControl mb={4}>
          <FormLabel>Title Blacklist (separe por vírgula)</FormLabel>
          <Input
            {...register("title_blacklist")}
            placeholder="Senior, Jr..."
          />
        </FormControl>

        <Heading size="sm" mt={6} mb={2}>
          Faixa de Aplicantes
        </Heading>
        <Flex gap={4} flexWrap="wrap">
          <FormControl>
            <FormLabel>Mínimo</FormLabel>
            <Input
              type="number"
              {...register("job_applicants_threshold.min_applicants")}
            />
          </FormControl>
          <FormControl>
            <FormLabel>Máximo</FormLabel>
            <Input
              type="number"
              {...register("job_applicants_threshold.max_applicants")}
            />
          </FormControl>
        </Flex>

        <Button
          mt={6}
          colorScheme="blue"
          type="submit"
          isLoading={isSubmitting || mutation.status === 'pending'}
        >
          Salvar
        </Button>
      </Box>
    </Container>
  )
}

export default JobPreferencesPage
