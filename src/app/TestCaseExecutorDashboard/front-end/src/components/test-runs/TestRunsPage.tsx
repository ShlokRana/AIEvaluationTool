import React, { useState } from "react";
import Header from "./Header";
import Filters from "./Filters";
import TestRunsTable from "./TestRunsTable";
import "./TestRunsPage.css";

const TestRunsPage: React.FC = () => {
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  const handleFilterChange = (filterType: string, value: string) => {
    setActiveFilters(prev => {
      if (!value) {
        const updated = { ...prev };
        delete updated[filterType];
        return updated;
      }

      return { ...prev, [filterType]: value };
    });
  };

  return (
    <div className="page-container">
      {/* <div className="header-container">
        <Header />
      </div> */}
      <Header />
      <Filters onFilterChange={handleFilterChange} />
      <TestRunsTable filters={activeFilters} onFilterChange={handleFilterChange} />
    </div>
  );
};

export default TestRunsPage;
