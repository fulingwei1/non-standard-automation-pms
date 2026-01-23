/**
 * ECN Change Log Component
 * ECN 变更日志组件
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import {
  Search,
  Calendar,
  User,
  FileText,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Plus,
  Edit,
  Download } from
"lucide-react";
import {
  logTypeConfigs,
  formatStatus as _formatStatus } from
"./ecnConstants";
import { cn, formatDate } from "../../lib/utils";import { toast } from "sonner";

export function ECNChangeLog({
  logs,
  ecn,
  loading: _loading
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("__all__");
  const [filterDateRange, setFilterDateRange] = useState("all");

  const filteredLogs = logs.filter((log) => {
    // 搜索过滤
    if (searchTerm && !log.description?.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }

    // 类型过滤
    if (filterType && log.log_type !== filterType) {
      return false;
    }

    // 日期范围过滤
    if (filterDateRange !== "all") {
      const now = new Date();
      const logDate = new Date(log.created_time);

      switch (filterDateRange) {
        case "today":
          if (logDate.toDateString() !== now.toDateString()) {return false;}
          break;
        case "week": {
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          if (logDate < weekAgo) {return false;}
          break;
        }
        case "month": {
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          if (logDate < monthAgo) {return false;}
          break;
        }
        default:
          break;
      }
    }

    return true;
  });

  const _getLogIcon = (logType) => {
    const config = logTypeConfigs[logType];
    return config ? config.icon : <FileText className="w-4 h-4" />;
  };

  const getLogConfig = (logType) => {
    return logTypeConfigs[logType] || logTypeConfigs.UPDATED;
  };

  const exportLogs = () => {
    const csvContent = [
    [
    "时间",
    "类型",
    "操作人",
    "描述",
    "详细信息"].
    join(","),
    ...filteredLogs.map((log) => [
    formatDate(log.created_time),
    getLogConfig(log.log_type).label,
    log.operator_name || log.operator,
    log.description || "",
    log.details || ""].
    join(","))].
    join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ECN_${ecn.ecn_no}_变更日志_${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.success("日志导出成功");
  };

  return (
    <div className="space-y-4">
      {/* 日志筛选 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">日志筛选</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索日志内容..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10" />

              </div>
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="日志类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部类型</SelectItem>
                {Object.entries(logTypeConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.icon} {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterDateRange} onValueChange={setFilterDateRange}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="时间范围" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部时间</SelectItem>
                <SelectItem value="today">今天</SelectItem>
                <SelectItem value="week">最近7天</SelectItem>
                <SelectItem value="month">最近30天</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={exportLogs}>
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 变更日志列表 */}
      <div className="relative">
        {/* 时间线背景线 */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-600" />
        
        {filteredLogs.length === 0 ?
        <Card>
            <CardContent className="py-8 text-center text-slate-400">
              {logs.length === 0 ? "暂无变更记录" : "没有符合条件的日志"}
            </CardContent>
        </Card> :

        <div className="space-y-4">
            {filteredLogs.map((log, index) => {
            const logConfig = getLogConfig(log.log_type);

            return (
              <div key={log.id || index} className="relative flex items-start gap-4">
                  {/* 日志类型图标 */}
                  <div className="relative z-10">
                    <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center border-2",
                    logConfig.color + " bg-slate-900"
                  )}>
                      <span className="text-sm">{logConfig.icon}</span>
                    </div>
                  </div>

                  {/* 日志内容 */}
                  <div className="flex-1 min-w-0">
                    <Card className="border-l-4 border-l-slate-600">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start gap-4 mb-2">
                          <div className="flex items-center gap-3">
                            <Badge className={cn(logConfig.color, logConfig.textColor, "text-xs")}>
                              {logConfig.label}
                            </Badge>
                            <div className="flex items-center gap-1 text-sm text-slate-500">
                              <User className="w-3 h-3" />
                              {log.operator_name || log.operator}
                            </div>
                            <div className="flex items-center gap-1 text-sm text-slate-500">
                              <Calendar className="w-3 h-3" />
                              {formatDate(log.created_time)}
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          {log.description &&
                        <div className="text-white">
                              {log.description}
                        </div>
                        }

                          {log.details &&
                        <div className="text-sm text-slate-400 bg-slate-800/50 p-3 rounded-lg">
                              <pre className="whitespace-pre-wrap font-sans">
                                {log.details}
                              </pre>
                        </div>
                        }

                          {/* 特殊字段展示 */}
                          {log.log_type === "EVALUATED" && log.evaluation_data &&
                        <div className="text-sm text-slate-300 bg-slate-800/30 p-2 rounded">
                              <div className="font-medium mb-1">评估结果:</div>
                              <div>部门: {log.evaluation_data.department}</div>
                              <div>风险等级: {log.evaluation_data.risk_level}</div>
                              <div>建议: {log.evaluation_data.recommendation}</div>
                        </div>
                        }

                          {log.log_type === "APPROVED" && log.approval_data &&
                        <div className="text-sm text-slate-300 bg-slate-800/30 p-2 rounded">
                              <div className="font-medium mb-1">审批信息:</div>
                              <div>审批人: {log.approval_data.approver}</div>
                              <div>审批意见: {log.approval_data.comment}</div>
                        </div>
                        }

                          {log.attachments && log.attachments.length > 0 &&
                        <div className="text-sm text-slate-400">
                              <div className="font-medium mb-1">附件:</div>
                              <div className="flex flex-wrap gap-2">
                                {log.attachments.map((attachment, idx) =>
                            <Badge key={idx} variant="outline" className="text-xs">
                                    {attachment.name}
                            </Badge>
                            )}
                              </div>
                        </div>
                        }
                        </div>
                      </CardContent>
                    </Card>
                  </div>
              </div>);

          })}
        </div>
        }
      </div>
    </div>);

}
