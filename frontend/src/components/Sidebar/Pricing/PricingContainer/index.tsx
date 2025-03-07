import {
  Center,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import BadgePricingCard from "../../../Pricing/BadgePricingCard"
import NormalPricingCard from "../../../Pricing/NormalPricingCard"
import useSubscriptionPlans from "../../../../hooks/useSubscriptionPlans"

export const PricingContainer = () => {
  const { 
    plans, 
    isLoading, 
    isError
  } = useSubscriptionPlans(true)
  
  if (isLoading) {
    return (
      <Center py={8}>
        <Spinner size="lg" color="teal.500" />
      </Center>
    )
  }

  if (isError) {
    return (
      <Center py={8}>
        <Text color="red.500">
          Erro ao carregar planos. Por favor, tente novamente.
        </Text>
      </Center>
    )
  }

  if (plans.length === 0) {
    return (
      <Center py={8}>
        <Text>Nenhum plano disponível no momento.</Text>
      </Center>
    )
  }

  return (
    <VStack spacing={4} align="stretch" w="full">
      {plans.map((plan) => {
        const {
          id,
          name,
          price,
          has_badge,
          badge_text,
          button_text,
          button_enabled,
          has_discount,
          price_without_discount,
          is_active,
          metric_type,
          benefits,
        } = plan

        const commonProps = {
          key: id,
          title: name,
          price: price,
          benefits: benefits ? benefits.map((b) => b.name) : [],
          buttonText: button_text,
          buttonEnabled: button_enabled,
          buttonLink: "/signup",
          disabled: !is_active,
          hasDiscount: has_discount,
          priceWithoutDiscount: price_without_discount,
          recurrence: metric_type,
          isMobile: false
        }

        if (has_badge) {
          return <BadgePricingCard {...commonProps} badgeText={badge_text} />
        }
        return <NormalPricingCard {...commonProps} />
      })}
    </VStack>
  )
}
