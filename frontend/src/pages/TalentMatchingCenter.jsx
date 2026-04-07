import { useMemo } from "react";

export default function TalentMatchingCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "tags",
        label: "标签管理",
        permission: "staff:tag:manage",
        render: () => <TagManagement />,
      },
      {
        value: "profiles",
        label: "员工档案",
        permission: "staff:profile:read",
        render: () => <EmployeeProfileList />,
      },
      {
        value: "needs",
        label: "人员需求",
        permission: "staff:need:read",
        render: () => <ProjectStaffingNeed />,
      },
      {
        value: "matching",
        label: "AI智能匹配",
        permission: "staff:match:read",
        render: () => <AIStaffMatching />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="tags"
    />
  );
}
