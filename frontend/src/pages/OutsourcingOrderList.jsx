/**
 * Outsourcing Order List Page - 外协订单列表页面
 * Features: 外协订单列表、创建、详情、进度跟踪、质检
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Package,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  Factory } from
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
import { outsourcingApi, projectApi } from "../services/api";
const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500" },
  SUBMITTED: { label: "已提交", color: "bg-blue-500" },
  APPROVED: { label: "已批准", color: "bg-emerald-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-amber-500" },
  DELIVERED: { label: "已交付", color: "bg-purple-500" },
  INSPECTED: { label: "已质检", color: "bg-violet-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" }
};
export default function OutsourcingOrderList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [projects, setProjects] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  // Form state
  const [newOrder, setNewOrder] = useState({
    vendor_id: null,
    project_id: null,
    machine_id: null,
    order_type: "MACHINING",
    order_name: "",
    planned_start_date: "",
    planned_end_date: "",
    delivery_address: "",
    remark: ""
  });
  useEffect(() => {
    fetchProjects();
    fetchOrders();
  }, [filterProject, filterStatus, searchKeyword]);
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };
  const fetchOrders = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject) {params.project_id = filterProject;}
      if (filterStatus) {params.status = filterStatus;}
      if (searchKeyword) {params.keyword = searchKeyword;}
      const res = await outsourcingApi.orders.list(params);
      const orderList = res.data?.items || res.data || [];
      setOrders(orderList);
    } catch (error) {
      console.error("Failed to fetch orders:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleCreateOrder = async () => {
    if (!newOrder.order_name || !newOrder.vendor_id) {
      alert("请填写订单名称和选择外协商");
      return;
    }
    try {
      await outsourcingApi.orders.create(newOrder);
      setShowCreateDialog(false);
      setNewOrder({
        vendor_id: null,
        project_id: null,
        machine_id: null,
        order_type: "MACHINING",
        order_name: "",
        planned_start_date: "",
        planned_end_date: "",
        delivery_address: "",
        remark: ""
      });
      fetchOrders();
    } catch (error) {
      console.error("Failed to create order:", error);
      alert(
        "创建外协订单失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };
  const _handleViewDetail = async (orderId) => {
    try {
      const res = await outsourcingApi.orders.get(orderId);
      setSelectedOrder(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch order detail:", error);
    }
  };
  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          order.order_no?.toLowerCase().includes(keyword) ||
          order.order_name?.toLowerCase().includes(keyword) ||
          order.vendor_name?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [orders, searchKeyword]);
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="外协订单管理"
        description="外协订单列表、创建、进度跟踪、质检" />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索订单号、订单名称..."
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
                {projects.map((proj) =>
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
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建外协订单
        </Button>
      </div>
      {/* Order List */}
      <Card>
        <CardHeader>
          <CardTitle>外协订单列表</CardTitle>
          <CardDescription>
            共 {filteredOrders.length} 个外协订单
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredOrders.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无外协订单</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>订单编号</TableHead>
                  <TableHead>订单名称</TableHead>
                  <TableHead>外协商</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>订单类型</TableHead>
                  <TableHead>计划交期</TableHead>
                  <TableHead>进度</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) =>
              <TableRow key={order.id}>
                    <TableCell className="font-mono text-sm">
                      {order.order_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {order.order_name}
                    </TableCell>
                    <TableCell>{order.vendor_name || "-"}</TableCell>
                    <TableCell>{order.project_name || "-"}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{order.order_type || "-"}</Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {order.planned_end_date ?
                  formatDate(order.planned_end_date) :
                  "-"}
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
                    statusConfigs[order.status]?.color || "bg-slate-500"
                    }>

                        {statusConfigs[order.status]?.label || order.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                      navigate(`/outsourcing-orders/${order.id}`)
                      }>

                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>
      {/* Create Order Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建外协订单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  订单名称 *
                </label>
                <Input
                  value={newOrder.order_name}
                  onChange={(e) =>
                  setNewOrder({ ...newOrder, order_name: e.target.value })
                  }
                  placeholder="请输入订单名称" />

              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">项目</label>
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
                      <SelectItem value="none">无</SelectItem>
                      {projects.map((proj) =>
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                          {proj.project_name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    订单类型
                  </label>
                  <Select
                    value={newOrder.order_type}
                    onValueChange={(val) =>
                    setNewOrder({ ...newOrder, order_type: val })
                    }>

                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MACHINING">机加工</SelectItem>
                      <SelectItem value="ASSEMBLY">装配</SelectItem>
                      <SelectItem value="TREATMENT">表面处理</SelectItem>
                      <SelectItem value="OTHER">其他</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划开始日期
                  </label>
                  <Input
                    type="date"
                    value={newOrder.planned_start_date}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      planned_start_date: e.target.value
                    })
                    } />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划结束日期
                  </label>
                  <Input
                    type="date"
                    value={newOrder.planned_end_date}
                    onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      planned_end_date: e.target.value
                    })
                    } />

                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  交付地址
                </label>
                <Input
                  value={newOrder.delivery_address}
                  onChange={(e) =>
                  setNewOrder({
                    ...newOrder,
                    delivery_address: e.target.value
                  })
                  }
                  placeholder="交付地址" />

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
      {/* Order Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedOrder?.order_name} - {selectedOrder?.order_no}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedOrder &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">订单编号</div>
                    <div className="font-mono">{selectedOrder.order_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge
                    className={statusConfigs[selectedOrder.status]?.color}>

                      {statusConfigs[selectedOrder.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">外协商</div>
                    <div>{selectedOrder.vendor_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedOrder.project_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">订单类型</div>
                    <div>{selectedOrder.order_type || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划交期</div>
                    <div>
                      {selectedOrder.planned_end_date ?
                    formatDate(selectedOrder.planned_end_date) :
                    "-"}
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
                </div>
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}