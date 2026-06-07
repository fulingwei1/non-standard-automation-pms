import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import ProjectBoard from "./ProjectBoard";
import ProjectDashboardCenter from "./ProjectDashboardCenter";
import TaskCenter from "./TaskCenter";
import GanttAndResource from "./GanttAndResource";
import ProjectCostCenter from "./ProjectCostCenter";
import ProjectClosing from "./ProjectClosing";
import AIProjectTools from "./AIProjectTools";
import ScheduleBoard from "./ScheduleBoard";
import ProgressReport from "./ProgressReport";
import MilestoneManagement from "./MilestoneManagement";
import WBSTemplateManagement from "./WBSTemplateManagement";

function ProjectTrackingCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "schedule",
        label: "排期看板",
        permission: "project:project:read",
        render: () => <ScheduleBoard />,
      },
      {
        value: "reports",
        label: "进度报告",
        permission: "project:project:read",
        render: () => <ProgressReport />,
      },
      {
        value: "milestones",
        label: "里程碑",
        permission: "project:project:read",
        render: () => <MilestoneManagement />,
      },
      {
        value: "wbs",
        label: "WBS模板",
        permission: "project:project:read",
        render: () => <WBSTemplateManagement />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="项目进度跟踪"
      description="统一查看排期、进度报告、里程碑与 WBS 模板"
      tabs={tabs}
      defaultTab="schedule"
      showHeader={false}
      searchParamName="trackingTab"
    />
  );
}

export default function ProjectManagementCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "board",
        label: "看板",
        permission: "project:project:read",
        render: () => <ProjectBoard />,
      },
      {
        value: "dashboard",
        label: "驾驶舱",
        permission: "project:project:read",
        render: () => (
          <ProjectDashboardCenter embedded searchParamName="dashboardTab" />
        ),
      },
      {
        value: "tasks",
        label: "任务",
        permission: "project:project:read",
        render: () => <TaskCenter />,
      },
      {
        value: "tracking",
        label: "进度",
        permission: "project:project:read",
        render: () => <ProjectTrackingCenter />,
      },
      {
        value: "planning",
        label: "计划资源",
        permissionAny: ["project:project:read", "project:read"],
        render: () => (
          <GanttAndResource embedded searchParamName="planningTab" />
        ),
      },
      {
        value: "cost",
        label: "成本",
        permissionAny: ["budget:read", "cost:accounting:read"],
        render: () => <ProjectCostCenter embedded searchParamName="costTab" />,
      },
      {
        value: "closing",
        label: "收尾",
        permission: "project:close",
        render: () => (
          <ProjectClosing embedded searchParamName="closingTab" />
        ),
      },
      {
        value: "ai",
        label: "AI工具",
        permission: "project:project:read",
        render: () => <AIProjectTools embedded searchParamName="aiTab" />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      title="项目管理中心"
      description="从项目看板、任务执行、计划资源、成本毛利到收尾复盘的一站式入口"
      tabs={tabs}
      defaultTab="board"
    />
  );
}
