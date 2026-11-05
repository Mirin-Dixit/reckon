import Link from "next/link";
import type { ReactNode } from "react";
import { WorkbenchNavigation } from "./workbench-navigation";
import { WorkflowLine } from "./workflow-line";
import { MarginNote } from "./margin-note";
import { ParticleWave } from "./particle-wave";
import { SufficiencyLine } from "./sufficiency-line";
import { DecisionMark } from "./decision-mark";

export function WorkbenchShell({ children, workspace = "workbench" }: { children: ReactNode; workspace?: "workbench" | "query-lab" | "experiments" | "evaluation" }) {
  return <div className="workbench-frame">
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <header className="masthead">
      <Link className="wordmark" href="/#main-content" aria-label="RAGBench Studio workbench">RAGBench <span>Studio</span></Link>
      <WorkbenchNavigation workspace={workspace} />
    </header>
    <main id="main-content" tabIndex={-1}>
      {workspace === "workbench" ? <><section className="notebook-opening" aria-labelledby="workbench-title">
        <ParticleWave />
        <div className="hero-copy"><p className="page-eyebrow">Retrieval / Evidence / Decision</p>
          <h1 id="workbench-title">Evaluating RAG<br />with <em>evidence.</em></h1>
          <p className="opening-copy">When should a RAG system <strong>answer, abstain,</strong> or ask for <strong>clarification?</strong></p>
        </div>
        <p className="wave-caption">Conceptual field / not experimental data</p>
      </section>
      <div className="workbench-tools">
        <div className="concept-primary"><SufficiencyLine />
          <MarginNote><p><strong>Concept only.</strong> Support matters more than passage count; unclear intent can require clarification at any evidence amount.</p></MarginNote>
        </div>
        <div className="operational-layout">{children}</div>
      </div>
      <section className="workflow-reference" aria-labelledby="workflow-heading">
        <div className="workflow-heading"><h2 id="workflow-heading">From question to evaluation</h2><p><strong>Planned sequence.</strong> Not executed by this screen.</p></div>
        <div className="workflow-with-notes"><WorkflowLine />
          <MarginNote><div className="notation-note" aria-label="Decision notation">
            <p><DecisionMark decision="answer" /> {"\u2013"} evidence is enough</p>
            <p><DecisionMark decision="abstain" /> {"\u2013"} evidence is not enough</p>
            <p><DecisionMark decision="clarify" /> {"\u2013"} the question is unclear</p>
          </div></MarginNote>
        </div>
      </section></> : children}
    </main>
    <footer className="workbench-footer">
      <div className="footer-identity"><p className="footer-wordmark">RAGBench Studio</p>
        <p>A workbench for evaluating evidence-grounded AI decisions.</p>
        <p className="footer-request-note">{workspace === "workbench" ? "No questions, experiments, or benchmark labels are requested here." : workspace === "evaluation" ? "Saved synthetic results only. No model inference is requested." : workspace === "experiments" ? "Synthetic experiments only. Empirical evaluation is deferred." : "Queries run only when submitted. Benchmark gold labels are not requested."}</p>
      </div>
      <div className="footer-local"><p><strong>Local prototype</strong><a href={workspace === "workbench" ? "#system-status" : "/#system-status"}>System status</a></p>
        <p>The API has no authentication. Keep this workspace on loopback.</p>
      </div>
    </footer>
  </div>;
}
