import { Card, type CardProps } from "@chakra-ui/react"
import { useEffect, useState } from "react"

interface AnimatedCardProps extends CardProps {
  children: React.ReactNode
  animationDelay?: number
}

export function AnimatedCard({
  children,
  animationDelay = 200,
  ...props
}: AnimatedCardProps) {
  const [animate, setAnimate] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setAnimate(true), animationDelay)
    return () => clearTimeout(timer)
  }, [animationDelay])

  return (
    <Card
      {...props}
      transform={animate ? "scale(1)" : "scale(0.95)"}
      opacity={animate ? 1 : 0}
      transition="all 0.5s ease-in-out"
    >
      {children}
    </Card>
  )
}
