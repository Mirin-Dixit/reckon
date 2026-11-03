"use client";

import { useState } from "react";

interface NavigationProps {
  workspace?: "workbench" | "query-lab";
  expanded: boolean;
  onToggle: () => void;
  onNavigate: () => void;
}

export function WorkbenchNavigationView({ expanded, onToggle, onNavigate, workspace = "workbench" }: NavigationProps) {
  return (
    <nav className="workbench-navigation" aria-label="Main navigation">
      <button
        className="navigation-toggle"
        type="button"
        aria-expanded={expanded}
        aria-controls="workspace-links"
        onClick={onToggle}
      >
        Workspaces <span aria-hidden="true">{expanded ? "Close" : "Open"}</span>
      </button>
      <ul id="workspace-links" className={`workspace-links${expanded ? " is-open" : ""}`}>
        <li><a href={workspace === "workbench" ? "#main-content" : "/#main-content"} aria-current={workspace === "workbench" ? "page" : undefined} onClick={onNavigate}>Workbench</a></li>
        <li><a href="/query-lab" aria-current={workspace === "query-lab" ? "page" : undefined} onClick={onNavigate}>Query Lab</a></li>
        <li><span className="planned-workspace" aria-disabled="true" tabIndex={0} title="Planned: controlled evaluation runs" data-description="Planned: controlled evaluation runs">Experiments <sup>soon</sup></span></li>
        <li><span className="planned-workspace" aria-disabled="true" tabIndex={0} title="Planned: observed results and comparisons" data-description="Planned: observed results and comparisons">Evaluation Results <sup>soon</sup></span></li>
        <li className="status-navigation"><a href={workspace === "workbench" ? "#system-status" : "/#system-status"} onClick={onNavigate}>System status</a></li>
      </ul>
    </nav>
  );
}

export function WorkbenchNavigation({ workspace = "workbench" }: { workspace?: "workbench" | "query-lab" }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <WorkbenchNavigationView
      workspace={workspace}
      expanded={expanded}
      onToggle={() => setExpanded(value => !value)}
      onNavigate={() => setExpanded(false)}
    />
  );
}
