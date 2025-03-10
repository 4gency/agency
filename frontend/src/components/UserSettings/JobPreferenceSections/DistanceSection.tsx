import {
  FormControl,
  FormLabel,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
  Text,
  Box,
  Checkbox,
  Flex,
  Tooltip,
  useColorModeValue
} from "@chakra-ui/react"
import type React from "react"
import { useState, useEffect } from "react"
import JobSectionContainer from "./JobSectionContainer"

interface DistanceSectionProps {
  value: number
  onChange: (value: number) => void
}

// Valores válidos para o slider
const VALID_DISTANCES = [0, 5, 10, 25, 50, 100];
const DEFAULT_DISTANCE = 25;

const DistanceSection: React.FC<DistanceSectionProps> = ({
  value,
  onChange
}) => {
  // Estado para controlar o uso do limite de distância
  const [useDistanceLimit, setUseDistanceLimit] = useState(value !== 0);
  // Estado para controlar o tooltip do slider
  const [showTooltip, setShowTooltip] = useState(false);
  // Valor visual do slider
  const [sliderValue, setSliderValue] = useState(value === 0 ? DEFAULT_DISTANCE : value);

  // Quando o valor externo muda, atualizar o estado local
  useEffect(() => {
    setUseDistanceLimit(value !== 0);
    setSliderValue(value === 0 ? DEFAULT_DISTANCE : value);
  }, [value]);

  // Função para encontrar o valor válido mais próximo
  const findClosestValidValue = (val: number): number => {
    // Se for 0, retornar o valor default
    if (val === 0) return DEFAULT_DISTANCE;
    
    // Encontrar o valor válido mais próximo
    return VALID_DISTANCES.reduce((prev, curr) => {
      return (Math.abs(curr - val) < Math.abs(prev - val)) ? curr : prev;
    });
  };

  // Lidar com a mudança do checkbox
  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setUseDistanceLimit(checked);
    
    // Se desmarcar, setar distance para 0 (sem limite)
    if (!checked) {
      onChange(0);
    } else {
      // Se marcar, usar o valor atual do slider
      onChange(sliderValue);
    }
  };

  // Lidar com a mudança do slider
  const handleSliderChange = (val: number) => {
    // Atualizando apenas o valor visual enquanto arrasta
    setSliderValue(val);
  };

  // Quando soltar o slider, encontrar o valor válido mais próximo
  const handleSliderChangeEnd = (val: number) => {
    const closestValue = findClosestValidValue(val);
    setSliderValue(closestValue);
    
    // Só atualizar o valor real se estiver usando limite de distância
    if (useDistanceLimit) {
      onChange(closestValue);
    }
  };

  const bgColor = useColorModeValue("gray.100", "gray.700");
  const textColor = useColorModeValue("gray.800", "white");

  return (
    <JobSectionContainer 
      title="Distance" 
      infoTooltip="Set your preferred distance range from your LinkedIn location. This filters jobs based on how far you're willing to commute."
    >
      <Box bg={bgColor} p={4} borderRadius="md" mb={4}>
        <Text fontSize="sm" color={textColor}>
          This setting uses your location from LinkedIn to filter job opportunities based on distance.
          Either set a specific range or choose "No distance limit" to see all job locations.
        </Text>
      </Box>

      <FormControl mb={4}>
        <Flex alignItems="center" mb={4}>
          <Checkbox 
            isChecked={useDistanceLimit}
            onChange={handleCheckboxChange}
            colorScheme="teal"
            size="md"
          >
            <Text fontWeight="500">Use distance limit</Text>
          </Checkbox>
          {useDistanceLimit && (
            <Text ml={3} fontWeight="bold">
              Current: {sliderValue} miles
            </Text>
          )}
          {!useDistanceLimit && (
            <Text ml={3} fontWeight="bold" color="gray.500">
              No distance limit
            </Text>
          )}
        </Flex>

        <Box opacity={useDistanceLimit ? 1 : 0.5} pointerEvents={useDistanceLimit ? "auto" : "none"}>
          <Box px={8} mt={6} position="relative">
            <Slider
              min={0}
              max={100}
              step={1}
              value={sliderValue}
              onChange={handleSliderChange}
              onChangeEnd={handleSliderChangeEnd}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              colorScheme="teal"
            >
              {/* Marcas para os valores válidos */}
              {VALID_DISTANCES.map((dist) => (
                <SliderMark
                  key={dist}
                  value={dist}
                  mt={3}
                  fontSize="sm"
                  fontWeight={sliderValue === dist ? "bold" : "normal"}
                  color={sliderValue === dist ? "teal.500" : "gray.500"}
                  textAlign="center"
                  width="24px"
                  ml="-12px" // Centraliza a marca em relação ao valor
                  whiteSpace="nowrap" // Impede a quebra de linha
                >
                  {dist}{dist === 0 ? "" : "mi"}
                </SliderMark>
              ))}

              <SliderTrack>
                <SliderFilledTrack bg="#00766C" />
              </SliderTrack>
              
              <Tooltip
                hasArrow
                bg="teal.500"
                color="white"
                placement="top"
                isOpen={showTooltip}
                label={`${sliderValue} miles`}
              >
                <SliderThumb boxSize={6} borderColor="#00766C" borderWidth="2px" />
              </Tooltip>
            </Slider>
          </Box>
        </Box>
        
        <Box mt={8} display="flex" justifyContent="space-between">
          <Text fontSize="sm" fontStyle="italic" color="gray.500">
            Values will snap to 0, 5, 10, 25, 50, or 100 miles
          </Text>
        </Box>
      </FormControl>
    </JobSectionContainer>
  )
}

export default DistanceSection 