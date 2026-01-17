/**
 * Installation Dispatch Management Page - 安装调试派工管理页面
 * Features: 安装调试派工单管理、批量派工、进度跟踪
 */

import { useState, useEffect, useMemo as _useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  Users,
  CheckSquare,
  Square,
  Clock,
  AlertTriangle,
  Calendar,
  MapPin,
  User,
  Settings,
  Play,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Download } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { cn, formatDate } from "../lib/utils";
import {
  installationDispatchApi,
  userApi,
  projectApi,
  machineApi } from
"../services/api";
import { toast } from "../components/ui/toast";
import {
  InstallationDispatchOverview,
  DISPATCH_STATUS,
  DISPATCH_STATUS_LABELS,
  DISPATCH_STATUS_COLORS,
  DISPATCH_PRIORITY,
  DISPATCH_PRIORITY_LABELS,
  PRIORITY_COLORS,
  INSTALLATION_TYPE,
  INSTALLATION_TYPE_LABELS,
  DISPATCH_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  validateDispatchData } from
"../components/installation-dispatch";

// 状态配置 - 使用新的配置系统
const statusConfig = {
  [DISPATCH_STATUS.PENDING]: {
    label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.PENDING],
    color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.PENDING]
  },
  [DISPATCH_STATUS.ASSIGNED]: {
    label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.ASSIGNED],
    color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.ASSIGNED]
  },
  [DISPATCH_STATUS.IN_PROGRESS]: {
    label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.IN_PROGRESS],
    color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.IN_PROGRESS]
  },
  [DISPATCH_STATUS.COMPLETED]: {
    label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.COMPLETED],
    color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.COMPLETED]
  },
  [DISPATCH_STATUS.CANCELLED]: {
    label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.CANCELLED],
    color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.CANCELLED]
  }
};

const priorityConfig = {
  [DISPATCH_PRIORITY.LOW]: {
    label: DISPATCH_PRIORITY_LABELS[DISPATCH_PRIORITY.LOW],
    color: PRIORITY_COLORS[DISPATCH_PRIORITY.LOW],
    bg: "bg-slate-500/20"
  },
  [DISPATCH_PRIORITY.MEDIUM]: {
    label: DISPATCH_PRIORITY_LABELS[DISPATCH_PRIORITY.MEDIUM],
    color: PRIORITY_COLORS[DISPATCH_PRIORITY.MEDIUM],
    bg: "bg-blue-500/20"
  },
  [DISPATCH_PRIORITY.HIGH]: {
    label: DISPATCH_PRIORITY_LABELS[DISPATCH_PRIORITY.HIGH],
    color: PRIORITY_COLORS[DISPATCH_PRIORITY.HIGH],
    bg: "bg-amber-500/20"
  }
};

const taskTypeConfig = {
  [INSTALLATION_TYPE.NEW]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.NEW], icon: "🔧" },
  [INSTALLATION_TYPE.MAINTENANCE]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.MAINTENANCE], icon: "🔨" },
  [INSTALLATION_TYPE.REPAIR]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.REPAIR], icon: "🛠️" },
  [INSTALLATION_TYPE.UPGRADE]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.UPGRADE], icon: "⚙️" },
  [INSTALLATION_TYPE.INSPECTION]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.INSPECTION], icon: "👥" }
};

export default function InstallationDispatchManagement() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [machines, setMachines] = useState([]);
  const [_stats, setStats] = useState({
    total: 0,
    pending: 0,
    assigned: 0,
    in_progress: 0,
    completed: 0,
    cancelled: 0,
    urgent: 0
  });

  // Filters
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterTaskType, setFilterTaskType] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Selection
  const [selectedOrders, setSelectedOrders] = useState(new Set());
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [progressData, setProgressData] = useState({
    progress: 0,
    execution_notes: ""
  });
  const [completeData, setCompleteData] = useState({
    actual_hours: "",
    execution_notes: "",
    issues_found: "",
    solution_provided: "",
    photos: []
  });

  const [assignData, setAssignData] = useState({
    assigned_to_id: null,
    remark: ""
  });

  const [createData, setCreateData] = useState({
    project_id: "",
    machine_id: "",
    customer_id: "",
    task_type: INSTALLATION_TYPE.NEW,
    task_title: "",
    task_description: "",
    location: "",
    scheduled_date: "",
    estimated_hours: "",
    priority: DISPATCH_PRIORITY.MEDIUM,
    customer_contact: "",
    customer_phone: "",
    customer_address: "",
    remark: ""
  });

  useEffect(() => {
    fetchUsers();
    fetchProjects();
    fetchOrders();
    fetchStatistics();
  }, [
  filterStatus,
  filterPriority,
  filterProject,
  filterTaskType,
  searchQuery]
  );

  useEffect(() => {
    if (createData.project_id) {
      fetchMachines(createData.project_id);
    } else {
      setMachines([]);
    }
  }, [createData.project_id]);

  // API Functions
  const fetchUsers = async () => {
    try {
      const res = await userApi.list({ page_size: 1000 });
      const data = res.data || res;
      setUsers(data.items || data || []);
    } catch (error) {
      console.error("Failed to fetch users:", error);
      toast.error("获取用户列表失败");
    }
  };

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
      toast.error("获取项目列表失败");
    }
  };

  const fetchMachines = async (projectId) => {
    try {
      const res = await machineApi.list({
        page_size: 1000,
        project_id: projectId
      });
      setMachines(res.data || []);
    } catch (error) {
      console.error("Failed to fetch machines:", error);
      toast.error("获取设备列表失败");
    }
  };

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 1000
      };
      if (filterStatus) params.status = filterStatus;
      if (filterPriority) params.priority = filterPriority;
      if (filterProject) params.project_id = filterProject;
      if (filterTaskType) params.task_type = filterTaskType;
      if (searchQuery) params.search = searchQuery;

      const res = await installationDispatchApi.list(params);
      setOrders(res.data || []);
    } catch (error) {
      console.error("Failed to fetch orders:", error);
      toast.error("获取派工单列表失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const res = await installationDispatchApi.statistics();
      setStats(res.data || {});
    } catch (error) {
      console.error("Failed to fetch statistics:", error);
    }
  };

  // CRUD Operations
  const handleCreateOrder = async () => {
    const validation = validateDispatchData(createData);
    if (!validation.isValid) {
      toast.error(validation.errors.join(", "));
      return;
    }

    try {
      await installationDispatchApi.create(createData);
      toast.success("派工单创建成功");
      setShowCreateDialog(false);
      setCreateData({
        project_id: "",
        machine_id: "",
        customer_id: "",
        task_type: INSTALLATION_TYPE.NEW,
        task_title: "",
        task_description: "",
        location: "",
        scheduled_date: "",
        estimated_hours: "",
        priority: DISPATCH_PRIORITY.MEDIUM,
        customer_contact: "",
        customer_phone: "",
        customer_address: "",
        remark: ""
      });
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to create order:", error);
      toast.error("创建派工单失败");
    }
  };

  const handleAssignOrder = async (orderId) => {
    try {
      await installationDispatchApi.assign(orderId, assignData);
      toast.success("派工成功");
      setShowAssignDialog(false);
      setAssignData({ assigned_to_id: null, remark: "" });
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to assign order:", error);
      toast.error("派工失败");
    }
  };

  const handleUpdateProgress = async () => {
    try {
      await installationDispatchApi.updateProgress(selectedOrder.id, progressData);
      toast.success("进度更新成功");
      setShowProgressDialog(false);
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to update progress:", error);
      toast.error("更新进度失败");
    }
  };

  const handleCompleteOrder = async () => {
    try {
      await installationDispatchApi.complete(selectedOrder.id, completeData);
      toast.success("派工单完成");
      setShowCompleteDialog(false);
      setCompleteData({
        actual_hours: "",
        execution_notes: "",
        issues_found: "",
        solution_provided: "",
        photos: []
      });
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to complete order:", error);
      toast.error("完成派工单失败");
    }
  };

  const _handleDeleteOrder = async (orderId) => {
    if (!confirm("确定要删除这个派工单吗？")) return;

    try {
      await installationDispatchApi.delete(orderId);
      toast.success("派工单删除成功");
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to delete order:", error);
      toast.error("删除派工单失败");
    }
  };

  const handleBatchAssign = async () => {
    if (selectedOrders.size === 0) {
      toast.error("请选择要派工的订单");
      return;
    }
    if (!assignData.assigned_to_id) {
      toast.error("请选择派工人员");
      return;
    }

    try {
      await installationDispatchApi.batchAssign({
        order_ids: Array.from(selectedOrders),
        assigned_to_id: assignData.assigned_to_id,
        remark: assignData.remark
      });
      toast.success("批量派工成功");
      setShowAssignDialog(false);
      setSelectedOrders(new Set());
      setAssignData({ assigned_to_id: null, remark: "" });
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to batch assign:", error);
      toast.error("批量派工失败");
    }
  };

  // Selection handlers
  const handleSelectOrder = (orderId) => {
    const newSelected = new Set(selectedOrders);
    if (newSelected.has(orderId)) {
      newSelected.delete(orderId);
    } else {
      newSelected.add(orderId);
    }
    setSelectedOrders(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedOrders.size === orders.length) {
      setSelectedOrders(new Set());
    } else {
      setSelectedOrders(new Set(orders.map((order) => order.id)));
    }
  };

  // Render functions
  const getStatusBadge = (status) => {
    const config = statusConfig[status];
    if (!config) return <Badge variant="secondary">{status}</Badge>;

    return (
      <Badge
        variant="secondary"
        className={cn("border-0", {
          "bg-slate-500 text-white": status === DISPATCH_STATUS.PENDING,
          "bg-blue-500 text-white": status === DISPATCH_STATUS.ASSIGNED,
          "bg-amber-500 text-white": status === DISPATCH_STATUS.IN_PROGRESS,
          "bg-emerald-500 text-white": status === DISPATCH_STATUS.COMPLETED,
          "bg-red-500 text-white": status === DISPATCH_STATUS.CANCELLED
        })}>

        {config.label}
      </Badge>);

  };

  const getPriorityBadge = (priority) => {
    const config = priorityConfig[priority];
    if (!config) return <Badge variant="secondary">{priority}</Badge>;

    return (
      <Badge
        variant="secondary"
        className={cn("border-0", config.bg, {
          "text-slate-400": priority === DISPATCH_PRIORITY.LOW,
          "text-blue-400": priority === DISPATCH_PRIORITY.MEDIUM,
          "text-amber-400": priority === DISPATCH_PRIORITY.HIGH
        })}>

        {config.label}
      </Badge>);

  };

  const getTaskTypeDisplay = (type) => {
    const config = taskTypeConfig[type];
    if (!config) return type;
    return `${config.icon} ${config.label}`;
  };

  // Quick action handlers for overview component
  const handleQuickAction = (action) => {
    switch (action) {
      case 'createDispatch':
        setShowCreateDialog(true);
        break;
      case 'viewPending':
        setFilterStatus(DISPATCH_STATUS.PENDING);
        break;
      case 'viewOverdue':
        // Filter overdue tasks
        {
          const today = new Date().toISOString().split('T')[0];
          setSearchQuery(today);
        }
        break;
      case 'technicianSchedule':
        // Navigate to technician schedule view
        navigate('/technician-schedule');
        break;
      default:
        break;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="安装调试派工管理"
        description="管理安装调试派工单、批量派工、进度跟踪"
        actions={
        <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建派工单
          </Button>
        } />


      {/* Overview Section */}
      <InstallationDispatchOverview
        dispatches={orders}
        technicians={users}
        onQuickAction={handleQuickAction} />


      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle>派工单列表</CardTitle>
          <CardDescription>
            管理所有安装调试派工单
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索派工单..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10" />

              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  {DISPATCH_FILTER_OPTIONS.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              <Select value={filterPriority} onValueChange={setFilterPriority}>
                <SelectTrigger>
                  <SelectValue placeholder="优先级" />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITY_FILTER_OPTIONS.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              <Select value={filterProject} onValueChange={setFilterProject}>
                <SelectTrigger>
                  <SelectValue placeholder="项目" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) =>
                  <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              <Select value={filterTaskType} onValueChange={setFilterTaskType}>
                <SelectTrigger>
                  <SelectValue placeholder="任务类型" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(INSTALLATION_TYPE).map(([_key, value]) =>
                  <SelectItem key={value} value={value}>
                      {INSTALLATION_TYPE_LABELS[value]}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Batch Actions */}
          {selectedOrders.size > 0 &&
          <div className="flex items-center justify-between p-4 bg-muted rounded-lg mb-4">
              <div className="flex items-center space-x-2">
                <CheckSquare className="h-4 w-4" />
                <span className="text-sm font-medium">
                  已选择 {selectedOrders.size} 个派工单
                </span>
              </div>
              <div className="flex space-x-2">
                <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAssignDialog(true)}>

                  <Users className="mr-2 h-4 w-4" />
                  批量派工
                </Button>
                <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedOrders(new Set())}>

                  取消选择
                </Button>
              </div>
            </div>
          }

          {/* Orders Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <CheckSquare
                      className="h-4 w-4 cursor-pointer"
                      onClick={handleSelectAll} />

                  </TableHead>
                  <TableHead>派工单号</TableHead>
                  <TableHead>任务标题</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>任务类型</TableHead>
                  <TableHead>优先级</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>负责人</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ?
                <TableRow>
                    <TableCell colSpan={10} className="text-center py-8">
                      加载中...
                    </TableCell>
                  </TableRow> :
                orders.length === 0 ?
                <TableRow>
                    <TableCell colSpan={10} className="text-center py-8">
                      暂无派工单
                    </TableCell>
                  </TableRow> :

                orders.map((order) =>
                <TableRow key={order.id}>
                      <TableCell>
                        <Square
                      className={cn(
                        "h-4 w-4 cursor-pointer",
                        selectedOrders.has(order.id) && "text-blue-500"
                      )}
                      onClick={() => handleSelectOrder(order.id)} />

                      </TableCell>
                      <TableCell className="font-medium">
                        {order.order_number}
                      </TableCell>
                      <TableCell>{order.task_title}</TableCell>
                      <TableCell>{order.project?.name}</TableCell>
                      <TableCell>
                        {getTaskTypeDisplay(order.task_type)}
                      </TableCell>
                      <TableCell>{getPriorityBadge(order.priority)}</TableCell>
                      <TableCell>{getStatusBadge(order.status)}</TableCell>
                      <TableCell>{order.assigned_to?.name}</TableCell>
                      <TableCell>
                        {formatDate(order.scheduled_date)}
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-1">
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedOrder(order);
                          setShowDetailDialog(true);
                        }}>

                            <Eye className="h-4 w-4" />
                          </Button>
                          {order.status === DISPATCH_STATUS.PENDING &&
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedOrder(order);
                          setShowAssignDialog(true);
                        }}>

                              <Users className="h-4 w-4" />
                            </Button>
                      }
                          {order.status === DISPATCH_STATUS.IN_PROGRESS &&
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedOrder(order);
                          setShowProgressDialog(true);
                        }}>

                              <Clock className="h-4 w-4" />
                            </Button>
                      }
                          {order.status === DISPATCH_STATUS.IN_PROGRESS &&
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedOrder(order);
                          setShowCompleteDialog(true);
                        }}>

                              <CheckCircle2 className="h-4 w-4" />
                            </Button>
                      }
                        </div>
                      </TableCell>
                    </TableRow>
                )
                }
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>新建派工单</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">项目</label>
              <Select
                value={createData.project_id}
                onValueChange={(value) =>
                setCreateData({ ...createData, project_id: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) =>
                  <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">设备</label>
              <Select
                value={createData.machine_id}
                onValueChange={(value) =>
                setCreateData({ ...createData, machine_id: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择设备" />
                </SelectTrigger>
                <SelectContent>
                  {machines.map((machine) =>
                  <SelectItem key={machine.id} value={machine.id}>
                      {machine.name}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">任务类型</label>
              <Select
                value={createData.task_type}
                onValueChange={(value) =>
                setCreateData({ ...createData, task_type: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择任务类型" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(INSTALLATION_TYPE).map(([_key, value]) =>
                  <SelectItem key={value} value={value}>
                      {INSTALLATION_TYPE_LABELS[value]}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">优先级</label>
              <Select
                value={createData.priority}
                onValueChange={(value) =>
                setCreateData({ ...createData, priority: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择优先级" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(DISPATCH_PRIORITY).map(([_key, value]) =>
                  <SelectItem key={value} value={value}>
                      {DISPATCH_PRIORITY_LABELS[value]}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2">
              <label className="text-sm font-medium">任务标题</label>
              <Input
                value={createData.task_title}
                onChange={(e) =>
                setCreateData({ ...createData, task_title: e.target.value })
                }
                placeholder="输入任务标题" />

            </div>
            <div className="col-span-2">
              <label className="text-sm font-medium">任务描述</label>
              <Textarea
                value={createData.task_description}
                onChange={(e) =>
                setCreateData({
                  ...createData,
                  task_description: e.target.value
                })
                }
                placeholder="输入任务描述"
                rows={3} />

            </div>
            <div>
              <label className="text-sm font-medium">地点</label>
              <Input
                value={createData.location}
                onChange={(e) =>
                setCreateData({ ...createData, location: e.target.value })
                }
                placeholder="输入安装地点" />

            </div>
            <div>
              <label className="text-sm font-medium">计划日期</label>
              <Input
                type="date"
                value={createData.scheduled_date}
                onChange={(e) =>
                setCreateData({
                  ...createData,
                  scheduled_date: e.target.value
                })
                } />

            </div>
            <div>
              <label className="text-sm font-medium">预计工时</label>
              <Input
                type="number"
                value={createData.estimated_hours}
                onChange={(e) =>
                setCreateData({
                  ...createData,
                  estimated_hours: e.target.value
                })
                }
                placeholder="小时" />

            </div>
            <div>
              <label className="text-sm font-medium">客户电话</label>
              <Input
                value={createData.customer_phone}
                onChange={(e) =>
                setCreateData({
                  ...createData,
                  customer_phone: e.target.value
                })
                }
                placeholder="输入客户电话" />

            </div>
            <div className="col-span-2">
              <label className="text-sm font-medium">客户地址</label>
              <Input
                value={createData.customer_address}
                onChange={(e) =>
                setCreateData({
                  ...createData,
                  customer_address: e.target.value
                })
                }
                placeholder="输入客户地址" />

            </div>
            <div className="col-span-2">
              <label className="text-sm font-medium">备注</label>
              <Textarea
                value={createData.remark}
                onChange={(e) =>
                setCreateData({ ...createData, remark: e.target.value })
                }
                placeholder="输入备注信息"
                rows={2} />

            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateOrder}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedOrders.size > 0 ? "批量派工" : "指派派工单"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">派工人员</label>
              <Select
                value={assignData.assigned_to_id}
                onValueChange={(value) =>
                setAssignData({ ...assignData, assigned_to_id: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择派工人员" />
                </SelectTrigger>
                <SelectContent>
                  {users.
                  filter((user) => user.role === "technician").
                  map((user) =>
                  <SelectItem key={user.id} value={user.id}>
                        {user.name}
                      </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">备注</label>
              <Textarea
                value={assignData.remark}
                onChange={(e) =>
                setAssignData({ ...assignData, remark: e.target.value })
                }
                placeholder="输入派工备注"
                rows={3} />

            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignDialog(false)}>
              取消
            </Button>
            <Button
              onClick={() =>
              selectedOrders.size > 0 ?
              handleBatchAssign() :
              handleAssignOrder(selectedOrder.id)
              }>

              {selectedOrders.size > 0 ? "批量派工" : "派工"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>派工单详情</DialogTitle>
          </DialogHeader>
          {selectedOrder &&
          <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">派工单号</label>
                  <p className="mt-1 text-sm">{selectedOrder.order_number}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">状态</label>
                  <div className="mt-1">{getStatusBadge(selectedOrder.status)}</div>
                </div>
                <div>
                  <label className="text-sm font-medium">任务标题</label>
                  <p className="mt-1 text-sm">{selectedOrder.task_title}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">任务类型</label>
                  <p className="mt-1 text-sm">
                    {getTaskTypeDisplay(selectedOrder.task_type)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium">项目</label>
                  <p className="mt-1 text-sm">{selectedOrder.project?.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">设备</label>
                  <p className="mt-1 text-sm">{selectedOrder.machine?.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">优先级</label>
                  <div className="mt-1">
                    {getPriorityBadge(selectedOrder.priority)}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">负责人</label>
                  <p className="mt-1 text-sm">
                    {selectedOrder.assigned_to?.name || "未分配"}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium">计划日期</label>
                  <p className="mt-1 text-sm">
                    {formatDate(selectedOrder.scheduled_date)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium">预计工时</label>
                  <p className="mt-1 text-sm">{selectedOrder.estimated_hours} 小时</p>
                </div>
                <div>
                  <label className="text-sm font-medium">地点</label>
                  <p className="mt-1 text-sm">{selectedOrder.location}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">客户电话</label>
                  <p className="mt-1 text-sm">{selectedOrder.customer_phone}</p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">任务描述</label>
                <p className="mt-1 text-sm whitespace-pre-wrap">
                  {selectedOrder.task_description}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium">客户地址</label>
                <p className="mt-1 text-sm">{selectedOrder.customer_address}</p>
              </div>
              {selectedOrder.remark &&
            <div>
                  <label className="text-sm font-medium">备注</label>
                  <p className="mt-1 text-sm whitespace-pre-wrap">
                    {selectedOrder.remark}
                  </p>
                </div>
            }
            </div>
          }
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Progress Dialog */}
      <Dialog open={showProgressDialog} onOpenChange={setShowProgressDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>更新进度</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">进度 (%)</label>
              <Input
                type="number"
                min="0"
                max="100"
                value={progressData.progress}
                onChange={(e) =>
                setProgressData({
                  ...progressData,
                  progress: parseInt(e.target.value) || 0
                })
                } />

            </div>
            <div>
              <label className="text-sm font-medium">执行记录</label>
              <Textarea
                value={progressData.execution_notes}
                onChange={(e) =>
                setProgressData({
                  ...progressData,
                  execution_notes: e.target.value
                })
                }
                placeholder="输入执行记录"
                rows={4} />

            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowProgressDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdateProgress}>更新进度</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Complete Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>完成派工单</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">实际工时</label>
              <Input
                type="number"
                value={completeData.actual_hours}
                onChange={(e) =>
                setCompleteData({
                  ...completeData,
                  actual_hours: e.target.value
                })
                }
                placeholder="小时" />

            </div>
            <div>
              <label className="text-sm font-medium">执行记录</label>
              <Textarea
                value={completeData.execution_notes}
                onChange={(e) =>
                setCompleteData({
                  ...completeData,
                  execution_notes: e.target.value
                })
                }
                placeholder="输入执行记录"
                rows={4} />

            </div>
            <div>
              <label className="text-sm font-medium">发现问题</label>
              <Textarea
                value={completeData.issues_found}
                onChange={(e) =>
                setCompleteData({
                  ...completeData,
                  issues_found: e.target.value
                })
                }
                placeholder="输入发现的问题"
                rows={3} />

            </div>
            <div>
              <label className="text-sm font-medium">解决方案</label>
              <Textarea
                value={completeData.solution_provided}
                onChange={(e) =>
                setCompleteData({
                  ...completeData,
                  solution_provided: e.target.value
                })
                }
                placeholder="输入解决方案"
                rows={3} />

            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompleteDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCompleteOrder}>完成</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}
