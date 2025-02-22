import React from "react";

interface BadgePricingCardProps {
  title: string;
  badge: string;
  price: number;
  benefits: string[];
  buttonText: string;
  buttonLink: string;
  hasDiscount?: boolean;
  priceWithoutDiscount?: number;
  recurrence: string;
}

const BadgePricingCard: React.FC<BadgePricingCardProps> = ({
  title,
  badge,
  price,
  benefits,
  buttonText,
  buttonLink,
  hasDiscount = false,
  priceWithoutDiscount,
  recurrence,
}) => {
  return (
    <div
      style={{
        backgroundColor: "#fff",
        border: "1.5px solid #e2ffe0",
        borderRadius: "20px",
        width: "300px",
        boxShadow: "0 6px 10px rgba(0, 150, 136, 0.1)",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        position: "relative",
        minWidth: "300px",
      }}
    >
      {/* Best Value Badge */}
      <div
        style={{
          position: "absolute",
          top: "-12px",
          right: "-10px",
          backgroundColor: "#009688",
          color: "#fff",
          padding: "6px 8px",
          borderRadius: "4px",
          fontSize: "14px",
          fontWeight: 600,
        }}
      >
        {badge}
      </div>
      <div>
        <h3
          style={{
            fontSize: "24px",
            fontWeight: 600,
            marginBottom: "10px",
            color: "#00766c",
          }}
        >
          {title}
        </h3>
        {hasDiscount && priceWithoutDiscount !== undefined && (
          <p
            style={{
              fontSize: "14px",
              fontWeight: 400,
              color: "#a0aec0",
              textDecoration: "line-through",
            }}
          >
            ${priceWithoutDiscount.toFixed(2)}
          </p>
        )}
        <p
          style={{
            fontSize: "26px",
            fontWeight: 600,
            marginBottom: "20px",
            color: "#00766c",
          }}
        >
          ${price.toFixed(2)}/{recurrence}
        </p>
        <ul
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            color: "#4a5568",
          }}
        >
          {benefits.map((benefit, index) => (
            <li
              key={index}
              style={{
                marginBottom: "8px",
                display: "flex",
                alignItems: "center",
              }}
            >
              <svg
                width="16"
                height="16"
                fill="#48bb78"
                style={{ marginRight: "8px" }}
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 10-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z"
                  clipRule="evenodd"
                />
              </svg>
              {benefit}
            </li>
          ))}
        </ul>
      </div>
      <a
        href={buttonLink}
        style={{
          display: "block",
          textAlign: "center",
          backgroundColor: "#009688",
          color: "#fff",
          padding: "12px",
          borderRadius: "4px",
          marginTop: "24px",
          textDecoration: "none",
          fontWeight: 600,
        }}
      >
        {buttonText}
      </a>
    </div>
  );
};

export default BadgePricingCard;
