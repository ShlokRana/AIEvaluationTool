import React,{useState, useEffect} from 'react';
import './ContinueTestRunPage.css';

// Import only the Bootstrap CSS for the select components

import CustomSelect from './CustomSelect/CustomSelect';
import Loop from './Loop/Loop';

interface RunFormData {
  runName: string;   // ✅ add this
  target: string;
  testPlan: string; 
  testCaseId: number | null;
  metric: string;     // ✅ name
  maxTestCases: string;
  domain: string;
  language: string;
}

interface FilterItem {
  filter_name: string;
}

interface AllFiltersResponse {
  domains: FilterItem[];
  languages: FilterItem[];
  targets: FilterItem[];
  plans: FilterItem[];
  metrics: FilterItem[];
  statuses: FilterItem[];
}

const ContinueRunPage: React.FC = () => {
  // Sample data for dropdowns
  // const targets = ['Vaidya AI', 'Target 2', 'Target 3'];
  const testPlans = ['Plan 1', 'Plan 2', 'Plan 3'];
  const metrics = ['Accuracy', 'Precision', 'Recall', 'F1 Score'];
  const maxTestCases = ['10', '20', '30', '50', '100'];
  const domains = ['E-commerce', 'Healthcare', 'Finance', 'Education'];
  const languages = ['English', 'Spanish', 'French', 'German', 'Chinese'];
  const [isRunning, setIsRunning] = useState(false);
  const [totalTestCases, setTotalTestCases] = useState(0);
  const [filters, setFilters] = useState<AllFiltersResponse | null>(null);
  const [planMetrics, setPlanMetrics] = useState<string[]>([]);
  
  const [formData, setFormData] = useState<RunFormData>({
    runName:"",   // ✅ initialize this
    target: "",
    testPlan: "",
    testCaseId:null,
    
    metric: "",
    maxTestCases: "10", // 👈 default selected
    domain: "",
    language: "",
  });
  const isStartDisabled = !formData.testPlan || isRunning
  useEffect(() => {
  const fetchFilters = async () => {
    try {
      const res = await fetch("http://localhost:7000/get_all_filters");
      const data: AllFiltersResponse = await res.json();
      setFilters(data);
    } catch (err) {
      console.error("Failed to fetch filters", err);
    }
  };

  fetchFilters();
}, []);
const fetchMetricsByPlan = async (planName: string) => {
  try {
    const res = await fetch(
      `http://localhost:7000/get_metrics_by_plan/${planName}`
    );
    const data = await res.json();
    setPlanMetrics(data.map((m: any) => m.filter_name));
  } catch (err) {
    console.error("Failed to fetch metrics", err);
    setPlanMetrics([]);
  }
};
const handleChange = (key: string, value: any) => {
  setFormData(prev => ({
    ...prev,
    [key]: value,
    ...(key === "testPlan" && { metric: "" })
  }));

  if (key === "testPlan") {
    fetchMetricsByPlan(value); // 🔥 second fetch happens here
  }
};

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();  // 🚨 VERY IMPORTANT

  console.log("Submitting run name:", formData.runName);

  try {
    const res = await fetch("http://localhost:7000/continue-run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        run_name: formData.runName,
      }),
    });

    if (!res.ok) {
      console.error("Run not found");
      return;
    }

    const data = await res.json();
    console.log("Continue Run Response:", data);

  } catch (err) {
    console.error("Error:", err);
  }
};  

  return (
    <div className="new-test-run-container">
      <h1>Continue Test Run</h1>
      <p className="subtitle">Configure and start AI evaluation run</p>
      
      

      <form className="filters-container" onSubmit={handleSubmit}>
        <div className="form-group">
        <label>Test Run Name</label>
        <input 
          type="text" 
          className="form-input" 
          defaultValue="Regression test" 
          onChange={(e) => handleChange("runName", e.target.value)}
        />
      </div>
        <div className="filters-row">
          <div className="filter-item">
            <label>Target</label>
            <CustomSelect
              options={filters?.targets.map(t => t.filter_name) ?? []}
              defaultText="Select Target"
              onChange={(val) => handleChange("target", val)}
            />
          </div>

          <div className="filter-item">
            <label>Test Plan</label>
            <CustomSelect
              options={filters?.plans.map(p => p.filter_name) ?? []}
              defaultText="Select Test Plan"
              onChange={(val) => handleChange("testPlan", val)}
            />
          </div>
          <div className="filter-item">
            <label>Test Case ID</label>
            <input
              type="number"
              placeholder="Enter Test Plan ID"
              value={formData.testCaseId?? ""}
              disabled={!formData.testPlan}
              onChange={(e) =>
                handleChange("testCaseId", Number(e.target.value))
              }
            />
          </div>

          <div className="filter-item">
            <label>Metric </label>
            <CustomSelect
              options={planMetrics}
              defaultText={
                formData.testPlan ? "Select Metric" : "Select Test Plan first"
              }
              
              disabled={!formData.testPlan}
              onChange={(val) => handleChange("metric", val)}
            />
          </div>
        </div>

        <div className="filters-row">
          <div className="filter-item">
            <label>Max test cases</label>
            <CustomSelect
              options={maxTestCases}
              defaultText="Select Max"
              onChange={(val) => handleChange("maxTestCases", val)}
            />
          </div>

          <div className="filter-item">
            <label>Domain</label>
            <CustomSelect
              options={filters?.domains.map(p => p.filter_name) ?? []}
              defaultText="Select Domain"
              onChange={(val) => handleChange("domain", val)}
            />
          </div>

          <div className="filter-item">
            <label>Language</label>
            <CustomSelect
              options={languages}
              defaultText="Select Language"
              onChange={(val) => handleChange("language", val)}
            />
          </div>
        </div>

        <button type="submit" className="start-button" disabled={isStartDisabled}>
          Start Run
        </button>
      </form>
      
      
    </div>
  );
};

export default ContinueRunPage;