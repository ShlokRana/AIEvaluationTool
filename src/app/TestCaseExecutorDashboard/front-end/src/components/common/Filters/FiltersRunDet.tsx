import React from "react";
import "./filterselect.css";

interface FilterOption {
  filter_name: string;
}

interface RunDetailsFiltersProps {
  metrics: FilterOption[];
  statuses: FilterOption[];
  loading: boolean;
  activeFilters: {
    metric?: string;
    status?: string;
  };
  onFilterChange: (filterType: "metric" | "status", value: string) => void;
}

const RunDetailsFilters: React.FC<RunDetailsFiltersProps> = ({
  metrics,
  statuses,
  loading,
  activeFilters,
  onFilterChange,
}) => {
  return (
    <div className="filters">
      {/* METRIC FILTER */}
      <select
        className="filter"
        disabled={loading}
        value={activeFilters.metric ?? ""}
        onChange={(e) => onFilterChange("metric", e.target.value)}
      >
        <option value="">Select Metric</option>
        {metrics.map((m) => (
          <option key={m.filter_name} value={m.filter_name}>
            {m.filter_name}
          </option>
        ))}
      </select>

      {/* STATUS FILTER */}
      <select
        className="filter"
        disabled={loading}
        value={activeFilters.status ?? ""}
        onChange={(e) => onFilterChange("status", e.target.value)}
      >
        <option value="">Select Status</option>
        {statuses.map((s) => (
          <option key={s.filter_name} value={s.filter_name}>
            {s.filter_name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default RunDetailsFilters;
