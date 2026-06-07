import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { presaleApi } from "../../services/api";
import { BOARD_STATUS_ORDER, PRIORITY_CONFIG, STATUS_CONFIG } from "./constants";
import { computeHoursDiff, extractApiPayload, safeDate, toTicketModel } from "./utils";

export default function usePresaleTickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [priorityUpdatingId, setPriorityUpdatingId] = useState(null);
  const [flowUpdatingId, setFlowUpdatingId] = useState(null);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setLoadError(null);

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
      setTickets([]);
      setLoadError(error.response?.data?.detail || error.message || "加载工单数据失败");
      toast.error("工单数据加载失败，请稍后重试");
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
    const reviewing = tickets.filter((ticket) => ticket.status === "REVIEWING").length;
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
      reviewing,
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
      REVIEWING: null,
      COMPLETED: null,
    };

    const nextStatus = nextStatusMap[ticket.status];
    if (!nextStatus) {
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
    if (status === "REVIEWING") {
      return "待评审";
    }
    return "已完结";
  };

  return {
    tickets,
    loading,
    loadError,
    searchKeyword,
    setSearchKeyword,
    statusFilter,
    setStatusFilter,
    priorityFilter,
    setPriorityFilter,
    selectedTicketId,
    setSelectedTicketId,
    priorityUpdatingId,
    flowUpdatingId,
    loadTickets,
    filteredTickets,
    selectedTicket,
    groupedByStatus,
    stats,
    priorityDistribution,
    handlePriorityChange,
    handleAdvanceFlow,
    renderFlowActionLabel,
  };
}
