/**
 * 客服工作台 - 数据聚合与构建函数
 * 负责将原始 API 数据组装为工程师画像、范围视图和统计
 */

import {
  engineerMatches,
  isIssueResolved,
  isOrderActive,
  isRecordActive,
  isTicketActive,
  isTicketResolved,
  normalizeProject,
  toTrimmedString,
} from "./constants";

// ── 项目 Map ──────────────────────────────────────────────

function ensureProjectFallback(projectMap, projectId, projectName) {
  if (!projectId || projectMap.has(projectId)) {
    return projectMap;
  }
  // 不可变：返回新 Map
  const next = new Map(projectMap);
  next.set(
    projectId,
    normalizeProject({
      id: projectId,
      project_name: projectName || `项目 #${projectId}`,
    }),
  );
  return next;
}

export function buildProjectMap(projects, tickets, records, orders) {
  let projectMap = new Map();

  (projects || []).forEach((project) => {
    if (project?.id) {
      projectMap.set(project.id, normalizeProject(project));
    }
  });

  (tickets || []).forEach((ticket) => {
    projectMap = ensureProjectFallback(projectMap, ticket.project_id, ticket.project_name);
  });
  (records || []).forEach((record) => {
    projectMap = ensureProjectFallback(projectMap, record.project_id, record.project_name);
  });
  (orders || []).forEach((order) => {
    projectMap = ensureProjectFallback(projectMap, order.project_id, order.project_name);
  });

  return projectMap;
}

// ── 问题按项目分组（不可变：用展开运算符替代 push） ──────

export function buildIssuesByProject(issues) {
  const issueMap = new Map();

  (issues || []).forEach((issue) => {
    if (!issue.project_id) {
      return;
    }
    const existing = issueMap.get(issue.project_id) || [];
    issueMap.set(issue.project_id, [...existing, issue]);
  });

  return issueMap;
}

// ── 客服工程师判定 ──────────────────────────────────────────

export function isServiceEngineerUser(user) {
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

// ── 工程师画像构建 ──────────────────────────────────────────

export function buildEngineerRoster({
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

// ── 范围视图 ──────────────────────────────────────────────

export function buildScopedView({ engineer, tickets, records, orders, projectsById, issues, issuesByProject }) {
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

// ── 范围统计 ──────────────────────────────────────────────

export function buildScopeStats(scope) {
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
