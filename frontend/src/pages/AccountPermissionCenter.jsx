import { useMemo } from "react";

export default function AccountPermissionCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "users",
        label: "用户管理",
        permission: "USER_VIEW",
        render: () => <UserManagement />,
      },
      {
        value: "roles",
        label: "角色管理",
        permission: "ROLE_VIEW",
        render: () => <RoleManagement />,
      },
      {
        value: "permissions",
        label: "权限管理",
        permission: "ROLE_VIEW",
        render: () => <PermissionManagement />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="users"
    />
  );
}
