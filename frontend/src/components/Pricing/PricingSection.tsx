import type React from "react"
import { useEffect, useState } from "react"
import {
  type SubscriptionPlanPublic,
  type SubscriptionPlansPublic,
  SubscriptionPlansService,
} from "../../client"
import {
  Box,
  Container,
  Heading,
  Text,
  Flex,
  Badge,
  VStack,
  useColorModeValue,
  Spinner,
  Center,
} from "@chakra-ui/react"
import BadgePricingCard from "./BadgePricingCard"
import NormalPricingCard from "./NormalPricingCard"

interface PricingSectionProps {
  isLandingPage?: boolean
}

const PricingSection: React.FC<PricingSectionProps> = ({ isLandingPage = false }) => {
  const [plans, setPlans] = useState<SubscriptionPlanPublic[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>("")

  const headingColor = isLandingPage ? "gray.800" : useColorModeValue("gray.800", "white")
  const sectionBg = isLandingPage ? "gray.50" : useColorModeValue("gray.50", "gray.900")

  useEffect(() => {
    SubscriptionPlansService.readSubscriptionPlans({ onlyActive: false })
      .then((response: SubscriptionPlansPublic) => {
        if (response.plans) {
          setPlans(response.plans)
        }
      })
      .catch((err: any) => {
        console.error("Error fetching subscription plans", err)
        setError("Failed to load subscription plans")
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <Center py={20} bg={isLandingPage ? "gray.50" : undefined}>
        <Spinner size="xl" color="ui.main" thickness="4px" />
      </Center>
    )
  }

  if (error) {
    return (
      <Center py={20} bg={isLandingPage ? "gray.50" : undefined}>
        <Text color="red.500" fontSize="lg">
          {error}
        </Text>
      </Center>
    )
  }

  return (
    <Box
      id="pricing"
      py={20}
      px={{ base: 4, md: "5vw" }}
      bg={sectionBg}
    >
      <Container maxW="container.xl">
        <VStack spacing={6} mb={12} textAlign="center">
          <Badge
            colorScheme="teal"
            px={3}
            py={1}
            borderRadius="md"
            fontSize="sm"
          >
            Our Pricing
          </Badge>
          
          <Heading 
            as="h2" 
            size="2xl" 
            fontWeight="bold"
            color={headingColor}
            letterSpacing="-0.02em"
          >
            Choose the Plan That Suits You
          </Heading>
          
          <Text fontSize="lg" maxW="container.md" color={isLandingPage ? "gray.600" : undefined}>
            {/* Texto adicional se necessário */}
          </Text>
        </VStack>

        <Box 
          overflowX={{ base: "auto" }} 
          pb={6}
          sx={{
            "&::-webkit-scrollbar": {
              height: "8px",
              borderRadius: "8px",
              backgroundColor: `rgba(0, 0, 0, 0.05)`,
            },
            "&::-webkit-scrollbar-thumb": {
              backgroundColor: `rgba(0, 0, 0, 0.1)`,
              borderRadius: "8px",
            },
          }}
        >
          <Flex 
            gap={6} 
            flexWrap={{ base: "nowrap", lg: "wrap" }}
            justifyContent={{ base: "flex-start", lg: "center" }}
            alignItems="stretch"
            py={4}
            px={{ base: 4, md: 0 }}
            minW={{ base: "fit-content", lg: "auto" }}
          >
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
                isLandingPage: isLandingPage,
              }

              if (has_badge) {
                return (
                  <BadgePricingCard {...commonProps} badgeText={badge_text} />
                )
              }
              return <NormalPricingCard {...commonProps} />
            })}
          </Flex>
        </Box>
      </Container>
    </Box>
  )
}

export default PricingSection
