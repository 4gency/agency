import { AddIcon } from "@chakra-ui/icons"
import {
  Flex,
  FormControl,
  FormLabel,
  IconButton,
  Input,
  Tag,
  TagCloseButton,
  TagLabel,
} from "@chakra-ui/react"
import type React from "react"
import { useState } from "react"

interface ArrayInputFieldProps {
  label: string
  items: string[]
  onChange: (items: string[]) => void
  placeholder?: string
}

/**
 * Componente reutilizável para campos que permitem adicionar múltiplos valores
 * Versão melhorada do ArrayInput com suporte a colagem múltipla e teclas Enter/vírgula
 */
const ArrayInputField: React.FC<ArrayInputFieldProps> = ({
  label,
  items,
  onChange,
  placeholder = "Add new item",
}) => {
  const [inputValue, setInputValue] = useState("")

  const handleAdd = () => {
    const trimmed = inputValue.trim()
    if (!trimmed) {
      return
    }
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
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      handleAdd()
    }
  }

  // Função para lidar com colagem de texto com múltiplos itens separados por vírgula
  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pasteData = e.clipboardData.getData('text');
    if (pasteData.includes(',')) {
      e.preventDefault();
      
      const newItems = pasteData
        .split(',')
        .map(item => item.trim())
        .filter(item => item !== '' && !items.includes(item));
      
      if (newItems.length > 0) {
        onChange([...items, ...newItems]);
      }
    }
  };

  return (
    <FormControl mb={4}>
      <FormLabel>{label}</FormLabel>
      <Flex gap={2} mb={2}>
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          onPaste={handlePaste}
          placeholder={placeholder}
        />
        <IconButton
          aria-label="Add item"
          icon={<AddIcon />}
          onClick={handleAdd}
        />
      </Flex>
      <Flex wrap="wrap" gap={1}>
        {items.map((item) => (
          <Tag key={item} m="2px" variant="subtle" colorScheme="teal">
            <TagLabel>{item}</TagLabel>
            <TagCloseButton onClick={() => handleRemove(item)} zIndex={10} />
          </Tag>
        ))}
      </Flex>
    </FormControl>
  )
}

export default ArrayInputField 