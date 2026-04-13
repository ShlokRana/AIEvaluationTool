import React, { useEffect, useState } from "react";
import "./Filters.css";
import { AllFilters } from "../../types/Filters";
import { useNavigate } from "react-router-dom";
import FilterSelect from "../common/Filters/Filters";
import AppButton from "../common/Button/AppButton";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";
import { redirectToLogin } from "../../utils/auth";
interface FiltersProps {
  onFilterChange?: (filterType: string, value: string) => void;
}

const Filters: React.FC<FiltersProps> = ({ onFilterChange }) => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<AllFilters>({
    domains: [],
    languages: [],
    targets: [],
    plans: [],
    metrics: [],
    statuses: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const getAuthHeaders = (): HeadersInit => {
    const token = localStorage.getItem("access_token");
    return token
      ? {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        }
      : {
          "Content-Type": "application/json",
        };
  };


  useEffect(() => {
    setIsLoading(true);
    fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_ALL_FILTERS}`, {
      headers: getAuthHeaders(),
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) {
          redirectToLogin();
          throw new Error("Unauthorized");
        }
        if (!res.ok) {
          throw new Error(`Failed to fetch filters (${res.status})`);
        }
        return res.json();
      })
      .then((data: AllFilters) => {
        setFilters(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching filters:", err);
        setIsLoading(false);
      });
  }, []);

  const filterConfigs = [
    { type: "domain", label: "Domain", options: filters.domains },
    { type: "target", label: "Target", options: filters.targets },
    { type: "status", label: "Status", options: filters.statuses },
  ];

  return (
    <div className={`filtersContainer ${isLoading ? 'isFetching' : ''}`}>
      {/* <div className="filtersList">
        {filterConfigs.map((config) => (
          <div key={config.type} className="filterWrapper withIcon"> */}
            {/* This SVG now sits inside the wrapper */}
            {/* <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2.5" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="innerFilterIcon"
            >
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
            <FilterSelect
              filterType={config.type}
              placeholder={config.label}
              options={config.options}
              isLoading={isLoading}
              onChange={onFilterChange}
            />
          </div>
        ))}

      </div> */}
    </div>
    
    
  );
};

export default Filters;
