"use client";

import { useState } from "react";
import type { Results } from "../lib/experiment-api";
import { filterObservations, observationCategory, observationOutcome, savedRetrievalRecall } from "../lib/evaluation-report";

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
      <figure className="evaluation-counts"><figcaption>Recorded outcomes / experiment <code>{detail.id}</code></figcaption>{outcomes.map(outcome => { const count = rows.filter(row => observationOutcome(row) === outcome).length; return <div key={outcome}><span>{outcome}</span><meter min={0} max={rows.length} value={count} aria-label={`${outcome}: ${count} of ${rows.length} observations`} /><span>{count}</span></div>; })}</figure>
      <details><summary>Recorded execution error kinds</summary><p>Execution error kinds come from saved run errors. Unsupported claims, contradiction failures and other semantic failure modes are unavailable without verified judgments.</p>{errors.length ? <figure className="evaluation-counts"><figcaption>Recorded error kinds / experiment <code>{detail.id}</code></figcaption>{errors.map(kind => { const count = rows.filter(row => row.error?.kind === kind).length; return <div key={kind}><span>{kind}</span><meter min={0} max={rows.length} value={count} aria-label={`${kind}: ${count} of ${rows.length} observations`} /><span>{count}</span></div>; })}</figure> : <p>No recorded run-error objects in this filtered view. Failed execution statuses remain visible separately in the outcome ledger.</p>}</details>
      <div className="ledger-scroll" role="region" tabIndex={0} aria-label="Filtered saved observations"><table className="evidence-table"><caption>Recorded outcomes; no reference answers are displayed</caption><thead><tr><th scope="col">Question</th><th scope="col">Category</th><th scope="col">Policy</th><th scope="col">Outcome</th><th scope="col">Execution status</th><th scope="col">Error kind</th></tr></thead><tbody>{rows.map((row, i) => <tr key={`${row.question_id}:${row.policy_name}:${i}`}><th scope="row"><code>{row.question_id}</code></th><td>{observationCategory(row)}</td><td>{row.policy_name}</td><td>{observationOutcome(row)}</td><td>{row.observed.execution_status}</td><td>{row.error?.kind ?? "None recorded"}</td></tr>)}</tbody></table></div>
    </>}
    <details><summary>Saved retrieval metric and scope</summary><p>Experiment <code>{detail.id}</code> / {String(detail.result?.retrieval_configuration.method ?? "Unavailable")}: retrieval recall {recall.value === null ? "Unavailable" : recall.value.toFixed(3)}. {recall.note}</p><p>This stored aggregate is not changed by ledger filters. It is not a cross-strategy comparison. No MRR, NDCG or semantic retrieval measure is invented when absent.</p></details>
  </section>;
}
