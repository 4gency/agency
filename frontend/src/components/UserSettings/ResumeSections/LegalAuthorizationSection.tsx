import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Checkbox,
  FormControl,
  Grid,
  GridItem,
  Text,
} from "@chakra-ui/react"
import { type UseFormRegister } from "react-hook-form"
import type { ResumeForm } from "../types"
import SectionContainer from "./SectionContainer"

interface LegalAuthorizationSectionProps {
  register: UseFormRegister<ResumeForm>
}

const LegalAuthorizationSection: React.FC<LegalAuthorizationSectionProps> = ({
  register,
}) => {
  const regions = [
    {
      name: "United States",
      fields: [
        {
          id: "us_work_authorization",
          label: "I have US work authorization",
        },
        {
          id: "requires_us_visa",
          label: "I require a US visa",
        },
        {
          id: "requires_us_sponsorship",
          label: "I require US sponsorship",
        },
        {
          id: "legally_allowed_to_work_in_us",
          label: "I am legally allowed to work in the US",
        },
      ],
    },
    {
      name: "European Union",
      fields: [
        {
          id: "eu_work_authorization",
          label: "I have EU work authorization",
        },
        {
          id: "requires_eu_visa",
          label: "I require an EU visa",
        },
        {
          id: "requires_eu_sponsorship",
          label: "I require EU sponsorship",
        },
        {
          id: "legally_allowed_to_work_in_eu",
          label: "I am legally allowed to work in the EU",
        },
      ],
    },
    {
      name: "Canada",
      fields: [
        {
          id: "canada_work_authorization",
          label: "I have Canada work authorization",
        },
        {
          id: "requires_canada_visa",
          label: "I require a Canada visa",
        },
        {
          id: "requires_canada_sponsorship",
          label: "I require Canada sponsorship",
        },
        {
          id: "legally_allowed_to_work_in_canada",
          label: "I am legally allowed to work in Canada",
        },
      ],
    },
    {
      name: "United Kingdom",
      fields: [
        {
          id: "uk_work_authorization",
          label: "I have UK work authorization",
        },
        {
          id: "requires_uk_visa",
          label: "I require a UK visa",
        },
        {
          id: "requires_uk_sponsorship",
          label: "I require UK sponsorship",
        },
        {
          id: "legally_allowed_to_work_in_uk",
          label: "I am legally allowed to work in the UK",
        },
      ],
    },
  ]

  return (
    <SectionContainer 
      title="Legal Authorization" 
      infoTooltip="Provide accurate information about your work authorization status. This is essential for employers to determine eligibility."
    >
      <Box p={4}>
        <Text mb={4} fontSize="sm" color="gray.600">
          Please indicate your work authorization status for different regions. This information helps employers understand your eligibility to work in various locations.
        </Text>
        
        <Accordion allowMultiple defaultIndex={[]}>
          {regions.map((region) => (
            <AccordionItem key={region.name}>
              <h2>
                <AccordionButton py={3}>
                  <Box flex="1" textAlign="left" fontWeight="medium">
                    {region.name}
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={2}>
                  {region.fields.map((field) => (
                    <GridItem key={field.id}>
                      <FormControl display="flex" alignItems="center" mb={2}>
                        <Checkbox
                          {...register(`legal_authorization.${field.id}` as any)}
                          colorScheme="teal"
                        >
                          {field.label}
                        </Checkbox>
                      </FormControl>
                    </GridItem>
                  ))}
                </Grid>
              </AccordionPanel>
            </AccordionItem>
          ))}
        </Accordion>
      </Box>
    </SectionContainer>
  )
}

export default LegalAuthorizationSection 