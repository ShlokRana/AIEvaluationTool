import React from "react";
import "./filterselect.css"


interface FilterOption {
  filter_name: string;
}

interface FilterSelectProps {
  placeholder: string;
  options: FilterOption[];
  filterType: string;
  isLoading?: boolean;
  multiple?: boolean; // 👈 optional
  onChange?: (filterType: string, value: string) => void;
}

const FilterSelect: React.FC<FilterSelectProps> = ({
  placeholder,
  options,
  filterType,
  isLoading = false,
  
  onChange,
}) => {
  return (
    <select
      className="filter"
      disabled={isLoading}
      
      defaultValue=""
      onChange={(e) => onChange?.(filterType, e.target.value)}
    >
      <option value="">
        Select {placeholder}
      </option>

      {options.map((opt) => (
        <option key={opt.filter_name} value={opt.filter_name}>
          {opt.filter_name}
        </option>
      ))}
    </select>
  );
};

export default FilterSelect;
