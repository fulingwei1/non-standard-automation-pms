import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import PerformanceManagement from "./PerformanceManagement";
import PerformanceContract from "./PerformanceContract";
import EvaluationWeightConfig from "./EvaluationWeightConfig";

export default function PerformanceCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "management",
        label: "绩效管理",
        permission: "performance:manage",
        render: () => <PerformanceManagement />,
      },
      {
        value: "contract",
        label: "绩效合约",
        permission: "performance:manage",
        render: () => <PerformanceContract />,
      },
      {
        value: "config",
        label: "评价配置",
        permission: "evaluation:config:manage",
        render: () => <EvaluationWeightConfig />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="management"
    />
  );
}
