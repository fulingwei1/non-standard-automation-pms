import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import IssueManagement from "./IssueManagement";
import ProductionExceptionList from "./ProductionExceptionList";

export default function ExceptionCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "issues",
        label: "问题异常",
        permission: "issue:read",
        render: () => <IssueManagement embedded />,
      },
      {
        value: "production",
        label: "生产异常",
        permission: "production:exception:read",
        render: () => <ProductionExceptionList embedded />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="异常中心"
      description="统一处理问题异常与生产异常"
      tabs={tabs}
    />
  );
}
