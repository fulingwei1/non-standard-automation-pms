/**
 * ECN List Table Component
 * ECN列表表格组件
 */
import { useState } from "react";
import { Eye, CheckCircle2, Clock, AlertTriangle, XCircle } from "lucide-react";
import { Checkbox } from "../ui/checkbox";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { formatDate } from "../../lib/utils";
import { 
  statusConfigs, 
  typeConfigs, 
  priorityConfigs,
  getStatusLabel,
  getTypeLabel,
  getPriorityLabel 
} from "@/lib/constants/ecn";

export function ECNListTable({
  ecns = [],
  loading = false,
  selectedECNIds = new Set(),
  onSelectionChange,
  onViewDetail,
  onSubmit,
}) {
  const [sortConfig, setSortConfig] = useState({
    key: "applied_at",
    direction: "desc"
  });

  // 排序函数
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === "desc" ? "asc" : "desc"
    }));
  };

  // 排序数据
  const sortedECNs = [...ecns].sort((a, b) => {
    let aValue = a[sortConfig.key];
    let bValue = b[sortConfig.key];
    
    // 申请时间缺失时回退到创建时间
    if (sortConfig.key === "applied_at") {
      aValue = a.applied_at || a.created_at || a.createdAt;
      bValue = b.applied_at || b.created_at || b.createdAt;
    }

    // 处理日期排序
    if (sortConfig.key.includes("_at") || sortConfig.key.includes("Date")) {
      const aDate = new Date(aValue);
      const bDate = new Date(bValue);
      aValue = Number.isNaN(aDate.getTime()) ? 0 : aDate.getTime();
      bValue = Number.isNaN(bDate.getTime()) ? 0 : bDate.getTime();
    }
    
    if (aValue < bValue) {return sortConfig.direction === "asc" ? -1 : 1;}
    if (aValue > bValue) {return sortConfig.direction === "asc" ? 1 : -1;}
    return 0;
  });

  // 处理单行选择
  const handleRowSelect = (ecnId, checked) => {
    const newSelection = new Set(selectedECNIds);
    if (checked) {
      newSelection.add(ecnId);
    } else {
      newSelection.delete(ecnId);
    }
    onSelectionChange(newSelection);
  };

  // 处理全选
  const handleSelectAll = (checked) => {
    if (checked) {
      onSelectionChange(new Set((sortedECNs || []).map(ecn => ecn.id)));
    } else {
      onSelectionChange(new Set());
    }
  };

  // 获取优先级图标
  const getPriorityIcon = (priority) => {
    switch (priority) {
      case "URGENT":
        return <AlertTriangle className="w-3 h-3 text-red-500" />;
      case "HIGH":
        return <Clock className="w-3 h-3 text-orange-500" />;
      default:
        return <Clock className="w-3 h-3 text-slate-400" />;
    }
  };

  // 获取状态图标
  const getStatusIcon = (status) => {
    switch (status) {
      case "COMPLETED":
        return <CheckCircle2 className="w-3 h-3 text-green-500" />;
      case "REJECTED":
      case "CANCELLED":
        return <XCircle className="w-3 h-3 text-red-500" />;
      default:
        return <Clock className="w-3 h-3 text-amber-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        <span className="ml-2 text-slate-600 dark:text-slate-400">加载中...</span>
      </div>
    );
  }

  if (sortedECNs.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-slate-400 mb-2">
          <Eye className="w-12 h-12 mx-auto opacity-50" />
        </div>
        <p className="text-slate-500 dark:text-slate-400">暂无ECN数据</p>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
          请调整筛选条件或创建新的ECN
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white dark:bg-slate-950">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50 dark:bg-slate-900/50">
            <TableHead className="w-12">
              <Checkbox
                checked={sortedECNs.length > 0 && selectedECNIds.size === sortedECNs.length}
                onCheckedChange={handleSelectAll}
              />
            </TableHead>
            
            {/* 可排序列头 */}
            <TableHead className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => handleSort("ecn_no")}>
              <div className="flex items-center gap-1">
                ECN编号
                {sortConfig.key === "ecn_no" && (
                  <span className="text-xs text-slate-400">
                    {sortConfig.direction === "asc" ? "↑" : "↓"}
                  </span>
                )}
              </div>
            </TableHead>

            <TableHead>标题</TableHead>

            <TableHead>项目</TableHead>

            <TableHead className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => handleSort("ecn_type")}>
              <div className="flex items-center gap-1">
                类型
                {sortConfig.key === "ecn_type" && (
                  <span className="text-xs text-slate-400">
                    {sortConfig.direction === "asc" ? "↑" : "↓"}
                  </span>
                )}
              </div>
            </TableHead>

            <TableHead>状态</TableHead>

            <TableHead className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => handleSort("priority")}>
              <div className="flex items-center gap-1">
                优先级
                {sortConfig.key === "priority" && (
                  <span className="text-xs text-slate-400">
                    {sortConfig.direction === "asc" ? "↑" : "↓"}
                  </span>
                )}
              </div>
            </TableHead>

            <TableHead>申请人</TableHead>

            <TableHead className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => handleSort("applied_at")}>
              <div className="flex items-center gap-1">
                申请时间
                {sortConfig.key === "applied_at" && (
                  <span className="text-xs text-slate-400">
                    {sortConfig.direction === "asc" ? "↑" : "↓"}
                  </span>
                )}
              </div>
            </TableHead>

            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {(sortedECNs || []).map((ecn) => (
            <TableRow 
              key={ecn.id}
              className={`hover:bg-slate-50 dark:hover:bg-slate-800/50 ${
                selectedECNIds.has(ecn.id) ? "bg-blue-50 dark:bg-blue-900/20" : ""
              }`}
            >
              <TableCell>
                <Checkbox
                  checked={selectedECNIds.has(ecn.id)}
                  onCheckedChange={(checked) => handleRowSelect(ecn.id, checked)}
                />
              </TableCell>

              <TableCell className="font-mono text-sm">
                {ecn.ecn_no || `ECN-${String(ecn.id).padStart(6, '0')}`}
              </TableCell>

              <TableCell className="max-w-xs">
                <div className="truncate font-medium" title={ecn.ecn_title}>
                  {ecn.ecn_title}
                </div>
              </TableCell>

              <TableCell className="max-w-[12rem]">
                <div className="truncate text-sm" title={ecn.project_name || ""}>
                  {ecn.project_name || "-"}
                </div>
              </TableCell>

              <TableCell>
                <Badge 
                  variant="secondary" 
                  className={`${typeConfigs[ecn.ecn_type]?.color || "bg-slate-500"} text-white`}
                >
                  {getTypeLabel(ecn.ecn_type)}
                </Badge>
              </TableCell>

              <TableCell>
                <div className="flex items-center gap-2">
                  {getStatusIcon(ecn.status)}
                  <Badge 
                    variant="outline"
                    className={`${(statusConfigs[ecn.status]?.color || "bg-slate-500").replace("bg-", "border-")} ${(statusConfigs[ecn.status]?.color || "bg-slate-500").replace("bg-", "text-")} border-2`}
                  >
                    {getStatusLabel(ecn.status)}
                  </Badge>
                </div>
              </TableCell>

              <TableCell>
                <div className="flex items-center gap-2">
                  {getPriorityIcon(ecn.priority)}
                  <Badge 
                    variant="secondary"
                    className={`${priorityConfigs[ecn.priority]?.color} text-white`}
                  >
                    {getPriorityLabel(ecn.priority)}
                  </Badge>
                </div>
              </TableCell>

              <TableCell>
                <div className="text-sm">
                  {ecn.applicant_name || ecn.created_by_name || "系统"}
                </div>
              </TableCell>

              <TableCell className="text-sm text-slate-600 dark:text-slate-400">
                {formatDate(ecn.applied_at || ecn.created_at || ecn.createdAt)}
              </TableCell>

              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewDetail(ecn)}
                    className="h-8 w-8 p-0"
                  >
                    <Eye className="w-4 h-4" />
                  </Button>

                  {ecn.status === "DRAFT" && onSubmit && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onSubmit(ecn.id)}
                      className="h-8 w-8 p-0"
                      title="提交ECN"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
