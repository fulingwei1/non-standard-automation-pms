/**
 * Work Order Management Page - 工单管理页面
 * Features: 工单列表、详情、创建、派工、进度跟踪
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Wrench,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  CheckCircle2,
  Clock,
  AlertTriangle,
  User,
  Calendar,
  Package,
  TrendingUp } from
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
import { Progress } from "../components/ui/progress";
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
import { cn as _cn, formatDate } from "../lib/utils";
import { productionApi, projectApi } from "../services/api";
const statusConfigs = {
  PENDING: { label: "待派工", color: "bg-slate-500" },
  ASSIGNED: { label: "已派工", color: "bg-blue-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-amber-500" },
  PAUSED: { label: "已暂停", color: "bg-purple-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" }
};
const priorityConfigs = {
  URGENT: { label: "紧急", color: "bg-red-500" },
  HIGH: { label: "高", color: "bg-orange-500" },
  MEDIUM: { label: "中", color: "bg-amber-500" },
  LOW: { label: "低", color: "bg-blue-500" }
};
export default function WorkOrderManagement() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [workOrders, setWorkOrders] = useState([]);
  const [projects, setProjects] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  // Form states
  const [newOrder, setNewOrder] = useState({
    task_name: "",
    task_type: "ASSEMBLY",
    project_id: null,
    machine_id: null,
    workshop_id: null,
    workstation_id: null,
    process_id: null,
    material_name: "",
    specification: "",
    plan_qty: 0,
    standard_hours: 0,
    plan_start_date: "",
    plan_end_date: "",
    priority: "MEDIUM",
    work_content: "",
    remark: ""
  });
  const [assignData, setAssignData] = useState({
    assigned_to: null,
    workstation_id: null
  });
  useEffect(() => {
    fetchProjects();
    fetchWorkOrders();
  }, [filterProject, filterStatus, filterPriority, searchKeyword]);
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };
  const fetchWorkOrders = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject) {params.project_id = filterProject;}
      if (filterStatus) {params.status = filterStatus;}
      if (filterPriority) {params.priority = filterPriority;}
      if (searchKeyword) {params.search = searchKeyword;}
      const res = await productionApi.workOrders.list(params);
      const orderList = res.data?.items || res.data?.items || res.data || [];
      setWorkOrders(orderList);
    } catch (error) {
      console.error("Failed to fetch work orders:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleCreateOrder = async () => {
    if (!newOrder.task_name || !newOrder.project_id) {
      alert("请填写任务名称和选择项目");
      return;
    }
    try {
      await productionApi.workOrders.create(newOrder);
      setShowCreateDialog(false);
      setNewOrder({
        task_name: "",
        task_type: "ASSEMBLY",
        project_id: null,
        machine_id: null,
        workshop_id: null,
        workstation_id: null,
        process_id: null,
        material_name: "",
        specification: "",
        plan_qty: 0,
        standard_hours: 0,
        plan_start_date: "",
        plan_end_date: "",
        priority: "MEDIUM",
        work_content: "",
        remark: ""
      });
      fetchWorkOrders();
    } catch (error) {
      console.error("Failed to create work order:", error);
      alert("创建工单失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const handleViewDetail = async (orderId) => {
    try {
      const res = await productionApi.workOrders.get(orderId);
      setSelectedOrder(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch work order detail:", error);
    }
  };
  const handleAssign = async () => {
    if (!selectedOrder) {return;}
    try {
      await productionApi.workOrders.assign(selectedOrder.id, assignData);
      setShowAssignDialog(false);
      setAssignData({
        assigned_to: null,
        workstation_id: null
      });
      fetchWorkOrders();
      if (showDetailDialog) {
        handleViewDetail(selectedOrder.id);
      }
    } catch (error) {
      console.error("Failed to assign work order:", error);
      alert("派工失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const filteredOrders = useMemo(() => {
    return (workOrders || []).filter((order) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          order.work_order_no?.toLowerCase().includes(keyword) ||
          order.task_name?.toLowerCase().includes(keyword) ||
          order.material_name?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [workOrders, searchKeyword]);
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="工单管理"
        description="生产工单管理，支持创建、派工、进度跟踪" />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索工单号、任务名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {(projects || []).map((proj) =>
                <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.project_name}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger>
                <SelectValue placeholder="选择优先级" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部优先级</SelectItem>
                {Object.entries(priorityConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建工单
        </Button>
      </div>
      {/* Work Order List */}
      <Card>
        <CardHeader>
          <CardTitle>工单列表</CardTitle>
          <CardDescription>共 {filteredOrders.length} 个工单</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredOrders.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无工单</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>工单号</TableHead>
                  <TableHead>任务名称</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>物料</TableHead>
                  <TableHead>计划数量</TableHead>
                  <TableHead>完成数量</TableHead>
                  <TableHead>进度</TableHead>
                  <TableHead>优先级</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(filteredOrders || []).map((order) =>
              <TableRow key={order.id}>
                    <TableCell className="font-mono text-sm">
                      {order.work_order_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {order.task_name}
                    </TableCell>
                    <TableCell>{order.project_name || "-"}</TableCell>
                    <TableCell>
                      {order.material_name || "-"}
                      {order.specification &&
                  <div className="text-xs text-slate-500">
                          {order.specification}
                  </div>
                  }
                    </TableCell>
                    <TableCell>{order.plan_qty || 0}</TableCell>
                    <TableCell className="font-medium">
                      {order.completed_qty || 0}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span>{order.progress || 0}%</span>
                        </div>
                        <Progress
                      value={order.progress || 0}
                      className="h-1.5" />

                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    priorityConfigs[order.priority]?.color ||
                    "bg-slate-500"
                    }>

                        {priorityConfigs[order.priority]?.label ||
                    order.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    statusConfigs[order.status]?.color || "bg-slate-500"
                    }>

                        {statusConfigs[order.status]?.label || order.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {order.plan_start_date ?
                  formatDate(order.plan_start_date) :
                  "-"}
                      {order.plan_end_date &&
                  <>
                          <span className="mx-1">-</span>
                          {formatDate(order.plan_end_date)}
                  </>
                  }
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/work-orders/${order.id}`)}>

                          <Eye className="w-4 h-4" />
                        </Button>
                        {order.status === "PENDING" &&
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedOrder(order);
                        setShowAssignDialog(true);
                      }}>

                            <User className="w-4 h-4" />
                    </Button>
                    }
                      </div>
                    </TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>
      {/* Create Work Order Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建工单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  任务名称 *
                </label>
                <Input
                  value={newOrder.task_name}
                  onChange={(e) =>
                  setNewOrder({ ...newOrder, task_name: e.target.value })
                  }
                  placeholder="请输入任务名称" />

              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    项目 *
                  </label>
                  <Select
                    value={newOrder.project_id?.toString() || ""}
                    onValueChange={(val) =>
                    setNewOrder({
                      ...newOrder,
                      project_id: val ? parseInt(val) : null
                    })
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      {(projects || []).map((proj) =>
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                          {proj.project_name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    任务类型
                  </label>
                  <Select
                    value={newOrder.task_type}
                    onValueChange={(val) =>
                    setNewOrder({ ...newOrder, task_type: val })
                    }>

                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ASSEMBLY">装配</SelectItem>
                      <SelectItem value="MACHINING">机加工</SelectItem>
                      <SelectItem value="WELDING">焊接</SelectItem>
                      <SelectItem value="PAINTING">喷涂</SelectItem>
                      <SelectItem value="OTHER">其他</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    物料名称
                  </label>
                  <Input
                    value={newOrder.material_name}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      material_name: e.target.value
                    })
                    }
                    placeholder="物料名称" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">规格</label>
                  <Input
                    value={newOrder.specification}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      specification: e.target.value
                    })
                    }
                    placeholder="规格" />

                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划数量
                  </label>
                  <Input
                    type="number"
                    value={newOrder.plan_qty}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      plan_qty: parseFloat(e.target.value) || 0
                    })
                    }
                    placeholder="0" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    标准工时（小时）
                  </label>
                  <Input
                    type="number"
                    value={newOrder.standard_hours}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      standard_hours: parseFloat(e.target.value) || 0
                    })
                    }
                    placeholder="0" />

                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划开始日期
                  </label>
                  <Input
                    type="date"
                    value={newOrder.plan_start_date}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      plan_start_date: e.target.value
                    })
                    } />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划结束日期
                  </label>
                  <Input
                    type="date"
                    value={newOrder.plan_end_date}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      plan_end_date: e.target.value
                    })
                    } />

                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">优先级</label>
                <Select
                  value={newOrder.priority}
                  onValueChange={(val) =>
                  setNewOrder({ ...newOrder, priority: val })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(priorityConfigs).map(([key, config]) =>
                    <SelectItem key={key} value={key}>
                        {config.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  工作内容
                </label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newOrder.work_content}
                  onChange={(e) =>
                  setNewOrder({ ...newOrder, work_content: e.target.value })
                  }
                  placeholder="工作内容描述..." />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreateOrder}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Work Order Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedOrder?.task_name} - {selectedOrder?.work_order_no}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedOrder &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">工单号</div>
                    <div className="font-mono">
                      {selectedOrder.work_order_no}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge
                    className={statusConfigs[selectedOrder.status]?.color}>

                      {statusConfigs[selectedOrder.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedOrder.project_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">优先级</div>
                    <Badge
                    className={priorityConfigs[selectedOrder.priority]?.color}>

                      {priorityConfigs[selectedOrder.priority]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划数量</div>
                    <div className="font-medium">
                      {selectedOrder.plan_qty || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">完成数量</div>
                    <div className="font-medium">
                      {selectedOrder.completed_qty || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">进度</div>
                    <div className="space-y-1">
                      <div className="text-lg font-bold">
                        {selectedOrder.progress || 0}%
                      </div>
                      <Progress
                      value={selectedOrder.progress || 0}
                      className="h-2" />

                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">标准工时</div>
                    <div>{selectedOrder.standard_hours || 0} 小时</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划开始</div>
                    <div>
                      {selectedOrder.plan_start_date ?
                    formatDate(selectedOrder.plan_start_date) :
                    "-"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划结束</div>
                    <div>
                      {selectedOrder.plan_end_date ?
                    formatDate(selectedOrder.plan_end_date) :
                    "-"}
                    </div>
                  </div>
                </div>
                {selectedOrder.work_content &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">工作内容</div>
                    <div>{selectedOrder.work_content}</div>
              </div>
              }
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            {selectedOrder && selectedOrder.status === "PENDING" &&
            <Button
              onClick={() => {
                setShowDetailDialog(false);
                setShowAssignDialog(true);
              }}>

                <User className="w-4 h-4 mr-2" />
                派工
            </Button>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Assign Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>派工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedOrder &&
            <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">工单号</div>
                  <div className="font-mono">{selectedOrder.work_order_no}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">任务名称</div>
                  <div className="font-medium">{selectedOrder.task_name}</div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    分配人员
                  </label>
                  <Input
                  type="number"
                  value={assignData.assigned_to || ""}
                  onChange={(e) =>
                  setAssignData({
                    ...assignData,
                    assigned_to: e.target.value ?
                    parseInt(e.target.value) :
                    null
                  })
                  }
                  placeholder="人员ID" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">工位</label>
                  <Input
                  type="number"
                  value={assignData.workstation_id || ""}
                  onChange={(e) =>
                  setAssignData({
                    ...assignData,
                    workstation_id: e.target.value ?
                    parseInt(e.target.value) :
                    null
                  })
                  }
                  placeholder="工位ID" />

                </div>
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAssignDialog(false)}>

              取消
            </Button>
            <Button onClick={handleAssign}>确认派工</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}