import { useMemo } from "react";

export default function FieldResourceCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "workshops",
        label: "车间管理",
        permission: "workshop:read",
        render: () => <WorkshopManagement />,
      },
      {
        value: "workers",
        label: "工人管理",
        permission: "worker:read",
        render: () => <WorkerManagement />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="workshops"
    />
  );
}
