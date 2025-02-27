import { useEffect, useState } from "react";
import BadgePricingCard from "../../../Pricing/BadgePricingCard";
import NormalPricingCard from "../../../Pricing/NormalPricingCard";
import {
  SubscriptionPlanPublic,
  SubscriptionPlansPublic,
  SubscriptionPlansService,
} from "../../../../client";

export const PricingContainer = () => {
  const [plans, setPlans] = useState<SubscriptionPlanPublic[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  // if (loading) {
  //   return <div></div>;
  // }

  // if (error) {
  //   return <div></div>;
  // }

  useEffect(() => {
    SubscriptionPlansService.readSubscriptionPlans({ onlyActive: true })
      .then((response: SubscriptionPlansPublic) => {
        if (response.plans) {
          setPlans(response.plans);
        }
      })
      .catch((err: any) => {
        console.error("Error fetching subscription plans", err);
        setError("Failed to load subscription plans");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
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
            badge,
            has_discount,
            price_without_discount,
            is_active,
            metric_type,
            benefits,
          } = plan;

          const commonProps = {
            key: id,
            title: name,
            price: price,
            benefits: benefits ? benefits.map((b) => b.name) : [],
            buttonText: "Get Started",
            buttonLink: "/signup",
            disabled: !is_active,
            hasDiscount: has_discount,
            priceWithoutDiscount: price_without_discount,
            recurrence: metric_type,
          };

          if (has_badge) {
            return <BadgePricingCard {...commonProps} badge={badge} />;
          } else {
            return <NormalPricingCard {...commonProps} />;
          }
        })}
      </div>
    </div>
  );
};
