import { useMemo } from "react";
import { Navigate } from "react-router-dom";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import { usePermission } from "../hooks/usePermission";
import SalesTeam from "./SalesTeam";
import PerformanceIncentive from "./SalesAI/PerformanceIncentive";

export default function SalesTeamCenter() {
  const { hasPermission, isLoading, isSuperuser } = usePermission();
  const canAccessSalesTeam = isSuperuser || hasPermission("sales_team:read");
  const tabs = useMemo(
    () => [
      {
        value: "team",
        label: "团队管理",
        permission: "sales_team:read",
        render: () => <SalesTeam embedded />,
      },
      {
        value: "incentives",
        label: "奖金激励",
        permission: "sales_team:read",
        render: () => <PerformanceIncentive embedded />,
      },
    ],
    [],
  );

  if (isLoading) {
    return null;
  }

  if (!canAccessSalesTeam) {
    return <Navigate to="/sales/workstation" replace />;
  }

  return (
    <TabbedCenterPage
      title="销售团队"
      description="统一管理销售组织与激励机制"
      tabs={tabs}
    />
  );
}
