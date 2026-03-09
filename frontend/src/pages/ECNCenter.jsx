import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import ECNManagement from "./ECNManagement";
import ECNTypeManagement from "./ECNTypeManagement";
import ECNStatistics from "./ECNStatistics";

export default function ECNCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "management",
        label: "ECN管理",
        permission: "ecn:read",
        render: () => <ECNManagement embedded />,
      },
      {
        value: "types",
        label: "ECN类型",
        permission: "ecn:type:read",
        render: () => <ECNTypeManagement embedded />,
      },
      {
        value: "statistics",
        label: "ECN统计",
        permission: "ecn:statistics:read",
        render: () => <ECNStatistics embedded />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="ECN中心"
      description="统一管理变更单、类型配置与统计分析"
      tabs={tabs}
    />
  );
}
