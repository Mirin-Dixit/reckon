"use client";

import { useState } from "react";

interface NavigationProps {
  expanded: boolean;
  onToggle: () => void;
  onNavigate: () => void;
}

export function WorkbenchNavigationView({ expanded, onToggle, onNavigate }: NavigationProps) {
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
        <li><a href="#main-content" aria-current="page" onClick={onNavigate}>Workbench</a></li>
        <li><span className="planned-workspace" aria-disabled="true" tabIndex={0} title="Planned: question and evidence inspection" data-description="Planned: question and evidence inspection">Query Lab <sup>soon</sup></span></li>
        <li><span className="planned-workspace" aria-disabled="true" tabIndex={0} title="Planned: controlled evaluation runs" data-description="Planned: controlled evaluation runs">Experiments <sup>soon</sup></span></li>
        <li><span className="planned-workspace" aria-disabled="true" tabIndex={0} title="Planned: observed results and comparisons" data-description="Planned: observed results and comparisons">Evaluation Results <sup>soon</sup></span></li>
        <li className="status-navigation"><a href="#system-status" onClick={onNavigate}>System status</a></li>
      </ul>
    </nav>
  );
}

export function WorkbenchNavigation() {
  const [expanded, setExpanded] = useState(false);
  return (
    <WorkbenchNavigationView
      expanded={expanded}
      onToggle={() => setExpanded(value => !value)}
      onNavigate={() => setExpanded(false)}
    />
  );
}
