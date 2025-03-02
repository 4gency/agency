import type React from "react"
import {
  Box,
  Text,
  VStack,
  List,
  ListItem,
  ListIcon,
  Button,
  useBreakpointValue,
} from "@chakra-ui/react"
import { CheckIcon } from "@chakra-ui/icons"
import { useNormalPricingCardTheme } from "./hooks/useNormalPricingCardTheme"

interface NormalPricingCardProps {
  title: string
  price: number
  recurrence: string
  benefits: string[]
  buttonText: string
  buttonEnabled?: boolean
  buttonLink?: string
  disabled?: boolean
  hasDiscount?: boolean
  priceWithoutDiscount?: number
  isLandingPage?: boolean
  onButtonClick?: () => void
}

const NormalPricingCard: React.FC<NormalPricingCardProps> = ({
  title,
  price,
  recurrence,
  benefits,
  buttonText,
  buttonEnabled,
  buttonLink,
  disabled = false,
  hasDiscount = false,
  priceWithoutDiscount,
  isLandingPage = false,
  onButtonClick,
}) => {
  const {
    bgColor,
    textColor,
    borderColor,
    priceColor,
    discountColor,
    iconColor,
  } = useNormalPricingCardTheme(isLandingPage)

  // Define the handler for click event
  const handleClick = buttonEnabled && onButtonClick ? onButtonClick : undefined;
  
  // Check if button is in loading state
  const isLoading = buttonEnabled && buttonText === "Loading...";

  // Responsividade extrema para a largura do card
  const minWidth = useBreakpointValue({ 
    base: "240px", 
    xs: "260px", 
    sm: "280px", 
    md: "320px" 
  });
  
  // Padding responsivo para dispositivos muito pequenos
  const horizontalPadding = useBreakpointValue({ 
    base: 3, 
    sm: 4, 
    md: 6 
  });
  
  // Ajustar tamanho de fonte para dispositivos muito pequenos
  const titleFontSize = useBreakpointValue({ base: "xl", sm: "2xl" });
  const priceFontSize = useBreakpointValue({ base: "2xl", sm: "3xl" });
  const benefitFontSize = useBreakpointValue({ base: "sm", sm: "md" });

  return (
    <Box
      bg={bgColor}
      borderRadius="xl"
      borderWidth="1px"
      borderColor={borderColor}
      boxShadow={disabled ? "md" : "sm"}
      width="100%"
      minW={minWidth}
      maxW={{ base: "100%", sm: "100%", md: "400px" }}
      height="100%"
      maxHeight={{ base: "430px", sm: "450px" }}
      minHeight={{ base: "370px", sm: "390px" }}
      p={{ base: horizontalPadding, md: 6 }}
      display="flex"
      flexDirection="column"
      justifyContent="space-between"
      filter={disabled ? "blur(5px)" : "none"}
      pointerEvents={disabled ? "none" : "auto"}
      transition="all 0.3s"
      mx="auto"
      my={2}
      _hover={!disabled ? { transform: "translateY(-5px)", boxShadow: "md" } : {}}
    >
      <VStack align="start" spacing={0.1} height="100%">
        <Text fontSize={titleFontSize} fontWeight="bold" color={textColor}>
          {title}
        </Text>
        
        {hasDiscount && priceWithoutDiscount !== undefined && (
          <Text fontSize={benefitFontSize} color={discountColor} textDecoration="line-through">
            ${priceWithoutDiscount.toFixed(2)}
          </Text>
        )}
        
        <Text fontSize={priceFontSize} fontWeight="bold" color={priceColor}>
          ${price.toFixed(2)}/{recurrence}
        </Text>
        
        <List spacing={1} w="100%" mt={2} flex="1" overflow="auto" maxH="180px">
          {benefits.map((benefit, index) => (
            <ListItem key={index} display="flex" alignItems="flex-start" py={1}>
              <ListIcon as={CheckIcon} color={iconColor} boxSize={4} mt="5px" />
              <Text color={textColor} fontSize={benefitFontSize}>
                {benefit}
              </Text>
            </ListItem>
          ))}
        </List>
      </VStack>
      
      {onButtonClick ? (
        <Button
          variant="primary"
          size="md"
          h={{ base: "45px", sm: "55px" }}
          w="100%"
          mt={4}
          isDisabled={!buttonEnabled}
          onClick={handleClick}
          isLoading={isLoading}
          loadingText="Loading..."
          fontSize={benefitFontSize}
        >
          {buttonText}
        </Button>
      ) : (
        <Button
          as="a"
          href={buttonEnabled ? buttonLink : undefined}
          variant="primary"
          size="md"
          h={{ base: "45px", sm: "55px" }}
          w="100%"
          mt={4}
          isDisabled={!buttonEnabled}
          fontSize={benefitFontSize}
        >
          {buttonText}
        </Button>
      )}
    </Box>
  )
}

export default NormalPricingCard
