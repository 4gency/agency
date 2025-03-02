import { Heading, Box } from "@chakra-ui/react"
import PricingSection from "../../Pricing/PricingSection"

export const Pricing = () => {
  return (
    <Box width="100%" maxWidth="100%" overflow="hidden" position="relative">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={6} px={4}>
        Our Plans
      </Heading>
      <Box 
        width="100%" 
        maxWidth="100%" 
        overflow="hidden" 
        position="relative"
        sx={{
          "&:after": {
            display: "block",
            position: "absolute",
            right: 0,
            top: 0,
            height: "100%",
            width: "20px",
            background: "linear-gradient(to right, transparent, var(--chakra-colors-gray-800, #1A202C))",
            zIndex: 1,
          },
          "&:before": {
            display: "block",
            position: "absolute",
            left: 0,
            top: 0,
            height: "100%",
            width: "20px",
            background: "linear-gradient(to left, transparent, var(--chakra-colors-gray-800, #1A202C))",
            zIndex: 1,
          }
        }}
      >
        <PricingSection isLandingPage={false} />
      </Box>
    </Box>
  )
}
