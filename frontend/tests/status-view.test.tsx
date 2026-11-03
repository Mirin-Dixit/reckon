import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { Children, isValidElement, type ReactElement, type ReactNode } from "react";
import { renderToStaticMarkup, renderToString } from "react-dom/server";
import { StatusView } from "../components/status-view";
import { SystemStatus } from "../components/system-status";
import { WorkbenchShell } from "../components/workbench-shell";
import { WorkbenchNavigationView } from "../components/workbench-navigation";
import type { HealthResponse, PublicFailure } from "../lib/api";
import { checkSystemStatus } from "../lib/system-status";

const health: HealthResponse = {
  status: "ok", application: "RAGBench Studio", api_version: "0.1.0",
  runtime_initialized: true, generation_configured: true, provider_connection_tested: false,
};

test("loading has an accessible live status without invented readiness", () => {
  const html = renderToStaticMarkup(<StatusView state={{ phase: "loading" }} />);
  assert.match(html, /role="status"/);
  assert.match(html, /Checking backend/);
  assert.doesNotMatch(html, /Backend configured/);
});

test("status shell renders the correct ellipsis and separator without mojibake", () => {
  const html = renderToStaticMarkup(<SystemStatus />);
  assert.match(html, /Checking\u2026/);
  assert.match(html, /Read-only \u00b7 no provider call/);
  assert.doesNotMatch(html, /\u00c2|\u00e2\u20ac/);
});

for (const [label, data] of [
  ["Backend configured", health],
  ["Generation not configured", { ...health, generation_configured: false }],
  ["Backend degraded", { ...health, status: "degraded", runtime_initialized: false, generation_configured: false }],
] as const) {
  test(`render ${label} with actual health values and no provider verification claim`, () => {
    const html = renderToStaticMarkup(<StatusView state={{ phase: "ready", health: data }} />);
    assert.match(html, new RegExp(label));
    assert.match(html, /<caption>Backend health response<\/caption>/);
    assert.match(html, /scope="row"/);
    assert.match(html, /0\.1\.0/);
    assert.match(html, /Provider connection tested<code class="field-name">provider_connection_tested<\/code><\/th><td>Not tested/);
    assert.doesNotMatch(html, /expected_answer|expected_safe_behavior|evidence_spans/);
  });
}

for (const kind of ["connection", "timeout", "malformed", "configuration", "http"] as const) {
  test(`render a safe accessible ${kind} error`, () => {
    const failure: PublicFailure = { kind, httpStatus: 503 };
    const html = renderToStaticMarkup(<StatusView state={{ phase: "error", failure }} />);
    assert.match(html, /role="alert"/);
    assert.doesNotMatch(html, /Backend configured/);
    assert.match(html, /No health result is available/);
  });
}

test("even unexpected injected failures never reach rendered output", async () => {
  const state = await checkSystemStatus({ getHealth: async () => {
    throw new Error('<script>alert("server-only-secret")</script>');
  } });
  const html = renderToStaticMarkup(<StatusView state={state} />);
  assert.doesNotMatch(html, /<script>|server-only-secret/);
  assert.match(html, /Cannot reach the backend/);
});

test("workbench establishes the research workflow without making planned workspaces functional", () => {
  const html = renderToStaticMarkup(<WorkbenchShell><SystemStatus /></WorkbenchShell>);
  assert.match(html, /Evaluating RAG/);
  assert.match(html, /Planned sequence\.<\/strong> Not executed by this screen/);
  for (const step of ["Question", "Retrieval", "Evidence", "Decision", "Evaluation"]) {
    assert.match(html, new RegExp(`<h3[^>]*>${step}</h3>`));
  }
  assert.equal((html.match(/aria-disabled="true"/g) ?? []).length, 2);
  assert.match(html, /href="#system-status"/);
  assert.match(html, /id="system-status"[^>]*tabindex="-1"/);
  assert.match(html, /href="#main-content"/);
  assert.match(html, /aria-label="Main navigation"/);
  assert.doesNotMatch(html, /href="\/(experiments|results)|<input|<form/);
  assert.match(html, /API has no authentication/);
});

for (const expanded of [false, true]) {
  test(`mobile navigation renders its ${expanded ? "expanded" : "collapsed"} state accessibly`, () => {
    const html = renderToStaticMarkup(<WorkbenchNavigationView expanded={expanded}
      onToggle={() => undefined} onNavigate={() => undefined} />);
    assert.match(html, new RegExp(`aria-expanded="${expanded}"`));
    assert.match(html, /type="button"/);
    assert.match(html, /aria-controls="workspace-links"/);
    assert.match(html, new RegExp(`class="workspace-links${expanded ? " is-open" : ""}"`));
    assert.match(html, /aria-disabled="true" tabindex="0" title="Planned:/);
  });
}

interface InteractiveProps { children?: ReactNode; onClick?: () => void; href?: string }

function findControl(node: ReactNode, type: string, href?: string): ReactElement<InteractiveProps> | undefined {
  const walk = (child: ReactNode): ReactElement<InteractiveProps> | undefined => {
    if (!isValidElement<InteractiveProps>(child)) return undefined;
    if (child.type === type && (href === undefined || child.props.href === href)) return child;
    for (const nested of Children.toArray(child.props.children)) {
      const found = walk(nested);
      if (found) return found;
    }
    return undefined;
  };
  return walk(node);
}

test("navigation toggle and in-page navigation invoke the disclosure handlers", () => {
  let expanded = false;
  const view = () => WorkbenchNavigationView({ expanded,
    onToggle: () => { expanded = !expanded; }, onNavigate: () => { expanded = false; } });
  const toggle = findControl(view(), "button");
  assert.ok(toggle?.props.onClick);
  toggle.props.onClick();
  assert.equal(expanded, true);
  const target = findControl(view(), "a", "#system-status");
  assert.ok(target?.props.onClick);
  target.props.onClick();
  assert.equal(expanded, false);
});

test("unknown values keep the operational table stable without invented health data", () => {
  for (const state of [{ phase: "loading" }, { phase: "error", failure: { kind: "connection" } }] as const) {
    const html = renderToStaticMarkup(<StatusView state={state} />);
    assert.equal((html.match(/scope="row"/g) ?? []).length, 6);
    assert.equal((html.match(/class="missing-value"/g) ?? []).length, 6);
    assert.doesNotMatch(html, /<td>Yes|<td>Not tested|<td>RAGBench Studio/);
  }
});

test("status motion and reduced-motion styles stay restrained; Canvas owns continuous wave motion", () => {
  const css = readFileSync("app/globals.css", "utf-8");
  assert.match(css, /particle-wave/);
  assert.match(css, /state-enter var\(--duration-state\)/);
  assert.match(css, /workflow-vertical/);
  const reduced = css.slice(css.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.match(reduced, /scroll-behavior: auto/);
  assert.match(reduced, /animation: none !important/);
  assert.match(reduced, /transition: none !important/);
  assert.doesNotMatch(css, /\binfinite\b|radial-gradient|linear-gradient|backdrop-filter/);
  assert.match(css, /focus-visible/);
  assert.match(css, /@media \(max-width: 600px\)/);
});

test("primary text and control colors retain AA contrast on near-black", () => {
  const css = readFileSync("app/tokens.css", "utf-8");
  const color = (name: string) => {
    const match = css.match(new RegExp(`--${name}: (#[0-9a-f]{6});`));
    assert.ok(match);
    return match[1];
  };
  const luminance = (hex: string) => {
    const channels = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16) / 255);
    const linear = channels.map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
    return linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722;
  };
  const contrast = (left: string, right: string) => {
    const values = [luminance(left), luminance(right)].sort((a, b) => a - b);
    return (values[1] + .05) / (values[0] + .05);
  };
  for (const name of ["ink", "muted", "positive", "highlight"]) {
    assert.ok(contrast(color(name), color("canvas")) >= 4.5, name);
  }
  assert.ok(contrast(color("canvas"), color("ink")) >= 4.5, "button label");
});


test("workbench uses a clear active state, inline notation and a separate vertical workflow", () => {
  const html = renderToStaticMarkup(<WorkbenchShell><SystemStatus /></WorkbenchShell>);
  assert.match(html, /class="workflow-horizontal"/);
  assert.match(html, /class="workflow-vertical"/);
  assert.match(html, /class="workflow-vertical"/);
  assert.match(html, /aria-current="page"/);
  assert.equal((html.match(/class="withheld-stamp"/g) ?? []).length, 1);
  assert.match(html, /class="notation-note"/);
  assert.doesNotMatch(html, /class="interpretation"|<input|<form|<mark/);
  const layout = readFileSync("app/layout.tsx", "utf-8");
  assert.match(layout, /next\/font\/local/);
  assert.match(layout, /display: "swap"/);
  assert.match(layout, /icons: \{ icon: "\/icon.svg" \}/);
  const css = readFileSync("app/globals.css", "utf-8");
  assert.match(css, /::selection/);
  assert.match(css, /tabular-nums/);
  assert.match(css, /rotate\(-1deg\)/);
});


test("review refinements remain conceptual and preserve planned navigation", () => {
  const html = renderToStaticMarkup(<WorkbenchShell><SystemStatus /></WorkbenchShell>);
  assert.match(html, /Concept, not data/);
  assert.match(html, /not measurements or a decision rule/);
  assert.match(html, /class="concept-marker"/);
  assert.equal((html.match(/<sup>soon<\/sup>/g) ?? []).length, 2);
  assert.match(html, /Answer<\/span> \u2013 evidence is enough/);
  assert.match(html, /the question is unclear/);
  assert.equal((html.match(/class="workflow-dot"/g) ?? []).length, 5);
  const css = readFileSync("app/globals.css", "utf-8");
  assert.match(css, /stroke-width: 1.5/);
  assert.match(html, /class="particle-wave" aria-hidden="true"/);
  assert.match(readFileSync("next.config.ts", "utf-8"), /devIndicators: false/);
});


test("review layout places real status controls under the hero beside the concept", () => {
  const html = renderToStaticMarkup(<WorkbenchShell><SystemStatus /></WorkbenchShell>);
  assert.ok(html.indexOf('id="system-status"') < html.indexOf('class="workflow-reference"'));
  assert.ok(html.indexOf('class="workflow-reference"') < html.indexOf('class="notation-note"'));
  assert.match(html, /class="concept-primary"/);
  assert.doesNotMatch(html, /<details[^>]*open/);
  assert.match(html, /class="workflow-steps"/);
  assert.match(html, /Inspect support and missing premises/);
  const css = readFileSync("app/globals.css", "utf-8");
  assert.match(css, /workflow-label \{ font: 400 var\(--type-body\)/);
  assert.match(css, /workflow-note \{ font-size: var\(--type-sm\)/);
});


test("theme is near-black with neutral text and selective green, without a blocking hero scrim", () => {
  const tokens = readFileSync("app/tokens.css", "utf-8");
  assert.match(tokens, /--canvas: #090d0c;/);
  assert.match(tokens, /--surface: #131b18;/);
  assert.match(tokens, /--ink: #eaede7;/);
  const css = readFileSync("app/globals.css", "utf-8");
  assert.doesNotMatch(css, /background: color-mix/);
  assert.match(css, /h1 em \{ color: var\(--positive\)/);
  const html = renderToStaticMarkup(<StatusView state={{ phase: "loading" }} />);
  assert.match(html, /<details class="health-details"><summary>Inspect health fields/);
  assert.doesNotMatch(html, /<details[^>]*open/);
});


test("initial SSR status has the same unconditional disclosure/table shape as the loading view", () => {
  // Effects do not run during SSR: the full client boundary must start in loading,
  // without a bare table, a server-only wrapper, or an initial backend result.
  const shell = renderToString(<SystemStatus />);
  const loading = renderToString(<StatusView state={{ phase: "loading" }} />);
  assert.ok(shell.includes(loading));
  assert.match(shell, /aria-busy="true"/);
  assert.match(shell, /<button[^>]*disabled=""/);
  assert.equal((shell.match(/<details class="health-details">/g) ?? []).length, 1);
  assert.match(shell, /<details class="health-details"><summary>Inspect health fields<\/summary><table class="health-table"><caption>/);
  assert.match(shell, /<tbody><tr>/);
  assert.equal((shell.match(/class="missing-value"/g) ?? []).length, 6);
  assert.equal(shell, renderToString(<SystemStatus />));
});

test("the health disclosure is structurally stable across loading, ready and failure", () => {
  const states = [
    { phase: "loading" }, { phase: "ready", health },
    { phase: "error", failure: { kind: "connection" } },
  ] as const;
  for (const state of states) {
    const html = renderToString(<StatusView state={state} />);
    assert.equal((html.match(/<details class="health-details">/g) ?? []).length, 1);
    assert.match(html, /<details class="health-details"><summary>Inspect health fields<\/summary><table class="health-table">/);
    assert.match(html, /<\/tbody><\/table><\/details>/);
    assert.doesNotMatch(html, /<table[^>]*>\s*<details|<p[^>]*>\s*<details/);
  }
});


test("review details retain strong ink workflow and a one-shot reduced-motion-safe concept marker", () => {
  const css = readFileSync("app/globals.css", "utf-8");
  assert.match(css, /workflow-track \{ fill: none; stroke: var\(--ink\); stroke-width: 1.5/);
  assert.match(css, /node-0 \.workflow-dot \{ background: var\(--ink\)/);
  assert.match(css, /workflow-label[^}]*font-source-serif/);
  assert.match(css, /concept-slide var\(--duration-draw\)/);
  assert.match(css, /margin-note \{ border-left: 1px solid var\(--stone\)/);
  const html = renderToStaticMarkup(<WorkbenchShell><SystemStatus /></WorkbenchShell>);
  assert.match(html, /<aside class="margin-note"><div class="notation-note"/);
  assert.match(html, /class="concept-primary"/);
});


test("header groups the wordmark and navigation; footer is a compact page landmark with real links", () => {
  const html = renderToStaticMarkup(<WorkbenchShell><SystemStatus /></WorkbenchShell>);
  const header = html.match(/<header class="masthead">[\s\S]*?<\/header>/)?.[0];
  assert.ok(header);
  assert.match(header, /class="wordmark"/);
  assert.match(header, /aria-label="Main navigation"/);
  assert.equal((header.match(/aria-disabled="true"/g) ?? []).length, 2);
  assert.doesNotMatch(header, /active-underline/);
  assert.ok(html.indexOf("</main>") < html.indexOf('<footer class="workbench-footer">'));
  const footer = html.slice(html.indexOf('<footer class="workbench-footer">'));
  assert.match(footer, /RAGBench Studio/);
  assert.match(footer, /A workbench for evaluating evidence-grounded AI decisions/);
  assert.match(footer, /Local prototype/);
  assert.match(footer, /API has no authentication/);
  const links = [...footer.matchAll(/href="([^"]+)"/g)].map(match => match[1]);
  assert.deepEqual(links, ["#system-status"]);
});
