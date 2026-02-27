import React, { useEffect, useState, useMemo } from "react";
import styles from "./runtimeline.module.css";

/* ===== TYPES ===== */

interface TimelineEvent {
  conversation_id: number;
  metric_name: string;
  plan_name: string;
  prompt_ts: string | null;
  response_ts: string | null;
}

interface Props {
  runName: string;
  hoveredMetric: string | null;
  hoveredPlan?: string | null;        // Make optional with ?
  onHoverPlan?: (plan: string | null) => void;  // Make optional with ?
  onHoverMetric: (metric: string | null) => void; // ✅ ADD
}

/* ===== COMPONENT ===== */

const RunTimeline: React.FC<Props> = ({ runName, hoveredMetric, onHoverMetric }) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);

  useEffect(() => {
    fetch(`http://localhost:7000/test-runs/${runName}/timeline`)
      .then(res => res.json())
      .then(setEvents);
  }, [runName]);

  if (events.length === 0) return null;

  // Always show all plans
  const filteredEvents = events;

  // Group by plan and sort events by prompt time
  const eventsByPlan = filteredEvents.reduce<Record<string, TimelineEvent[]>>(
    (acc, e) => {
      acc[e.plan_name] ||= [];
      acc[e.plan_name].push(e);
      return acc;
    },
    {}
  );

  // Sort events within each plan by prompt time
  Object.values(eventsByPlan).forEach(planEvents =>
    planEvents.sort(
      (a, b) =>
        new Date(a.prompt_ts!).getTime() -
        new Date(b.prompt_ts!).getTime()
    )
  );

  const planNames = Object.keys(eventsByPlan);
  if (planNames.length === 0) return null;

  // Calculate time gaps between plans
  const planGaps = planNames.slice(0, -1).map((plan, i) => {
    const currentPlan = eventsByPlan[plan];
    const nextPlan = eventsByPlan[planNames[i + 1]];
    
    if (!currentPlan.length || !nextPlan.length) return 0;
    
    const lastEventOfCurrent = currentPlan.reduce((latest, event) => {
      const time = new Date(event.response_ts!).getTime();
      return time > latest ? time : latest;
    }, 0);
    
    const firstEventOfNext = nextPlan.reduce((earliest, event) => {
      const time = new Date(event.prompt_ts!).getTime();
      return time < earliest ? time : earliest;
    }, Infinity);
    
    return firstEventOfNext - lastEventOfCurrent;
  });

  return (
    <div className={styles.timelineCard}>
      <div className={styles.timelineHeader}>
        <h3>Execution Timeline</h3>
      </div>
      {/* HEADER */}

      {/* HORIZONTAL ROW (SCROLLS, STICKY SAFE) */}
      <div className={styles.planRow}>
        {planNames.map((plan, index) => {
          const planEvents = eventsByPlan[plan];

          const start = Math.min(
            ...planEvents.map(e => new Date(e.prompt_ts!).getTime())
          );
          const end = Math.max(
            ...planEvents.map(e => new Date(e.response_ts!).getTime())
          );
          const total = end - start || 1;

          return (
            <React.Fragment key={plan}>
              {/* PLAN BLOCK */}
              <div className={styles.planBlock}>
                <div className={styles.planHeader}>
                  {plan}
                  <div className={styles.duration}>
                    {formatDuration(total)}
                  </div>
                </div>

                {/* TIMELINE */}
                <div className={styles.timeline}>
                  {planEvents.map(e => {
                    const prompt = new Date(e.prompt_ts!).getTime();
                    const response = new Date(e.response_ts!).getTime();

                    const left = ((prompt - start) / total) * 100;
                    const width = ((response - prompt) / total) * 100;

                    return (
                      <div
                        key={e.conversation_id}
                        className={styles.block}
                        style={{
                          left: `${left}%`,
                          width: `${width}%`,
                          opacity:
                            hoveredMetric === null
                              ? 0.3
                              : hoveredMetric === e.metric_name
                              ? 1
                              : 0.25,
                        }}
                        onMouseEnter={() => onHoverMetric(e.metric_name)} // update parent state
                        onMouseLeave={() => onHoverMetric(null)} 
                        />
                    );
                  })}
                </div>

                {/* SCALE */}
                <div className={styles.scale}>
                  {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
                    <div
                      key={i}
                      className={styles.scaleItem}
                      style={{ left: `${p * 100}%` }}
                    >
                      {Math.round((total * p) / 1000)}s
                    </div>
                  ))}
                </div>
              </div>

              {/* DOTTED GAP - Only show on hover */}
              {index < planNames.length - 1 && (
                <div 
                  className={styles.planConnector}
                  data-gap={`${(planGaps[index] / 1000).toFixed(2)}s gap`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

// Helper function to format duration in a human-readable way
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  
  if (seconds < 1) return '<1s';
  if (seconds < 60) return `${seconds}s`;
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  
  if (minutes < 60) {
    return remainingSeconds > 0 
      ? `${minutes}m ${remainingSeconds}s`
      : `${minutes}m`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  return remainingMinutes > 0
    ? `${hours}h ${remainingMinutes}m`
    : `${hours}h`;
}

// Alias for backward compatibility
const formatTimeGap = formatDuration;

export default RunTimeline;