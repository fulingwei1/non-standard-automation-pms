/**
 * Acceptance Order List Page - 验收单列表页面
 * Features: 验收单列表、创建、执行、问题管理
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  ClipboardCheck,
  Plus,
  Search,
  Filter,
  Eye,
  Play,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  Edit,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui/dialog";
import { formatDate } from "../lib/utils";
import { acceptanceApi, projectApi } from "../services/api";
const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};
const typeConfigs = {
  FAT: { label: "FAT", color: "bg-blue-500" },
  SAT: { label: "SAT", color: "bg-purple-500" },
  FINAL: { label: "终验收", color: "bg-emerald-500" },
};
const resultConfigs = {
  PASS: { label: "通过", color: "bg-emerald-500" },
  FAIL: { label: "不通过", color: "bg-red-500" },
  CONDITIONAL: { label: "有条件通过", color: "bg-amber-500" },
};
export default function AcceptanceOrderList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [projects, setProjects] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  // Form state
  const [newOrder, setNewOrder] = useState({
    project_id: null,
    machine_id: null,
    acceptance_type: "FAT",
    template_id: null,
    planned_date: "",
    location: "",
  });
  useEffect(() => {
    fetchProjects();
    fetchOrders();
  }, [filterProject, filterType, filterStatus, searchKeyword]);
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
      if (filterProject) params.project_id = filterProject;
      if (filterType) params.acceptance_type = filterType;
      if (filterStatus) params.status = filterStatus;
      if (searchKeyword) params.keyword = searchKeyword;
      const res = await acceptanceApi.orders.list(params);
      const orderList = res.data?.items || res.data || [];
      setOrders(orderList);
    } catch (error) {
      console.error("Failed to fetch orders:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleCreateOrder = async () => {
    if (!newOrder.project_id || !newOrder.planned_date) {
      alert("请填写项目和计划日期");
      return;
    }
    try {
      await acceptanceApi.orders.create(newOrder);
      setShowCreateDialog(false);
      setNewOrder({
        project_id: null,
        machine_id: null,
        acceptance_type: "FAT",
        template_id: null,
        planned_date: "",
        location: "",
      });
      fetchOrders();
    } catch (error) {
      console.error("Failed to create order:", error);
      alert(
        "创建验收单失败: " + (error.response?.data?.detail || error.message),
      );
    }
  };
  const handleViewDetail = async (orderId) => {
    try {
      const res = await acceptanceApi.orders.get(orderId);
      setSelectedOrder(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch order detail:", error);
    }
  };
  const handleStart = async (orderId) => {
    if (!confirm("确认开始验收？")) return;
    try {
      await acceptanceApi.orders.start(orderId, { location: "" });
      fetchOrders();
      if (showDetailDialog) {
        handleViewDetail(orderId);
      }
    } catch (error) {
      console.error("Failed to start acceptance:", error);
      alert("开始验收失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          order.order_no?.toLowerCase().includes(keyword) ||
          order.project_name?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [orders, searchKeyword]);
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="验收单管理"
        description="验收单列表、创建、执行、问题管理"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索验收单号..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {projects.map((proj) => (
                  <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建验收单
        </Button>
      </div>
      {/* Order List */}
      <Card>
        <CardHeader>
          <CardTitle>验收单列表</CardTitle>
          <CardDescription>共 {filteredOrders.length} 个验收单</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无验收单</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>验收单号</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>机台</TableHead>
                  <TableHead>验收类型</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead>通过率</TableHead>
                  <TableHead>开放问题</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-mono text-sm">
                      {order.order_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {order.project_name || "-"}
                    </TableCell>
                    <TableCell>{order.machine_name || "-"}</TableCell>
                    <TableCell>
                      <Badge
                        className={
                          typeConfigs[order.acceptance_type]?.color ||
                          "bg-slate-500"
                        }
                      >
                        {typeConfigs[order.acceptance_type]?.label ||
                          order.acceptance_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {order.planned_date
                        ? formatDate(order.planned_date)
                        : "-"}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {order.pass_rate ? `${order.pass_rate}%` : "-"}
                        </span>
                        {order.pass_rate && (
                          <Progress
                            value={order.pass_rate}
                            className="h-1.5 w-16"
                          />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {order.open_issues > 0 ? (
                        <Badge variant="destructive">{order.open_issues}</Badge>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          statusConfigs[order.status]?.color || "bg-slate-500"
                        }
                      >
                        {statusConfigs[order.status]?.label || order.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(order.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {order.status === "DRAFT" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStart(order.id)}
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                        )}
                        {order.status === "IN_PROGRESS" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              navigate(`/acceptance-orders/${order.id}/execute`)
                            }
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      {/* Create Order Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建验收单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">项目 *</label>
                <Select
                  value={newOrder.project_id?.toString() || ""}
                  onValueChange={(val) =>
                    setNewOrder({
                      ...newOrder,
                      project_id: val ? parseInt(val) : null,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((proj) => (
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                        {proj.project_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    验收类型
                  </label>
                  <Select
                    value={newOrder.acceptance_type}
                    onValueChange={(val) =>
                      setNewOrder({ ...newOrder, acceptance_type: val })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typeConfigs).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划日期 *
                  </label>
                  <Input
                    type="date"
                    value={newOrder.planned_date}
                    onChange={(e) =>
                      setNewOrder({ ...newOrder, planned_date: e.target.value })
                    }
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  验收地点
                </label>
                <Input
                  value={newOrder.location}
                  onChange={(e) =>
                    setNewOrder({ ...newOrder, location: e.target.value })
                  }
                  placeholder="验收地点"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
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
            <DialogTitle>{selectedOrder?.order_no} - 验收单详情</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedOrder && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">验收单号</div>
                    <div className="font-mono">{selectedOrder.order_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge
                      className={statusConfigs[selectedOrder.status]?.color}
                    >
                      {statusConfigs[selectedOrder.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedOrder.project_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">机台</div>
                    <div>{selectedOrder.machine_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">验收类型</div>
                    <Badge
                      className={
                        typeConfigs[selectedOrder.acceptance_type]?.color
                      }
                    >
                      {typeConfigs[selectedOrder.acceptance_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划日期</div>
                    <div>
                      {selectedOrder.planned_date
                        ? formatDate(selectedOrder.planned_date)
                        : "-"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">通过率</div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold">
                        {selectedOrder.pass_rate || 0}%
                      </span>
                      {selectedOrder.pass_rate && (
                        <Progress
                          value={selectedOrder.pass_rate}
                          className="h-2 flex-1"
                        />
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">总体结果</div>
                    {selectedOrder.overall_result && (
                      <Badge
                        className={
                          resultConfigs[selectedOrder.overall_result]?.color
                        }
                      >
                        {resultConfigs[selectedOrder.overall_result]?.label}
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">总项数</div>
                    <div className="text-lg font-bold">
                      {selectedOrder.total_items || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">通过</div>
                    <div className="text-lg font-bold text-emerald-600">
                      {selectedOrder.passed_items || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">不通过</div>
                    <div className="text-lg font-bold text-red-600">
                      {selectedOrder.failed_items || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">不适用</div>
                    <div className="text-lg font-bold text-slate-400">
                      {selectedOrder.na_items || 0}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}
            >
              关闭
            </Button>
            {selectedOrder && selectedOrder.status === "DRAFT" && (
              <Button onClick={() => handleStart(selectedOrder.id)}>
                <Play className="w-4 h-4 mr-2" />
                开始验收
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
