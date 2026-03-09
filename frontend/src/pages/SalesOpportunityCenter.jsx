import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import LeadManagement from "./LeadManagement";
import OpportunityManagement from "./OpportunityManagement";

export default function SalesOpportunityCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "leads",
        label: "线索管理",
        permission: "sales:lead:read",
        render: () => <LeadManagement embedded />,
      },
      {
        value: "opportunities",
        label: "商机管理",
        permission: "sales:opportunity:read",
        render: () => <OpportunityManagement embedded />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="商机中心"
      description="统一管理销售线索与商机推进"
      tabs={tabs}
    />
  );
}
