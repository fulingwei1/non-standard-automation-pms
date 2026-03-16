import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import AcceptanceManagement from "./AcceptanceManagement";
import FieldCommissioning from "./FieldCommissioning";
import InstallationDispatchManagement from "./InstallationDispatchManagement";

export default function DeliveryAcceptanceCenter() {
  const tabs = useMemo(
    () => [
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
      defaultTab="acceptance"
    />
  );
}
