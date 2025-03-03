import {
  Box,
  Container,
  Flex,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Badge,
  useColorModeValue,
  Spinner,
  Link,
  Button,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type SubscriptionPublic,
  UsersService,
} from "../../client"

const Subscriptions = () => {
  const color = useColorModeValue("inherit", "ui.light")
  const navigate = useNavigate()

  // Query to get user subscriptions
  const { data: subscriptions, isLoading, isError } = useSubscriptions()

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  // Função simplificada para navegar para a página de detalhes da assinatura
  const handleGoToDetails = (subscriptionId: string) => {
    console.log("Navegando para detalhes da assinatura:", subscriptionId);
    window.location.href = `/settings/subscription/${subscriptionId}`;
  }

  if (isLoading) {
    return (
      <Flex justify="center" align="center" minH="200px">
        <Spinner />
      </Flex>
    )
  }

  if (isError) {
    return (
      <Container maxW="full">
        <Heading size="sm" py={4}>
          Subscriptions
        </Heading>
        <Text color="red.500">Unable to load subscriptions. Please try again later.</Text>
      </Container>
    )
  }

  return (
    <Box>
      <Heading size="md" my={4}>
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
                      {subscription.subscription_plan?.description || "No description available"}
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
        <Text>You don't have any subscriptions yet.</Text>
      )}
    </Box>
  )
}

// Custom hook to fetch user subscriptions
function useSubscriptions() {
  return useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => UsersService.getUserSubscriptions(),
  })
}

export default Subscriptions 