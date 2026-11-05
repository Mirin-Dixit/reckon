import { QueryLab } from "../../components/query-lab";
import { WorkbenchShell } from "../../components/workbench-shell";

export const metadata = { title: "Query Lab | Reckon" };
export default function QueryLabPage() {
  return <WorkbenchShell workspace="query-lab"><QueryLab /></WorkbenchShell>;
}
