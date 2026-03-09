import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import WorkOrderManagement from "./WorkOrderManagement";
import DispatchManagement from "./DispatchManagement";
import ProductionPlanList from "./ProductionPlanList";

export default function ProductionExecutionCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "work-orders",
        label: "工单管理",
        permission: "workorder:read",
        render: () => <WorkOrderManagement />,
      },
      {
        value: "dispatch",
        label: "派工管理",
        permission: "dispatch:read",
        render: () => <DispatchManagement />,
      },
      {
        value: "plans",
        label: "生产计划",
        permission: "production:plan:read",
        render: () => <ProductionPlanList />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="work-orders"
    />
  );
}
