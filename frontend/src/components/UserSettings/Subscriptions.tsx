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
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"

import {
  type SubscriptionPublic,
  UsersService,
} from "../../client"

const Subscriptions = () => {
  const color = useColorModeValue("inherit", "ui.light")

  // Query to get user subscriptions
  const { data: subscriptions, isLoading, isError } = useSubscriptions()

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
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
        <Text color="red.500">Error loading subscriptions</Text>
      </Container>
    )
  }

  return (
    <Container maxW="full">
      <Heading size="sm" py={4}>
        Your Subscriptions
      </Heading>
      {subscriptions && subscriptions.length > 0 ? (
        <Box overflowX="auto">
          <Table variant="simple" size="md">
            <Thead>
              <Tr>
                <Th color={color}>Plan</Th>
                <Th color={color}>Start Date</Th>
                <Th color={color}>End Date</Th>
                <Th color={color}>Status</Th>
                <Th color={color}>Usage</Th>
              </Tr>
            </Thead>
            <Tbody>
              {subscriptions.map((subscription: SubscriptionPublic) => (
                <Tr key={subscription.id}>
                  <Td>{subscription.subscription_plan_id}</Td>
                  <Td>{formatDate(subscription.start_date)}</Td>
                  <Td>{formatDate(subscription.end_date)}</Td>
                  <Td>
                    <Badge
                      colorScheme={subscription.is_active ? "green" : "red"}
                    >
                      {subscription.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </Td>
                  <Td>
                    {subscription.metric_type}: {subscription.metric_status}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      ) : (
        <Text>You don't have any subscriptions yet.</Text>
      )}
    </Container>
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