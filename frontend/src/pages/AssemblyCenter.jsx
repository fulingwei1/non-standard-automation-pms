import { useMemo } from "react";

export default function AssemblyCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "tasks",
        label: "装配任务",
        permission: "assembly:task:read",
        render: () => <AssemblerTaskCenter />,
      },
      {
        value: "kit-rate",
        label: "装配齐套率管理",
        permission: "production:board:read",
        render: () => <AssemblyKitBoard />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="tasks"
    />
  );
}
