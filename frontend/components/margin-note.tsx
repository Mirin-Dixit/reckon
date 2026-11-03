import type { ReactNode } from "react";

export function MarginNote({ children }: { children: ReactNode }) {
  return <aside className="margin-note">{children}</aside>;
}
