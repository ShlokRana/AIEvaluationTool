import React,{useState, useEffect} from 'react';
import './NewTestRunPage.css';

// Import only the Bootstrap CSS for the select components

import CustomSelect from './CustomSelect/CustomSelect';
import Loop from './Loop/Loop';

interface RunFormData {
  runName?: string;   // 👈 add this
  target: string;
  testPlan: string; 
  testCaseId: string ;
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

const NewTestRunPage: React.FC = () => {
  // Sample data for dropdowns
  // const targets = ['Vaidya AI', 'Target 2', 'Target 3'];
  const testPlans = ['Plan 1', 'Plan 2', 'Plan 3'];
  const metrics = ['Accuracy', 'Precision', 'Recall', 'F1 Score'];
  const maxTestCases = ['10', '20', '30', '50', '100'];
  const domains = ['E-commerce', 'Healthcare', 'Finance', 'Education'];
  const languages = ['Tamil', 'Hindi', 'Assamese', 'Bengali', 'Sindhi', 'Bodo'];
  const [isRunning, setIsRunning] = useState(false);
  const [totalTestCases, setTotalTestCases] = useState(0);
  const [filters, setFilters] = useState<AllFiltersResponse | null>(null);
  const [planMetrics, setPlanMetrics] = useState<string[]>([]);
  
  const [formData, setFormData] = useState<RunFormData>({
    runName: "",   
    target: "",
    testPlan: "",
    testCaseId:"",
    metric: "",
    maxTestCases: "10", 
    domain: "",
    language: "",
  });
  const isStartDisabled = !formData.testPlan || !formData.target  || isRunning
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
    e.preventDefault();
    setIsRunning(true); 
    const res = await fetch("http://localhost:7000/start-run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    const runData = await res.json(); // <-- this should now include runName, runId, testPlanId, metricId
    console.log("POST /start-run response:", runData);
    setTotalTestCases(runData.totalTestCases);
    setIsRunning(true); // now we can start the Loop component

    // 2️⃣ Open WebSocket to get live updates
    const ws = new WebSocket("ws://localhost:7000/ws/test-run");

    ws.onopen = () => {
      console.log("WebSocket connected, sending run info");
      ws.send(JSON.stringify(runData)); // send metric_id, runId, etc.
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data); // backend sends JSON updates
      console.log("Update from backend:", data);

      // Example: if backend sends total_test_cases
      // setTotalTestCases(data.total);
      // setCurrentTestCase(data.current);
  };

  ws.onclose = () => {
    console.log("WebSocket closed");
  };
  };

  return (
    <div className="new-test-run-container">
      <h1>Create New Test Run</h1>
      <p className="subtitle">Configure and start AI evaluation run</p>
      
      

      <form className="filters-container" onSubmit={handleSubmit}>
        <div className="form-group">
        <label>Test Run Name</label>
        <input 
          type="text" 
          className="form-input" 
          placeholder="Enter run name (optional)"
          value={formData.runName}
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
              type="text"
              placeholder="Enter Test Plan ID"
              value={formData.testCaseId?? ""}
              disabled={!formData.testPlan}
              onChange={(e) =>
                handleChange("testCaseId", e.target.value)
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
      {isRunning && <Loop isRunning={isRunning} totalTestCases={totalTestCases} stepsPerTestCase={4} stepNames={["Prepare", "Finding elements", "Execute", "Store"]}/>}       
      
    </div>
  );
};

export default NewTestRunPage;