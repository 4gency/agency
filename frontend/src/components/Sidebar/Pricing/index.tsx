import { Container, Flex, Heading } from "@chakra-ui/react";
import { PricingContainer } from "./PricingContainer";

export const Pricing = () => {

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Our Plans
      </Heading>
      <Flex
        align="center"
        justify="center"
      >
      <PricingContainer/>
      </Flex>
    </Container>
  );
};
