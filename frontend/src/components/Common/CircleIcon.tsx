import { Flex, Icon, FlexProps } from "@chakra-ui/react"
import React from "react"

interface CircleIconProps extends FlexProps {
  icon: React.ElementType
  color?: string
  bgColor: string
  iconSize?: number
}

export function CircleIcon({
  icon,
  color = "white",
  bgColor,
  iconSize = 5,
  ...props
}: CircleIconProps) {
  return (
    <Flex
      bg={bgColor}
      w="45px"
      h="45px"
      borderRadius="full"
      justifyContent="center"
      alignItems="center"
      mb={1}
      {...props}
    >
      <Icon as={icon} w={iconSize} h={iconSize} color={color} />
    </Flex>
  )
} 