import React from "react";

type ButtonVariant =
  | "primary"
  | "secondary"
  | "success"
  | "danger"
  | "warning"
  | "info"
  | "light"
  | "dark"
  | "outline-primary"
  | "outline-secondary";

interface AppButtonProps{
    label: string;
    variant?: ButtonVariant;
    icon?: string;
    onClick?: () => void;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    minWidth?: number;
    maxWidth?: number;
    size?: "sm" | "md" | "lg";
    className?: string;
}
const AppButton: React.FC<AppButtonProps> = ({
  label,
  variant = "primary",
  icon,
  onClick,
  type = "button",
  disabled = false,
  minWidth = 120,
  maxWidth = 240,
  size = "md",
  className = "",
}) => {
  const sizeClass =
    size === "sm" ? "btn-sm" : size === "lg" ? "btn-lg" : "";

  return (
    <button
      type={type}
      className={`btn btn-${variant} ${sizeClass} d-inline-flex align-items-center gap-2 ${className}`}
      style={{
        minWidth,
        maxWidth,
        whiteSpace: "nowrap",
      }}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && <i className={`bi ${icon}`} />}
      <span className="text-truncate">{label}</span>
    </button>
  );
};

export default AppButton;