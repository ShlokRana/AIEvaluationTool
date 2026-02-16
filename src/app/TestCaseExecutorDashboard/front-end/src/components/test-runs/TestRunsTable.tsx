import React, { useEffect, useState, useMemo } from "react";
import "./TestRunsTable.css";
import { useNavigate } from "react-router-dom";
import AppButton from "../common/Button/AppButton";
import { Pagination } from "react-bootstrap";

// Define the structure of a test run (for future use)
interface TestRun {
  run_id: number;
  run_name: string;
  target: string;
  status: string;
  start_ts: string;
  end_ts: string | null;
  domain: string;
  
}

interface Props {
  filters: Record<string, string>; // e.g. { domain: "qaoncloud.com", target: "api" }
}

const TestRunsTable: React.FC<Props> = ({filters}) => {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [filteredRuns, setFilteredRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  // Table headers
  const headers = [
    "Run Id", "Run Name", "Target", "Started At","Ended At", 
    "Duration", "Status", "Domain",  "Report"
  ];

  // Get Data from backend
  useEffect(() => {
    setLoading(true);
    
    const params = new URLSearchParams(filters).toString();
    const url = `http://localhost:7000/get_all_test_runs?${params}`;
    
    fetch(url)
      .then(res => res.json())
      .then((data: TestRun[]) => {
        setRuns(data);
        setFilteredRuns(data);
        setCurrentPage(1); // Reset to first page when filters change
      })
      .catch(err => console.error("Error fetching test runs:", err))
      .finally(() => setLoading(false));
  }, [filters]);

  // Get current runs
  const indexOfLastRun = currentPage * itemsPerPage;
  const indexOfFirstRun = indexOfLastRun - itemsPerPage;
  const currentRuns = filteredRuns.slice(indexOfFirstRun, indexOfLastRun);
  const totalPages = Math.ceil(filteredRuns.length / itemsPerPage);

  // Change page
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  // Generate page numbers for pagination
  const pageNumbers = [];
  for (let i = 1; i <= totalPages; i++) {
    pageNumbers.push(i);
  }
  
  
  // Apply filters when they change
  // useEffect(() => {
  //   if (Object.keys(filters).length === 0) {
  //     setFilteredRuns(runs);
  //     return;
  //   }
    
  //   const filtered = runs.filter(run => {
  //     return Object.entries(filters).every(([key, value]) => {
  //       if (!value) return true;
        
  //       switch(key) {
  //         case 'domain':
  //           return run.domain.toLowerCase() === value.toLowerCase();
  //         case 'target':
  //           return run.target.toLowerCase() === value.toLowerCase();
  //         case 'language':
  //           // Assuming language might be in another property or needs special handling
  //           return true;
  //         default:
  //           return true;
  //       }
  //     });
  //   });
    
  //   setFilteredRuns(filtered);
  // }, [filters, runs]);
  return (
    <div>
      <div className="table-responsive table-container mb-3">
        <table className="table table-hover table-bordered align-middle mb-0">
          <thead className="table-light">
            <tr>
              {headers.map(header => (
                <th key={header} scope="col">
                  {header}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={headers.length} className="text-center py-4">
                  <div className="spinner-border spinner-border-sm me-2" role="status" />
                  Loading test runs...
                </td>
              </tr>
            ) : !Array.isArray(currentRuns) || currentRuns.length === 0 ? (
              <tr>
                <td colSpan={headers.length} className="text-center py-4 text-muted">
                  No test runs match the selected filters
                </td>
              </tr>
            ) : (
              currentRuns.map(run => (
      <tr
        key={run.run_id}
        role="button"
        className="cursor-pointer"
        onClick={() => navigate(`/test-runs/${run.run_name}`)}
      >
        <td>{run.run_id}</td>
        <td>{run.run_name}</td>
        <td>{run.target}</td>
        <td>{new Date(run.start_ts).toLocaleString()}</td>
        <td>{run.end_ts ? new Date(run.end_ts).toLocaleString() : "-"}</td>
        <td>
          {run.end_ts
            ? `${Math.round(
                (new Date(run.end_ts).getTime() -
                  new Date(run.start_ts).getTime()) / 1000
              )}s`
            : "-"}
        </td>
        <td>
          <span
            className={`badge ${
              run.status === "PASSED"
                ? "bg-success"
                : run.status === "FAILED"
                ? "bg-danger"
                : "bg-secondary"
            }`}
          >
            {run.status}
          </span>
        </td>
        <td>{run.domain}</td>
        <td onClick={e => e.stopPropagation()}>
          <AppButton
            label="Report"
            variant="outline-primary"
            size="sm"
            icon="bi-file-earmark-text"
            onClick={() => {
              const link = document.createElement("a");
              link.href = `http://localhost:7000/test-runs/${run.run_name}/evaluation-report`;
              link.setAttribute(
                "download",
                `${run.run_name}-evaluation.xlsx`
              );
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            }}
          /> 
        </td>
      </tr>
    ))
  )}
</tbody>
  </table>
  
</div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="d-flex justify-content-center">
          <Pagination className="mb-0">
            <Pagination.First 
              onClick={() => paginate(1)} 
              disabled={currentPage === 1} 
            />
            <Pagination.Prev 
              onClick={() => paginate(currentPage - 1)} 
              disabled={currentPage === 1} 
            />
            
            {pageNumbers.map(number => (
              <Pagination.Item 
                key={number} 
                active={number === currentPage}
                onClick={() => paginate(number)}
              >
                {number}
              </Pagination.Item>
            ))}
            
            <Pagination.Next 
              onClick={() => paginate(currentPage + 1)} 
              disabled={currentPage === totalPages} 
            />
            <Pagination.Last 
              onClick={() => paginate(totalPages)} 
              disabled={currentPage === totalPages} 
            />
          </Pagination>
        </div>
      )}
      
      <div className="text-muted text-center mt-2">
        Showing {currentRuns.length} of {filteredRuns.length} test runs
      </div>
    </div>

  );
};

export default TestRunsTable;
