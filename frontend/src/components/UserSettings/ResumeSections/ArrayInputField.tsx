import {
  Flex,
  FormControl,
  FormLabel,
  HStack,
  IconButton,
  Input,
  Tag,
  TagCloseButton,
  TagLabel,
  useColorModeValue,
} from "@chakra-ui/react"
import { AddIcon } from "@chakra-ui/icons"
import { useState } from "react"

interface ArrayInputFieldProps {
  label: string
  items: string[]
  onChange: (items: string[]) => void
  placeholder?: string
  onBlur?: () => void
}

/**
 * Componente reutilizável para campos que permitem adicionar múltiplos valores
 */
const ArrayInputField: React.FC<ArrayInputFieldProps> = ({
  label,
  items,
  onChange,
  placeholder = "Add new item",
  onBlur
}) => {
  const [inputValue, setInputValue] = useState("")
  const buttonBgColor = "#00766C" // Mantendo a cor padrão usada no JobPreferences
  const buttonHoverColor = "#00655D"

  const handleAdd = () => {
    const trimmed = inputValue.trim()
    if (!trimmed) return
    if (!items.includes(trimmed)) {
      onChange([...items, trimmed])
    }
    setInputValue("")
  }

  const handleRemove = (item: string) => {
    const filtered = items.filter((i) => i !== item)
    onChange(filtered)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <FormControl mb={4}>
      <FormLabel>{label}</FormLabel>
      <Flex gap={2} mb={2}>
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          onBlur={onBlur}
        />
        <IconButton
          aria-label="Add item"
          icon={<AddIcon />}
          onClick={handleAdd}
          bg={buttonBgColor}
          color="white"
          _hover={{ bg: buttonHoverColor }}
        />
      </Flex>
      <HStack flexWrap="wrap" spacing={2}>
        {items.map((item) => (
          <Tag key={item} m="2px" variant="subtle" colorScheme="teal">
            <TagLabel>{item}</TagLabel>
            <TagCloseButton onClick={() => handleRemove(item)} />
          </Tag>
        ))}
      </HStack>
    </FormControl>
  )
}

export default ArrayInputField 