import { InfoIcon } from "@chakra-ui/icons"
import { 
  Box, 
  Divider, 
  Flex, 
  HStack, 
  Heading, 
  Tooltip,
  IconButton,
  useMediaQuery,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow
} from "@chakra-ui/react"
import type React from "react"
import { useState } from "react"

interface SectionContainerProps {
  title: string
  children: React.ReactNode
  actionButton?: React.ReactNode
  showInfoIcon?: boolean
  infoTooltip?: string
}

/**
 * Componente reutilizável para padronizar o layout de cada seção do formulário de Resume
 */
const SectionContainer: React.FC<SectionContainerProps> = ({
  title,
  children,
  actionButton,
  showInfoIcon = true, // Por padrão, mostrar o ícone para manter compatibilidade
  infoTooltip = "", // Texto do tooltip para o ícone de informação
}) => {
  // Detecta se é um dispositivo móvel (tela pequena)
  const [isMobile] = useMediaQuery("(max-width: 768px)")
  // Estado para controlar se o popover está aberto (usado apenas em mobile)
  const [isPopoverOpen, setIsPopoverOpen] = useState(false)

  // Toggle para o popover em dispositivos móveis
  const handleInfoClick = () => {
    if (isMobile) {
      setIsPopoverOpen(!isPopoverOpen)
    }
  }

  return (
    <Box mb={8}>
      <Flex justify="space-between" align="center" mb={4}>
        <HStack spacing={2}>
          <Heading size="md" color="#00766C">
            {title}
          </Heading>
          {showInfoIcon && infoTooltip && (
            isMobile ? (
              // Em dispositivos móveis, usar Popover que responde ao toque
              <Popover
                isOpen={isPopoverOpen}
                onClose={() => setIsPopoverOpen(false)}
                placement="top"
                closeOnBlur={true}
              >
                <PopoverTrigger>
                  <IconButton
                    icon={<InfoIcon />}
                    aria-label={`Information about ${title}`}
                    size="xs"
                    variant="ghost"
                    colorScheme="gray"
                    onClick={handleInfoClick}
                  />
                </PopoverTrigger>
                <PopoverContent bg="gray.700" color="white" maxW="300px">
                  <PopoverArrow bg="gray.700" />
                  <PopoverBody fontSize="sm" p={3}>
                    {infoTooltip}
                  </PopoverBody>
                </PopoverContent>
              </Popover>
            ) : (
              // Em desktop, continuar usando Tooltip ativado por hover
              <Tooltip 
                label={infoTooltip} 
                fontSize="sm" 
                placement="top" 
                hasArrow 
                bg="gray.700" 
                color="white"
              >
                <InfoIcon color="gray.400" cursor="help" />
              </Tooltip>
            )
          )}
        </HStack>
        {actionButton}
      </Flex>
      <Divider borderColor="gray.300" mb={4} />
      {children}
    </Box>
  )
}

export default SectionContainer
