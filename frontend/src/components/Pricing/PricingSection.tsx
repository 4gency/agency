import {
  useBreakpointValue,
  useColorModeValue,
  Box,
  Center,
  Container,
  Heading,
  IconButton,
  Spinner,
  Text,
  VStack,
  Badge,
} from "@chakra-ui/react"
import type React from "react"
import { useRef, useState } from "react"
import Slider from "react-slick"
import useSubscriptionPlans from "../../hooks/useSubscriptionPlans"
import { useCheckoutHandler } from "../../hooks/useCheckoutHandler"

import "slick-carousel/slick/slick-theme.css"
import "slick-carousel/slick/slick.css"
import "./PricingCarouselStyles.css"

import { FiArrowLeft, FiArrowRight } from "react-icons/fi"
import BadgePricingCard from "./BadgePricingCard"
import NormalPricingCard from "./NormalPricingCard"

interface PricingSectionProps {
  isLandingPage?: boolean
}

// Componente para as setas do carrossel
const CarouselArrow = ({
  direction,
  onClick,
}: { direction: "left" | "right"; onClick?: () => void }) => {
  const bgColor = useColorModeValue("white", "gray.800")
  const arrowColor = useColorModeValue("gray.800", "white")

  return (
    <IconButton
      aria-label={`${direction} arrow`}
      icon={direction === "left" ? <FiArrowLeft /> : <FiArrowRight />}
      onClick={onClick}
      position="absolute"
      top="50%"
      transform="translateY(-50%)"
      zIndex={2}
      {...(direction === "left"
        ? { left: { base: "5px", md: "10px" } }
        : { right: { base: "5px", md: "10px" } })}
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

const PricingSection: React.FC<PricingSectionProps> = ({
  isLandingPage = false,
}) => {
  const { 
    plans, 
    isLoading, 
    isError 
  } = useSubscriptionPlans(false)
  const sliderRef = useRef<Slider>(null)
  const [currentSlide, setCurrentSlide] = useState(0)
  const { handleSubscribeClick, isPlanLoading } = useCheckoutHandler()

  const headingColor = isLandingPage
    ? "gray.800"
    : useColorModeValue("gray.800", "white")
  const sectionBg = isLandingPage
    ? "gray.50"
    : useColorModeValue("gray.50", "gray.900")

  // Número de slides a mostrar baseado no breakpoint
  const slidesToShow = useBreakpointValue({ base: 1, md: 2, lg: 3 }) || 1
  const showArrows = useBreakpointValue({ base: false, md: true }) || false

  // Determine se devemos mostrar os botões prev/next
  const showPrevButton = currentSlide > 0
  const showNextButton = currentSlide < plans.length - slidesToShow

  // Determine se devemos centralizar os slides (quando há poucos cards)
  const shouldCenterSlides = plans.length <= slidesToShow

  // Configurações simplificadas para o Slider
  const settings = {
    dots: true,
    infinite: false,
    speed: 500,
    slidesToShow: shouldCenterSlides ? plans.length : slidesToShow,
    slidesToScroll: 1,
    arrows: false,
    centerMode: true,
    centerPadding: "10px",
    variableWidth: false,
    adaptiveHeight: true,
    swipeToSlide: true,
    draggable: true,
    className: "pricing-carousel-inner",
    dotsClass: "slick-dots",
    beforeChange: (_current: number, next: number) => setCurrentSlide(next),
    afterChange: (current: number) => setCurrentSlide(current),
    responsive: [
      {
        breakpoint: 1280,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 1,
          dots: true,
          centerMode: true,
          centerPadding: "10px",
        },
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
          dots: true,
          centerMode: true,
          centerPadding: "0px",
        },
      },
    ],
  }

  if (isLoading) {
    return (
      <Center py={20} bg={isLandingPage ? "gray.50" : undefined}>
        <Spinner size="xl" color="teal.500" />
      </Center>
    )
  }

  if (isError) {
    return (
      <Center py={20} bg={isLandingPage ? "gray.50" : undefined}>
        <Text color="red.500" fontSize="lg">
          Erro ao carregar planos. Por favor, tente novamente.
        </Text>
      </Center>
    )
  }

  return (
    <Box
      id="pricing"
      py={{ base: 6, md: 10 }}
      bg={isLandingPage ? sectionBg : "transparent"}
      width="100%"
      overflow="hidden"
      zIndex="-1"
    >
      <Container
        maxW={isLandingPage ? "container.xl" : "100%"}
        p={isLandingPage ? { base: 2, md: 4 } : 0}
      >
        {isLandingPage && (
          <VStack
            spacing={{ base: 4, md: 6 }}
            mb={{ base: 8, md: 12 }}
            textAlign="center"
          >
            <Badge
              textTransform="none"
              bg="#E2FFE0"
              color="#009688"
              px={3}
              py={1}
              borderRadius="md"
              fontSize={{ base: "sm", md: "initial" }}
            >
              Our Pricing
            </Badge>

            <Heading
              as="h2"
              size={{ base: "xl", md: "2xl" }}
              fontWeight="bold"
              color={headingColor}
              letterSpacing="-0.02em"
            >
              Choose the Plan That Suits You
            </Heading>

            <Text
              fontSize={{ base: "md", md: "lg" }}
              maxW="container.md"
              color={isLandingPage ? "gray.600" : undefined}
            >
              {/* Texto adicional se necessário */}
            </Text>
          </VStack>
        )}

        <Box
          position="relative"
          width="100%"
          maxW="1300px"
          mx="auto"
          className={`pricing-carousel ${
            !isLandingPage ? "pricing-carousel-sidebar" : ""
          }`}
        >
          {showArrows && showPrevButton && (
            <CarouselArrow
              direction="left"
              onClick={() => sliderRef.current?.slickPrev()}
            />
          )}

          <Box width="100%" pb={6} mx="auto" px={{ base: 1, md: 4 }}>
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

                // Props comuns para os dois tipos de card
                const commonProps = {
                  title: name,
                  price: price,
                  recurrence: metric_type,
                  benefits: benefits ? benefits.map((b) => b.name) : [],
                  buttonText: isPlanLoading(id) ? "Loading..." : button_text,
                  buttonEnabled: button_enabled && !isPlanLoading(id),
                  buttonLink: "",
                  hasDiscount: has_discount,
                  priceWithoutDiscount: price_without_discount,
                  isLandingPage: isLandingPage,
                  onButtonClick: () => handleSubscribeClick(id),
                }

                if (has_badge) {
                  return (
                    <div key={id} style={{ width: "100%", padding: "10px" }}>
                      <BadgePricingCard
                        {...commonProps}
                        badgeText={badge_text}
                      />
                    </div>
                  )
                } else {
                  return (
                    <div key={id} style={{ width: "100%", padding: "10px" }}>
                      <NormalPricingCard
                        {...commonProps}
                        disabled={!is_active}
                      />
                    </div>
                  )
                }
              })}
            </Slider>
          </Box>

          {showArrows && showNextButton && (
            <CarouselArrow
              direction="right"
              onClick={() => sliderRef.current?.slickNext()}
            />
          )}
        </Box>
      </Container>
    </Box>
  )
}

export default PricingSection
