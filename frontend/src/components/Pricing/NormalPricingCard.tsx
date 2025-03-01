import type React from "react"

interface NormalPricingCardProps {
  title: string
  price: number
  recurrence: string
  benefits: string[]
  buttonText: string
  buttonEnabled?: boolean
  buttonLink: string
  disabled?: boolean
  hasDiscount?: boolean
  priceWithoutDiscount?: number
}

const NormalPricingCard: React.FC<NormalPricingCardProps> = ({
  title,
  price,
  recurrence,
  benefits,
  buttonText,
  buttonEnabled,
  buttonLink,
  disabled = false,
  hasDiscount = false,
  priceWithoutDiscount,
}) => {
  return (
    <div
      style={{
        backgroundColor: "#fff",
        ...(disabled
          ? { boxShadow: "0 4px 10px rgba(0,0,0,0.2)" }
          : { boxShadow: "0 4px 10px rgba(0,0,0,0.1)" }),
        borderRadius: "20px",
        width: "300px",
        minWidth: "300px",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        ...(disabled ? { filter: "blur(5px)", pointerEvents: "none" } : {}),
      }}
    >
      <div>
        <h3
          style={{
            fontSize: "24px",
            fontWeight: 600,
            marginBottom: "10px",
            color: "#2d3748",
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
            color: "#2d3748",
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
                fill="#000000"
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
        href={buttonEnabled ? buttonLink : undefined}
        onClick={buttonEnabled ? undefined : (e) => e.preventDefault()}
        style={{
          display: "block",
          textAlign: "center",
          backgroundColor: "#3a3a3a",
          color: "#fff",
          padding: "12px",
          borderRadius: "4px",
          marginTop: "24px",
          textDecoration: "none",
          fontWeight: 600,
          // Cursor "not-allowed" indica visualmente que o link está desabilitado.
          cursor: buttonEnabled ? "pointer" : "not-allowed",
          // Opacidade menor quando desabilitado.
          opacity: buttonEnabled ? 1 : 0.5,
          // pointerEvents "none" impede qualquer interação no estado desabilitado.
          pointerEvents: buttonEnabled ? "auto" : "none",
        }}
      >
        {buttonText}
      </a>
    </div>
  )
}

export default NormalPricingCard
