export function SufficiencyLine() {
  return <figure className="sufficiency-line" aria-labelledby="concept-caption">
    <figcaption id="concept-caption">Concept, not data</figcaption>
    <svg viewBox="0 0 720 112" role="img" aria-labelledby="concept-title concept-description">
      <title id="concept-title">Conceptual evidence sufficiency line</title>
      <desc id="concept-description">Evidence amount increases from left to right. Abstain, clarify and answer are illustrative regions, not measurements or a decision rule.</desc>
      <path className="concept-axis" d="M12 64 H704 M698 60 L704 64 L698 68" />
      <text x="28" y="34">Abstain</text><path className="concept-motif" d="M28 28 H94" />
      <text x="270" y="34">Clarify</text><path className="concept-motif concept-dashed" d="M270 40 H326" />
      <text x="522" y="34">Answer</text><path className="concept-motif" d="M522 40 H584" />
      <circle className="concept-marker" cx="552" cy="64" r="4" />
      <text className="concept-axis-label" x="12" y="100">Evidence amount increases left to right</text>
    </svg>
  </figure>;
}
