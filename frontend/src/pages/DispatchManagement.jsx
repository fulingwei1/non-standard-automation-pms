/**
 * Dispatch Management Page - 派工管理页面
 * Features: 批量派工、工单分配、工人选择
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Users,
  CheckSquare,
  Square } from
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
import { cn, formatDate } from "../lib/utils";
import { productionApi } from "../services/api";
export default function DispatchManagement() {
  const _navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [workOrders, setWorkOrders] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [workshops, setWorkshops] = useState([]);
  // Filters
  const [filterWorkshop, setFilterWorkshop] = useState("");
  const [filterStatus, setFilterStatus] = useState("PENDING");
  // Selection
  const [selectedOrders, setSelectedOrders] = useState(new Set());
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [assignData, setAssignData] = useState({
    worker_id: null,
    workstation_id: null,
    remark: ""
  });
  useEffect(() => {
    fetchWorkshops();
    fetchWorkers();
    fetchWorkOrders();
  }, [filterWorkshop, filterStatus]);
  const fetchWorkshops = async () => {
    try {
      const res = await productionApi.workshops.list({ page_size: 1000 });
      setWorkshops(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch workshops:", error);
    }
  };
  const fetchWorkers = async () => {
    try {
      const res = await productionApi.workers.list({ page_size: 1000 });
      setWorkers(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch workers:", error);
      setWorkers([]);
    }
  };
  const fetchWorkOrders = async () => {
    try {
      setLoading(true);
      const params = { status: filterStatus || "PENDING" };
      if (filterWorkshop) {params.workshop_id = filterWorkshop;}
      const res = await productionApi.workOrders.list(params);
      const orderList = res.data?.items || res.data || [];
      setWorkOrders(orderList);
    } catch (error) {
      console.error("Failed to fetch work orders:", error);
    } finally {
      setLoading(false);
    }
  };
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
    if (selectedOrders.size === workOrders.length) {
      setSelectedOrders(new Set());
    } else {
      setSelectedOrders(new Set(workOrders.map((wo) => wo.id)));
    }
  };
  const handleBatchAssign = async () => {
    if (selectedOrders.size === 0) {
      alert("请选择要派工的工单");
      return;
    }
    if (!assignData.worker_id) {
      alert("请选择工人");
      return;
    }
    try {
      const orderIds = Array.from(selectedOrders);
      for (const orderId of orderIds) {
        await productionApi.workOrders.assign(orderId, {
          assigned_to: assignData.worker_id,
          workstation_id: assignData.workstation_id,
          remark: assignData.remark
        });
      }
      setShowAssignDialog(false);
      setSelectedOrders(new Set());
      setAssignData({
        worker_id: null,
        workstation_id: null,
        remark: ""
      });
      fetchWorkOrders();
      alert(`成功派工 ${orderIds.length} 个工单`);
    } catch (error) {
      console.error("Failed to assign work orders:", error);
      alert("派工失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const pendingOrders = useMemo(() => {
    return workOrders.filter((wo) => wo.status === "PENDING");
  }, [workOrders]);
  return (
    <div className="space-y-6 p-6">
      <PageHeader title="派工管理" description="批量派工、工单分配、工人选择" />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select value={filterWorkshop} onValueChange={setFilterWorkshop}>
              <SelectTrigger>
                <SelectValue placeholder="选择车间" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部车间</SelectItem>
                {workshops.map((ws) =>
                <SelectItem key={ws.id} value={ws.id.toString()}>
                    {ws.workshop_name}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PENDING">待派工</SelectItem>
                <SelectItem value="ASSIGNED">已派工</SelectItem>
                <SelectItem value="all">全部</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">
            已选择 {selectedOrders.size} 个工单
          </span>
          {selectedOrders.size > 0 &&
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedOrders(new Set())}>

              清空选择
          </Button>
          }
        </div>
        <Button
          onClick={() => setShowAssignDialog(true)}
          disabled={selectedOrders.size === 0}>

          <Users className="w-4 h-4 mr-2" />
          批量派工 ({selectedOrders.size})
        </Button>
      </div>
      {/* Work Order List */}
      <Card>
        <CardHeader>
          <CardTitle>待派工工单列表</CardTitle>
          <CardDescription>
            共 {pendingOrders.length} 个待派工工单
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          pendingOrders.length === 0 ?
          <div className="text-center py-8 text-slate-400">
              暂无待派工工单
          </div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Button variant="ghost" size="sm" onClick={handleSelectAll}>
                      {selectedOrders.size === pendingOrders.length ?
                    <CheckSquare className="w-4 h-4" /> :

                    <Square className="w-4 h-4" />
                    }
                    </Button>
                  </TableHead>
                  <TableHead>工单编号</TableHead>
                  <TableHead>任务名称</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>车间</TableHead>
                  <TableHead>计划数量</TableHead>
                  <TableHead>计划开始</TableHead>
                  <TableHead>计划结束</TableHead>
                  <TableHead>优先级</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingOrders.map((order) =>
              <TableRow
                key={order.id}
                className={cn(selectedOrders.has(order.id) && "bg-blue-50")}>

                    <TableCell>
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSelectOrder(order.id)}>

                        {selectedOrders.has(order.id) ?
                    <CheckSquare className="w-4 h-4" /> :

                    <Square className="w-4 h-4" />
                    }
                      </Button>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {order.work_order_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {order.task_name}
                    </TableCell>
                    <TableCell>{order.project_name || "-"}</TableCell>
                    <TableCell>{order.workshop_name || "-"}</TableCell>
                    <TableCell>{order.plan_qty || 0}</TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {order.plan_start_date ?
                  formatDate(order.plan_start_date) :
                  "-"}
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {order.plan_end_date ?
                  formatDate(order.plan_end_date) :
                  "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{order.priority || "-"}</Badge>
                    </TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>
      {/* Batch Assign Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量派工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-2">
                  已选择 {selectedOrders.size} 个工单
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  选择工人 *
                </label>
                <Select
                  value={assignData.worker_id?.toString() || ""}
                  onValueChange={(val) =>
                  setAssignData({
                    ...assignData,
                    worker_id: val ? parseInt(val) : null
                  })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择工人" />
                  </SelectTrigger>
                  <SelectContent>
                    {workers.map((worker) =>
                    <SelectItem key={worker.id} value={worker.id.toString()}>
                        {worker.worker_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {workers.length === 0 &&
                <div className="text-xs text-slate-400 mt-1">
                    暂无工人数据，请先配置工人信息
                </div>
                }
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  选择工位（可选）
                </label>
                <Select
                  value={assignData.workstation_id?.toString() || ""}
                  onValueChange={(val) =>
                  setAssignData({
                    ...assignData,
                    workstation_id: val ? parseInt(val) : null
                  })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择工位" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">无</SelectItem>
                    {/* 这里需要根据车间获取工位列表 */}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">备注</label>
                <Input
                  value={assignData.remark}
                  onChange={(e) =>
                  setAssignData({ ...assignData, remark: e.target.value })
                  }
                  placeholder="派工备注" />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAssignDialog(false)}>

              取消
            </Button>
            <Button
              onClick={handleBatchAssign}
              disabled={!assignData.worker_id}>

              确认派工
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}