import { useMemo } from "react";

export default function OrganizationCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "organization",
        label: "组织管理",
        permission: "system:org:manage",
        render: () => <OrganizationManagement />,
      },
      {
        value: "positions",
        label: "岗位管理",
        permission: "system:position:manage",
        render: () => <PositionManagement />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="organization"
    />
  );
}
