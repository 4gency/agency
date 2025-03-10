import { 
  Flex,
  Button,
  FormControl,
  FormLabel,
  useColorModeValue
} from "@chakra-ui/react"
import type React from "react"

export type Option = {
  label: string
  value: string
}

interface MultiSelectToggleFieldProps {
  label: string
  options: Option[]
  selected: string[]
  onChange: (selected: string[]) => void
}

/**
 * Componente reutilizável para seleção múltipla de opções com botões de toggle
 */
const MultiSelectToggleField: React.FC<MultiSelectToggleFieldProps> = ({
  label,
  options,
  selected,
  onChange,
}) => {
  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  return (
    <FormControl mb={4}>
      <FormLabel>{label}</FormLabel>
      <Flex wrap="wrap" gap={2} my={2}>
        {options.map((option) => {
          const isSelected = selected.includes(option.value)
          return (
            <Button
              key={option.value}
              bg={
                isSelected ? "#00766C" : useColorModeValue("white", "gray.800")
              }
              color={
                isSelected ? "white" : useColorModeValue("black", "white")
              }
              border="1px solid #00766C"
              _hover={{
                bg: isSelected
                  ? "#00655D"
                  : useColorModeValue("gray.100", "gray.700"),
              }}
              onClick={() => handleToggle(option.value)}
              size="sm"
            >
              {option.label}
            </Button>
          )
        })}
      </Flex>
    </FormControl>
  )
}

export default MultiSelectToggleField 