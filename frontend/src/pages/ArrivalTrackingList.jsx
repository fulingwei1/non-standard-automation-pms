/**
 * Arrival Tracking List Page - 到货跟踪列表页面
 * Features: 到货跟踪列表、创建、状态更新、延迟跟踪
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Package,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
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
import { cn, formatDate } from "../lib/utils";
import { shortageApi, supplierApi } from "../services/api";
const statusConfigs = {
  PENDING: { label: "待到货", color: "bg-blue-500" },
  IN_TRANSIT: { label: "运输中", color: "bg-amber-500" },
  ARRIVED: { label: "已到货", color: "bg-emerald-500" },
  RECEIVED: { label: "已收货", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};
export default function ArrivalTrackingList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [arrivals, setArrivals] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterSupplier, setFilterSupplier] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterDelayed, setFilterDelayed] = useState("all");
  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedArrival, setSelectedArrival] = useState(null);
  useEffect(() => {
    fetchSuppliers();
    fetchArrivals();
  }, [filterSupplier, filterStatus, filterDelayed, searchKeyword]);
  const fetchSuppliers = async () => {
    try {
      const res = await supplierApi.list({ page_size: 1000 });
      // Handle different response formats
      const data = res.data?.data || res.data || res;
      const supplierList = data?.items || (Array.isArray(data) ? data : []);
      setSuppliers(supplierList);
    } catch (error) {
      console.error("Failed to fetch suppliers:", error);
      setSuppliers([]);
    }
  };
  const fetchArrivals = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterSupplier && filterSupplier !== "all")
        {params.supplier_id = filterSupplier;}
      if (filterStatus && filterStatus !== "all") {params.status = filterStatus;}
      if (filterDelayed && filterDelayed !== "all")
        {params.is_delayed = filterDelayed === "true";}
      if (searchKeyword) {params.keyword = searchKeyword;}
      const res = await shortageApi.arrivals.list(params);
      // Handle different response formats
      const data = res.data?.data || res.data || res;
      const arrivalList = data?.items || (Array.isArray(data) ? data : []);
      setArrivals(arrivalList);
    } catch (error) {
      console.error("Failed to fetch arrivals:", error);
      setArrivals([]);
    } finally {
      setLoading(false);
    }
  };
  const handleViewDetail = async (arrivalId) => {
    try {
      const res = await shortageApi.arrivals.get(arrivalId);
      setSelectedArrival(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch arrival detail:", error);
    }
  };
  const filteredArrivals = useMemo(() => {
    return (arrivals || []).filter((arrival) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          arrival.arrival_no?.toLowerCase().includes(keyword) ||
          arrival.material_code?.toLowerCase().includes(keyword) ||
          arrival.material_name?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [arrivals, searchKeyword]);
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="到货跟踪管理"
          description="到货跟踪列表、创建、状态更新、延迟跟踪"
        />
        {/* Filters */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索到货单号、物料编码..."
                  value={searchKeyword || "unknown"}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={filterSupplier || "unknown"} onValueChange={setFilterSupplier}>
                <SelectTrigger>
                  <SelectValue placeholder="选择供应商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部供应商</SelectItem>
                  {(suppliers || []).map((supplier) => {
                    const supplierId =
                      supplier.id?.toString() ||
                      supplier.supplier_id?.toString();
                    if (!supplierId || supplierId === "") {return null;}
                    return (
                      <SelectItem
                        key={supplier.id || supplier.supplier_id}
                        value={supplierId || "unknown"}
                      >
                        {supplier.supplier_name ||
                          supplier.name ||
                          "未知供应商"}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              <Select value={filterStatus || "unknown"} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  {Object.entries(statusConfigs)
                    .filter(([key]) => key && key !== "")
                    .map(([key, config]) => (
                      <SelectItem key={key} value={key || "unknown"}>
                        {config.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              <Select value={filterDelayed || "unknown"} onValueChange={setFilterDelayed}>
                <SelectTrigger>
                  <SelectValue placeholder="延迟状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="true">已延迟</SelectItem>
                  <SelectItem value="false">未延迟</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
        {/* Action Bar */}
        <div className="flex justify-end">
          <Button onClick={() => navigate("/arrival-tracking/new")}>
            <Plus className="w-4 h-4 mr-2" />
            新建到货跟踪
          </Button>
        </div>
        {/* Arrival List */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-slate-200">到货跟踪列表</CardTitle>
            <CardDescription className="text-slate-400">
              共 {filteredArrivals.length} 个到货跟踪
              {(filteredArrivals || []).filter((a) => a.is_delayed).length > 0 && (
                <span className="ml-2 text-red-400">
                  （延迟: {(filteredArrivals || []).filter((a) => a.is_delayed).length}
                  ）
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredArrivals.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                暂无到货跟踪
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-400">到货单号</TableHead>
                    <TableHead className="text-slate-400">物料编码</TableHead>
                    <TableHead className="text-slate-400">物料名称</TableHead>
                    <TableHead className="text-slate-400">供应商</TableHead>
                    <TableHead className="text-slate-400">预期数量</TableHead>
                    <TableHead className="text-slate-400">预期日期</TableHead>
                    <TableHead className="text-slate-400">实际日期</TableHead>
                    <TableHead className="text-slate-400">延迟天数</TableHead>
                    <TableHead className="text-slate-400">状态</TableHead>
                    <TableHead className="text-right text-slate-400">
                      操作
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(filteredArrivals || []).map((arrival) => (
                    <TableRow
                      key={arrival.id}
                      className={cn(
                        "border-slate-700",
                        arrival.is_delayed && "bg-red-500/10",
                      )}
                    >
                      <TableCell className="font-mono text-sm text-slate-200">
                        {arrival.arrival_no}
                      </TableCell>
                      <TableCell className="font-mono text-sm text-slate-300">
                        {arrival.material_code}
                      </TableCell>
                      <TableCell className="font-medium text-slate-200">
                        {arrival.material_name}
                      </TableCell>
                      <TableCell className="text-slate-300">
                        {arrival.supplier_name || "-"}
                      </TableCell>
                      <TableCell className="text-slate-300">
                        {arrival.expected_qty || 0}
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {arrival.expected_date
                          ? formatDate(arrival.expected_date)
                          : "-"}
                      </TableCell>
                      <TableCell
                        className={cn(
                          "text-sm",
                          arrival.actual_date
                            ? "text-emerald-400"
                            : "text-slate-400",
                        )}
                      >
                        {arrival.actual_date
                          ? formatDate(arrival.actual_date)
                          : "未到货"}
                      </TableCell>
                      <TableCell>
                        {arrival.is_delayed && arrival.delay_days ? (
                          <Badge variant="destructive">
                            {arrival.delay_days} 天
                          </Badge>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            statusConfigs[arrival.status]?.color ||
                            "bg-slate-500"
                          }
                        >
                          {statusConfigs[arrival.status]?.label ||
                            arrival.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(arrival.id)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
        {/* Arrival Detail Dialog */}
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">
                {selectedArrival?.arrival_no} - 到货跟踪详情
              </DialogTitle>
            </DialogHeader>
            <DialogBody>
              {selectedArrival && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        到货单号
                      </div>
                      <div className="font-mono text-slate-200">
                        {selectedArrival.arrival_no}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">状态</div>
                      <Badge
                        className={statusConfigs[selectedArrival.status]?.color}
                      >
                        {statusConfigs[selectedArrival.status]?.label}
                      </Badge>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        物料编码
                      </div>
                      <div className="font-mono text-slate-200">
                        {selectedArrival.material_code}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        物料名称
                      </div>
                      <div className="text-slate-200">
                        {selectedArrival.material_name}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">供应商</div>
                      <div className="text-slate-200">
                        {selectedArrival.supplier_name || "-"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        预期数量
                      </div>
                      <div className="font-medium text-slate-200">
                        {selectedArrival.expected_qty || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        预期日期
                      </div>
                      <div className="text-slate-200">
                        {selectedArrival.expected_date
                          ? formatDate(selectedArrival.expected_date)
                          : "-"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        实际日期
                      </div>
                      <div
                        className={
                          selectedArrival.actual_date
                            ? "text-emerald-400"
                            : "text-slate-400"
                        }
                      >
                        {selectedArrival.actual_date
                          ? formatDate(selectedArrival.actual_date)
                          : "未到货"}
                      </div>
                    </div>
                    {selectedArrival.is_delayed && (
                      <div>
                        <div className="text-sm text-slate-400 mb-1">
                          延迟天数
                        </div>
                        <Badge variant="destructive">
                          {selectedArrival.delay_days || 0} 天
                        </Badge>
                      </div>
                    )}
                    {selectedArrival.received_qty !== undefined && (
                      <div>
                        <div className="text-sm text-slate-500 mb-1">
                          已收货数量
                        </div>
                        <div className="font-medium text-emerald-600">
                          {selectedArrival.received_qty || 0}
                        </div>
                      </div>
                    )}
                  </div>
                  {selectedArrival.remark && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">备注</div>
                      <div>{selectedArrival.remark}</div>
                    </div>
                  )}
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
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
