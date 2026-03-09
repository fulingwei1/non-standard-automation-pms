import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import PMODashboard from "./PMODashboard";
import ProjectHealthMonitor from "./ProjectHealthMonitor";

export default function ProjectDashboardCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "pmo",
        label: "PMO驾驶舱",
        permission: "project:project:read",
        render: () => <PMODashboard embedded />,
      },
      {
        value: "health",
        label: "项目健康监控",
        permission: "project:project:read",
        render: () => <ProjectHealthMonitor embedded />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="项目驾驶舱"
      description="统一查看 PMO 总览与项目健康监控"
      tabs={tabs}
    />
  );
}
