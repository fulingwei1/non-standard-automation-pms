/**
 * Delivery Plan
 * 交付计划组件：以表格形式展示待发货/准备中等计划类任务
 * Refactored to shadcn/Tailwind Dark Theme
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../ui";
import { Calendar, Package, Truck, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

import { DELIVERY_STATUS, DELIVERY_PRIORITY, SHIPPING_METHODS, PACKAGE_TYPES } from "@/lib/constants/service";

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c" };
};

const DeliveryPlan = ({ deliveries = [], loading }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const shippedOrInTransitCount = (deliveries || []).filter((d) => d.status === "shipped" || d.status === "in_transit").length;

  // Pagination
  const totalPages = Math.ceil((deliveries?.length || 0) / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentData = deliveries?.slice(startIndex, endIndex) || [];

  const getStatusBadgeClass = (status) => {
    const cfg = getConfigByValue(DELIVERY_STATUS, status, status);
    return cn(
      "border",
      cfg.color === 'red' && "bg-red-500/20 text-red-400 border-red-500/30",
      cfg.color === 'green' && "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      cfg.color === 'blue' && "bg-blue-500/20 text-blue-400 border-blue-500/30",
      cfg.color === 'gold' && "bg-amber-500/20 text-amber-400 border-amber-500/30",
      cfg.color === 'orange' && "bg-orange-500/20 text-orange-400 border-orange-500/30",
      cfg.color === 'purple' && "bg-purple-500/20 text-purple-400 border-purple-500/30",
      cfg.color === 'cyan' && "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
      !cfg.color || cfg.color === '#8c8c8c' && "bg-slate-500/20 text-slate-400 border-slate-500/30"
    );
  };

  const getPriorityBadgeClass = (priority) => {
    const cfg = getConfigByValue(DELIVERY_PRIORITY, priority, priority);
    return cn(
      "border",
      cfg.color === 'red' && "bg-red-500/20 text-red-400 border-red-500/30",
      cfg.color === 'gold' && "bg-amber-500/20 text-amber-400 border-amber-500/30",
      cfg.color === 'orange' && "bg-orange-500/20 text-orange-400 border-orange-500/30",
      cfg.color === 'green' && "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      !cfg.color || cfg.color === '#8c8c8c' && "bg-slate-500/20 text-slate-400 border-slate-500/30"
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="bg-surface-100/50">
        <CardHeader className="border-b border-white/10 pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Calendar size={18} />
              交付计划
            </CardTitle>
            <div className="flex gap-2">
              <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                <Package size={14} className="mr-1" />
                待发货/准备中：{deliveries?.length}
              </Badge>
              <Badge variant="outline" className="bg-cyan-500/20 text-cyan-400 border-cyan-500/30">
                <Truck size={14} className="mr-1" />
                已发货/在途：{shippedOrInTransitCount}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-b border-white/5">
                  <TableHead className="text-left p-4 text-sm font-medium text-slate-400 w-[160px]">订单号</TableHead>
                  <TableHead className="text-left p-4 text-sm font-medium text-slate-400 w-[220px]">客户</TableHead>
                  <TableHead className="text-left p-4 text-sm font-medium text-slate-400 w-[120px]">状态</TableHead>
                  <TableHead className="text-left p-4 text-sm font-medium text-slate-400 w-[100px]">优先级</TableHead>
                  <TableHead className="text-left p-4 text-sm font-medium text-slate-400 w-[130px]">运输方式</TableHead>
                  <TableHead className="text-left p-4 text-sm font-medium text-slate-400 w-[130px]">包装类型</TableHead>
                  <TableHead className="text-left p-4 text-sm font-medium text-slate-400 w-[120px]">计划日期</TableHead>
                  <TableHead className="text-right p-4 text-sm font-medium text-slate-400 w-[80px]">件数</TableHead>
                  <TableHead className="text-right p-4 text-sm font-medium text-slate-400 w-[100px]">重量 (kg)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {currentData.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="p-8 text-center text-slate-400">
                      暂无数据
                    </TableCell>
                  </TableRow>
                ) : (
                  currentData.map((row) => {
                    const statusCfg = getConfigByValue(DELIVERY_STATUS, row.status, row.status);
                    const priorityCfg = getConfigByValue(DELIVERY_PRIORITY, row.priority, row.priority);
                    const methodCfg = getConfigByValue(SHIPPING_METHODS, row.shippingMethod, row.shippingMethod);
                    const packageCfg = getConfigByValue(PACKAGE_TYPES, row.packageType, row.packageType);

                    return (
                      <TableRow key={row.id ?? row.orderNumber} className="border-b border-white/5 hover:bg-surface-100 transition-colors">
                        <TableCell className="p-4">
                          <span className="font-medium text-white">{row.orderNumber}</span>
                        </TableCell>
                        <TableCell className="p-4 text-sm text-slate-400 truncate max-w-[220px]">
                          {row.customerName}
                        </TableCell>
                        <TableCell className="p-4">
                          <Badge 
                            variant="outline" 
                            className={getStatusBadgeClass(row.status)}
                            style={{ borderColor: statusCfg.color, color: statusCfg.color }}
                          >
                            {statusCfg.label}
                          </Badge>
                        </TableCell>
                        <TableCell className="p-4">
                          <Badge 
                            variant="outline" 
                            className={getPriorityBadgeClass(row.priority)}
                            style={{ borderColor: priorityCfg.color, color: priorityCfg.color }}
                          >
                            {priorityCfg.label}
                          </Badge>
                        </TableCell>
                        <TableCell className="p-4 text-sm text-slate-400">
                          {methodCfg.label}
                        </TableCell>
                        <TableCell className="p-4 text-sm text-slate-400">
                          {packageCfg.label}
                        </TableCell>
                        <TableCell className="p-4 text-sm text-white">
                          {row.scheduledDate || "-"}
                        </TableCell>
                        <TableCell className="p-4 text-right text-sm text-white">
                          {row.itemCount ?? "-"}
                        </TableCell>
                        <TableCell className="p-4 text-right text-sm text-white">
                          {row.totalWeight ?? "-"}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-white/5">
              <div className="text-sm text-slate-400">
                共 {deliveries?.length} 条，第 {currentPage} / {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={pageSize || "unknown"}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="px-3 py-1.5 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value={10 || "unknown"}>10 条/页</option>
                  <option value={20 || "unknown"}>20 条/页</option>
                  <option value={50 || "unknown"}>50 条/页</option>
                </select>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="h-8 w-8 p-0"
                >
                  <ChevronLeft size={16} />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="h-8 w-8 p-0"
                >
                  <ChevronRight size={16} />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DeliveryPlan;
