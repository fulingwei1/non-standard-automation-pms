/**
 * Arrival Tracking List Page - 到货跟踪列表页面
 * Features: 到货跟踪列表、筛选、跳转详情/新建
 */
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, Eye } from "lucide-react";
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
import { cn, formatDate } from "../lib/utils";
import { shortageApi, supplierApi } from "../services/api";

const statusConfigs = {
  PENDING: { label: "待到货", color: "bg-blue-500" },
  IN_TRANSIT: { label: "运输中", color: "bg-amber-500" },
  ARRIVED: { label: "已到货", color: "bg-emerald-500" },
  RECEIVED: { label: "已收货", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};

const extractApiData = (response) => response?.data?.data ?? response?.data ?? response ?? null;

export default function ArrivalTrackingList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [arrivals, setArrivals] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterSupplier, setFilterSupplier] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterDelayed, setFilterDelayed] = useState("all");

  useEffect(() => {
    fetchSuppliers();
  }, []);

  useEffect(() => {
    fetchArrivals();
  }, [filterSupplier, filterStatus, filterDelayed, searchKeyword]);

  const fetchSuppliers = async () => {
    try {
      const res = await supplierApi.list({ page_size: 1000 });
      const data = extractApiData(res);
      setSuppliers(data?.items || (Array.isArray(data) ? data : []));
    } catch (error) {
      console.error("Failed to fetch suppliers:", error);
      setSuppliers([]);
    }
  };

  const fetchArrivals = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterSupplier !== "all") {
        params.supplier_id = filterSupplier;
      }
      if (filterStatus !== "all") {
        params.status = filterStatus;
      }
      if (filterDelayed !== "all") {
        params.is_delayed = filterDelayed === "true";
      }
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      const res = await shortageApi.arrivals.list(params);
      const data = extractApiData(res);
      setArrivals(data?.items || (Array.isArray(data) ? data : []));
    } catch (error) {
      console.error("Failed to fetch arrivals:", error);
      setArrivals([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredArrivals = useMemo(() => {
    return (arrivals || []).filter((arrival) => {
      if (!searchKeyword) {
        return true;
      }
      const keyword = searchKeyword.toLowerCase();
      return (
        arrival.arrival_no?.toLowerCase().includes(keyword) ||
        arrival.material_code?.toLowerCase().includes(keyword) ||
        arrival.material_name?.toLowerCase().includes(keyword)
      );
    });
  }, [arrivals, searchKeyword]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="到货跟踪管理"
          description="直接使用真实 arrivals API，查看、筛选并进入详情"
        />

        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索到货单号、物料编码..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10"
                />
              </div>

              <Select value={filterSupplier} onValueChange={setFilterSupplier}>
                <SelectTrigger>
                  <SelectValue placeholder="选择供应商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部供应商</SelectItem>
                  {(suppliers || []).map((supplier) => {
                    const supplierId =
                      supplier.id?.toString() || supplier.supplier_id?.toString();
                    if (!supplierId) {
                      return null;
                    }
                    return (
                      <SelectItem key={supplierId} value={supplierId}>
                        {supplier.supplier_name || supplier.name || "未知供应商"}
                      </SelectItem>
                    );
                  })}
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

              <Select value={filterDelayed} onValueChange={setFilterDelayed}>
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

        <div className="flex justify-end">
          <Button onClick={() => navigate("/arrival-tracking/new")}>
            <Plus className="w-4 h-4 mr-2" />
            新建到货跟踪
          </Button>
        </div>

        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-slate-200">到货跟踪列表</CardTitle>
            <CardDescription className="text-slate-400">
              共 {filteredArrivals.length} 个到货跟踪
              {(filteredArrivals || []).filter((a) => a.is_delayed).length > 0 && (
                <span className="ml-2 text-red-400">
                  （延迟: {(filteredArrivals || []).filter((a) => a.is_delayed).length}）
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredArrivals.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无到货跟踪</div>
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
                    <TableHead className="text-right text-slate-400">操作</TableHead>
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
                        {arrival.expected_date ? formatDate(arrival.expected_date) : "-"}
                      </TableCell>
                      <TableCell
                        className={cn(
                          "text-sm",
                          arrival.actual_date ? "text-emerald-400" : "text-slate-400",
                        )}
                      >
                        {arrival.actual_date ? formatDate(arrival.actual_date) : "未到货"}
                      </TableCell>
                      <TableCell>
                        {arrival.is_delayed && arrival.delay_days ? (
                          <Badge variant="destructive">{arrival.delay_days} 天</Badge>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusConfigs[arrival.status]?.color || "bg-slate-500"}>
                          {statusConfigs[arrival.status]?.label || arrival.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/arrival-tracking/${arrival.id}`)}
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
      </div>
    </div>
  );
}
