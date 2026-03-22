/**
 * 客服工作台 - 核心 Hook
 * 封装全部 state、数据加载、派生计算
 */

import { useEffect, useState } from "react";

import { useAuth } from "../../../context/AuthContext";
import { isManagerRole } from "../../../lib/roleConfig/roleUtils";
import { userApi } from "../../../services/api/auth";
import { issueApi } from "../../../services/api/issues";
import { projectApi } from "../../../services/api/projects";
import { installationDispatchApi, serviceApi } from "../../../services/api/service";
import {
  PAGE_SIZE,
  SERVICE_MANAGER_ROLES,
  TEAM_OVERVIEW_KEY,
  normalizeIssue,
  normalizeOrder,
  normalizeProject,
  normalizeRecord,
  normalizeTicket,
  normalizeUser,
  toTrimmedString,
  unwrapItems,
} from "../constants";
import {
  buildEngineerRoster,
  buildIssuesByProject,
  buildProjectMap,
  buildScopeStats,
  buildScopedView,
  isServiceEngineerUser,
} from "../dataBuilders";

export function useCustomerServiceWorkbench() {
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

  // 权限判断
  const userRole = toTrimmedString(user?.role);
  const canViewTeam =
    SERVICE_MANAGER_ROLES.has(userRole) ||
    (isManagerRole(userRole) && userRole !== "customer_service_engineer") ||
    Boolean(user?.is_superuser || user?.isSuperuser);
  const hasUserReadPermission =
    Boolean(user?.is_superuser || user?.isSuperuser) ||
    (Array.isArray(user?.permissions) && user.permissions.includes("user:read"));

  // 首次加载
  useEffect(() => {
    loadWorkbenchData();
  }, [user?.id]);

  // 选中工程师自动修正
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

  // ── 数据加载 ──────────────────────────────────────────────

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
      setError(loadError?.response?.data?.detail || loadError?.message || "加载客服工作台失败");
    } finally {
      setLoading(false);
    }
  }

  // ── 派生数据（仅在非 loading、无 error 时计算） ──────────

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

  return {
    // 基础状态
    user,
    loading,
    error,
    activeTab,
    setActiveTab,
    selectedEngineerKey,
    setSelectedEngineerKey,
    canViewTeam,

    // 派生数据
    engineers,
    selectedEngineer,
    scope,
    stats,
    scopeTitle,
    scopeDescription,

    // 操作
    loadWorkbenchData,
  };
}
