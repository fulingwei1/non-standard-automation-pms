import { useMemo } from "react";

export default function MaterialCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "bom",
        label: "BOM管理",
        permission: "bom:read",
        render: () => <BOMManagement />,
      },
      {
        value: "materials",
        label: "物料管理",
        permission: "material:read",
        render: () => <MaterialList />,
      },
      {
        value: "demands",
        label: "物料需求",
        permission: "material:demand:read",
        render: () => <MaterialDemandSummary />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="bom"
    />
  );
}
