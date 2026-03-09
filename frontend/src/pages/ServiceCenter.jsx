import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import ServiceTicketManagement from "./ServiceTicketManagement";
import CustomerCommunication from "./CustomerCommunication";
import CustomerSatisfaction from "./CustomerSatisfaction";
import ServiceAnalytics from "./ServiceAnalytics";

export default function ServiceCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "tickets",
        label: "服务工单",
        permission: "service:ticket:read",
        render: () => <ServiceTicketManagement />,
      },
      {
        value: "communication",
        label: "客户沟通",
        permission: "customer:communication:read",
        render: () => <CustomerCommunication />,
      },
      {
        value: "satisfaction",
        label: "满意度调查",
        permission: "customer:satisfaction:read",
        render: () => <CustomerSatisfaction />,
      },
      {
        value: "analytics",
        label: "服务分析",
        permission: "service:analytics:read",
        render: () => <ServiceAnalytics />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="tickets"
    />
  );
}
