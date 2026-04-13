import React, { Component } from 'react'

export default class PlanTimeline extends Component {
  render() {
    return (
      <div>PlanTimeline</div>
    )
  }
}


// import React from "react";
// import styles from "./runtimeline.module.css";

// /* ===== TYPES ===== */

// export interface TimelineEvent {
//   conversation_id: number;
//   metric_name: string;
//   plan_name: string;
//   prompt_ts: string | null;
//   response_ts: string | null;
// }

// interface Props {
//   planName: string;
//   events: TimelineEvent[];
//   hoveredMetric: string | null;
// }

// /* ===== COMPONENT ===== */

// const PlanTimeline: React.FC<Props> = ({
//   planName,
//   events,
//   hoveredMetric,
// }) => {
//   if (!events || events.length === 0) return null;

//   /* ---- TIME MATH (RESET PER PLAN) ---- */

//   const start = Math.min(
//     ...events.map(e => new Date(e.prompt_ts!).getTime())
//   );

//   const end = Math.max(
//     ...events.map(e => new Date(e.response_ts!).getTime())
//   );

//   const total = end - start || 1;

//   return (
//     <div className={styles.planBlock}>
//       {/* PLAN NAME */}
//       <div className={styles.planHeader}>{planName}</div>

//       {/* TIMELINE BAR */}
//       <div className={styles.timeline}>
//         {events.map(e => {
//           const prompt = new Date(e.prompt_ts!).getTime();
//           const response = new Date(e.response_ts!).getTime();

//           const left = ((prompt - start) / total) * 100;
//           const width = ((response - prompt) / total) * 100;

//           return (
//             <div
//               key={e.conversation_id}
//               className={styles.block}
//               style={{
//                 left: `${left}%`,
//                 width: `${width}%`,
//                 opacity:
//                   hoveredMetric === null
//                     ? 0.35
//                     : hoveredMetric === e.metric_name
//                     ? 1
//                     : 0.25,
//               }}
//             />
//           );
//         })}
//       </div>

//       {/* SCALE */}
//       <div className={styles.scale}>
//         {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
//           <div
//             key={i}
//             className={styles.scaleItem}
//             style={{ left: `${p * 100}%` }}
//           >
//             {Math.round((total * p) / 1000)}s
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// };

// export default PlanTimeline;
