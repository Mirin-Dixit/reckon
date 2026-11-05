import { ExperimentRunner } from "../../components/experiment-runner";
import { WorkbenchShell } from "../../components/workbench-shell";

export const metadata = { title: "Experiments | Reckon" };
export default function ExperimentsPage() {
  return <WorkbenchShell workspace="experiments"><ExperimentRunner /></WorkbenchShell>;
}
