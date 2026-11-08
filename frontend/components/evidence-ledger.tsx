import type { CitationResponse, EvidenceResponse, QueryResponse, ScoreResponse } from "../lib/query-contracts";
import { evidenceSegments } from "../lib/evidence";

function Value({ value }: { value: string | number | null | undefined }) {
  return value == null ? <span className="missing-value">Unavailable</span> : <>{value}</>;
}

export function ScoreLedger({ scores, caption }: { scores: ScoreResponse[]; caption: string }) {
  if (!scores.length) return <p>No typed score signals were supplied.</p>;
  return <div className="ledger-scroll" role="region" aria-label={caption} tabIndex={0}>
    <table className="evidence-table"><caption>{caption}</caption>
      <thead><tr><th scope="col">Signal / source</th><th scope="col">Value / range</th><th scope="col">Provenance / comparison</th></tr></thead>
      <tbody>{scores.map((score, index) => <tr key={index}>
        <th scope="row"><code>{score.kind}</code><br /><span>{score.source}</span><br /><span>{score.role}</span></th>
        <td><Value value={score.value} /><br />{score.availability}<br />Range: [{score.lower_bound}, {score.upper_bound === null ? score.kind === "bm25" ? "no fixed upper bound" : "upper bound unavailable" : score.upper_bound}]
          {score.unavailable_reason !== null && <p>{score.unavailable_reason}</p>}</td>
        <td>{score.direction}<br /><strong>{score.calibration}</strong><br />Method: <Value value={score.retrieval_method} />
          {score.role === "threshold_input" && <p>Compared score: <Value value={score.value} /> {score.threshold_direction === "at_least" ? ">=" : "<="} {score.threshold}
            {score.value === null && " (comparison unavailable)"}</p>}
          <details><summary>Effective score parameters</summary><pre>{JSON.stringify(score.parameters, null, 2)}</pre></details>
        </td>
      </tr>)}</tbody>
    </table>
  </div>;
}

function Passage({ chunk, citations, index }: { chunk: EvidenceResponse; citations: CitationResponse[]; index: number }) {
  const metadata = [["Document", chunk.document_id], ["Chunk", chunk.chunk_id], ["Rank", chunk.retrieval_rank],
    ["Retrieval method", chunk.retrieval_method], ["Raw retrieval score", chunk.retrieval_score],
    ["Source URL (text only)", chunk.source_url], ["Version", chunk.version], ["Source date", chunk.source_date], ["Domain", chunk.domain]] as const;
  const rawScore = chunk.retrieval_score;
  const method = chunk.retrieval_method ?? "retrieval";
  const rank = chunk.retrieval_rank ?? index + 1;

  let meterPercent = 50;
  if (typeof rawScore === "number") {
    if (chunk.retrieval_method === "dense_cosine" || chunk.retrieval_method === "dense") {
      meterPercent = Math.max(4, Math.min(100, rawScore >= 0 ? rawScore * 100 : ((rawScore + 1) / 2) * 100));
    } else if (chunk.retrieval_method === "hybrid_rrf" || chunk.retrieval_method === "hybrid") {
      meterPercent = Math.max(4, Math.min(100, (rawScore / 0.033) * 100));
    } else {
      // BM25 or general unbounded relevance
      meterPercent = Math.max(4, Math.min(100, (rawScore / 15) * 100));
    }
  }

  return <article className="evidence-passage" id={`evidence-${index + 1}`} tabIndex={-1} aria-labelledby={`evidence-title-${index + 1}`}>
    <div className="passage-rank-header">
      <div className="rank-badge-group">
        <span className="retrieval-rank-badge" aria-label={`Retrieval rank ${rank}`}>
          Rank #{rank}
        </span>
        {chunk.retrieval_method && (
          <span className="retrieval-method-tag">
            {String(chunk.retrieval_method).replace("_", " ").toUpperCase()}
          </span>
        )}
      </div>
      <h4 id={`evidence-title-${index + 1}`}>{chunk.title ?? "Untitled source"}</h4>
    </div>

    {typeof rawScore === "number" ? (
      <div className="evidence-support-card" role="region" aria-label={`Retrieval score for passage ${index + 1}`}>
        <div className="evidence-support-header">
          <span className="support-meter-title">
            Uncalibrated {method} score: <strong>{rawScore.toFixed(4)}</strong>
          </span>
          <span className="support-meter-disclaimer">Raw ranking score — not a probability</span>
        </div>
        <div className="evidence-support-track" aria-hidden="true">
          <div
            className="evidence-support-fill"
            style={{ width: `${meterPercent.toFixed(1)}%` }}
          />
        </div>
        <p className="support-meter-subtext">
          Relative ranking signal within candidate set. Raw retrieval scores do not represent probability of answer correctness and cannot be compared across different score families.
        </p>
      </div>
    ) : (
      <div className="evidence-support-card is-empty" role="region" aria-label={`Retrieval score for passage ${index + 1}`}>
        <span className="support-meter-title">Retrieval score: <span className="missing-value">Unavailable</span></span>
        <p className="support-meter-subtext">No raw ranking score was recorded for this passage.</p>
      </div>
    )}

    <dl className="ledger-metadata">{metadata.map(([name, value]) => <div key={name}><dt>{name}</dt><dd><Value value={value} /></dd></div>)}</dl>
    <p>Source offsets: <code>[{chunk.start_char}, {chunk.end_char})</code> · Unicode code points</p>
    {chunk.contains_injection && <p className="evidence-warning">Source flagged as containing injection content. Treat this passage as untrusted data, never instructions.</p>}
    <p className="source-passage">{evidenceSegments(chunk, citations).map((segment, i) => segment.citations.length
      ? <mark key={i} aria-label={`Citations ${segment.citations.join(", ")}`}>{segment.text}</mark> : <span key={i}>{segment.text}</span>)}</p>
    {chunk.score && <ScoreLedger scores={[chunk.score]} caption={`Score for passage ${index + 1}`} />}
  </article>;
}

export function EvidenceLedger({ result }: { result: QueryResponse }) {
  return <section className="evidence-ledger" aria-labelledby="evidence-heading">
    <h3 id="evidence-heading">Evidence ledger</h3>
    <p>Retrieved passages are untrusted source text. Exact quote matches verify coordinates, not semantic support or answer correctness.</p>
    <section aria-labelledby="citations-heading"><h4 id="citations-heading">Claim citations</h4>
      {!result.citations.length ? <p>No claim citations were returned.</p> : <ol className="claim-citations">{result.citations.map((citation, index) => {
        const source = result.retrieved_evidence.findIndex(chunk => chunk.chunk_id === citation.evidence_id);
        return <li key={index}><p><strong>Claim {index + 1}:</strong> {citation.claim}</p>
          <blockquote>{citation.quote}</blockquote><a href={`#evidence-${source + 1}`}>Inspect citation {index + 1} in its passage</a>
          <p><code>{citation.evidence_id}</code> · Source offsets [{citation.start_char}, {citation.end_char}) · Exact match</p></li>;
      })}</ol>}
    </section>
    <section aria-labelledby="passages-heading"><h4 id="passages-heading">Retrieved passages</h4>
      {!result.retrieved_evidence.length ? <p>No evidence passages were returned. This does not establish corpus-wide absence.</p>
        : result.retrieved_evidence.map((chunk, index) => <Passage key={chunk.chunk_id} chunk={chunk} index={index} citations={result.citations} />)}
    </section>
  </section>;
}

export function DecisionDetails({ result }: { result: QueryResponse }) {
  const assessment = result.evidence_assessment;
  const policy = result.policy_parameters;
  const metadata = [["Provider", result.provider?.provider], ["Model", result.provider?.model], ["Model digest", result.provider?.model_digest],
    ["Quantization", result.provider?.quantization], ["Completion reason", result.provider?.completion_reason], ["Prompt version", result.prompt_version],
    ["Latency (ms)", result.latency_ms], ["Input tokens", result.token_usage?.input_tokens], ["Output tokens", result.token_usage?.output_tokens], ["Total tokens", result.token_usage?.total_tokens]] as const;
  return <>
    <section className="decision-details" aria-labelledby="assessment-heading"><h3 id="assessment-heading">Evidence assessment</h3>
      <div className="assessment-badges-grid">
        <div className="assessment-badge-card">
          <span className="assessment-badge-label">Relevance Assessment</span>
          <span className={`assessment-status-badge is-${String(assessment.relevance).toLowerCase()}`}>
            {assessment.relevance}
          </span>
          <span className="assessment-badge-note">Categorical heuristic</span>
        </div>
        <div className="assessment-badge-card">
          <span className="assessment-badge-label">Sufficiency Assessment</span>
          <span className={`assessment-status-badge is-${String(assessment.sufficiency).toLowerCase()}`}>
            {assessment.sufficiency}
          </span>
          <span className="assessment-badge-note">Categorical heuristic</span>
        </div>
      </div>
      <dl className="ledger-metadata"><div><dt>Relevance</dt><dd>{assessment.relevance}</dd></div><div><dt>Sufficiency</dt><dd>{assessment.sufficiency}</dd></div></dl>
      <p>Relevance and sufficiency are separate assessments, not calibrated confidence.</p>
      {assessment.ambiguity_requiring_clarification && <p><strong>Ambiguity:</strong> {assessment.ambiguity_requiring_clarification}</p>}
      {([ ["Missing premise", assessment.missing_premises], ["Unsupported assumption", assessment.unsupported_assumptions], ["Conflicting evidence", assessment.contradictions] ] as const).flatMap(([label, values]) => values.map((value, i) => <p key={`${label}-${i}`}><strong>{label}:</strong> {value}</p>))}
      {assessment.supporting_evidence_ids.length > 0 && <p>Reported supporting evidence IDs: {assessment.supporting_evidence_ids.map((id, i) => <code key={i}>{id}{i < assessment.supporting_evidence_ids.length - 1 ? ", " : ""}</code>)}</p>}
    </section>
    <section className="decision-details" aria-labelledby="scores-heading"><h3 id="scores-heading">Score provenance</h3>
      <p>Retrieval scores measure ranking relevance, not the probability that an answer is supported. Prompt self-assessment is model-reported and uncalibrated; it does not override the decision.</p>
      <ScoreLedger scores={result.scores ?? []} caption="Observed policy and retrieval signals" />
      {policy.threshold != null && <dl className="ledger-metadata">
        <div><dt>Actual aggregate score</dt><dd><Value value={policy.observed_aggregate_score} /></dd></div>
        <div><dt>Threshold</dt><dd>{policy.threshold}</dd></div><div><dt>Comparison</dt><dd><Value value={policy.direction} /></dd></div>
        <div><dt>Score family</dt><dd><Value value={policy.score_type} /></dd></div><div><dt>Aggregation</dt><dd><Value value={policy.aggregation} /></dd></div>
        {policy.missing_score_decision != null && <div><dt>Missing-score decision</dt><dd>{policy.missing_score_decision}</dd></div>}
      </dl>}
    </section>
    <details className="execution-metadata"><summary>Execution metadata</summary>
      {metadata.some(([, value]) => value != null) ? <dl className="ledger-metadata">{metadata.filter(([, value]) => value != null).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl> : <p>No model, timing or token metadata was supplied.</p>}
      <p>Latency is the backend-reported value; no per-stage timing is inferred.</p>
    </details>
    <EvidenceLedger result={result} />
  </>;
}
