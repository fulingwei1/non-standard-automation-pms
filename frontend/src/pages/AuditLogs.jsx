import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Eye,
  Filter,
  Calendar,
  User,
  Shield,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { auditApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { fadeIn } from "../lib/animations";

export default function AuditLogs() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [audits, setAudits] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 筛选条件
  const [operatorId, setOperatorId] = useState("");
  const [targetType, setTargetType] = useState("");
  const [targetId, setTargetId] = useState("");
  const [action, setAction] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // 详情对话框
  const [selectedAudit, setSelectedAudit] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const loadAudits = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        page_size: pageSize,
      };

      if (operatorId) {params.operator_id = parseInt(operatorId);}
      if (targetType) {params.target_type = targetType;}
      if (targetId) {params.target_id = parseInt(targetId);}
      if (action) {params.action = action;}
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}

      const response = await auditApi.list(params);
      const data = response.data?.data || response.data || response;

      if (data && typeof data === "object" && "items" in data) {
        setAudits(data.items || []);
        setTotal(data.total || 0);
      } else if (Array.isArray(data)) {
        setAudits(data);
        setTotal(data.length);
      } else {
        setAudits([]);
        setTotal(0);
      }
    } catch (err) {
      console.error("Failed to load audits:", err);
      setError(err.response?.data?.detail || err.message || "加载审计日志失败");
      setAudits([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [
    page,
    pageSize,
    operatorId,
    targetType,
    targetId,
    action,
    startDate,
    endDate,
  ]);

  useEffect(() => {
    loadAudits();
  }, [loadAudits]);

  const handleViewDetail = async (auditId) => {
    try {
      const response = await auditApi.get(auditId);
      const data = response.data?.data || response.data || response;
      setSelectedAudit(data);
      setDetailDialogOpen(true);
    } catch (err) {
      console.error("Failed to load audit detail:", err);
      setError(err.response?.data?.detail || err.message || "加载审计详情失败");
    }
  };

  const handleResetFilters = () => {
    setOperatorId("");
    setTargetType("");
    setTargetId("");
    setAction("");
    setStartDate("");
    setEndDate("");
    setPage(1);
  };

  const getActionBadgeColor = (action) => {
    if (action?.includes("CREATE") || action?.includes("ADD"))
      {return "bg-green-100 text-green-800";}
    if (action?.includes("UPDATE") || action?.includes("MODIFY"))
      {return "bg-blue-100 text-blue-800";}
    if (action?.includes("DELETE") || action?.includes("REMOVE"))
      {return "bg-red-100 text-red-800";}
    if (action?.includes("VIEW") || action?.includes("READ"))
      {return "bg-gray-100 text-gray-800";}
    return "bg-purple-100 text-purple-800";
  };

  const getTargetTypeLabel = (type) => {
    const labels = {
      user: "用户",
      role: "角色",
      permission: "权限",
    };
    return labels[type] || type;
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="space-y-6"
    >
      <PageHeader title="权限审计日志" />

      {/* 筛选区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            筛选条件
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div>
              <Label>操作人ID</Label>
              <Input
                type="number"
                placeholder="操作人ID"
                value={operatorId}
                onChange={(e) => setOperatorId(e.target.value)}
              />
            </div>

            <div>
              <Label>目标类型</Label>
              <Select value={targetType} onValueChange={setTargetType}>
                <SelectTrigger>
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="user">用户</SelectItem>
                  <SelectItem value="role">角色</SelectItem>
                  <SelectItem value="permission">权限</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>目标ID</Label>
              <Input
                type="number"
                placeholder="目标ID"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
              />
            </div>

            <div>
              <Label>操作类型</Label>
              <Input
                placeholder="操作类型"
                value={action}
                onChange={(e) => setAction(e.target.value)}
              />
            </div>

            <div>
              <Label>开始日期</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            <div>
              <Label>结束日期</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button onClick={loadAudits}>
              <Search className="h-4 w-4 mr-2" />
              查询
            </Button>
            <Button variant="outline" onClick={handleResetFilters}>
              <RefreshCw className="h-4 w-4 mr-2" />
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* 审计日志列表 */}
      <Card>
        <CardHeader>
          <CardTitle>审计日志列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : audits.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无审计日志</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">ID</th>
                      <th className="text-left p-2">操作人</th>
                      <th className="text-left p-2">操作类型</th>
                      <th className="text-left p-2">目标类型</th>
                      <th className="text-left p-2">目标ID</th>
                      <th className="text-left p-2">IP地址</th>
                      <th className="text-left p-2">操作时间</th>
                      <th className="text-left p-2">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {audits.map((audit) => (
                      <tr key={audit.id} className="border-b hover:bg-gray-50">
                        <td className="p-2">{audit.id}</td>
                        <td className="p-2">
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-gray-500" />
                            {audit.operator_name || `ID: ${audit.operator_id}`}
                          </div>
                        </td>
                        <td className="p-2">
                          <Badge className={getActionBadgeColor(audit.action)}>
                            {audit.action}
                          </Badge>
                        </td>
                        <td className="p-2">
                          <Badge variant="outline">
                            {getTargetTypeLabel(audit.target_type)}
                          </Badge>
                        </td>
                        <td className="p-2">{audit.target_id}</td>
                        <td className="p-2 text-sm text-gray-600">
                          {audit.ip_address || "-"}
                        </td>
                        <td className="p-2 text-sm">
                          {formatDate(audit.created_at)}
                        </td>
                        <td className="p-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(audit.id)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* 分页 */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-600">共 {total} 条记录</div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    上一页
                  </Button>
                  <span className="px-4 py-2 text-sm">
                    第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= Math.ceil(total / pageSize)}
                    onClick={() => setPage(page + 1)}
                  >
                    下一页
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* 详情对话框 */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>审计日志详情</DialogTitle>
          </DialogHeader>
          {selectedAudit && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>ID</Label>
                  <div className="mt-1">{selectedAudit.id}</div>
                </div>
                <div>
                  <Label>操作人</Label>
                  <div className="mt-1 flex items-center gap-2">
                    <User className="h-4 w-4" />
                    {selectedAudit.operator_name ||
                      `ID: ${selectedAudit.operator_id}`}
                  </div>
                </div>
                <div>
                  <Label>操作类型</Label>
                  <div className="mt-1">
                    <Badge
                      className={getActionBadgeColor(selectedAudit.action)}
                    >
                      {selectedAudit.action}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label>目标类型</Label>
                  <div className="mt-1">
                    <Badge variant="outline">
                      {getTargetTypeLabel(selectedAudit.target_type)}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label>目标ID</Label>
                  <div className="mt-1">{selectedAudit.target_id}</div>
                </div>
                <div>
                  <Label>IP地址</Label>
                  <div className="mt-1">{selectedAudit.ip_address || "-"}</div>
                </div>
                <div>
                  <Label>操作时间</Label>
                  <div className="mt-1">
                    {formatDate(selectedAudit.created_at)}
                  </div>
                </div>
                {selectedAudit.user_agent && (
                  <div className="col-span-2">
                    <Label>User Agent</Label>
                    <div className="mt-1 text-sm text-gray-600 break-all">
                      {selectedAudit.user_agent}
                    </div>
                  </div>
                )}
                {selectedAudit.detail && (
                  <div className="col-span-2">
                    <Label>详细信息</Label>
                    <div className="mt-1 p-3 bg-gray-50 rounded text-sm">
                      {selectedAudit.detail}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
