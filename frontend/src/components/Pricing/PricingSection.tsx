import type React from "react"
import { useEffect, useState, useRef } from "react"
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
  Badge,
  VStack,
  useColorModeValue,
  Spinner,
  Center,
  IconButton,
  useBreakpointValue,
} from "@chakra-ui/react"
import BadgePricingCard from "./BadgePricingCard"
import NormalPricingCard from "./NormalPricingCard"
import Slider from "react-slick"
import { ChevronLeftIcon, ChevronRightIcon } from "@chakra-ui/icons"

// Importações necessárias para o CSS do Slick
import "slick-carousel/slick/slick.css"
import "slick-carousel/slick/slick-theme.css"
import "./PricingCarouselStyles.css"

interface PricingSectionProps {
  isLandingPage?: boolean
}

// Componente para as setas do carrossel
const CarouselArrow = ({ direction, onClick }: { direction: 'left' | 'right', onClick?: () => void }) => {
  const bgColor = useColorModeValue("white", "gray.800")
  const arrowColor = useColorModeValue("gray.800", "white")
  
  return (
    <IconButton
      aria-label={`${direction} arrow`}
      icon={direction === 'left' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
      onClick={onClick}
      position="absolute"
      top="50%"
      transform="translateY(-50%)"
      zIndex={2}
      {...(direction === 'left' 
        ? { left: { base: "5px", md: "10px" } } 
        : { right: { base: "5px", md: "10px" } }
      )}
      rounded="full"
      bg={bgColor}
      color={arrowColor}
      boxShadow="md"
      size="lg"
      className="pricing-carousel-arrow"
      _hover={{
        bg: useColorModeValue("gray.100", "gray.700"),
      }}
    />
  )
}

const PricingSection: React.FC<PricingSectionProps> = ({ isLandingPage = false }) => {
  const [plans, setPlans] = useState<SubscriptionPlanPublic[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>("")
  const sliderRef = useRef<Slider>(null)
  const [currentSlide, setCurrentSlide] = useState(0)

  const headingColor = isLandingPage ? "gray.800" : useColorModeValue("gray.800", "white")
  const sectionBg = isLandingPage ? "gray.50" : useColorModeValue("gray.50", "gray.900")
  
  // Número de slides a mostrar baseado no breakpoint
  const slidesToShow = useBreakpointValue({ base: 1, md: 2, lg: 3 }) || 1
  const showArrows = useBreakpointValue({ base: false, md: true }) || false

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

  // Determine se devemos mostrar os botões prev/next
  const showPrevButton = currentSlide > 0
  const showNextButton = currentSlide < plans.length - slidesToShow

  // Determine se devemos centralizar os slides (quando há poucos cards)
  const shouldCenterSlides = plans.length <= slidesToShow
  
  const settings = {
    dots: true,
    infinite: false,
    speed: 500,
    slidesToShow: shouldCenterSlides ? plans.length : slidesToShow,
    slidesToScroll: 1,
    arrows: false,
    centerMode: shouldCenterSlides,
    centerPadding: '0px',
    variableWidth: false,
    adaptiveHeight: false,
    swipeToSlide: true,
    draggable: !shouldCenterSlides,
    beforeChange: (_current: number, next: number) => setCurrentSlide(next),
    afterChange: (current: number) => setCurrentSlide(current),
    responsive: [
      {
        breakpoint: 1280,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 1,
        }
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
        }
      }
    ]
  }

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
      py={10}
      bg={isLandingPage ? sectionBg : 'transparent'}
      width="100%"
      overflow="hidden"
      sx={{
        ".chakra-container": {
          maxWidth: "100% !important",
          padding: isLandingPage ? undefined : "0 !important",
          overflow: "hidden"
        }
      }}
    >
      <Container maxW={isLandingPage ? "container.xl" : "100%"} px={isLandingPage ? { base: 4, md: 8 } : 0}>
        {isLandingPage && (
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
        )}

        <Box 
          position="relative" 
          width="100%"
          mx="auto"
          px={isLandingPage ? { base: 6, md: 10 } : { base: 0, md: 6 }}
          overflow="hidden"
        >
          {showArrows && showPrevButton && (
            <CarouselArrow direction="left" onClick={() => sliderRef.current?.slickPrev()} />
          )}
          
          <Box 
            width="100%"
            mx="auto"
            pt={4} // Adicionando espaço superior para o badge não ser cortado
            className={`pricing-carousel ${!isLandingPage ? 'pricing-carousel-sidebar' : ''} ${shouldCenterSlides ? 'centered-slides' : ''}`}
            sx={{
              '.slick-track': {
                display: 'flex !important',
                width: '100% !important',
                ...(shouldCenterSlides && {
                  justifyContent: 'center !important',
                  margin: '0 auto !important',
                }),
              },
              '.slick-slide': {
                height: 'inherit !important',
                '> div': {
                  height: '100%',
                  display: 'flex',
                  justifyContent: 'center',
                }
              }
            }}
          >
            <Slider ref={sliderRef} {...settings}>
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

                return (
                  <Box key={id} height="100%" px={2} pt={2}>
                    {has_badge ? (
                      <BadgePricingCard 
                        {...commonProps} 
                        badgeText={badge_text} 
                      />
                    ) : (
                      <NormalPricingCard 
                        {...commonProps} 
                      />
                    )}
                  </Box>
                )
              })}
            </Slider>
          </Box>
          
          {showArrows && showNextButton && (
            <CarouselArrow direction="right" onClick={() => sliderRef.current?.slickNext()} />
          )}
        </Box>
      </Container>
    </Box>
  )
}

export default PricingSection
