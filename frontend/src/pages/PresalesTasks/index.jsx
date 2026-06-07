/**
 * 售前技术任务中心
 * 管理技术支持请求、方案设计、投标任务等
 */
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useLocation } from "react-router-dom";
import {
  ListTodo,
  Search,
  Plus,
  List,
  Kanban,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { presaleApi } from "../../services/api";
import { taskTypes, taskStatuses } from "./constants";
import TaskCard from "./TaskCard";
import TaskDetailPanel from "./TaskDetailPanel";

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
    const typeInfo = (taskTypes || []).find((t) => t.id === type) || taskTypes[0];
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
      const transformedTasks = (ticketsData || []).map((ticket) => {
        const type = mapTicketType(ticket.ticket_type);
        const typeInfo = getTypeInfo(type);
        return {
          id: ticket.id,
          ticketId: ticket.id,
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
  const filteredTasks = (tasks || []).filter((task) => {
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
  const tasksByStatus = (taskStatuses || []).map((status) => ({
    ...status,
    tasks: (filteredTasks || []).filter((task) => task.status === status.id)
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
            {(taskTypes || []).map((type) =>
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
                )}  />

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
              {(taskStatuses || []).map((status) =>
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
        (filteredTasks || []).map((task) =>
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

          {(tasksByStatus || []).map((column) =>
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
                      {column.tasks?.length}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 space-y-3 min-h-[400px] max-h-[calc(100vh-300px)] overflow-y-auto custom-scrollbar">
                  {column.tasks?.length > 0 ?
              (column.tasks || []).map((task) =>
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
