import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  ClipboardList,
  Headphones,
  RefreshCw,
  UserRound,
  Wrench,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { isManagerRole } from "../lib/roleConfig/roleUtils";
import {
  cn,
  formatDate,
  formatDateTime,
  formatPercent,
  getStageName,
} from "../lib/utils";
import { userApi } from "../services/api/auth";
import { issueApi } from "../services/api/issues";
import { projectApi } from "../services/api/projects";
import { installationDispatchApi, serviceApi } from "../services/api/service";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  DashboardStatCard,
  EmptyState,
  ErrorMessage,
  HealthBadge,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";

const PAGE_SIZE = 500;
const TEAM_OVERVIEW_KEY = "team";
const SERVICE_MANAGER_ROLES = new Set([
  "customer_service_manager",
  "admin",
  "super_admin",
  "gm",
  "chairman",
]);
const RESOLVED_TICKET_STATUSES = new Set(["RESOLVED", "CLOSED"]);
const ACTIVE_TICKET_STATUSES = new Set(["PENDING", "IN_PROGRESS", "PENDING_VERIFY"]);
const RESOLVED_ISSUE_STATUSES = new Set(["RESOLVED", "CLOSED", "VERIFIED", "DONE"]);
const ACTIVE_RECORD_STATUSES = new Set(["SCHEDULED", "IN_PROGRESS", "ACTIVE"]);
const ACTIVE_ORDER_STATUSES = new Set(["PENDING", "ASSIGNED", "IN_PROGRESS"]);

function unwrapResponseBody(response) {
  if (!response) {
    return null;
  }

  if (response.data?.data !== undefined) {
    return response.data.data;
  }

  if (response.data !== undefined) {
    return response.data;
  }

  return response;
}

function unwrapItems(response) {
  const body = unwrapResponseBody(response);
  if (Array.isArray(body)) {
    return body;
  }
  return Array.isArray(body?.items) ? body.items : [];
}

function toNumber(value, fallback = 0) {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : fallback;
}

function toTrimmedString(value) {
  return String(value || "").trim();
}

function normalizeTicket(ticket = {}) {
  return {
    ...ticket,
    id: ticket.id,
    ticket_no: ticket.ticket_no || `T-${ticket.id}`,
    project_id: ticket.project_id,
    project_name: ticket.project_name || "未关联项目",
    problem_desc: ticket.problem_desc || ticket.title || "-",
    urgency: ticket.urgency || "-",
    status: toTrimmedString(ticket.status).toUpperCase() || "PENDING",
    reported_time: ticket.reported_time || ticket.created_at || null,
    assigned_to_id: ticket.assigned_to_id ?? null,
    assigned_to_name: ticket.assigned_to_name || ticket.assignee_name || "",
  };
}

function normalizeRecord(record = {}) {
  return {
    ...record,
    id: record.id,
    record_no: record.record_no || `R-${record.id}`,
    project_id: record.project_id,
    project_name: record.project_name || "未关联项目",
    service_type: record.service_type || "-",
    service_date: record.service_date || record.created_at || null,
    status: toTrimmedString(record.status).toUpperCase() || "SCHEDULED",
    service_engineer_id: record.service_engineer_id ?? null,
    service_engineer_name: record.service_engineer_name || "",
    service_content: record.service_content || "-",
    issues_found: record.issues_found || "",
  };
}

function normalizeOrder(order = {}) {
  return {
    ...order,
    id: order.id,
    order_no: order.order_no || `D-${order.id}`,
    project_id: order.project_id,
    project_name: order.project_name || "未关联项目",
    task_title: order.task_title || "-",
    task_type: order.task_type || "-",
    status: toTrimmedString(order.status).toUpperCase() || "PENDING",
    priority: order.priority || "-",
    scheduled_date: order.scheduled_date || order.created_at || null,
    assigned_to_id: order.assigned_to_id ?? null,
    assigned_to_name: order.assigned_to_name || "",
    progress: toNumber(order.progress),
  };
}

function normalizeProject(project = {}) {
  return {
    ...project,
    id: project.id,
    project_code: project.project_code || `P-${project.id}`,
    project_name: project.project_name || "未命名项目",
    customer_name: project.customer_name || "-",
    stage: project.stage || "-",
    health: project.health || null,
    progress_pct: toNumber(project.progress_pct),
    pm_name: project.pm_name || "-",
  };
}

function normalizeIssue(issue = {}) {
  return {
    ...issue,
    id: issue.id,
    issue_no: issue.issue_no || `I-${issue.id}`,
    title: issue.title || "-",
    project_id: issue.project_id ?? null,
    project_name: issue.project_name || "未关联项目",
    status: toTrimmedString(issue.status).toUpperCase() || "OPEN",
    severity: issue.severity || "-",
    priority: issue.priority || "-",
    assignee_id: issue.assignee_id ?? null,
    assignee_name: issue.assignee_name || "",
    responsible_engineer_id: issue.responsible_engineer_id ?? null,
    responsible_engineer_name: issue.responsible_engineer_name || "",
    solution: issue.solution || "",
    report_date: issue.report_date || issue.created_at || null,
  };
}

function normalizeUser(user = {}) {
  return {
    ...user,
    id: user.id,
    username: user.username || "",
    real_name: user.real_name || user.username || "未命名工程师",
    department: user.department || "",
    position: user.position || "",
    roles: Array.isArray(user.roles) ? user.roles : [],
  };
}

function isTicketResolved(status) {
  return RESOLVED_TICKET_STATUSES.has(toTrimmedString(status).toUpperCase());
}

function isTicketActive(status) {
  return ACTIVE_TICKET_STATUSES.has(toTrimmedString(status).toUpperCase());
}

function isIssueResolved(status) {
  return RESOLVED_ISSUE_STATUSES.has(toTrimmedString(status).toUpperCase());
}

function isRecordActive(status) {
  return ACTIVE_RECORD_STATUSES.has(toTrimmedString(status).toUpperCase());
}

function isOrderActive(status) {
  return ACTIVE_ORDER_STATUSES.has(toTrimmedString(status).toUpperCase());
}

function getTicketStatusLabel(status) {
  return (
    {
      PENDING: "待处理",
      IN_PROGRESS: "处理中",
      PENDING_VERIFY: "待验证",
      RESOLVED: "已解决",
      CLOSED: "已关闭",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

function getIssueStatusLabel(status) {
  return (
    {
      OPEN: "待处理",
      PROCESSING: "处理中",
      IN_PROGRESS: "处理中",
      RESOLVED: "已解决",
      VERIFIED: "已验证",
      CLOSED: "已关闭",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

function getRecordStatusLabel(status) {
  return (
    {
      SCHEDULED: "待执行",
      IN_PROGRESS: "进行中",
      ACTIVE: "进行中",
      COMPLETED: "已完成",
      APPROVED: "已归档",
      CANCELLED: "已取消",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

function getOrderStatusLabel(status) {
  return (
    {
      PENDING: "待派工",
      ASSIGNED: "已派工",
      IN_PROGRESS: "进行中",
      COMPLETED: "已完成",
      CANCELLED: "已取消",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

function getStatusBadgeVariant(status) {
  const normalized = toTrimmedString(status).toUpperCase();
  if (
    ["CLOSED", "RESOLVED", "VERIFIED", "DONE", "COMPLETED", "APPROVED"].includes(
      normalized,
    )
  ) {
    return "success";
  }
  if (["PENDING_VERIFY", "ASSIGNED", "SCHEDULED"].includes(normalized)) {
    return "warning";
  }
  if (["IN_PROGRESS", "PROCESSING", "ACTIVE", "OPEN"].includes(normalized)) {
    return "info";
  }
  if (["CANCELLED", "REJECTED", "FAILED", "BLOCKED"].includes(normalized)) {
    return "danger";
  }
  return "secondary";
}

function getUrgencyBadgeVariant(urgency) {
  const normalized = toTrimmedString(urgency).toUpperCase();
  if (["URGENT", "CRITICAL", "HIGH", "紧急", "高"].includes(normalized)) {
    return "danger";
  }
  if (["MEDIUM", "中"].includes(normalized)) {
    return "warning";
  }
  return "secondary";
}

function engineerMatches(engineer, userId, userName) {
  if (!engineer) {
    return false;
  }

  if (engineer.id !== null && engineer.id !== undefined && userId !== null && userId !== undefined) {
    return Number(engineer.id) === Number(userId);
  }

  const normalizedEngineerName = toTrimmedString(engineer.name);
  const normalizedUserName = toTrimmedString(userName);
  return Boolean(normalizedEngineerName && normalizedUserName && normalizedEngineerName === normalizedUserName);
}

function ensureProjectFallback(projectMap, projectId, projectName) {
  if (!projectId || projectMap.has(projectId)) {
    return;
  }

  projectMap.set(
    projectId,
    normalizeProject({
      id: projectId,
      project_name: projectName || `项目 #${projectId}`,
    }),
  );
}

function buildProjectMap(projects, tickets, records, orders) {
  const projectMap = new Map();

  (projects || []).forEach((project) => {
    if (project?.id) {
      projectMap.set(project.id, normalizeProject(project));
    }
  });

  (tickets || []).forEach((ticket) => {
    ensureProjectFallback(projectMap, ticket.project_id, ticket.project_name);
  });
  (records || []).forEach((record) => {
    ensureProjectFallback(projectMap, record.project_id, record.project_name);
  });
  (orders || []).forEach((order) => {
    ensureProjectFallback(projectMap, order.project_id, order.project_name);
  });

  return projectMap;
}

function buildIssuesByProject(issues) {
  const issueMap = new Map();

  (issues || []).forEach((issue) => {
    if (!issue.project_id) {
      return;
    }
    if (!issueMap.has(issue.project_id)) {
      issueMap.set(issue.project_id, []);
    }
    issueMap.get(issue.project_id).push(issue);
  });

  return issueMap;
}

function isServiceEngineerUser(user) {
  const candidates = [
    user.role,
    user.position,
    ...(Array.isArray(user.roles) ? user.roles : []),
  ]
    .flatMap((item) => {
      if (!item) {
        return [];
      }
      if (typeof item === "string") {
        return [item];
      }
      return [item.role_code, item.role_name, item.role].filter(Boolean);
    })
    .map((item) => toTrimmedString(item).toLowerCase());

  return candidates.some((item) =>
    item === "customer_service_engineer" || item.includes("客服工程师"),
  );
}

function buildEngineerRoster({
  tickets,
  records,
  orders,
  projectsById,
  issuesByProject,
  serviceEngineers,
  currentUser,
}) {
  const engineerMap = new Map();

  const ensureEngineer = (id, name, extra = {}) => {
    const resolvedName = toTrimmedString(name) || (id ? `工程师 #${id}` : "未命名工程师");
    const key = id ? String(id) : `name:${resolvedName}`;

    if (!engineerMap.has(key)) {
      engineerMap.set(key, {
        key,
        id: id ?? null,
        name: resolvedName,
        department: extra.department || "",
        position: extra.position || "",
        projectIds: new Set(),
        ticketCount: 0,
        openTicketCount: 0,
        resolvedTicketCount: 0,
        recordCount: 0,
        activeRecordCount: 0,
        orderCount: 0,
        activeOrderCount: 0,
      });
    }

    const engineer = engineerMap.get(key);
    engineer.department = engineer.department || extra.department || "";
    engineer.position = engineer.position || extra.position || "";
    if ((!engineer.id || engineer.id === null) && id) {
      engineer.id = id;
      engineer.key = String(id);
      engineerMap.delete(key);
      engineerMap.set(engineer.key, engineer);
    }
    return engineer;
  };

  (serviceEngineers || []).forEach((user) => {
    ensureEngineer(user.id, user.real_name || user.username, {
      department: user.department,
      position: user.position,
    });
  });

  (tickets || []).forEach((ticket) => {
    if (!ticket.assigned_to_id && !ticket.assigned_to_name) {
      return;
    }
    const engineer = ensureEngineer(ticket.assigned_to_id, ticket.assigned_to_name);
    engineer.ticketCount += 1;
    engineer.openTicketCount += isTicketActive(ticket.status) ? 1 : 0;
    engineer.resolvedTicketCount += isTicketResolved(ticket.status) ? 1 : 0;
    if (ticket.project_id) {
      engineer.projectIds.add(ticket.project_id);
    }
  });

  (records || []).forEach((record) => {
    if (!record.service_engineer_id && !record.service_engineer_name) {
      return;
    }
    const engineer = ensureEngineer(record.service_engineer_id, record.service_engineer_name);
    engineer.recordCount += 1;
    engineer.activeRecordCount += isRecordActive(record.status) ? 1 : 0;
    if (record.project_id) {
      engineer.projectIds.add(record.project_id);
    }
  });

  (orders || []).forEach((order) => {
    if (!order.assigned_to_id && !order.assigned_to_name) {
      return;
    }
    const engineer = ensureEngineer(order.assigned_to_id, order.assigned_to_name);
    engineer.orderCount += 1;
    engineer.activeOrderCount += isOrderActive(order.status) ? 1 : 0;
    if (order.project_id) {
      engineer.projectIds.add(order.project_id);
    }
  });

  if (currentUser?.id) {
    ensureEngineer(currentUser.id, currentUser.real_name || currentUser.username, {
      department: currentUser.department,
      position: currentUser.position,
    });
  }

  return Array.from(engineerMap.values())
    .map((engineer) => {
      const projectIds = Array.from(engineer.projectIds);
      const issueCount = projectIds.reduce(
        (count, projectId) => count + (issuesByProject.get(projectId)?.length || 0),
        0,
      );
      return {
        ...engineer,
        projectIds,
        projectCount: projectIds.length,
        issueCount,
        activeLoad:
          engineer.openTicketCount + engineer.activeRecordCount + engineer.activeOrderCount,
        primaryProjectName:
          projectIds.length > 0 ? projectsById.get(projectIds[0])?.project_name || "未命名项目" : "",
      };
    })
    .sort((left, right) => {
      if (right.activeLoad !== left.activeLoad) {
        return right.activeLoad - left.activeLoad;
      }
      if (right.projectCount !== left.projectCount) {
        return right.projectCount - left.projectCount;
      }
      return left.name.localeCompare(right.name, "zh-CN");
    });
}

function buildScopedView({ engineer, tickets, records, orders, projectsById, issues, issuesByProject }) {
  const scopedTickets = engineer
    ? tickets.filter((ticket) =>
        engineerMatches(engineer, ticket.assigned_to_id, ticket.assigned_to_name),
      )
    : [...tickets];

  const scopedRecords = engineer
    ? records.filter((record) =>
        engineerMatches(engineer, record.service_engineer_id, record.service_engineer_name),
      )
    : [...records];

  const scopedOrders = engineer
    ? orders.filter((order) =>
        engineerMatches(engineer, order.assigned_to_id, order.assigned_to_name),
      )
    : [...orders];

  const relatedProjectIds = new Set();
  (scopedTickets || []).forEach((ticket) => ticket.project_id && relatedProjectIds.add(ticket.project_id));
  (scopedRecords || []).forEach((record) => record.project_id && relatedProjectIds.add(record.project_id));
  (scopedOrders || []).forEach((order) => order.project_id && relatedProjectIds.add(order.project_id));
  (engineer?.projectIds || []).forEach((projectId) => relatedProjectIds.add(projectId));

  const scopedProjects = Array.from(relatedProjectIds)
    .map((projectId) => projectsById.get(projectId))
    .filter(Boolean)
    .map((project) => {
      const projectIssues = issuesByProject.get(project.id) || [];
      const unresolvedIssues = projectIssues.filter((issue) => !isIssueResolved(issue.status)).length;
      const projectTickets = scopedTickets.filter((ticket) => ticket.project_id === project.id).length;
      return {
        ...project,
        ticketCount: projectTickets,
        issueCount: projectIssues.length,
        unresolvedIssues,
      };
    })
    .sort((left, right) => right.unresolvedIssues - left.unresolvedIssues || right.ticketCount - left.ticketCount);

  const scopedIssues = (issues || [])
    .filter((issue) => {
      if (relatedProjectIds.has(issue.project_id)) {
        return true;
      }
      if (!engineer) {
        return false;
      }
      return (
        engineerMatches(engineer, issue.assignee_id, issue.assignee_name) ||
        engineerMatches(
          engineer,
          issue.responsible_engineer_id,
          issue.responsible_engineer_name,
        )
      );
    })
    .sort((left, right) => new Date(right.report_date || 0) - new Date(left.report_date || 0));

  return {
    tickets: scopedTickets.sort(
      (left, right) => new Date(right.reported_time || 0) - new Date(left.reported_time || 0),
    ),
    records: scopedRecords.sort(
      (left, right) => new Date(right.service_date || 0) - new Date(left.service_date || 0),
    ),
    orders: scopedOrders.sort(
      (left, right) =>
        new Date(right.scheduled_date || 0) - new Date(left.scheduled_date || 0),
    ),
    projects: scopedProjects,
    issues: scopedIssues,
  };
}

function buildScopeStats(scope) {
  const openTickets = scope.tickets.filter((ticket) => isTicketActive(ticket.status)).length;
  const resolvedIssues = scope.issues.filter((issue) => isIssueResolved(issue.status)).length;
  const unresolvedIssues = scope.issues.length - resolvedIssues;
  const activeFieldTasks =
    scope.records.filter((record) => isRecordActive(record.status)).length +
    scope.orders.filter((order) => isOrderActive(order.status)).length;

  return {
    projectCount: scope.projects.length,
    openTickets,
    unresolvedIssues,
    resolvedIssues,
    activeFieldTasks,
  };
}

function WorkbenchLoading() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-32 rounded-2xl" />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Skeleton className="h-[520px] rounded-2xl" />
        <Skeleton className="h-[520px] rounded-2xl" />
      </div>
    </div>
  );
}

function ScopeSummary({ title, description, stats }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <DashboardStatCard
        icon={Briefcase}
        label={`${title}负责项目`}
        value={stats.projectCount}
        description={description}
        iconColor="text-cyan-300"
        iconBg="bg-cyan-500/10"
      />
      <DashboardStatCard
        icon={ClipboardList}
        label="待跟进工单"
        value={stats.openTickets}
        description="待处理 / 处理中 / 待验证"
        iconColor="text-amber-300"
        iconBg="bg-amber-500/10"
      />
      <DashboardStatCard
        icon={AlertTriangle}
        label="未解决问题"
        value={stats.unresolvedIssues}
        description={`已解决 ${stats.resolvedIssues} 项`}
        iconColor="text-rose-300"
        iconBg="bg-rose-500/10"
      />
      <DashboardStatCard
        icon={Wrench}
        label="现场任务"
        value={stats.activeFieldTasks}
        description="服务记录 + 安装调试派工"
        iconColor="text-emerald-300"
        iconBg="bg-emerald-500/10"
      />
    </div>
  );
}

function EngineerRoster({
  engineers,
  selectedKey,
  onSelect,
  canViewTeam,
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>工程师画像</CardTitle>
        <CardDescription>
          经理可以先看团队总览，再切换到单个售后工程师。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {canViewTeam ? (
          <button
            type="button"
            onClick={() => onSelect(TEAM_OVERVIEW_KEY)}
            className={cn(
              "w-full rounded-2xl border px-4 py-3 text-left transition-all",
              selectedKey === TEAM_OVERVIEW_KEY
                ? "border-cyan-400/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/10"
                : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]",
            )}
          >
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-white">团队总览</div>
                <div className="mt-1 text-xs text-slate-400">
                  查看全部工程师、全部工单和全部项目情况
                </div>
              </div>
              <Badge variant="info">总览</Badge>
            </div>
          </button>
        ) : null}

        {engineers.length === 0 ? (
          <EmptyState
            icon={UserRound}
            title="暂无工程师数据"
            message="当前还没有可展示的售后工程师数据。"
          />
        ) : (
          <div className="space-y-3">
            {engineers.map((engineer) => (
              <button
                key={engineer.key}
                type="button"
                onClick={() => onSelect(engineer.key)}
                className={cn(
                  "w-full rounded-2xl border px-4 py-3 text-left transition-all",
                  selectedKey === engineer.key
                    ? "border-violet-400/50 bg-violet-500/10 shadow-lg shadow-violet-500/10"
                    : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-sm font-semibold text-white">
                        {(engineer.name || "?").slice(0, 1)}
                      </div>
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-white">
                          {engineer.name}
                        </div>
                        <div className="truncate text-xs text-slate-400">
                          {engineer.position || engineer.department || "售后服务工程师"}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300">
                      <Badge variant="secondary">项目 {engineer.projectCount}</Badge>
                      <Badge variant="warning">待办 {engineer.activeLoad}</Badge>
                      <Badge variant="outline">工单 {engineer.ticketCount}</Badge>
                    </div>
                  </div>
                  {engineer.openTicketCount > 0 ? (
                    <Badge variant="danger">{engineer.openTicketCount} 待跟进</Badge>
                  ) : (
                    <Badge variant="success">可响应</Badge>
                  )}
                </div>
                {engineer.primaryProjectName ? (
                  <div className="mt-3 text-xs text-slate-400">
                    当前重点项目: {engineer.primaryProjectName}
                  </div>
                ) : (
                  <div className="mt-3 text-xs text-slate-500">当前暂无关联项目</div>
                )}
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ProjectTable({ projects }) {
  if (projects.length === 0) {
    return (
      <EmptyState
        icon={Briefcase}
        title="暂无项目数据"
        message="当前范围内还没有关联的售后项目。"
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>项目</TableHead>
          <TableHead>阶段</TableHead>
          <TableHead>健康度</TableHead>
          <TableHead>进度</TableHead>
          <TableHead>服务工单</TableHead>
          <TableHead>未解决问题</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {projects.map((project) => (
          <TableRow key={project.id}>
            <TableCell>
              <div className="space-y-1">
                <div className="font-medium text-white">{project.project_name}</div>
                <div className="text-xs text-slate-400">
                  {project.project_code} · 客户 {project.customer_name || "-"}
                </div>
              </div>
            </TableCell>
            <TableCell>{getStageName(project.stage || "-")}</TableCell>
            <TableCell>
              {project.health ? <HealthBadge health={project.health} /> : <span>-</span>}
            </TableCell>
            <TableCell>{formatPercent(project.progress_pct || 0, 0)}</TableCell>
            <TableCell>{project.ticketCount || 0}</TableCell>
            <TableCell>
              <Badge variant={project.unresolvedIssues > 0 ? "danger" : "success"}>
                {project.unresolvedIssues || 0}
              </Badge>
            </TableCell>
            <TableCell className="text-right">
              <Button asChild size="sm" variant="outline">
                <Link to={`/projects/${project.id}/workspace`}>查看项目</Link>
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function TicketTable({ tickets }) {
  if (tickets.length === 0) {
    return (
      <EmptyState
        icon={Headphones}
        title="暂无服务工单"
        message="当前范围内没有可展示的服务工单。"
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>工单</TableHead>
          <TableHead>项目</TableHead>
          <TableHead>问题描述</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>紧急度</TableHead>
          <TableHead>提报时间</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tickets.map((ticket) => (
          <TableRow key={ticket.id}>
            <TableCell>
              <div className="space-y-1">
                <div className="font-medium text-white">{ticket.ticket_no}</div>
                <div className="text-xs text-slate-400">
                  负责人: {ticket.assigned_to_name || "未指派"}
                </div>
              </div>
            </TableCell>
            <TableCell>{ticket.project_name}</TableCell>
            <TableCell className="max-w-[340px] truncate">{ticket.problem_desc}</TableCell>
            <TableCell>
              <Badge variant={getStatusBadgeVariant(ticket.status)}>
                {getTicketStatusLabel(ticket.status)}
              </Badge>
            </TableCell>
            <TableCell>
              <Badge variant={getUrgencyBadgeVariant(ticket.urgency)}>{ticket.urgency}</Badge>
            </TableCell>
            <TableCell>{formatDateTime(ticket.reported_time) || "-"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function IssueTable({ issues }) {
  if (issues.length === 0) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="暂无项目问题"
        message="当前范围内没有问题数据，或当前账号暂无问题查看权限。"
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>问题</TableHead>
          <TableHead>项目</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>严重度</TableHead>
          <TableHead>责任人</TableHead>
          <TableHead>解决情况</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {issues.map((issue) => (
          <TableRow key={issue.id}>
            <TableCell>
              <div className="space-y-1">
                <div className="font-medium text-white">{issue.title}</div>
                <div className="text-xs text-slate-400">{issue.issue_no}</div>
              </div>
            </TableCell>
            <TableCell>{issue.project_name}</TableCell>
            <TableCell>
              <Badge variant={getStatusBadgeVariant(issue.status)}>
                {getIssueStatusLabel(issue.status)}
              </Badge>
            </TableCell>
            <TableCell>{issue.severity}</TableCell>
            <TableCell>
              {issue.responsible_engineer_name || issue.assignee_name || "未分配"}
            </TableCell>
            <TableCell>
              {isIssueResolved(issue.status) ? (
                <span className="inline-flex items-center gap-1 text-emerald-300">
                  <CheckCircle2 className="h-4 w-4" />
                  已解决
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-amber-300">
                  <AlertTriangle className="h-4 w-4" />
                  待处理
                </span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function FieldTaskTables({ records, orders }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>服务记录</CardTitle>
          <CardDescription>售后上门、维修、维护等现场服务记录</CardDescription>
        </CardHeader>
        <CardContent>
          {records.length === 0 ? (
            <EmptyState
              icon={Wrench}
              title="暂无服务记录"
              message="当前范围内没有现场服务记录。"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>记录</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>服务类型</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>服务日期</TableHead>
                  <TableHead>问题摘要</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {records.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-white">{record.record_no}</div>
                        <div className="text-xs text-slate-400">
                          工程师: {record.service_engineer_name || "未指定"}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{record.project_name}</TableCell>
                    <TableCell>{record.service_type}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(record.status)}>
                        {getRecordStatusLabel(record.status)}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(record.service_date) || "-"}</TableCell>
                    <TableCell className="max-w-[340px] truncate">
                      {record.issues_found || record.service_content}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>安装调试派工</CardTitle>
          <CardDescription>安装、调试和现场支持任务跟进</CardDescription>
        </CardHeader>
        <CardContent>
          {orders.length === 0 ? (
            <EmptyState
              icon={ClipboardList}
              title="暂无派工任务"
              message="当前范围内没有安装调试派工任务。"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>派工单</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>任务</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead>进度</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-white">{order.order_no}</div>
                        <div className="text-xs text-slate-400">
                          工程师: {order.assigned_to_name || "未派工"}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{order.project_name}</TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div>{order.task_title}</div>
                        <div className="text-xs text-slate-400">{order.task_type}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(order.status)}>
                        {getOrderStatusLabel(order.status)}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(order.scheduled_date) || "-"}</TableCell>
                    <TableCell>{formatPercent(order.progress || 0, 0)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function CustomerServiceWorkbench() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("projects");
  const [selectedEngineerKey, setSelectedEngineerKey] = useState(TEAM_OVERVIEW_KEY);
  const [data, setData] = useState({
    tickets: [],
    records: [],
    orders: [],
    projects: [],
    issues: [],
    serviceEngineers: [],
  });

  const userRole = toTrimmedString(user?.role);
  const canViewTeam =
    SERVICE_MANAGER_ROLES.has(userRole) ||
    (isManagerRole(userRole) && userRole !== "customer_service_engineer") ||
    Boolean(user?.is_superuser || user?.isSuperuser);
  const hasUserReadPermission =
    Boolean(user?.is_superuser || user?.isSuperuser) ||
    (Array.isArray(user?.permissions) && user.permissions.includes("user:read"));

  useEffect(() => {
    loadWorkbenchData();
  }, [user?.id]);

  useEffect(() => {
    const nextEngineers = buildEngineerRoster({
      tickets: data.tickets,
      records: data.records,
      orders: data.orders,
      projectsById: buildProjectMap(data.projects, data.tickets, data.records, data.orders),
      issuesByProject: buildIssuesByProject(data.issues),
      serviceEngineers: data.serviceEngineers,
      currentUser: user,
    });

    if (!canViewTeam) {
      const selfKey = user?.id ? String(user.id) : nextEngineers[0]?.key || TEAM_OVERVIEW_KEY;
      if (selectedEngineerKey !== selfKey) {
        setSelectedEngineerKey(selfKey);
      }
      return;
    }

    const hasSelection =
      selectedEngineerKey === TEAM_OVERVIEW_KEY ||
      nextEngineers.some((engineer) => engineer.key === selectedEngineerKey);
    if (!hasSelection) {
      setSelectedEngineerKey(TEAM_OVERVIEW_KEY);
    }
  }, [
    canViewTeam,
    data.issues,
    data.orders,
    data.projects,
    data.records,
    data.serviceEngineers,
    data.tickets,
    selectedEngineerKey,
    user,
  ]);

  async function loadWorkbenchData() {
    setLoading(true);
    setError("");

    const requests = [
      serviceApi.tickets.list({ page: 1, page_size: PAGE_SIZE }),
      serviceApi.records.list({ page: 1, page_size: PAGE_SIZE }),
      installationDispatchApi.orders.list({ page: 1, page_size: PAGE_SIZE }),
      projectApi
        .list({ page: 1, page_size: PAGE_SIZE, is_active: true })
        .catch(() => ({ data: { items: [] } })),
      issueApi.list({ page: 1, page_size: PAGE_SIZE }).catch(() => ({ data: { items: [] } })),
      hasUserReadPermission
        ? userApi
            .list({ page: 1, page_size: PAGE_SIZE, is_active: true })
            .catch(() => ({ data: { items: [] } }))
        : Promise.resolve({ data: { items: [] } }),
    ];

    try {
      const [ticketsRes, recordsRes, ordersRes, projectsRes, issuesRes, usersRes] =
        await Promise.all(requests);

      const tickets = unwrapItems(ticketsRes).map(normalizeTicket);
      const records = unwrapItems(recordsRes).map(normalizeRecord);
      const orders = unwrapItems(ordersRes).map(normalizeOrder);
      const projects = unwrapItems(projectsRes).map(normalizeProject);
      const issues = unwrapItems(issuesRes).map(normalizeIssue);
      const serviceEngineers = unwrapItems(usersRes)
        .map(normalizeUser)
        .filter(isServiceEngineerUser);

      setData({
        tickets,
        records,
        orders,
        projects,
        issues,
        serviceEngineers,
      });
    } catch (loadError) {
      console.error("加载客服工作台失败:", loadError);
      setError(loadError?.response?.data?.detail || loadError?.message || "加载客服工作台失败");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <WorkbenchLoading />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="客服工作台加载失败"
        message={error}
        onRetry={loadWorkbenchData}
      />
    );
  }

  const projectsById = buildProjectMap(data.projects, data.tickets, data.records, data.orders);
  const issuesByProject = buildIssuesByProject(data.issues);
  const engineers = buildEngineerRoster({
    tickets: data.tickets,
    records: data.records,
    orders: data.orders,
    projectsById,
    issuesByProject,
    serviceEngineers: data.serviceEngineers,
    currentUser: user,
  });

  const selectedEngineer = canViewTeam
    ? engineers.find((engineer) => engineer.key === selectedEngineerKey) || null
    : engineers.find((engineer) => engineer.id === user?.id) ||
      engineers.find((engineer) => engineer.key === selectedEngineerKey) ||
      null;

  const scope = buildScopedView({
    engineer: selectedEngineerKey === TEAM_OVERVIEW_KEY && canViewTeam ? null : selectedEngineer,
    tickets: data.tickets,
    records: data.records,
    orders: data.orders,
    projectsById,
    issues: data.issues,
    issuesByProject,
  });
  const stats = buildScopeStats(scope);
  const scopeTitle =
    selectedEngineerKey === TEAM_OVERVIEW_KEY && canViewTeam
      ? "团队"
      : selectedEngineer?.name || "我的";
  const scopeDescription =
    selectedEngineerKey === TEAM_OVERVIEW_KEY && canViewTeam
      ? `覆盖 ${engineers.length} 位售后工程师，集中查看全部服务工单与项目情况。`
      : `聚焦 ${selectedEngineer?.name || "当前工程师"} 的负责项目、现场任务和问题闭环。`;

  return (
    <div className="space-y-6">
      <PageHeader
        title={canViewTeam ? "客服工作台" : "我的售后工作台"}
        description={
          canViewTeam
            ? "从客服部经理视角快速切换工程师，查看个人数据、全部服务工单和项目情况。"
            : "查看自己负责项目的服务工单、具体问题和解决状态。"
        }
        actions={{
          label: "刷新数据",
          icon: RefreshCw,
          variant: "outline",
          onClick: loadWorkbenchData,
        }}
      />

      <ScopeSummary title={scopeTitle} description={scopeDescription} stats={stats} />

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        {canViewTeam ? (
          <EngineerRoster
            engineers={engineers}
            selectedKey={selectedEngineerKey}
            onSelect={setSelectedEngineerKey}
            canViewTeam={canViewTeam}
          />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>当前工程师</CardTitle>
              <CardDescription>登录后默认聚焦本人负责的项目与售后任务。</CardDescription>
            </CardHeader>
            <CardContent>
              {selectedEngineer ? (
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-violet-500/15 text-lg font-semibold text-white">
                      {(selectedEngineer.name || "?").slice(0, 1)}
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-white">
                        {selectedEngineer.name}
                      </div>
                      <div className="text-sm text-slate-400">
                        {selectedEngineer.position || selectedEngineer.department || "售后服务工程师"}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Badge variant="secondary">项目 {selectedEngineer.projectCount}</Badge>
                    <Badge variant="warning">待办 {selectedEngineer.activeLoad}</Badge>
                    <Badge variant="outline">服务记录 {selectedEngineer.recordCount}</Badge>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={UserRound}
                  title="暂未识别到个人画像"
                  message="当前账号还没有产生售后服务数据，后续有工单或服务记录后会自动展示。"
                />
              )}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>
              {selectedEngineerKey === TEAM_OVERVIEW_KEY && canViewTeam
                ? "团队运营明细"
                : `${selectedEngineer?.name || "当前工程师"}明细`}
            </CardTitle>
            <CardDescription>{scopeDescription}</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList
                className="grid w-full gap-2"
                style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}
              >
                <TabsTrigger value="projects">项目情况</TabsTrigger>
                <TabsTrigger value="tickets">服务工单</TabsTrigger>
                <TabsTrigger value="issues">项目问题</TabsTrigger>
                <TabsTrigger value="field">现场任务</TabsTrigger>
              </TabsList>

              <TabsContent value="projects" className="mt-6">
                <ProjectTable projects={scope.projects} />
              </TabsContent>

              <TabsContent value="tickets" className="mt-6">
                <TicketTable tickets={scope.tickets} />
              </TabsContent>

              <TabsContent value="issues" className="mt-6">
                <IssueTable issues={scope.issues} />
              </TabsContent>

              <TabsContent value="field" className="mt-6">
                <FieldTaskTables records={scope.records} orders={scope.orders} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
