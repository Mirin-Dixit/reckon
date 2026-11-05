import { EvaluationDashboard } from "../../components/evaluation-dashboard";
import { WorkbenchShell } from "../../components/workbench-shell";

export const metadata = { title: "Evaluation Dashboard | RAGBench Studio" };

export default function EvaluationPage() {
  return <WorkbenchShell workspace="evaluation"><EvaluationDashboard /></WorkbenchShell>;
}
