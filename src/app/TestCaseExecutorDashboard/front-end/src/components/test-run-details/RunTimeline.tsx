import React, { useEffect, useState } from "react";
import styles from "./runtimeline.module.css";
import { API_ENDPOINTS } from "../../config/api";
import { redirectToLogin } from "../../utils/auth";

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
  hoveredPlan?: string | null;
  onHoverPlan?: (plan: string | null) => void;
  onHoverMetric: (metric: string | null) => void;
  onDurationCalculated?: (duration: string) => void;
}

/* ===== COMPONENT ===== */

const RunTimeline: React.FC<Props> = ({ runName, hoveredMetric, onHoverMetric, onDurationCalculated }) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);

  const getAuthHeaders = (): HeadersInit => {
    const token = localStorage.getItem("access_token");
    return token
      ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
      : { "Content-Type": "application/json" };
  };

  useEffect(() => {
    fetch(API_ENDPOINTS.GET_TIMELINE(runName), {
      headers: getAuthHeaders(),
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) {
          redirectToLogin();
          throw new Error("Unauthorized");
        }
        return res.json();
      })
      .then(setEvents);
  }, [runName]);

  /* ================= CALCULATE TOTAL EXECUTION TIME ================= */

  useEffect(() => {
    if (!events.length) return;

    const eventsByPlan = events.reduce<Record<string, TimelineEvent[]>>((acc, e) => {
      acc[e.plan_name] ||= [];
      acc[e.plan_name].push(e);
      return acc;
    }, {});

    let totalMs = 0;

    Object.values(eventsByPlan).forEach(planEvents => {
      const start = Math.min(...planEvents.map(e => new Date(e.prompt_ts!).getTime()));
      const end = Math.max(...planEvents.map(e => new Date(e.response_ts!).getTime()));
      totalMs += (end - start);
    });

    const formatted = formatDuration(totalMs);
    onDurationCalculated?.(formatted);
  }, [events, onDurationCalculated]);

  if (events.length === 0) return null;

  /* ================= GROUP INTO SEQUENTIAL PLAN BLOCKS ================= */
  // Sort ALL events by prompt time first
  const sortedEvents = [...events].sort(
    (a, b) => new Date(a.prompt_ts!).getTime() - new Date(b.prompt_ts!).getTime()
  );

  // Split into blocks: same plan name with a significant time gap = new block
  const GAP_THRESHOLD_MS = 5000; // 5 seconds

  const planBlocks: { key: string; name: string; events: TimelineEvent[] }[] = [];

  for (const event of sortedEvents) {
    const last = planBlocks[planBlocks.length - 1];
    const eventTime = new Date(event.prompt_ts!).getTime();

    if (last && last.name === event.plan_name) {
      const lastResponseTime = Math.max(
        ...last.events.map(e => new Date(e.response_ts!).getTime())
      );
      if (eventTime - lastResponseTime < GAP_THRESHOLD_MS) {
        // Continuous run — same block
        last.events.push(event);
        continue;
      }
    }

    // New block (different name, or same name after a gap)
    const count = planBlocks.filter(b => b.name === event.plan_name).length;
    planBlocks.push({
      key: `${event.plan_name}__${count}`,
      name: event.plan_name,
      events: [event],
    });
  }

  const eventsByPlan: Record<string, TimelineEvent[]> = Object.fromEntries(
    planBlocks.map(b => [b.key, b.events])
  );
  const planDisplayNames: Record<string, string> = Object.fromEntries(
    planBlocks.map(b => [b.key, b.name])
  );
  const planNames = planBlocks.map(b => b.key);

  if (planNames.length === 0) return null;

  /* ================= CALCULATE GAPS BETWEEN BLOCKS ================= */
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
      <div className={styles.timelineHeader} />

      <div className={styles.planRow}>
        {planNames.map((planKey, index) => {
          const planEvents = eventsByPlan[planKey];

          const start = Math.min(...planEvents.map(e => new Date(e.prompt_ts!).getTime()));
          const end = Math.max(...planEvents.map(e => new Date(e.response_ts!).getTime()));
          const total = end - start || 1;

          if (total <= 0) return null;

          return (
            <React.Fragment key={planKey}>
              <div className={styles.planBlock}>
                <div className={styles.planHeader}>
                  {planDisplayNames[planKey]}
                  <div className={styles.duration}>{formatDuration(total)}</div>
                </div>

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
                        onMouseEnter={() => onHoverMetric(e.metric_name)}
                        onMouseLeave={() => onHoverMetric(null)}
                      />
                    );
                  })}
                </div>

                <div className={styles.scale}>
                  {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
                    <div
                      key={i}
                      className={styles.scaleItem}
                      style={{ left: `${p * 100}%` }}
                    >
                      {p === 0 ? "0" : formatDuration(total * p)}
                    </div>
                  ))}
                </div>
              </div>

              {index < planNames.length - 1 && (
                <div
                  className={styles.planConnector}
                  data-gap={`${formatDuration(planGaps[index])} gap`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

function formatDuration(ms: number): string {
  if (!ms || ms < 0) return "-";
  const totalSeconds = Math.floor(ms / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default RunTimeline;