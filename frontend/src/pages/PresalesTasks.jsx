/**
 * 售前技术任务中心
 * 管理技术支持请求、方案设计、投标任务等
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import {
  ListTodo,
  Search,
  Filter,
  Plus,
  Calendar,
  Clock,
  Users,
  Building2,
  FileText,
  Target,
  ClipboardList,
  MessageSquare,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronRight,
  MoreHorizontal,
  Flag,
  ArrowUpRight,
  Eye,
  Edit,
  Trash2,
  LayoutGrid,
  List,
  Kanban,
  Briefcase,
  Timer,
  User,
  X,
  DollarSign } from
"lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger } from
"../components/ui/dropdown-menu";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi, opportunityApi as _opportunityApi } from "../services/api";

// 任务类型配置
const taskTypes = [
{ id: "all", name: "全部", icon: ListTodo, color: "text-slate-400" },
{
  id: "survey",
  name: "需求调研",
  icon: ClipboardList,
  color: "text-emerald-400"
},
{
  id: "exchange",
  name: "技术交流",
  icon: MessageSquare,
  color: "text-blue-400"
},
{
  id: "solution",
  name: "方案设计",
  icon: FileText,
  color: "text-violet-400"
},
{ id: "review", name: "方案评审", icon: Eye, color: "text-pink-400" },
{
  id: "costing",
  name: "成本核算",
  icon: DollarSign,
  color: "text-emerald-400"
},
{ id: "bidding", name: "投标支持", icon: Target, color: "text-amber-400" }];


// 任务状态配置
const taskStatuses = [
{
  id: "pending",
  name: "待处理",
  color: "bg-slate-500",
  textColor: "text-slate-400"
},
{
  id: "in_progress",
  name: "进行中",
  color: "bg-blue-500",
  textColor: "text-blue-400"
},
{
  id: "reviewing",
  name: "待评审",
  color: "bg-amber-500",
  textColor: "text-amber-400"
},
{
  id: "completed",
  name: "已完成",
  color: "bg-emerald-500",
  textColor: "text-emerald-400"
}];


// Mock 任务数据
// Mock data - 已移除，使用真实API
// 获取优先级样式
const getPriorityStyle = (priority) => {
  switch (priority) {
    case "high":
      return { bg: "bg-red-500/10", text: "text-red-400", label: "紧急" };
    case "medium":
      return { bg: "bg-amber-500/10", text: "text-amber-400", label: "中等" };
    case "low":
      return { bg: "bg-slate-500/10", text: "text-slate-400", label: "普通" };
    default:
      return { bg: "bg-slate-500/10", text: "text-slate-400", label: "普通" };
  }
};

// 任务卡片组件
function TaskCard({ task, onClick }) {
  const priorityStyle = getPriorityStyle(task.priority);
  const statusConfig = taskStatuses.find((s) => s.id === task.status);

  return (
    <motion.div
      variants={fadeIn}
      className="p-4 rounded-xl bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group"
      onClick={() => onClick(task)}>

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", task.typeColor)}>
              {task.typeName}
            </Badge>
            <Badge
              className={cn("text-xs", priorityStyle.bg, priorityStyle.text)}>

              {priorityStyle.label}
            </Badge>
            <Badge className={cn("text-xs", statusConfig?.color)}>
              {statusConfig?.name}
            </Badge>
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors line-clamp-2">
            {task.title}
          </h4>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}>

              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem className="text-red-400">
              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <p className="text-xs text-slate-500 line-clamp-2 mb-3">
        {task.description}
      </p>

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <Building2 className="w-3 h-3" />
          {task.customer}
        </span>
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3" />
          {task.source}
        </span>
      </div>

      {task.status !== "completed" && task.status !== "pending" &&
      <div className="space-y-1 mb-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">进度</span>
            <span className="text-white">{task.progress}%</span>
          </div>
          <Progress value={task.progress} className="h-1.5" />
      </div>
      }

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {task.deadline}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {task.actualHours}/{task.estimatedHours}h
          </span>
        </div>
        {task.amount &&
        <span className="text-emerald-400">¥{task.amount}万</span>
        }
      </div>
    </motion.div>);

}

// 任务详情面板
function TaskDetailPanel({ task, onClose, onUpdate }) {
  const [progress, setProgress] = useState(task?.progress || 0);
  const [progressNote, setProgressNote] = useState("");
  const [actualHours, setActualHours] = useState(task?.actualHours || 0);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [isAccepting, setIsAccepting] = useState(false);

  if (!task) {return null;}

  const priorityStyle = getPriorityStyle(task.priority);
  const statusConfig = taskStatuses.find((s) => s.id === task.status);

  // 接单
  const handleAccept = async () => {
    try {
      setIsAccepting(true);
      await presaleApi.tickets.accept(task.ticketId, {});
      alert("接单成功！");
      onUpdate?.();
      onClose();
    } catch (err) {
      console.error("Failed to accept ticket:", err);
      alert(
        "接单失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    } finally {
      setIsAccepting(false);
    }
  };

  // 更新进度
  const handleUpdateProgress = async () => {
    try {
      setIsUpdating(true);
      await presaleApi.tickets.updateProgress(task.ticketId, {
        progress_percent: progress,
        progress_note: progressNote
      });
      alert("进度已更新！");
      onUpdate?.();
      setProgressNote("");
    } catch (err) {
      console.error("Failed to update progress:", err);
      alert(
        "更新失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    } finally {
      setIsUpdating(false);
    }
  };

  // 完成工单
  const handleComplete = async () => {
    if (!actualHours || actualHours <= 0) {
      alert("请输入实际工时");
      return;
    }

    try {
      setIsCompleting(true);
      await presaleApi.tickets.complete(task.ticketId, {
        actual_hours: actualHours
      });
      alert("工单已完成！");
      onUpdate?.();
      onClose();
    } catch (err) {
      console.error("Failed to complete ticket:", err);
      alert(
        "完成失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-full md:w-[450px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <h2 className="text-lg font-semibold text-white">任务详情</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5 text-slate-400" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
          {/* Title and badges */}
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <Badge className={cn("text-xs", task.typeColor)}>
                {task.typeName}
              </Badge>
              <Badge
                className={cn("text-xs", priorityStyle.bg, priorityStyle.text)}>

                {priorityStyle.label}
              </Badge>
              <Badge className={cn("text-xs", statusConfig?.color)}>
                {statusConfig?.name}
              </Badge>
            </div>
            <h3 className="text-xl font-semibold text-white">{task.title}</h3>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">任务描述</h4>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {task.description}
            </p>
          </div>

          {/* Basic Info */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">基本信息</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">客户</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <Building2 className="w-3 h-3 text-primary" />
                  {task.customer}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">来源</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <Users className="w-3 h-3 text-primary" />
                  {task.source}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">负责人</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <User className="w-3 h-3 text-primary" />
                  {task.assignee}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">关联商机</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <Briefcase className="w-3 h-3 text-primary" />
                  {task.opportunity}
                </p>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">时间信息</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">创建时间</p>
                <p className="text-sm text-white">{task.createdAt}</p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">截止时间</p>
                <p className="text-sm text-white">{task.deadline}</p>
              </div>
            </div>
          </div>

          {/* Progress */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">进度 & 工时</h4>
            <div className="bg-surface-50 p-4 rounded-lg space-y-3">
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">完成进度</span>
                  <span className="text-white">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">工时</span>
                <span className="text-white">
                  {actualHours}h / {task.estimatedHours || 0}h
                </span>
              </div>
              {task.estimatedHours > 0 &&
              <Progress
                value={actualHours / task.estimatedHours * 100}
                className="h-2" />

              }
            </div>
          </div>

          {/* Deliverables */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">交付物</h4>
            <div className="space-y-2">
              {task.deliverables.map((item, index) =>
              <div
                key={index}
                className="flex items-center gap-2 bg-surface-50 p-3 rounded-lg">

                  <FileText className="w-4 h-4 text-slate-500" />
                  <span className="text-sm text-white">{item}</span>
                  {task.status === "completed" &&
                <CheckCircle className="w-4 h-4 text-emerald-500 ml-auto" />
                }
              </div>
              )}
            </div>
          </div>

          {/* Amount */}
          {task.amount &&
          <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 p-4 rounded-lg border border-emerald-500/20">
              <p className="text-xs text-slate-400 mb-1">关联金额</p>
              <p className="text-2xl font-bold text-emerald-400">
                ¥{task.amount}万
              </p>
          </div>
          }
        </div>

        {/* 操作区域 */}
        {task.status === "pending" &&
        <div className="p-4 border-t border-white/5">
            <Button
            onClick={handleAccept}
            disabled={isAccepting}
            className="w-full">

              <CheckCircle className="w-4 h-4 mr-2" />
              {isAccepting ? "接单中..." : "接单处理"}
            </Button>
        </div>
        }

        {(task.status === "in_progress" || task.status === "reviewing") &&
        <div className="p-4 border-t border-white/5 space-y-3">
            <div className="space-y-2">
              <label className="text-sm text-slate-400">更新进度</label>
              <div className="flex items-center gap-3">
                <Input
                type="number"
                min="0"
                max="100"
                value={progress}
                onChange={(e) => setProgress(parseInt(e.target.value) || 0)}
                className="flex-1" />

                <span className="text-sm text-slate-400">%</span>
              </div>
              <Progress value={progress} className="h-2" />
              <Input
              type="text"
              placeholder="进度说明..."
              value={progressNote}
              onChange={(e) => setProgressNote(e.target.value)}
              className="w-full" />

              <Button
              onClick={handleUpdateProgress}
              disabled={isUpdating}
              variant="outline"
              className="w-full">

                <Clock className="w-4 h-4 mr-2" />
                {isUpdating ? "更新中..." : "更新进度"}
              </Button>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">实际工时（小时）</label>
              <Input
              type="number"
              min="0"
              value={actualHours}
              onChange={(e) =>
              setActualHours(parseFloat(e.target.value) || 0)
              }
              className="w-full" />

              <Button
              onClick={handleComplete}
              disabled={isCompleting || !actualHours || actualHours <= 0}
              className="w-full">

                <CheckCircle className="w-4 h-4 mr-2" />
                {isCompleting ? "完成中..." : "完成工单"}
              </Button>
            </div>
        </div>
        }

        {/* Footer */}
        <div className="p-4 border-t border-white/5 flex gap-2">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            <X className="w-4 h-4 mr-2" />
            关闭
          </Button>
        </div>
      </motion.div>
    </AnimatePresence>);

}

export default function PresalesTasks({ embedded = false } = {}) {
  const location = useLocation();
  const [viewMode, setViewMode] = useState("list"); // 'list', 'kanban'
  const [selectedType, setSelectedType] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTask, setSelectedTask] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [_loading, setLoading] = useState(true);
  const [_error, setError] = useState(null);

  // Map backend ticket type to frontend type
  const mapTicketType = (backendType) => {
    const typeMap = {
      SOLUTION: "solution",
      SOLUTION_DESIGN: "solution",
      SOLUTION_REVIEW: "review",
      QUOTATION: "costing",
      COST_ESTIMATE: "costing",
      COST_SUPPORT: "costing",
      TENDER: "bidding",
      TENDER_SUPPORT: "bidding",
      MEETING: "exchange",
      TECHNICAL_EXCHANGE: "exchange",
      SURVEY: "survey",
      REQUIREMENT_RESEARCH: "survey",
      FEASIBILITY_ASSESSMENT: "survey",
      CONSULT: "survey",
      SITE_VISIT: "survey"
    };
    return typeMap[backendType] || "solution";
  };

  // Map backend status to frontend status
  const mapTicketStatus = (backendStatus) => {
    const statusMap = {
      PENDING: "pending",
      ACCEPTED: "in_progress",
      IN_PROGRESS: "in_progress",
      PROCESSING: "in_progress",
      REVIEW: "reviewing",
      REVIEWING: "reviewing",
      COMPLETED: "completed",
      CLOSED: "completed",
      CANCELLED: "completed"
    };
    return statusMap[backendStatus] || "pending";
  };

  // Get type name and color
  const getTypeInfo = (type) => {
    const typeInfo = taskTypes.find((t) => t.id === type) || taskTypes[0];
    return {
      name: typeInfo.name,
      color: typeInfo.color.replace("text-", "bg-")
    };
  };

  // Load tasks from API
  const loadTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100
      };

      if (selectedStatus !== "all") {
        const statusMap = {
          pending: "PENDING",
          in_progress: "ACCEPTED,IN_PROGRESS,PROCESSING",
          reviewing: "REVIEW",
          completed: "COMPLETED,CLOSED,CANCELLED"
        };
        params.status = statusMap[selectedStatus] || selectedStatus;
      }

      if (searchTerm) {
        params.keyword = searchTerm;
      }

      const response = await presaleApi.tickets.list(params);
      const ticketsData = response.data?.items || response.data?.items || response.data || [];

      // Transform tickets to tasks
      const transformedTasks = ticketsData.map((ticket) => {
        const type = mapTicketType(ticket.ticket_type);
        const typeInfo = getTypeInfo(type);
        return {
          id: ticket.id,
          title: ticket.title,
          type,
          typeName: typeInfo.name,
          typeColor: typeInfo.color,
          status: mapTicketStatus(ticket.status),
          priority: ticket.urgency?.toLowerCase() || "medium",
          customer: ticket.customer_name || "",
          source: ticket.applicant_name ?
          `销售：${ticket.applicant_name}` :
          "内部流程",
          deadline: ticket.deadline || ticket.expected_date || "",
          createdAt: ticket.apply_time || ticket.created_at || "",
          progress: ticket.progress || 0,
          description: ticket.description || ticket.requirement || "",
          opportunity: ticket.opportunity_name || "",
          amount: ticket.estimated_value ? ticket.estimated_value / 10000 : 0,
          estimatedHours: ticket.estimated_hours || 0,
          actualHours: ticket.actual_hours || 0,
          assignee: ticket.assignee_name || ticket.owner_name || "未分配",
          deliverables: ticket.deliverables || []
        };
      });

      setTasks(transformedTasks);
    } catch (err) {
      console.error("Failed to load tasks:", err);
      setError(err.response?.data?.detail || err.message || "加载任务失败");
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, searchTerm]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const type = params.get("type");
    const status = params.get("status");
    if (type) {
      setSelectedType(type);
    }
    if (status) {
      setSelectedStatus(status);
    }
  }, [location.search]);

  // Load tasks when filters change
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // 筛选任务
  const filteredTasks = tasks.filter((task) => {
    const matchesType = selectedType === "all" || task.type === selectedType;
    const matchesStatus =
    selectedStatus === "all" || task.status === selectedStatus;
    const searchLower = (searchTerm || "").toLowerCase();
    const matchesSearch =
    (task.title || "").toLowerCase().includes(searchLower) ||
    (task.customer || "").toLowerCase().includes(searchLower) ||
    (task.description || "").toLowerCase().includes(searchLower);
    return matchesType && matchesStatus && matchesSearch;
  });

  // 按状态分组任务（看板视图用）
  const tasksByStatus = taskStatuses.map((status) => ({
    ...status,
    tasks: filteredTasks.filter((task) => task.status === status.id)
  }));

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 页面头部 */}
      {!embedded && (
        <PageHeader
          title="技术任务中心"
          description="管理技术支持请求、方案设计、投标任务"
          actions={
          <motion.div variants={fadeIn} className="flex gap-2">
              <Button className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                新建任务
              </Button>
          </motion.div>
          } />
      )}


      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4">

        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 类型筛选 */}
          <div className="flex flex-wrap gap-2">
            {taskTypes.map((type) =>
            <Button
              key={type.id}
              variant={selectedType === type.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedType(type.id)}
              className="flex items-center gap-1.5">

                <type.icon
                className={cn(
                  "w-3.5 h-3.5",
                  selectedType === type.id ? "" : type.color
                )} />

                {type.name}
            </Button>
            )}
          </div>

          {/* 搜索和视图切换 */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                type="text"
                placeholder="搜索任务..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 w-64" />

            </div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">

              <option value="all">全部状态</option>
              {taskStatuses.map((status) =>
              <option key={status.id} value={status.id}>
                  {status.name}
              </option>
              )}
            </select>
            <div className="flex bg-surface-50 rounded-lg p-1">
              <Button
                variant={viewMode === "list" ? "default" : "ghost"}
                size="icon"
                onClick={() => setViewMode("list")}>

                <List className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "kanban" ? "default" : "ghost"}
                size="icon"
                onClick={() => setViewMode("kanban")}>

                <Kanban className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* 任务列表/看板 */}
      {viewMode === "list" ?
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">

          {filteredTasks.length > 0 ?
        filteredTasks.map((task) =>
        <TaskCard key={task.id} task={task} onClick={setSelectedTask} />
        ) :

        <div className="col-span-full text-center py-16 text-slate-400">
              <ListTodo className="w-12 h-12 mx-auto mb-4 text-slate-600" />
              <p className="text-lg font-medium">暂无任务</p>
              <p className="text-sm">请调整筛选条件或创建新任务</p>
        </div>
        }
      </motion.div> :

      <motion.div
        variants={fadeIn}
        className="flex overflow-x-auto custom-scrollbar pb-4 -mx-6 px-6 gap-4">

          {tasksByStatus.map((column) =>
        <div key={column.id} className="flex-shrink-0 w-80">
              <Card className="bg-surface-50/70 backdrop-blur-sm border border-white/5 shadow-md">
                <CardHeader className="py-3 px-4 border-b border-white/5">
                  <CardTitle className="text-base font-semibold text-white flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <span
                    className={cn("w-2 h-2 rounded-full", column.color)} />

                      {column.name}
                    </span>
                    <Badge variant="secondary" className="bg-white/10">
                      {column.tasks.length}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 space-y-3 min-h-[400px] max-h-[calc(100vh-300px)] overflow-y-auto custom-scrollbar">
                  {column.tasks.length > 0 ?
              column.tasks.map((task) =>
              <TaskCard
                key={task.id}
                task={task}
                onClick={setSelectedTask} />

              ) :

              <div className="text-center py-8 text-slate-400">
                      <ListTodo className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                      <p className="text-sm">暂无任务</p>
              </div>
              }
                </CardContent>
              </Card>
        </div>
        )}
      </motion.div>
      }

      {/* 任务详情面板 */}
      {selectedTask &&
      <TaskDetailPanel
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
        onUpdate={loadTasks} />

      }
    </motion.div>);

}
