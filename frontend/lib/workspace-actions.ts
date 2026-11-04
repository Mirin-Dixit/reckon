/** A synchronous guard: a React disabled state alone cannot prevent same-tick POSTs. */
export function createMutationGate() {
  let active = false;
  return {
    enter() { if (active) return false; active = true; return true; },
    leave() { active = false; },
  };
}

/** Hand JSON to the browser; completion does not assert that a file was saved. */
export function downloadJson(value: unknown, filename: string): void {
  const payload = JSON.stringify(value, null, 2);
  if (payload === undefined) throw new Error("No JSON to export");
  const url = URL.createObjectURL(new Blob([payload], { type: "application/json" }));
  try {
    const link = document.createElement("a");
    link.href = url; link.download = filename; link.click();
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}
