import { useMemo } from "react";

export default function ProjectCostCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "budget",
        label: "预算管理",
        permission: "budget:read",
        render: () => <BudgetManagement embedded />,
      },
      {
        value: "margin",
        label: "工时成本毛利",
        permission: "cost:accounting:read",
        render: () => <TimeCostMarginFlow embedded />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="项目成本中心"
      description="统一查看项目预算与工时成本毛利联动"
      tabs={tabs}
    />
  );
}
