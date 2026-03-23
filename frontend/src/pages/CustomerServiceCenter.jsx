import { useMemo } from "react";

export default function CustomerServiceCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "workbench",
        label: "客服工作台",
        permission: "service:read",
        render: () => <CustomerServiceWorkbench />,
      },
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
      {
        value: "acceptance",
        label: "验收管理",
        permission: "acceptance:read",
        render: () => <AcceptanceManagement />,
      },
      {
        value: "commissioning",
        label: "现场调试",
        permission: "installation_dispatch:read",
        render: () => <FieldCommissioning />,
      },
      {
        value: "installation",
        label: "安装调试",
        permission: "installation_dispatch:read",
        render: () => <InstallationDispatchManagement />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="workbench"
    />
  );
}
