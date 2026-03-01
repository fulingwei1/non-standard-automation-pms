import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Filter,
  Gauge,
  KanbanSquare,
  ListFilter,
  RefreshCw,
  Search,
  Ticket,
  Timer,
  TrendingUp,
  UserRound,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "../components/layout";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Progress,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui";
import { cn } from "../lib/utils";
import { presaleApi } from "../services/api";

const STATUS_CONFIG = {
  PENDING: {
    label: "待受理",
    badgeClass: "bg-slate-500/20 text-slate-200 border border-slate-500/40",
    dotClass: "bg-slate-400",
  },
  ACCEPTED: {
    label: "已接单",
    badgeClass: "bg-blue-500/20 text-blue-300 border border-blue-500/40",
    dotClass: "bg-blue-400",
  },
  IN_PROGRESS: {
    label: "处理中",
    badgeClass: "bg-amber-500/20 text-amber-300 border border-amber-500/40",
    dotClass: "bg-amber-400",
  },
  COMPLETED: {
    label: "已完成",
    badgeClass: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40",
    dotClass: "bg-emerald-400",
  },
};

const BOARD_STATUS_ORDER = ["PENDING", "ACCEPTED", "IN_PROGRESS", "COMPLETED"];

const PRIORITY_CONFIG = {
  LOW: {
    label: "低",
    badgeClass: "bg-slate-500/20 text-slate-200 border border-slate-500/40",
    weight: 1,
  },
  NORMAL: {
    label: "普通",
    badgeClass: "bg-blue-500/20 text-blue-300 border border-blue-500/40",
    weight: 2,
  },
  HIGH: {
    label: "高",
    badgeClass: "bg-amber-500/20 text-amber-300 border border-amber-500/40",
    weight: 3,
  },
  URGENT: {
    label: "紧急",
    badgeClass: "bg-red-500/20 text-red-300 border border-red-500/40",
    weight: 4,
  },
};

const TYPE_LABELS = {
  SOLUTION_DESIGN: "方案设计",
  SOLUTION_REVIEW: "方案评审",
  TECHNICAL_EXCHANGE: "技术交流",
  COST_ESTIMATE: "成本核算",
  TENDER_SUPPORT: "投标支持",
  REQUIREMENT_RESEARCH: "需求调研",
  FEASIBILITY_ASSESSMENT: "可行性评估",
};

const MOCK_TICKETS = [
  {
    id: "mock-1",
    ticket_no: "PS-2026-0098",
    title: "新能源产线扩容方案澄清",
    ticket_type: "TECHNICAL_EXCHANGE",
    urgency: "URGENT",
    status: "IN_PROGRESS",
    customer_name: "宁德时代",
    applicant_name: "张可",
    assignee_name: "李海峰",
    apply_time: "2026-02-23T09:20:00",
    accept_time: "2026-02-23T11:45:00",
    deadline: "2026-03-03T23:59:59",
    description: "客户要求 3 天内补齐双工位节拍、能耗和防呆逻辑。",
    expected_date: "2026-03-03",
    complete_time: null,
  },
  {
    id: "mock-2",
    ticket_no: "PS-2026-0101",
    title: "海外项目报价风险复核",
    ticket_type: "COST_ESTIMATE",
    urgency: "HIGH",
    status: "PENDING",
    customer_name: "海外渠道项目",
    applicant_name: "王晨",
    assignee_name: "",
    apply_time: "2026-02-27T15:10:00",
    accept_time: null,
    deadline: "2026-03-05T18:00:00",
    description: "需核对汇率波动、物流税费及海外安装成本风险。",
    expected_date: "2026-03-05",
    complete_time: null,
  },
  {
    id: "mock-3",
    ticket_no: "PS-2026-0093",
    title: "储能模组工艺评审支持",
    ticket_type: "SOLUTION_REVIEW",
    urgency: "NORMAL",
    status: "ACCEPTED",
    customer_name: "比亚迪",
    applicant_name: "周宁",
    assignee_name: "赵文博",
    apply_time: "2026-02-20T08:30:00",
    accept_time: "2026-02-20T10:10:00",
    deadline: "2026-03-02T17:30:00",
    description: "完成工艺风险清单与关键工位节拍论证。",
    expected_date: "2026-03-02",
    complete_time: null,
  },
  {
    id: "mock-4",
    ticket_no: "PS-2026-0086",
    title: "试制线 PoC 方案交付",
    ticket_type: "SOLUTION_DESIGN",
    urgency: "LOW",
    status: "COMPLETED",
    customer_name: "欣旺达",
    applicant_name: "陈锐",
    assignee_name: "黄雅婷",
    apply_time: "2026-02-12T09:00:00",
    accept_time: "2026-02-12T09:30:00",
    deadline: "2026-02-24T18:00:00",
    description: "已完成 PoC 报告、3D 布局和成本测算，待商务转入报价。",
    expected_date: "2026-02-24",
    complete_time: "2026-02-23T16:45:00",
  },
];

function extractApiPayload(response) {
  if (response?.formatted !== undefined) {
    return response.formatted;
  }
  if (response?.data?.data !== undefined) {
    return response.data.data;
  }
  return response?.data;
}

function normalizeStatus(status) {
  const resolved = String(status || "").toUpperCase();
  if (BOARD_STATUS_ORDER.includes(resolved)) {
    return resolved;
  }
  if (resolved === "PROCESSING") {
    return "IN_PROGRESS";
  }
  if (resolved === "CLOSED" || resolved === "CANCELLED") {
    return "COMPLETED";
  }
  return "PENDING";
}

function normalizePriority(priority) {
  const resolved = String(priority || "").toUpperCase();
  if (PRIORITY_CONFIG[resolved]) {
    return resolved;
  }
  if (resolved === "MEDIUM") {
    return "NORMAL";
  }
  return "NORMAL";
}

function safeDate(dateString) {
  if (!dateString) {
    return null;
  }
  const date = new Date(dateString);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDateTime(dateString) {
  const date = safeDate(dateString);
  if (!date) {
    return "-";
  }
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(dateString) {
  const date = safeDate(dateString);
  if (!date) {
    return "-";
  }
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function computeHoursDiff(startDateString, endDateString) {
  const start = safeDate(startDateString);
  const end = safeDate(endDateString);
  if (!start || !end) {
    return null;
  }
  return (end.getTime() - start.getTime()) / (1000 * 60 * 60);
}

function toTicketModel(ticket, forcedStatus = null) {
  return {
    id: ticket.id,
    ticketNo: ticket.ticket_no || `PS-${String(ticket.id).padStart(6, "0")}`,
    title: ticket.title || "未命名工单",
    ticketType: ticket.ticket_type || "SOLUTION_DESIGN",
    ticketTypeLabel: TYPE_LABELS[ticket.ticket_type] || ticket.ticket_type || "售前支持",
    priority: normalizePriority(ticket.urgency),
    status: forcedStatus || normalizeStatus(ticket.status),
    customerName: ticket.customer_name || "未知客户",
    applicantName: ticket.applicant_name || "未知申请人",
    assigneeName: ticket.assignee_name || "未指派",
    applyTime: ticket.apply_time || ticket.created_at,
    acceptTime: ticket.accept_time,
    completeTime: ticket.complete_time,
    deadline: ticket.deadline,
    expectedDate: ticket.expected_date,
    description: ticket.description || "暂无工单描述",
  };
}

export default function PresaleTicketBoard() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [usingMockData, setUsingMockData] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [priorityUpdatingId, setPriorityUpdatingId] = useState(null);
  const [flowUpdatingId, setFlowUpdatingId] = useState(null);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setUsingMockData(false);

    try {
      const boardResponse = await presaleApi.tickets.getBoard();
      const boardPayload = extractApiPayload(boardResponse) || {};
      const boardTickets = BOARD_STATUS_ORDER.flatMap((status) =>
        (boardPayload[status.toLowerCase()] || []).map((ticket) =>
          toTicketModel(ticket, status),
        ),
      );

      if (boardTickets.length > 0) {
        setTickets(boardTickets);
        return;
      }

      const listResponse = await presaleApi.tickets.list({ page: 1, page_size: 200 });
      const listPayload = extractApiPayload(listResponse) || {};
      const listItems = listPayload.items || listPayload;
      const normalizedList = Array.isArray(listItems)
        ? listItems.map((ticket) => toTicketModel(ticket))
        : [];

      setTickets(normalizedList);
    } catch (error) {
      console.error("加载售前工单失败:", error);
      setTickets(MOCK_TICKETS.map((ticket) => toTicketModel(ticket)));
      setUsingMockData(true);
      toast.warning("接口暂不可用，当前展示演示数据");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  const filteredTickets = useMemo(() => {
    const keyword = searchKeyword.trim().toLowerCase();

    return [...tickets]
      .filter((ticket) => {
        const matchKeyword =
          !keyword ||
          ticket.ticketNo.toLowerCase().includes(keyword) ||
          ticket.title.toLowerCase().includes(keyword) ||
          ticket.customerName.toLowerCase().includes(keyword) ||
          ticket.applicantName.toLowerCase().includes(keyword);

        const matchStatus = statusFilter === "all" || ticket.status === statusFilter;
        const matchPriority =
          priorityFilter === "all" || ticket.priority === priorityFilter;

        return matchKeyword && matchStatus && matchPriority;
      })
      .sort((a, b) => {
        const priorityScore =
          PRIORITY_CONFIG[b.priority].weight - PRIORITY_CONFIG[a.priority].weight;
        if (priorityScore !== 0) {
          return priorityScore;
        }

        const dateA = safeDate(a.applyTime)?.getTime() || 0;
        const dateB = safeDate(b.applyTime)?.getTime() || 0;
        return dateB - dateA;
      });
  }, [tickets, searchKeyword, statusFilter, priorityFilter]);

  useEffect(() => {
    if (filteredTickets.length === 0) {
      setSelectedTicketId(null);
      return;
    }

    const selectedStillExists = filteredTickets.some(
      (ticket) => ticket.id === selectedTicketId,
    );
    if (!selectedStillExists) {
      setSelectedTicketId(filteredTickets[0].id);
    }
  }, [filteredTickets, selectedTicketId]);

  const selectedTicket = useMemo(
    () => filteredTickets.find((ticket) => ticket.id === selectedTicketId) || null,
    [filteredTickets, selectedTicketId],
  );

  const groupedByStatus = useMemo(() => {
    return BOARD_STATUS_ORDER.reduce((acc, status) => {
      acc[status] = filteredTickets.filter((ticket) => ticket.status === status);
      return acc;
    }, {});
  }, [filteredTickets]);

  const stats = useMemo(() => {
    const total = tickets.length;
    const pending = tickets.filter((ticket) => ticket.status === "PENDING").length;
    const accepted = tickets.filter((ticket) => ticket.status === "ACCEPTED").length;
    const inProgress = tickets.filter((ticket) => ticket.status === "IN_PROGRESS").length;
    const completed = tickets.filter((ticket) => ticket.status === "COMPLETED").length;
    const highPriority = tickets.filter(
      (ticket) => ticket.priority === "HIGH" || ticket.priority === "URGENT",
    ).length;

    const responseHoursList = tickets
      .map((ticket) => computeHoursDiff(ticket.applyTime, ticket.acceptTime))
      .filter((hours) => hours != null);
    const avgResponseHours = responseHoursList.length
      ? responseHoursList.reduce((sum, item) => sum + item, 0) / responseHoursList.length
      : 0;

    const handleHoursList = tickets
      .map((ticket) =>
        computeHoursDiff(ticket.acceptTime || ticket.applyTime, ticket.completeTime),
      )
      .filter((hours) => hours != null);
    const avgHandleHours = handleHoursList.length
      ? handleHoursList.reduce((sum, item) => sum + item, 0) / handleHoursList.length
      : 0;

    const now = Date.now();
    const overdue = tickets.filter((ticket) => {
      const deadline = safeDate(ticket.deadline)?.getTime();
      if (!deadline || ticket.status === "COMPLETED") {
        return false;
      }
      return deadline < now;
    }).length;

    const completedOnTime = tickets.filter((ticket) => {
      if (ticket.status !== "COMPLETED") {
        return false;
      }
      const completeTime = safeDate(ticket.completeTime)?.getTime();
      const deadline = safeDate(ticket.deadline)?.getTime();
      if (!completeTime || !deadline) {
        return false;
      }
      return completeTime <= deadline;
    }).length;

    return {
      total,
      pending,
      accepted,
      inProgress,
      completed,
      highPriority,
      overdue,
      completionRate: total > 0 ? (completed / total) * 100 : 0,
      avgResponseHours,
      avgHandleHours,
      onTimeRate: completed > 0 ? (completedOnTime / completed) * 100 : 0,
    };
  }, [tickets]);

  const priorityDistribution = useMemo(() => {
    const counts = Object.keys(PRIORITY_CONFIG).reduce((acc, key) => {
      acc[key] = 0;
      return acc;
    }, {});

    tickets.forEach((ticket) => {
      counts[ticket.priority] += 1;
    });

    return Object.entries(counts).map(([priority, count]) => ({
      priority,
      count,
      percent: tickets.length > 0 ? (count / tickets.length) * 100 : 0,
    }));
  }, [tickets]);

  const handlePriorityChange = async (ticket, nextPriority) => {
    const previousPriority = ticket.priority;

    setTickets((prevTickets) =>
      prevTickets.map((item) =>
        item.id === ticket.id ? { ...item, priority: nextPriority } : item,
      ),
    );

    if (String(ticket.id).startsWith("mock-")) {
      toast.success(`工单 ${ticket.ticketNo} 优先级已更新为 ${PRIORITY_CONFIG[nextPriority].label}`);
      return;
    }

    try {
      setPriorityUpdatingId(ticket.id);
      await presaleApi.tickets.update(ticket.id, { urgency: nextPriority });
      toast.success(`工单 ${ticket.ticketNo} 优先级已更新`);
    } catch (error) {
      console.error("更新优先级失败:", error);
      setTickets((prevTickets) =>
        prevTickets.map((item) =>
          item.id === ticket.id ? { ...item, priority: previousPriority } : item,
        ),
      );
      toast.error(error.response?.data?.detail || "更新优先级失败");
    } finally {
      setPriorityUpdatingId(null);
    }
  };

  const handleAdvanceFlow = async (ticket) => {
    const nextStatusMap = {
      PENDING: "ACCEPTED",
      ACCEPTED: "IN_PROGRESS",
      IN_PROGRESS: "COMPLETED",
      COMPLETED: null,
    };

    const nextStatus = nextStatusMap[ticket.status];
    if (!nextStatus) {
      return;
    }

    if (String(ticket.id).startsWith("mock-")) {
      setTickets((prevTickets) =>
        prevTickets.map((item) =>
          item.id === ticket.id ? { ...item, status: nextStatus } : item,
        ),
      );
      toast.success(`工单 ${ticket.ticketNo} 已流转到 ${STATUS_CONFIG[nextStatus].label}`);
      return;
    }

    try {
      setFlowUpdatingId(ticket.id);

      if (ticket.status === "PENDING") {
        await presaleApi.tickets.accept(ticket.id, {});
      } else if (ticket.status === "ACCEPTED") {
        await presaleApi.tickets.updateProgress(ticket.id, {
          progress_note: "看板流转更新",
          progress_percent: 35,
        });
      } else if (ticket.status === "IN_PROGRESS") {
        await presaleApi.tickets.complete(ticket.id, {
          actual_hours: 8,
        });
      }

      toast.success(`工单 ${ticket.ticketNo} 已推进到 ${STATUS_CONFIG[nextStatus].label}`);
      await loadTickets();
    } catch (error) {
      console.error("工单流转失败:", error);
      toast.error(error.response?.data?.detail || "工单流转失败");
    } finally {
      setFlowUpdatingId(null);
    }
  };

  const renderFlowActionLabel = (status) => {
    if (status === "PENDING") {
      return "接单";
    }
    if (status === "ACCEPTED") {
      return "转处理中";
    }
    if (status === "IN_PROGRESS") {
      return "标记完成";
    }
    return "已完结";
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="售前工单看板"
        description="统一查看工单列表、流转状态、优先级与处理效率统计。"
        actions={[
          {
            label: "刷新数据",
            icon: RefreshCw,
            variant: "outline",
            onClick: loadTickets,
            disabled: loading,
          },
        ]}
      />

      {usingMockData && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-sm text-amber-200">
              <AlertTriangle className="h-4 w-4" />
              当前为演示数据，接口恢复后将自动显示真实工单。
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm text-slate-300">
              工单总量
              <Ticket className="h-4 w-4 text-blue-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold text-white">{stats.total}</div>
            <p className="mt-1 text-xs text-slate-400">待受理 {stats.pending} · 处理中 {stats.inProgress}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm text-slate-300">
              完成率
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-semibold text-emerald-300">
              {stats.completionRate.toFixed(1)}%
            </div>
            <Progress value={stats.completionRate} color="success" />
            <p className="text-xs text-slate-400">已完成 {stats.completed} 单</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm text-slate-300">
              响应时效
              <Clock3 className="h-4 w-4 text-cyan-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold text-cyan-300">
              {stats.avgResponseHours.toFixed(1)}h
            </div>
            <p className="mt-1 text-xs text-slate-400">
              平均处理周期 {stats.avgHandleHours.toFixed(1)}h
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm text-slate-300">
              风险工单
              <Gauge className="h-4 w-4 text-amber-400" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-semibold text-amber-300">
              {stats.highPriority + stats.overdue}
            </div>
            <p className="text-xs text-slate-400">
              高优先级 {stats.highPriority} · 超期 {stats.overdue}
            </p>
            <p className="text-xs text-slate-400">按期完结率 {stats.onTimeRate.toFixed(1)}%</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <ListFilter className="h-4 w-4 text-violet-400" />
            工单列表
          </CardTitle>
          <CardDescription>支持关键词、状态和优先级组合筛选，并可直接调整优先级。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <Input
                value={searchKeyword}
                onChange={(event) => setSearchKeyword(event.target.value)}
                placeholder="搜索工单号 / 标题 / 客户"
                className="pl-9"
              />
            </div>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-slate-500" />
                  <SelectValue placeholder="全部状态" />
                </div>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {BOARD_STATUS_ORDER.map((status) => (
                  <SelectItem key={status} value={status}>
                    {STATUS_CONFIG[status].label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-slate-500" />
                  <SelectValue placeholder="全部优先级" />
                </div>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部优先级</SelectItem>
                {Object.entries(PRIORITY_CONFIG).map(([priority, config]) => (
                  <SelectItem key={priority} value={priority}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>工单</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>优先级管理</TableHead>
                <TableHead>处理人</TableHead>
                <TableHead>截止时间</TableHead>
                <TableHead className="text-right">流转</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTickets.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-slate-400">
                    当前筛选下暂无工单
                  </TableCell>
                </TableRow>
              )}

              {filteredTickets.map((ticket) => {
                const statusConfig = STATUS_CONFIG[ticket.status];
                const priorityConfig = PRIORITY_CONFIG[ticket.priority];
                return (
                  <TableRow
                    key={ticket.id}
                    className={cn(
                      "cursor-pointer",
                      selectedTicketId === ticket.id && "bg-slate-800/60",
                    )}
                    onClick={() => setSelectedTicketId(ticket.id)}
                  >
                    <TableCell>
                      <div className="space-y-1">
                        <p className="font-medium text-white">{ticket.title}</p>
                        <p className="text-xs text-slate-400">
                          {ticket.ticketNo} · {ticket.customerName} · {ticket.ticketTypeLabel}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusConfig.badgeClass}>{statusConfig.label}</Badge>
                    </TableCell>
                    <TableCell>
                      <Select
                        value={ticket.priority}
                        onValueChange={(value) => handlePriorityChange(ticket, value)}
                        disabled={priorityUpdatingId === ticket.id}
                      >
                        <SelectTrigger className="h-8 w-[120px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(PRIORITY_CONFIG).map(([priority, config]) => (
                            <SelectItem key={priority} value={priority}>
                              {config.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Badge className={cn("mt-2", priorityConfig.badgeClass)}>
                        当前：{priorityConfig.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1 text-sm">
                        <p className="text-slate-200">{ticket.assigneeName}</p>
                        <p className="text-xs text-slate-500">申请：{ticket.applicantName}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1 text-sm">
                        <p className="text-slate-200">{formatDate(ticket.deadline || ticket.expectedDate)}</p>
                        <p className="text-xs text-slate-500">创建：{formatDate(ticket.applyTime)}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant={ticket.status === "COMPLETED" ? "secondary" : "outline"}
                        size="sm"
                        disabled={ticket.status === "COMPLETED" || flowUpdatingId === ticket.id}
                        onClick={(event) => {
                          event.stopPropagation();
                          handleAdvanceFlow(ticket);
                        }}
                      >
                        {renderFlowActionLabel(ticket.status)}
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[1.5fr,1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KanbanSquare className="h-4 w-4 text-cyan-400" />
              工单流转
            </CardTitle>
            <CardDescription>按状态查看当前排队，点击卡片可联动左侧工单列表。</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {BOARD_STATUS_ORDER.map((status) => {
                const statusConfig = STATUS_CONFIG[status];
                const columnTickets = groupedByStatus[status] || [];
                return (
                  <div
                    key={status}
                    className="rounded-xl border border-slate-800/70 bg-slate-900/40 p-3"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                        <span className={cn("h-2 w-2 rounded-full", statusConfig.dotClass)} />
                        {statusConfig.label}
                      </div>
                      <Badge className="bg-slate-800 text-slate-200">{columnTickets.length}</Badge>
                    </div>

                    <div className="space-y-2">
                      {columnTickets.slice(0, 4).map((ticket) => (
                        <button
                          key={ticket.id}
                          type="button"
                          onClick={() => setSelectedTicketId(ticket.id)}
                          className={cn(
                            "w-full rounded-lg border border-slate-800 bg-slate-950/70 p-2 text-left transition hover:border-cyan-500/40",
                            selectedTicketId === ticket.id && "border-cyan-400/60",
                          )}
                        >
                          <p className="truncate text-xs font-medium text-slate-100">{ticket.title}</p>
                          <p className="mt-1 text-[11px] text-slate-400">
                            {ticket.ticketNo} · {ticket.customerName}
                          </p>
                        </button>
                      ))}

                      {columnTickets.length > 4 && (
                        <p className="pt-1 text-[11px] text-slate-500">还有 {columnTickets.length - 4} 条...</p>
                      )}

                      {columnTickets.length === 0 && (
                        <p className="py-2 text-[11px] text-slate-500">暂无工单</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-amber-400" />
              优先级管理
            </CardTitle>
            <CardDescription>按优先级分布识别资源倾斜，避免高优工单堆积。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {priorityDistribution.map((item) => {
              const config = PRIORITY_CONFIG[item.priority];
              const progressColor =
                item.priority === "URGENT"
                  ? "danger"
                  : item.priority === "HIGH"
                    ? "warning"
                    : "primary";

              return (
                <div key={item.priority} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <Badge className={config.badgeClass}>{config.label}</Badge>
                    <span className="text-slate-300">
                      {item.count} 单 ({item.percent.toFixed(1)}%)
                    </span>
                  </div>
                  <Progress value={item.percent} color={progressColor} />
                </div>
              );
            })}

            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-300">
              高优先级（高+紧急）共 {stats.highPriority} 单，建议每日站会优先过单。
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Timer className="h-4 w-4 text-emerald-400" />
            处理统计
          </CardTitle>
          <CardDescription>关注响应、处理、按期交付三项核心指标。</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-[1.1fr,1fr]">
          <div className="space-y-3 rounded-xl border border-slate-800/70 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">平均响应时长</span>
              <span className="font-medium text-cyan-300">{stats.avgResponseHours.toFixed(1)}h</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">平均处理时长</span>
              <span className="font-medium text-amber-300">{stats.avgHandleHours.toFixed(1)}h</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">按期完结率</span>
              <span className="font-medium text-emerald-300">{stats.onTimeRate.toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">已接单待处理</span>
              <span className="font-medium text-blue-300">{stats.accepted + stats.inProgress} 单</span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/70 p-4">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
              <UserRound className="h-4 w-4 text-violet-400" />
              当前选中工单
            </h3>

            {selectedTicket ? (
              <div className="space-y-3 text-sm">
                <div>
                  <p className="font-medium text-white">{selectedTicket.title}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    {selectedTicket.ticketNo} · {selectedTicket.customerName}
                  </p>
                </div>

                <p className="rounded-lg bg-slate-900/70 p-3 text-slate-300">
                  {selectedTicket.description}
                </p>

                <div className="space-y-2 text-xs text-slate-400">
                  <p>创建时间：{formatDateTime(selectedTicket.applyTime)}</p>
                  <p>接单时间：{formatDateTime(selectedTicket.acceptTime)}</p>
                  <p>完成时间：{formatDateTime(selectedTicket.completeTime)}</p>
                  <p>截止时间：{formatDateTime(selectedTicket.deadline || selectedTicket.expectedDate)}</p>
                </div>

                <Button
                  size="sm"
                  variant={selectedTicket.status === "COMPLETED" ? "secondary" : "default"}
                  disabled={selectedTicket.status === "COMPLETED" || flowUpdatingId === selectedTicket.id}
                  onClick={() => handleAdvanceFlow(selectedTicket)}
                >
                  {renderFlowActionLabel(selectedTicket.status)}
                </Button>
              </div>
            ) : (
              <p className="text-sm text-slate-500">请选择一条工单查看详情</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
