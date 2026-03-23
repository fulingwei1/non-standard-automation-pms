import { useMemo } from "react";

export default function TemplateCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "stages",
        label: "阶段模板",
        permission: "system:template:manage",
        render: () => <StageTemplateManagement />,
      },
      {
        value: "configs",
        label: "模板配置",
        permission: "system:template:manage",
        render: () => <TemplateConfigList />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="stages"
    />
  );
}
