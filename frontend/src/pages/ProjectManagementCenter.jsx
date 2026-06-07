import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui";
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
import {
  Calculator,
  ClipboardCheck,
  ClipboardList,
  ExternalLink,
  Lightbulb,
  ListTodo,
  Settings,
  Target,
} from "lucide-react";

const PRESALES_CONTEXT_FIELDS = [
  { target: "ticket_id", keys: ["ticket_id", "ticketId"] },
  { target: "lead_id", keys: ["lead_id", "leadId"] },
  { target: "opportunity_id", keys: ["opportunity_id", "opportunityId"] },
  { target: "project_id", keys: ["project_id", "projectId"] },
];

function getFirstSearchValue(searchParams, keys) {
  for (const key of keys) {
    const value = searchParams.get(key);
    if (value) {
      return value;
    }
  }
  return "";
}

function appendPresalesContext(searchParams, targetParams) {
  PRESALES_CONTEXT_FIELDS.forEach(({ target, keys }) => {
    const value = getFirstSearchValue(searchParams, keys);
    if (value) {
      targetParams.set(target, value);
    }
  });
}

function buildUnifiedPresalesPath(searchParams, tab) {
  const params = new URLSearchParams();
  params.set("tab", tab);
  appendPresalesContext(searchParams, params);
  return `/presales/technical-solutions?${params.toString()}`;
}

function buildProjectWorkspacePath(searchParams) {
  const projectId = getFirstSearchValue(searchParams, ["project_id", "projectId"]);
  if (!projectId) {
    return null;
  }

  const params = new URLSearchParams();
  appendPresalesContext(searchParams, params);
  const query = params.toString();
  return `/projects/${projectId}/workspace${query ? `?${query}` : ""}`;
}

function ProjectPresalesHandoverCenter() {
  const [searchParams] = useSearchParams();
  const workspacePath = buildProjectWorkspacePath(searchParams);
  const presalesLinks = [
    {
      title: "工单看板",
      description: "查看售前工单、PM介入、交付追踪和工单产出。",
      tab: "reviews",
      icon: ListTodo,
    },
    {
      title: "需求调研",
      description: "补齐客户现场、节拍、治具、上下料和验收口径。",
      tab: "surveys",
      icon: ClipboardList,
    },
    {
      title: "方案管理",
      description: "承接销售需求，沉淀方案版本和项目交接输入。",
      tab: "solutions",
      icon: Lightbulb,
    },
    {
      title: "技术参数",
      description: "维护 ICT、FCT、EOL 等模板，支撑成本估算。",
      tab: "parameters",
      icon: Settings,
    },
    {
      title: "成本估算",
      description: "对齐售前估算、报价成本和项目成本基线。",
      tab: "cost",
      icon: Calculator,
    },
    {
      title: "投标支持",
      description: "管理标书、投标阶段和成本方案联动。",
      tab: "bids",
      icon: Target,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">售前交接</h2>
          <p className="mt-1 text-sm text-slate-400">
            从项目管理中心进入统一售前技术支持中心，并保留当前项目、商机、线索和工单上下文。
          </p>
        </div>
        {workspacePath && (
          <Button asChild variant="outline" className="shrink-0">
            <Link to={workspacePath}>
              <ClipboardCheck className="h-4 w-4" />
              项目交接包
            </Link>
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {presalesLinks.map(({ title, description, tab, icon: Icon }) => (
          <Card key={tab} className="border-white/5 bg-surface-100/50">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base text-white">
                <Icon className="h-4 w-4 text-primary" />
                {title}
              </CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="secondary" size="sm">
                <Link to={buildUnifiedPresalesPath(searchParams, tab)}>
                  打开{title}
                  <ExternalLink className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

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
        value: "presales",
        label: "售前",
        permissionAny: ["project:project:read", "presales:task:read"],
        render: () => <ProjectPresalesHandoverCenter />,
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
