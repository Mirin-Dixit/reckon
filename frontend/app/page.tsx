import { SystemStatus } from "../components/system-status";
import { WorkbenchShell } from "../components/workbench-shell";

export default function Home() {
  return (
    <WorkbenchShell>
        <SystemStatus />
    </WorkbenchShell>
  );
}
