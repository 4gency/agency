import type React from "react"
import { useEffect, useState } from "react"
import {
  type SubscriptionPlanPublic,
  type SubscriptionPlansPublic,
  SubscriptionPlansService,
} from "../../client"
import BadgePricingCard from "./BadgePricingCard"
import NormalPricingCard from "./NormalPricingCard"

const PricingSection: React.FC = () => {
  const [plans, setPlans] = useState<SubscriptionPlanPublic[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>("")

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
    return <div />
  }

  if (error) {
    return <div />
  }

  return (
    <div
      id="pricing"
      className="block-group is-layout-flow block-group-is-layout-flow"
      style={{
        paddingTop: 80,
        paddingRight: "5vw",
        paddingBottom: 100,
        paddingLeft: "5vw",
      }}
    >
      <div className="block-group is-vertical is-content-justification-center is-layout-flex container-core-group-is-layout-54 block-group-is-layout-flex">
        <div
          className="block-group has-theme-7-background-color has-background has-inter-font-family is-nowrap is-layout-flex container-core-group-is-layout-38 block-group-is-layout-flex"
          style={{
            borderRadius: 5,
            paddingTop: 6,
            paddingRight: 11,
            paddingBottom: 6,
            paddingLeft: 11,
          }}
        >
          <h3
            className="block-heading has-theme-3-color has-text-color has-link-color has-inter-font-family"
            style={{
              fontSize: 16,
              fontStyle: "normal",
              fontWeight: 600,
              lineHeight: "1.3",
            }}
          >
            Our Pricing
          </h3>
        </div>
        <h2
          className="block-heading has-text-align-center has-theme-0-color has-text-color has-link-color has-h-1-alt-font-size"
          style={{
            fontStyle: "normal",
            fontWeight: 600,
            letterSpacing: "-0.02em",
            lineHeight: "1.2",
          }}
        >
          Choose the Plan That Suits You
        </h2>
        <div
          className="block-group is-content-justification-center is-nowrap is-layout-flex container-core-group-is-layout-39 block-group-is-layout-flex"
          style={{ marginBottom: "40px" }}
        >
          <p style={{ fontSize: 18 }}>{/* Additional text if needed */}</p>
        </div>
        {/* Horizontally Scrollable Pricing Cards Container */}
        <div style={{ maxWidth: "100%", overflowX: "auto", paddingBottom: 16 }}>
          <div
            style={{
              display: "flex",
              gap: "40px",
              flexWrap: "nowrap",
              padding: "20px",
            }}
            className="pricing-scroll-container"
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
              }

              if (has_badge) {
                return (
                  <BadgePricingCard {...commonProps} badgeText={badge_text} />
                )
              }
              return <NormalPricingCard {...commonProps} />
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default PricingSection
