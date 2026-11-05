"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { createQueryClient } from "../lib/query-api";
import { buildQuery, initialDraft, querySession, type QueryDraft, type QueryState } from "../lib/query-lab";
import { DecisionDetails } from "./evidence-ledger";

export function QueryResult({ state }: { state: QueryState }) {
  if (state.phase === "idle") return <p>No query has been submitted. Results will appear here.</p>;
  if (state.phase === "loading") return <p role="status">Running local retrieval and generation…</p>;
  if (state.phase === "error") return <div role="alert"><h3>Request failed</h3><p>{state.message}</p></div>;
  if (state.phase === "cancelled") return <p role="status">{state.message}</p>;
  const { result, request } = state;
  return <div className={`query-result decision-${result.decision.toLowerCase()}`}>
    <p className="page-eyebrow">Execution succeeded / {request.retrieval?.method} / {request.policy.name}</p>
    <div className="decision-announcement" role="status"><h3>{result.decision}</h3></div>
    {result.decision === "ABSTAIN" && <p>Intentional abstention: the policy withheld an answer.</p>}
    {result.decision === "CLARIFY" && <p>Clarification requested: resolve the question before answering.</p>}
    {result.decision === "ANSWER" && <p>Answer returned. Inspect its citations and source evidence below.</p>}
    <p className="query-answer">{result.answer ?? result.clarification_question}</p>
    {result.decision_reason ? <p><strong>Reason:</strong> <code>{result.decision_reason.code}</code> — {result.decision_reason.explanation}</p> : <p>No decision reason was supplied.</p>}
    {result.unsupported_premises.map((text, i) => <p key={i}><strong>Unsupported premise:</strong> {text}</p>)}
    {result.surfaced_contradictions.map((text, i) => <p key={i}><strong>Contradiction:</strong> {text}</p>)}
    <p>{result.citations.length} citation references returned. Citation presence alone does not establish grounding.</p>
    <DecisionDetails result={result} />
  </div>;
}

export function QueryLab() {
  const [draft, setDraft] = useState<QueryDraft>(initialDraft);
  const [state, setState] = useState<QueryState>({ phase: "idle" });
  const [validation, setValidation] = useState("");
  const responseHeading = useRef<HTMLHeadingElement>(null);
  const validationMessage = useRef<HTMLParagraphElement>(null);
  const cancelButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (state.phase === "loading") cancelButton.current?.focus();
    if (["ready", "error", "cancelled"].includes(state.phase)) responseHeading.current?.focus();
  }, [state.phase]);
  useEffect(() => { if (validation) validationMessage.current?.focus(); }, [validation]);
  const session = useRef<ReturnType<typeof querySession> | null>(null);
  useEffect(() => {
    const client = createQueryClient(process.env.NEXT_PUBLIC_RECKON_API_BASE_URL);
    const current = querySession(client.query, setState); session.current = current;
    return () => { current.dispose(); session.current = null; };
  }, []);
  const change = (key: keyof QueryDraft, value: string) => {
    setValidation(""); setDraft(previous => ({ ...previous, [key]: value, ...(key === "method" ? { threshold: "0" } : {}) }));
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    try { const request = buildQuery(draft); setValidation(""); void session.current?.submit(request); }
    catch (error: unknown) { setValidation(error instanceof Error ? error.message : "Check the query settings."); }
  };
  const busy = state.phase === "loading";
  return <section className="query-lab" aria-labelledby="query-title">
    <header className="query-heading"><p className="page-eyebrow">Question / Retrieval / Decision</p><h1 id="query-title">Query Lab</h1>
      <p>Inspect one evidence-grounded response from your configured local backend.</p></header>
    <div className="query-workspace">
      <form onSubmit={submit} noValidate aria-describedby="query-safety">
        <fieldset disabled={busy}><legend>Query configuration</legend>
          <label htmlFor="question">Question</label>
          <textarea id="question" value={draft.question} onChange={e => change("question", e.target.value)} rows={5} required aria-describedby="question-help query-validation" aria-invalid={!!validation && (!draft.question.trim() || [...draft.question.trim()].length > 8000)} />
          <p id="question-help">1–8,000 characters. Use a question about the local corpus; do not enter secrets.</p>
          <div className="query-settings">
            <label>Retrieval<select value={draft.method} onChange={e => change("method", e.target.value)}><option value="bm25">BM25</option><option value="dense">Dense</option><option value="hybrid">Hybrid (RRF)</option></select></label>
            <label>Decision policy<select value={draft.policy} onChange={e => change("policy", e.target.value)}><option value="always_answer">Always-answer</option><option value="threshold">Threshold</option><option value="prompt_abstention">Prompt-abstention</option></select></label>
            <label>Top k<input type="number" min={1} max={20} step={1} value={draft.topK} onChange={e => change("topK", e.target.value)} /></label>
            {draft.method === "hybrid" && <>
              <label>Candidate k (optional)<input type="number" min={Number(draft.topK) || 1} max={256} step={1} placeholder="Backend automatic" value={draft.candidateK} onChange={e => change("candidateK", e.target.value)} /></label>
              <label>RRF k<input type="number" min={1} max={1000} step={1} value={draft.rrfK} onChange={e => change("rrfK", e.target.value)} /></label>
            </>}
            {draft.policy === "threshold" && <label>Threshold (at least)<input type="number" step="any" value={draft.threshold} onChange={e => change("threshold", e.target.value)} /></label>}
          </div>
          {draft.policy === "threshold" && <p>Uncalibrated {draft.method === "bm25" ? "BM25 relevance: 0 and above, no fixed maximum" : draft.method === "dense" ? "cosine similarity: −1 to 1" : "RRF relevance: bounded by effective rank lists and RRF k"}. Not an answerability probability. Missing scores abstain. Changing retrieval resets the threshold to 0.</p>}
          {draft.method !== "bm25" && <p>Requires the local all-minilm:22m embedding model. No BM25 fallback.</p>}
        </fieldset>
        <p id="query-validation" ref={validationMessage} tabIndex={-1} role={validation ? "alert" : undefined}>{validation}</p>
        <div className="query-actions"><button className="check-button" type="submit" disabled={busy}>{busy ? "Running…" : "Run query"}</button>
          {busy && <button type="button" ref={cancelButton} onClick={() => session.current?.cancel()}>Cancel request</button>}</div>
        <p id="query-safety">Local inference only. No automatic retries. Generation settings remain server-side. Cancelling stops waiting; the backend may continue processing.</p>
      </form>
      <section className="query-output" aria-labelledby="response-title" aria-busy={busy}><h2 id="response-title" ref={responseHeading} tabIndex={-1}>Observed response</h2><QueryResult state={state} /></section>
    </div>
  </section>;
}
