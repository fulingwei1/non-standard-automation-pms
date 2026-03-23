import { useMemo } from "react";

export default function SalesTeamCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "team",
        label: "团队管理",
        permission: "sales:team:read",
        render: () => <SalesTeam embedded />,
      },
      {
        value: "incentives",
        label: "奖金激励",
        permission: "sales:opportunity:read",
        render: () => <PerformanceIncentive embedded />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="销售团队"
      description="统一管理销售组织与激励机制"
      tabs={tabs}
    />
  );
}
