import React from "react";
import "./DetailCard.css";

interface DetailCardProps {
  label: string;
  value: string | number | React.ReactNode;
  icon?: string; // bootstrap icon class e.g., "bi-bullseye"
  status?: "COMPLETED" | "RUNNING" | "FAILED"; // only for Status card
  className?: string;
}

const DetailCard: React.FC<DetailCardProps> = ({
  label,
  value,
  icon,
  status,
  className = "",
}) => {
  const getStatusClass = () => {
    switch (status) {
      case "COMPLETED":
        return "status-completed";
      case "RUNNING":
        return "status-running";
      case "FAILED":
        return "status-failed";
      default:
        return "";
    }
  };

  return (
    <div className={`detail-card ${className}`}>
      <div className="detail-label">
        {icon && <i className={`bi ${icon} me-2`}></i>}
        {label}
      </div>
      <div className={`detail-value ${status ? getStatusClass() : ""}`}>
        {value ?? "-"}
      </div>
    </div>
  );
};

export default DetailCard;
