import { useMemo } from "react";

export default function ServiceCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "tickets",
        label: "服务工单",
        permission: "service:read",
        render: () => <ServiceTicketManagement />,
      },
      {
        value: "communication",
        label: "客户沟通",
        permission: "service:read",
        render: () => <CustomerCommunication />,
      },
      {
        value: "satisfaction",
        label: "满意度调查",
        permission: "service:read",
        render: () => <CustomerSatisfaction />,
      },
      {
        value: "analytics",
        label: "服务分析",
        permission: "service:read",
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
