const steps = [
  { name: "Question", note: "State the information need." },
  { name: "Retrieval", note: "Find relevant passages." },
  { name: "Evidence", note: "Inspect support and missing premises." },
  { name: "Decision", note: "Answer, abstain, or clarify." },
  { name: "Evaluation", note: "Compare observed and expected behavior." },
] as const;

export function WorkflowLine() {
  return <div className="workflow-line">
    <svg className="workflow-horizontal" width="100%" height="24" aria-hidden="true">
      <line className="workflow-track" x1="6" y1="12" x2="100%" y2="12" pathLength="1" />
    </svg>
    <svg className="workflow-vertical" width="24" height="100%" aria-hidden="true">
      <line className="workflow-track" x1="6" y1="12" x2="6" y2="100%" pathLength="1" />
    </svg>
    <ol className="workflow-steps">{steps.map((step, index) => <li className={`workflow-step node-${index}`} key={step.name}>
      <span className="workflow-number">{String(index + 1).padStart(2, "0")}</span>
      <span className="workflow-dot" aria-hidden="true" />
      <h3 className="workflow-label">{step.name}</h3>
      <p className="workflow-note">{step.note}</p>
    </li>)}</ol>
  </div>;
}
