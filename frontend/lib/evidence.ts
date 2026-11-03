import type { CitationResponse, EvidenceResponse } from "./query-contracts";

const boundary = (value: number) => Number.isSafeInteger(value) && value >= 0;
const nonempty = (value: string) => !!value.trim();

/** Match Python source coordinates: Unicode code points, half-open [start, end). */
export function validateEvidence(evidence: EvidenceResponse[], citations: CitationResponse[]): void {
  const byId = new Map<string, EvidenceResponse>();
  const codePoints = new Map<string, string[]>();
  for (const chunk of evidence) {
    const chars = [...chunk.text];
    if (!nonempty(chunk.chunk_id) || !nonempty(chunk.document_id) || byId.has(chunk.chunk_id) ||
        !boundary(chunk.start_char) || !boundary(chunk.end_char) || chunk.end_char <= chunk.start_char ||
        chars.length !== chunk.end_char - chunk.start_char ||
        (chunk.retrieval_rank != null && (!Number.isSafeInteger(chunk.retrieval_rank) || chunk.retrieval_rank <= 0))) {
      throw new Error("Invalid evidence coordinates or identifiers.");
    }
    byId.set(chunk.chunk_id, chunk);
    codePoints.set(chunk.chunk_id, chars);
  }
  for (const citation of citations) {
    const chunk = byId.get(citation.evidence_id);
    if (!chunk || !nonempty(citation.claim) || !nonempty(citation.quote) ||
        !boundary(citation.start_char) || !boundary(citation.end_char) || citation.end_char <= citation.start_char ||
        citation.start_char < chunk.start_char || citation.end_char > chunk.end_char ||
        codePoints.get(chunk.chunk_id)!.slice(citation.start_char - chunk.start_char, citation.end_char - chunk.start_char).join("") !== citation.quote) {
      throw new Error("Invalid citation coordinates or quote.");
    }
  }
}

export interface EvidenceSegment { text: string; citations: number[] }

/** Split at exact citation boundaries; overlaps share a mark without nesting marks. */
export function evidenceSegments(chunk: EvidenceResponse, citations: CitationResponse[]): EvidenceSegment[] {
  const selected = citations.flatMap((citation, index) => citation.evidence_id === chunk.chunk_id ? [{ citation, number: index + 1 }] : []);
  validateEvidence([chunk], selected.map(item => item.citation));
  const chars = [...chunk.text];
  const boundaries = [...new Set([chunk.start_char, chunk.end_char, ...selected.flatMap(({ citation }) => [citation.start_char, citation.end_char])])].sort((a, b) => a - b);
  return boundaries.slice(0, -1).map((start, i) => {
    const end = boundaries[i + 1];
    return { text: chars.slice(start - chunk.start_char, end - chunk.start_char).join(""),
      citations: selected.filter(({ citation }) => citation.start_char <= start && citation.end_char >= end).map(item => item.number) };
  });
}
