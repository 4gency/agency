import React, { useState } from "react"
import {
  Box,
  Button,
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
  HStack,
  Tooltip,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"

import {
  type PaymentPublic,
  UsersService,
} from "../../client"

const Payments = () => {
  const color = useColorModeValue("inherit", "ui.light")
  
  // Estados para paginação
  const PAGE_SIZE = 10
  const [page, setPage] = useState(0)

  // Query para buscar pagamentos
  const { data: paymentsData, isLoading, isError } = usePayments(page, PAGE_SIZE)
  const payments = paymentsData?.data || []
  const totalCount = paymentsData?.count || 0

  // Formatar moeda
  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(amount)
  }

  // Formatar data
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  // Navegar entre páginas
  const handleNextPage = () => {
    if ((page + 1) * PAGE_SIZE < totalCount) {
      setPage(page + 1)
    }
  }

  const handlePrevPage = () => {
    if (page > 0) {
      setPage(page - 1)
    }
  }

  // Status do pagamento
  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, string> = {
      completed: "green",
      pending: "yellow",
      failed: "red",
      refunded: "purple",
    }
    
    return (
      <Badge colorScheme={statusMap[status.toLowerCase()] || "gray"}>
        {status}
      </Badge>
    )
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
          Payment History
        </Heading>
        <Text color="red.500">Error loading payment data</Text>
      </Container>
    )
  }

  return (
    <Container maxW="full">
      <Heading size="sm" py={4}>
        Payment History
      </Heading>
      {payments.length > 0 ? (
        <>
          <Box overflowX="auto">
            <Table variant="simple" size="md">
              <Thead>
                <Tr>
                  <Th color={color}>Transaction ID</Th>
                  <Th color={color}>Date</Th>
                  <Th color={color}>Amount</Th>
                  <Th color={color}>Payment Method</Th>
                  <Th color={color}>Status</Th>
                </Tr>
              </Thead>
              <Tbody>
                {payments.map((payment: PaymentPublic) => (
                  <Tr key={payment.id}>
                    <Td>
                      <Tooltip label={payment.transaction_id}>
                        <Text>{payment.transaction_id}</Text>
                      </Tooltip>
                    </Td>
                    <Td>{formatDate(payment.payment_date)}</Td>
                    <Td>{formatCurrency(payment.amount, payment.currency)}</Td>
                    <Td>{payment.payment_gateway}</Td>
                    <Td>{getStatusBadge(payment.payment_status)}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
          
          {/* Paginação */}
          <Flex justify="space-between" mt={4}>
            <Text>
              Showing {page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, totalCount)} of {totalCount}
            </Text>
            <HStack>
              <Button 
                onClick={handlePrevPage} 
                isDisabled={page === 0}
                size="sm"
              >
                Previous
              </Button>
              <Button 
                onClick={handleNextPage} 
                isDisabled={(page + 1) * PAGE_SIZE >= totalCount}
                size="sm"
              >
                Next
              </Button>
            </HStack>
          </Flex>
        </>
      ) : (
        <Text>You don't have any payment records yet.</Text>
      )}
    </Container>
  )
}

// Custom hook para buscar pagamentos
function usePayments(page: number, pageSize: number) {
  return useQuery({
    queryKey: ["payments", page, pageSize],
    queryFn: () => UsersService.readPaymentsByCurrentUser({
      skip: page * pageSize,
      limit: pageSize
    }),
  })
}

export default Payments 