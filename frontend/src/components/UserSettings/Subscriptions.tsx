import {
  Box,
  Container,
  Flex,
  Heading,
  Spinner,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  useColorModeValue,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { is404Error } from "../../utils/errorUtils"

import { UsersService } from "../../client"

const Subscriptions = () => {
  // Query to get user subscriptions
  const { data: subscriptions, isLoading, isError, error } = useSubscriptions()

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  // Função para navegar para a página de detalhes da assinatura
  const handleGoToDetails = (subscriptionId: string) => {
    console.log("Navegando para detalhes da assinatura:", subscriptionId)

    // Devido aos problemas de navegação, continuamos usando window.location.href
    // O TanStack Router requer parâmetros tipados específicos que podem causar problemas
    window.location.href = `/settings/subscription/${subscriptionId}`
  }

  if (isLoading) {
    return (
      <Flex justify="center" align="center" minH="200px">
        <Spinner />
      </Flex>
    )
  }

  // Verificar se é um erro 404 usando o utilitário da aplicação
  const isNotFoundError = isError && is404Error(error)

  if (isError) {
    // Se for o erro 404, mostra a mensagem amigável
    if (isNotFoundError) {
      return (
        <Container maxW="full">
          <Heading size="sm" py={4}>
            My Subscriptions
          </Heading>
          <Text>No subscriptions found.</Text>
        </Container>
      )
    }

    // Para outros erros, mostra a mensagem de erro genérica
    return (
      <Container maxW="full">
        <Heading size="sm" py={4}>
          My Subscriptions
        </Heading>
        <Text color="red.500">
          Unable to load subscriptions. Please try again later.
        </Text>
      </Container>
    )
  }

  return (
    <Container maxW="full">
      <Heading size="sm" py={4}>
        My Subscriptions
      </Heading>

      {subscriptions && subscriptions.length > 0 ? (
        <Box overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Plan</Th>
                <Th>End Date</Th>
                <Th>Price</Th>
              </Tr>
            </Thead>
            <Tbody>
              {subscriptions.map((subscription) => (
                <Tr
                  key={subscription.id}
                  onClick={() => handleGoToDetails(subscription.id)}
                  cursor="pointer"
                  _hover={{ bg: useColorModeValue("gray.100", "gray.700") }}
                  transition="background-color 0.2s"
                >
                  <Td>
                    <Text fontWeight="medium">
                      {subscription.subscription_plan?.name || "Unknown Plan"}
                    </Text>
                    <Text fontSize="sm" color="gray.500">
                      {subscription.subscription_plan?.description ||
                        "No description available"}
                    </Text>
                  </Td>
                  <Td>{formatDate(subscription.end_date)}</Td>
                  <Td>
                    {subscription.subscription_plan?.price
                      ? `${subscription.subscription_plan.price} ${
                          subscription.subscription_plan.currency || "USD"
                        }`
                      : "N/A"}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      ) : (
        <Text>No subscriptions found.</Text>
      )}
    </Container>
  )
}

// Custom hook to fetch user subscriptions
function useSubscriptions() {
  return useQuery({
    queryKey: ["subscriptions"],
    queryFn: async () => {
      try {
        return await UsersService.getUserSubscriptions()
      } catch (error) {
        // Se for um erro 404, tratamos como um resultado válido (array vazio)
        // em vez de lançar um erro que será logado no console
        if (is404Error(error)) {
          return []
        }
        // Outros erros são propagados normalmente
        throw error
      }
    },
  })
}

export default Subscriptions
