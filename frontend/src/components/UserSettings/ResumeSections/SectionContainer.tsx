import { InfoIcon } from "@chakra-ui/icons"
import { Box, Divider, Flex, HStack, Heading } from "@chakra-ui/react"
import type React from "react"

interface SectionContainerProps {
  title: string
  children: React.ReactNode
  actionButton?: React.ReactNode
}

/**
 * Componente reutilizável para padronizar o layout de cada seção do formulário de Resume
 */
const SectionContainer: React.FC<SectionContainerProps> = ({
  title,
  children,
  actionButton,
}) => {
  return (
    <Box mb={8}>
      <Flex justify="space-between" align="center" mb={4}>
        <HStack spacing={2}>
          <Heading size="md" color="#00766C">
            {title}
          </Heading>
          <InfoIcon color="gray.400" />
        </HStack>
        {actionButton}
      </Flex>
      <Divider borderColor="gray.300" mb={4} />
      {children}
    </Box>
  )
}

export default SectionContainer
