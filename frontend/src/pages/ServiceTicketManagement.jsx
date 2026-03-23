/**
 * Service Ticket Management - Refactored Version
 * 服务工单管理系统 - 重构版本
 *
 * 功能：
 * 1. 服务工单创建、编辑、查看
 * 2. 工单状态跟踪（待分配/处理中/待验证/已关闭）
 * 3. 工单转派和分配
 * 4. 工单搜索和筛选
 * 5. 工单统计分析
 * 6. 客户满意度记录
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { cn } from "../lib/utils";

// Import components

// Import constants and utilities
import { urgencyConfigs } from "@/lib/constants/service";
import { serviceApi } from "../services/api";

export default function ServiceTicketManagement() {
  const _navigate = useNavigate();

  const getPriorityValue = (ticket) => {
    const urgency = ticket?.urgency;
    if (!urgency) {return 0;}

    if (urgencyConfigs[urgency]?.level !== undefined) {
      return urgencyConfigs[urgency].level;
    }

    const matched = Object.values(urgencyConfigs).find(
      (config) => config.label === urgency
    );
    return matched?.level ?? 0;
  };

  // State management
  const [tickets, setTickets] = useState([]);
  const [filteredTickets, setFilteredTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [submitting, _setSubmitting] = useState(false);
  const [statistics, setStatistics] = useState({
    total: 0,
    pending: 0,
    inProgress: 0,
    pendingVerify: 0,
    closed: 0,
    overdue: 0
  });

  // Search and filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [filterUrgency, setFilterUrgency] = useState("ALL");
  const [filterProblemType, setFilterProblemType] = useState("ALL");
  const [filterDateRange, setFilterDateRange] = useState({ start: "", end: "" });

  // Sort state
  const [sortField, setSortField] = useState("reported_time");
  const [sortDirection, setSortDirection] = useState("desc");

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);

  // Selection state
  const [selectedTickets, setSelectedTickets] = useState([]);

  // Load data
  const loadTickets = useCallback(async () => {
    try {
      setLoading(true);
      const response = await serviceApi.tickets.list({
        page_size: 1000,
        order_by: sortField,
        order_direction: sortDirection
      });
      const ticketList = response.data?.items || response.data?.items || response.data || [];
      setTickets(ticketList);
    } catch (error) {
      toast.error("加载工单列表失败: " + (error.message || "请稍后重试"));
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, [sortField, sortDirection]);

  const loadStatistics = useCallback(async () => {
    try {
      const response = await serviceApi.tickets.getStatistics();
      setStatistics(response.data || {
        total: 0,
        pending: 0,
        inProgress: 0,
        pendingVerify: 0,
        closed: 0,
        overdue: 0
      });
    } catch (_error) {
      // 非关键操作失败时静默降级
    }
  }, []);

  // Initialize data
  useEffect(() => {
    loadTickets();
    loadStatistics();
  }, [loadTickets, loadStatistics]);

  // Filter and search logic
  useEffect(() => {
    let filtered = [...tickets];

    // Search filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = (filtered || []).filter((ticket) =>
      ticket.ticket_no?.toLowerCase().includes(term) ||
      ticket.project_name?.toLowerCase().includes(term) ||
      ticket.project_code?.toLowerCase().includes(term) ||
      ticket.customer_name?.toLowerCase().includes(term) ||
      ticket.problem_desc?.toLowerCase().includes(term) ||
      ticket.reported_by?.toLowerCase().includes(term) ||
      ticket.assignee_name?.toLowerCase().includes(term)
      );
    }

    // Status filter
    if (filterStatus && filterStatus !== "ALL") {
      const normalizedStatus = filterStatus === "ASSIGNED" ? "IN_PROGRESS" : filterStatus;
      filtered = (filtered || []).filter((ticket) => ticket.status === normalizedStatus);
    }

    // Urgency filter
    if (filterUrgency && filterUrgency !== "ALL") {
      filtered = (filtered || []).filter((ticket) => ticket.urgency === filterUrgency);
    }

    if (filterProblemType && filterProblemType !== "ALL") {
      filtered = (filtered || []).filter((ticket) => ticket.problem_type === filterProblemType);
    }

    if (filterDateRange.start || filterDateRange.end) {
      filtered = (filtered || []).filter((ticket) => {
        const ticketDate = new Date(ticket.reported_time || ticket.created_time);
        if (Number.isNaN(ticketDate.getTime())) {
          return false;
        }
        const afterStart = !filterDateRange.start || ticketDate >= new Date(`${filterDateRange.start}T00:00:00`);
        const beforeEnd = !filterDateRange.end || ticketDate <= new Date(`${filterDateRange.end}T23:59:59`);
        return afterStart && beforeEnd;
      });
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      // Handle date fields
      if (sortField.includes('_time')) {
        aValue = aValue ? new Date(aValue) : new Date(0);
        bValue = bValue ? new Date(bValue) : new Date(0);
      }

      // Handle priority
      if (sortField === 'priority') {
        aValue = getPriorityValue(a);
        bValue = getPriorityValue(b);
      }

      let comparison = 0;
      if (aValue < bValue) {comparison = -1;}
      if (aValue > bValue) {comparison = 1;}

      return sortDirection === 'desc' ? -comparison : comparison;
    });

    setFilteredTickets(filtered);
  }, [tickets, searchTerm, filterStatus, filterUrgency, filterProblemType, filterDateRange, sortField, sortDirection]);

  // Event handlers
  const handleCreateTicket = async (ticketData) => {
    try {
      await serviceApi.tickets.create(ticketData);
      toast.success("服务工单创建成功");
      setShowCreateDialog(false);
      await loadTickets();
      await loadStatistics();
    } catch (error) {
      toast.error("创建失败: " + (error.response?.data?.detail || error.message || "请稍后重试"));
    }
  };

  const handleAssignTicket = async (ticketId, assignData) => {
    try {
      await serviceApi.tickets.assign(ticketId, assignData);
      toast.success("工单分配成功");
      await loadTickets();
      await loadStatistics();
    } catch (error) {
      toast.error("分配失败: " + (error.response?.data?.detail || error.message || "请稍后重试"));
    }
  };

  const handleCloseTicket = async (ticketId, closeData) => {
    try {
      await serviceApi.tickets.close(ticketId, closeData);
      toast.success("工单关闭成功");
      setShowDetailDialog(false);
      await loadTickets();
      await loadStatistics();
    } catch (error) {
      toast.error("关闭失败: " + (error.response?.data?.detail || error.message || "请稍后重试"));
    }
  };

  const handleBatchAssign = async (assignData) => {
    try {
      await serviceApi.tickets.batchAssign(assignData);
      toast.success(`成功分配 ${assignData.ticket_ids?.length} 个工单`);
      await loadTickets();
      await loadStatistics();
    } catch (error) {
      toast.error("批量分配失败: " + (error.response?.data?.detail || error.message || "请稍后重试"));
    }
  };

  const handleBatchDelete = async (ticketIds) => {
    try {
      await serviceApi.tickets.batchDelete(ticketIds);
      toast.success(`成功删除 ${ticketIds.length} 个工单`);
      await loadTickets();
      await loadStatistics();
    } catch (error) {
      toast.error("批量删除失败: " + (error.response?.data?.detail || error.message || "请稍后重试"));
    }
  };

  const handleBatchExport = async (ticketsToExport) => {
    try {
      const csvContent = [
      [
      "工单号",
      "项目编号",
      "项目名称",
      "客户名称",
      "问题类型",
      "紧急程度",
      "状态",
      "报告人",
      "报告时间",
      "负责人",
      "创建时间"].
      join(","),
      ...(ticketsToExport || []).map((ticket) =>
      [
      ticket.ticket_no,
      ticket.project_code,
      ticket.project_name,
      ticket.customer_name,
      ticket.problem_type,
      ticket.urgency,
      ticket.status,
      ticket.reported_by,
      ticket.created_time ? new Date(ticket.created_time).toLocaleString() : "",
      ticket.assignee_name || "",
      ticket.created_time ? new Date(ticket.created_time).toLocaleDateString() : ""].
      join(",")
      )].
      join("\n");

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `服务工单_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success(`成功导出 ${ticketsToExport.length} 条工单记录`);
    } catch (error) {
      toast.error("导出失败: " + (error.response?.data?.detail || error.message || "请稍后重试"));
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadTickets();
      await loadStatistics();
      toast.success("数据已刷新");
    } catch (_error) {
      toast.error("刷新失败");
    } finally {
      setRefreshing(false);
    }
  };

  const handleViewDetail = (ticket) => {
    setSelectedTicket(ticket);
    setShowDetailDialog(true);
  };

  const _handleSelectTicket = (ticketId) => {
    setSelectedTickets((prev) =>
    prev.includes(ticketId) ?
    (prev || []).filter((id) => id !== ticketId) :
    [...prev, ticketId]
    );
  };

  const _handleSelectAll = () => {
    if (selectedTickets.length === filteredTickets.length) {
      setSelectedTickets([]);
    } else {
      setSelectedTickets((filteredTickets || []).map((ticket) => ticket.id));
    }
  };

  const handleClearSelection = () => {
    setSelectedTickets([]);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">

      <PageHeader
        title="服务工单管理"
        subtitle="管理客户服务工单，跟踪问题解决进度"
        actions={
        <div className="flex items-center gap-3">
            <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-slate-600 bg-slate-800/50 text-slate-300 hover:bg-slate-700/50 hover:text-white">

              <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
              刷新
            </Button>
            <Button
            onClick={() => setShowCreateDialog(true)}
            className="bg-blue-600 hover:bg-blue-700">

              <Plus className="w-4 h-4 mr-2" />
              创建工单
            </Button>
        </div>
        } />


      <div className="p-6 max-w-[1600px] mx-auto space-y-6">
        {/* Statistics Cards */}
        <ServiceTicketStats tickets={filteredTickets} stats={statistics} loading={loading} />

        {/* Filters and Search */}
        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg text-slate-200">搜索和筛选</CardTitle>
          </CardHeader>
          <CardContent>
            <ServiceTicketListHeader
              searchQuery={searchTerm}
              onSearchChange={setSearchTerm}
              statusFilter={filterStatus}
              onStatusChange={setFilterStatus}
              urgencyFilter={filterUrgency}
              onUrgencyChange={setFilterUrgency}
              problemTypeFilter={filterProblemType}
              onProblemTypeChange={setFilterProblemType}
              dateRange={filterDateRange}
              onDateRangeChange={setFilterDateRange}
              sortBy={sortField}
              onSortChange={setSortField}
              sortOrder={sortDirection}
              onSortOrderChange={setSortDirection}
              onCreateTicket={() => setShowCreateDialog(true)}
              onRefresh={handleRefresh}
              exporting={loading}
              onExport={() => handleBatchExport(filteredTickets)}
            />

          </CardContent>
        </Card>

        {/* Tickets Table */}
        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg text-slate-200">
              工单列表 ({filteredTickets.length} 条记录)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ServiceTicketListTable
              tickets={filteredTickets}
              loading={loading}
              selectedTicketIds={new Set(selectedTickets)}
              onSelectionChange={(selection) => setSelectedTickets(Array.from(selection))}
              onViewDetail={handleViewDetail}
              onEditTicket={(ticket) => {
                setSelectedTicket(ticket);
                setShowDetailDialog(true);
              }}
            />

          </CardContent>
        </Card>
      </div>

      {/* Create Dialog */}
      {showCreateDialog &&
      <ServiceTicketCreateDialog
        onClose={() => setShowCreateDialog(false)}
        onSubmit={handleCreateTicket}
        submitting={submitting} />

      }

      {/* Detail Dialog */}
      {showDetailDialog && selectedTicket &&
      <ServiceTicketDetailDialog
        ticket={selectedTicket}
        onClose={() => setShowDetailDialog(false)}
        onAssign={handleAssignTicket}
        onCloseTicket={handleCloseTicket} />

      }

      {/* Batch Actions */}
      <ServiceTicketBatchActions
        selectedTickets={selectedTickets}
        tickets={tickets}
        onClearSelection={handleClearSelection}
        onBatchAssign={handleBatchAssign}
        onBatchExport={handleBatchExport}
        onBatchDelete={handleBatchDelete} />

    </motion.div>);

}
