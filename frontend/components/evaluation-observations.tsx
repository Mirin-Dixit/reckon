"use client";

import { useId, useState } from "react";
import type { Observation, Results } from "../lib/experiment-api";
import { filterObservations, observationCategory, observationOutcome, savedRetrievalRecall } from "../lib/evaluation-report";

export function OutcomeBreakdownChart({ observations }: { observations: Observation[] }) {
  const title = useId();
  if (!observations.length) return null;

  const policies = [...new Set(observations.map(o => o.policy_name))].sort();
  const outcomes = [
    { id: "ANSWER", label: "Answer", color: "var(--accent)" },
    { id: "ABSTAIN", label: "Abstain", color: "var(--muted)" },
    { id: "CLARIFY", label: "Clarify", color: "var(--positive)" },
    { id: "EXECUTION_FAILURE", label: "Failure", color: "#d47373" },
    { id: "UNCLASSIFIED", label: "Unclassified", color: "var(--stone)" },
  ] as const;

  const rows = [
    { label: "Filtered cohort", items: observations },
    ...policies.map(p => ({ label: p, items: observations.filter(o => o.policy_name === p) })),
  ];

  const barWidth = 360;
  const chartHeight = 25 + rows.length * 36 + 25;

  return (
    <figure className="risk-plot outcome-breakdown-chart" tabIndex={0} aria-label="Outcome breakdown stacked chart">
      <svg viewBox={`0 0 560 ${chartHeight}`} role="img" aria-labelledby={title}>
        <title id={title}>Distribution of Answer, Abstain, Clarify, and Failure outcomes</title>
        {rows.map((row, rIdx) => {
          const ry = 20 + rIdx * 36;
          const total = row.items.length;
          let currentX = 130;
          return (
            <g key={row.label}>
              <text x="120" y={ry + 15} textAnchor="end" fontSize="11" fill="var(--ink)">
                {row.label.length > 15 ? row.label.slice(0, 14) + "…" : row.label}
              </text>
              {total === 0 ? (
                <rect x="130" y={ry} width={barWidth} height="20" rx="2" fill="var(--surface-subtle)" stroke="var(--stone)" />
              ) : (
                outcomes.map(out => {
                  const count = row.items.filter(o => observationOutcome(o) === out.id).length;
                  if (count === 0) return null;
                  const segW = (count / total) * barWidth;
                  const segX = currentX;
                  currentX += segW;
                  return (
                    <g key={out.id}>
                      <rect x={segX} y={ry} width={segW} height="20" fill={out.color} rx="1">
                        <title>{`${row.label} - ${out.label}: ${count}/${total} (${((count/total)*100).toFixed(1)}%)`}</title>
                      </rect>
                      {segW >= 20 && (
                        <text x={segX + segW / 2} y={ry + 14} textAnchor="middle" fontSize="10" fill="var(--canvas)" fontWeight="600">
                          {count}
                        </text>
                      )}
                    </g>
                  );
                })
              )}
              <text x={130 + barWidth + 10} y={ry + 15} fontSize="11" fill="var(--muted)">
                n={total}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption>Segmented outcome distribution across policies. Failures are distinct from intentional abstentions.</figcaption>
      <ul className="risk-legend" aria-label="Outcome categories legend">
        {outcomes.map(out => (
          <li key={out.id} style={{ display: "inline-block", marginRight: "1rem" }}>
            <span aria-hidden="true" className="risk-swatch" style={{ backgroundColor: out.color }} />
            {out.label}
          </li>
        ))}
      </ul>
    </figure>
  );
}

export function RetrievalPerformancePlot({ detail }: { detail: Results }) {
  const title = useId();
  const quality = detail.result?.metrics?.evidence_quality as Record<string, unknown> | undefined;
  const breakdowns = detail.result?.metrics?.breakdowns as Record<string, unknown> | undefined;
  const retrievalBreakdown = (breakdowns?.retrieval_method ?? {}) as Record<string, Record<string, unknown>>;
  const activeMethod = String(detail.result?.retrieval_configuration?.method ?? detail.configuration?.retrieval ?? "bm25").toLowerCase();

  const methods = [
    { id: "bm25", name: "BM25" },
    { id: "dense", name: "Dense" },
    { id: "hybrid", name: "Hybrid" },
  ];

  const y = (idx: number) => 35 + idx * 42;

  return (
    <figure className="risk-plot retrieval-performance-plot" tabIndex={0} aria-label="Retrieval performance comparison chart">
      <svg viewBox="0 0 560 175" role="img" aria-labelledby={title}>
        <title id={title}>Gold evidence retrieval recall by method</title>
        <path d="M120 20V145H510" fill="none" stroke="currentColor" strokeWidth="1.5" />
        {[0, 0.25, 0.5, 0.75, 1].map(t => {
          const bx = 120 + t * 370;
          return (
            <g key={t}>
              <line x1={bx} y1="145" x2={bx} y2="150" stroke="currentColor" strokeWidth="1" />
              <text x={bx} y="165" textAnchor="middle" fontSize="11">{t}</text>
            </g>
          );
        })}
        {methods.map((m, idx) => {
          const by = y(idx);
          const methodData = retrievalBreakdown[m.id];
          let recallValue: number | null = null;
          if (methodData && typeof methodData === "object") {
            const eq = methodData.evidence_quality as Record<string, unknown> | undefined;
            const rec = eq?.gold_evidence_retrieval_recall as Record<string, unknown> | undefined;
            if (rec && typeof rec.value === "number") recallValue = rec.value;
          }
          if (recallValue === null && (activeMethod === m.id || activeMethod.includes(m.id))) {
            const rec = quality?.gold_evidence_retrieval_recall as Record<string, unknown> | undefined;
            if (rec && typeof rec.value === "number") recallValue = rec.value;
          }
          const isEvaluated = recallValue !== null;
          return (
            <g key={m.id}>
              <text x="110" y={by + 16} textAnchor="end" fontSize="12" fill={isEvaluated ? "var(--ink)" : "var(--muted)"}>
                {m.name}
              </text>
              {isEvaluated ? (
                <g>
                  <rect x="120" y={by} width={Math.max(4, recallValue! * 370)} height="22" rx="2" fill="var(--accent)" opacity="0.9">
                    <title>{`${m.name}: Gold recall ${recallValue!.toFixed(3)}`}</title>
                  </rect>
                  <text x={120 + Math.max(4, recallValue! * 370) + 8} y={by + 16} fontSize="11" fill="var(--ink)">
                    {recallValue!.toFixed(3)} (Active run)
                  </text>
                </g>
              ) : (
                <g>
                  <rect x="120" y={by} width="370" height="22" rx="2" fill="none" stroke="var(--stone)" strokeDasharray="3 3" />
                  <text x="305" y={by + 15} textAnchor="middle" fontSize="11" fill="var(--muted)">
                    Not evaluated in this run
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
      <figcaption>Gold-evidence retrieval recall across recorded observations. Comparing BM25 vs Dense vs Hybrid across runs requires selecting compatible runs in experiment history.</figcaption>
    </figure>
  );
}

export function EvaluationObservations({ detail }: { detail: Results }) {
  const [policy, setPolicy] = useState(""), [category, setCategory] = useState("");
  const rows = filterObservations(detail.observations, policy, category);
  const policies = [...new Set(detail.observations.map(row => row.policy_name))].sort();
  const categories = [...new Set(detail.observations.map(observationCategory))].sort();
  const outcomes = ["ANSWER", "ABSTAIN", "CLARIFY", "EXECUTION_FAILURE", "UNCLASSIFIED"];
  const errors = [...new Set(rows.filter(row => row.error !== null).map(row => row.error!.kind))].sort();
  const recall = savedRetrievalRecall(detail);
  return <section className="evaluation-section" aria-labelledby="saved-outcomes-heading">
    <h2 id="saved-outcomes-heading">Saved outcomes and execution errors</h2>
    <p>Experiment <code>{detail.id}</code>. These are observation counts, not independent question samples. Filters affect this ledger only; R1 metrics and exports keep the full matched analysis cohort.</p>
    <div className="evaluation-filters"><label htmlFor="outcome-policy">Observation policy<select id="outcome-policy" value={policy} onChange={event => setPolicy(event.target.value)}><option value="">All saved policies</option>{policies.map(name => <option key={name} value={name}>{name}</option>)}</select></label><label htmlFor="outcome-category">Question category<select id="outcome-category" value={category} onChange={event => setCategory(event.target.value)}><option value="">All saved categories</option>{categories.map(name => <option key={name} value={name}>{name}</option>)}</select></label></div>
    <p role="status">{rows.length} of {detail.observations.length} saved observations shown.</p>
    {!rows.length ? <p>No observations match these filters.</p> : <>
      <OutcomeBreakdownChart observations={rows} />
      <figure className="evaluation-counts"><figcaption>Recorded outcomes / experiment <code>{detail.id}</code></figcaption>{outcomes.map(outcome => { const count = rows.filter(row => observationOutcome(row) === outcome).length; return <div key={outcome}><span>{outcome}</span><meter min={0} max={rows.length} value={count} aria-label={`${outcome}: ${count} of ${rows.length} observations`} /><span>{count}</span></div>; })}</figure>
      <details><summary>Recorded execution error kinds</summary><p>Execution error kinds come from saved run errors. Unsupported claims, contradiction failures and other semantic failure modes are unavailable without verified judgments.</p>{errors.length ? <figure className="evaluation-counts"><figcaption>Recorded error kinds / experiment <code>{detail.id}</code></figcaption>{errors.map(kind => { const count = rows.filter(row => row.error?.kind === kind).length; return <div key={kind}><span>{kind}</span><meter min={0} max={rows.length} value={count} aria-label={`${kind}: ${count} of ${rows.length} observations`} /><span>{count}</span></div>; })}</figure> : <p>No recorded run-error objects in this filtered view. Failed execution statuses remain visible separately in the outcome ledger.</p>}</details>
      <div className="ledger-scroll" role="region" tabIndex={0} aria-label="Filtered saved observations"><table className="evidence-table"><caption>Recorded outcomes; no reference answers are displayed</caption><thead><tr><th scope="col">Question</th><th scope="col">Category</th><th scope="col">Policy</th><th scope="col">Outcome</th><th scope="col">Execution status</th><th scope="col">Error kind</th></tr></thead><tbody>{rows.map((row, i) => <tr key={`${row.question_id}:${row.policy_name}:${i}`}><th scope="row"><code>{row.question_id}</code></th><td>{observationCategory(row)}</td><td>{row.policy_name}</td><td>{observationOutcome(row)}</td><td>{row.observed.execution_status}</td><td>{row.error?.kind ?? "None recorded"}</td></tr>)}</tbody></table></div>
    </>}
    <details><summary>Saved retrieval metric and scope</summary><p>Experiment <code>{detail.id}</code> / {String(detail.result?.retrieval_configuration.method ?? "Unavailable")}: retrieval recall {recall.value === null ? "Unavailable" : recall.value.toFixed(3)}. {recall.note}</p><p>This stored aggregate is not changed by ledger filters. It is not a cross-strategy comparison. No MRR, NDCG or semantic retrieval measure is invented when absent.</p><RetrievalPerformancePlot detail={detail} /></details>
  </section>;
}
