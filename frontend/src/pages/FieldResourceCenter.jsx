import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import WorkshopManagement from "./WorkshopManagement";
import WorkerManagement from "./WorkerManagement";

export default function FieldResourceCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "workshops",
        label: "车间管理",
        permission: "workshop:read",
        render: () => <WorkshopManagement />,
      },
      {
        value: "workers",
        label: "工人管理",
        permission: "worker:read",
        render: () => <WorkerManagement />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="workshops"
    />
  );
}
