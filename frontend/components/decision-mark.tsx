type Decision = "answer" | "abstain" | "clarify";

export function DecisionMark({ decision }: { decision: Decision }) {
  return <span className={`decision-mark decision-${decision}`}>
    {decision === "answer" ? "Answer" : decision === "abstain" ? "Abstain" : "Clarify"}
    {decision === "abstain" && <small className="withheld-stamp">withheld</small>}
  </span>;
}
