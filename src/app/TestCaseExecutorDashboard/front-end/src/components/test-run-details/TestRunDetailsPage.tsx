import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import styles from "./TestRunDetails.module.css";
import Modal from "./Modal";
import RunTimeline from "./RunTimeline";
import DetailCard from "../common/DetailCard/DetailCard";
import Filters from "./Filters";
import RunDetailsFilters from "../common/Filters/FiltersRunDet";


/* ======================
   TYPES
====================== */

interface RunSummary {
  run_id: number;
  run_name: string;
  target: string | null;
  domain: string | null;
  status: string;
  start_ts: string;
  end_ts: string | null;
}

interface RunDetail {
  detail_id: number;
  run_name: string;
  testcase_name: string;
  metric_name: string;
  plan_name: string;
  conversation_id: string;
  status: string;
  score?: number | null;
}

interface RunDetailsResponse {
  summary: RunSummary;
  details: RunDetail[];
}
interface FilterOption {
  filter_name: string;
}

interface AllFilters {
  metrics: FilterOption[];
  statuses: FilterOption[];
}
/* ======================
   COMPONENT
====================== */

const RunDetails: React.FC = () => {
  const { runName } = useParams<{ runName: string }>();

  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [details, setDetails] = useState<RunDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);
  const [hoveredPlan, setHoveredPlan] = useState<string | null>(null);
  const [filtersData, setFiltersData] = useState<AllFilters>({
    metrics: [],
    statuses: [],
  });

  const [activeFilters, setActiveFilters] = useState<{
    metric?: string;
    status?: string;
  }>({});
  useEffect(() => {
    console.log("🔴 hoveredMetric changed to:", hoveredMetric);
  }, [hoveredMetric]);

  useEffect(() => {
    console.log("🔵 hoveredPlan changed to:", hoveredPlan);
  }, [hoveredPlan]);
  const statusMap = (status: string | null | undefined): "COMPLETED" | "RUNNING" | "FAILED" | undefined => {
    if (status === "COMPLETED" || status === "RUNNING" || status === "FAILED") return status;
    return undefined;
  };
   const handleFilterChange = (
    filterType: "metric" | "status",
    value: string
  ) => {
    setActiveFilters((prev) => {
      if (!value) {
        const copy = { ...prev };
        delete copy[filterType];
        return copy;
      }
      return { ...prev, [filterType]: value };
    });
  };

  useEffect(() => {
    fetch("http://localhost:7000/get_all_filters")
      .then((res) => res.json())
      .then((data) => {
        setFiltersData({
          metrics: data.metrics,
          statuses: data.statuses,
        });
      })
      .catch(console.error);
  }, []);

  /* ======================
     FETCH RUN DETAILS
  ====================== */

  useEffect(() => {
    if (!runName) return;

    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (activeFilters.metric) params.append("metric", activeFilters.metric);
    if (activeFilters.status) params.append("status", activeFilters.status);

    fetch(
      `http://localhost:7000/test-runs/${encodeURIComponent(
        runName
      )}?${params.toString()}`
    )
      .then((res) => {
        if (!res.ok) throw new Error(`API ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setSummary(data.summary);
        setDetails(data.details);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [runName, activeFilters]);
  /* ======================
     STATES
  ====================== */

  if (loading) return <p className={styles.loading}>Loading test run...</p>;
  if (error) return <p className={styles.error}>{error}</p>;
  if (!summary) return <p>No test run found</p>;

  const durationSeconds =
    summary.end_ts
      ? Math.round(
          (new Date(summary.end_ts).getTime() -
            new Date(summary.start_ts).getTime()) / 1000
        )
      : null;

  /* ======================
     UI
  ====================== */

  // Group details by plan name
  const groupedByPlan = details.reduce((acc, detail) => {
    if (!acc[detail.plan_name]) {
      acc[detail.plan_name] = [];
    }
    acc[detail.plan_name].push(detail);
    return acc;
  }, {} as Record<string, RunDetail[]>);
  
  const planNames = Object.keys(groupedByPlan);

  return (
    <div className={styles.container}>
      {/* Header Section */}
      <div className={styles.summaryCard}>
        <div className={styles.headerRow}>
          <h1 className={styles.title}>
            {summary.run_name}
          </h1>
          {/* {planNames.length > 0 && (
            <div className={styles.planBadge}>
              <i className="bi-journal-text"></i>
              {planNames.length === 1 ? planNames[0] : `${planNames.length} Plans`}
            </div>
          )} */}
        </div>

        <div className={styles.detailsGrid}>
          <DetailCard
            label="Target"
            value={summary.target ?? "-"}
            icon="bi-bullseye"
          />
          <DetailCard
            label="Domain"
            value={summary.domain ?? "-"}
            icon="bi-globe"
          />
          <DetailCard
            label="Status"
            value={summary.status}
            status={statusMap(summary.status)}
            icon="bi-activity"
          />
          <DetailCard
            label="Started At"
            value={new Date(summary.start_ts).toLocaleString()}
            icon="bi-calendar-event"
          />
          <DetailCard
            label="Ended At"
            value={summary.end_ts ? new Date(summary.end_ts).toLocaleString() : "-"}
            icon="bi-calendar-check"
          />
          <DetailCard
            label="Duration"
            value={durationSeconds !== null ? `${durationSeconds}s` : "-"}
            icon="bi-clock"
          />
        </div>
      </div>

      {/* Timeline Section */}
      <RunTimeline 
        runName={summary.run_name} 
        hoveredMetric={hoveredMetric}
        hoveredPlan={hoveredPlan}
        onHoverPlan={setHoveredPlan}
        onHoverMetric={setHoveredMetric} 
        
      />

      {/* Filters Section */}
      <div className={styles.filtersContainer}>
        <div className={styles.filtersCard}>
          <h2 className={styles.filtersTitle}>
            <i className="bi-funnel"></i>
            Filter Results
          </h2>
          <RunDetailsFilters
            metrics={filtersData.metrics}
            statuses={filtersData.statuses}
            loading={loading}
            activeFilters={activeFilters}
            onFilterChange={handleFilterChange}
          />
        </div>
      </div>

      {/* Table Section */}
       <section className={styles.tableSection}>
  <div className={styles.tableContainer}>
    <div className="table-responsive">
      <table className="table table-bordered table-hover">
        <thead>
          <tr>
            <th style={{ width: '20%' }}>Plan Name</th>
            <th>Test Case</th>
            <th>Metric</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {details.length === 0 ? (
            <tr>
              <td colSpan={5} className="text-center py-4 text-muted">
                No test case details found
              </td>
            </tr>
          ) : (
            Object.entries(groupedByPlan).flatMap(([planName, planDetails]) =>
              planDetails.map((d, index) => {
                // ✅ Log info when rendering each row
                console.log("Rendering rowwwwww:", d.metric_name, "Hovered metric:", hoveredMetric);

                return (
                  <tr
                    key={d.detail_id}
                    role="button"
                    className={`cursor-pointer ${
                      hoveredMetric === d.metric_name ? styles.metricRowHover : ""
                    }`}
                    data-bs-toggle="modal"
                    data-bs-target="#conversationModal"
                    onClick={() => setSelectedConversationId(Number(d.conversation_id))}
                    onMouseEnter={() => {
                      console.log("Mouse enter row:", d.metric_name);
                      setHoveredMetric(d.metric_name);
                    }}
                    onMouseLeave={() => {
                      console.log("Mouse leave row:", d.metric_name);
                      setHoveredMetric(null);
                    }}
                  >
                    {/* <td >{`Metric: ${d.metric_name}, Hovered: ${hoveredMetric}, Match: ${hoveredMetric === d.metric_name}, ClassName: ${hoveredMetric === d.metric_name ? styles.metricRowHover : "NONE"}`}</td> */}
                    {index === 0 && (
                      <td
                        rowSpan={planDetails.length}
                        className={`${styles.planCell} align-middle text-center`}
                        style={{
                          fontWeight: 500,
                          borderRight: '1px solid #e2e8f0',
                          minWidth: '200px',
                        }}
                      >
                        {planName}
                      </td>
                    )}
                    <td className="font-medium text-gray-900">{d.testcase_name}</td>
                    <td className="text-gray-700">{d.metric_name}</td>
                    <td className="font-medium text-gray-900">{d.score ?? "-"}</td>
                    <td>
                      <span
                        className={`${styles.statusCell} ${
                          d.status === "Completed"
                            ? styles.statusCompleted
                            : d.status === "FAILED"
                            ? styles.statusFailed
                            : styles.statusRunning
                        }`}
                      >
                        {d.status.toLowerCase()}
                      </span>
                    </td>
                  </tr>
                );
              })
            )
          )}
        </tbody>
      </table>
    </div>
  </div>
</section>

      <Modal conversationId={selectedConversationId} />
    </div>
  );
};

export default RunDetails;