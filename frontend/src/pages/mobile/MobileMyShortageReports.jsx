/**
 * Mobile My Shortage Reports - 移动端我的缺料上报记录
 * 功能：查看我的缺料上报记录和进度
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Package,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent } from "../../components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { cn, formatDate } from "../../lib/utils";
import { shortageApi } from "../../services/api";

const statusConfigs = {
  REPORTED: { label: "已上报", color: "bg-blue-500" },
  CONFIRMED: { label: "已确认", color: "bg-amber-500" },
  HANDLING: { label: "处理中", color: "bg-purple-500" },
  RESOLVED: { label: "已解决", color: "bg-emerald-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};

const urgentLevelConfigs = {
  LOW: { label: "低", color: "bg-slate-500" },
  MEDIUM: { label: "中", color: "bg-blue-500" },
  HIGH: { label: "高", color: "bg-amber-500" },
  URGENT: { label: "紧急", color: "bg-red-500" },
};

export default function MobileMyShortageReports() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState([]);
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    fetchReports();
  }, [filterStatus]);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 100 };
      if (filterStatus) {
        params.status = filterStatus;
      }
      const res = await shortageApi.reports.list(params);
      const allReports = res.data?.items || res.data?.items || res.data || [];

      // 这里应该根据当前登录用户筛选，暂时显示所有
      setReports(allReports);
    } catch (error) {
      console.error("Failed to fetch reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: reports.length,
    reported: reports.filter((r) => r.status === "REPORTED").length,
    handling: reports.filter((r) => r.status === "HANDLING").length,
    resolved: reports.filter((r) => r.status === "RESOLVED").length,
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* 顶部导航栏 */}
      <div className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="p-2"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-lg font-semibold">我的上报记录</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchReports}
              className="p-2"
            >
              <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/mobile/shortage-report")}
              className="p-2"
            >
              <Package className="w-5 h-5 text-red-500" />
            </Button>
          </div>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-3 p-4">
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-500">已上报</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-blue-600">
            {stats.reported}
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-500">处理中</span>
            <AlertCircle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600">
            {stats.handling}
          </div>
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="px-4 mb-3">
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-full">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="REPORTED">已上报</SelectItem>
            <SelectItem value="CONFIRMED">已确认</SelectItem>
            <SelectItem value="HANDLING">处理中</SelectItem>
            <SelectItem value="RESOLVED">已解决</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 记录列表 */}
      <div className="px-4 space-y-3">
        {loading ? (
          <div className="text-center py-12 text-slate-400">加载中...</div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12 text-slate-400">暂无上报记录</div>
        ) : (
          reports.map((report) => (
            <Card
              key={report.id}
              className="active:scale-[0.98] transition-transform"
              onClick={() => navigate(`/shortage/reports/${report.id}`)}
            >
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge
                          className={
                            statusConfigs[report.status]?.color ||
                            "bg-slate-500"
                          }
                        >
                          {statusConfigs[report.status]?.label || report.status}
                        </Badge>
                        <Badge
                          className={
                            urgentLevelConfigs[report.urgent_level]?.color ||
                            "bg-slate-500"
                          }
                        >
                          {urgentLevelConfigs[report.urgent_level]?.label ||
                            report.urgent_level}
                        </Badge>
                        <span className="font-mono text-xs text-slate-500">
                          {report.report_no}
                        </span>
                      </div>
                      <h3 className="font-medium text-base mb-1">
                        {report.material_name}
                      </h3>
                      <div className="text-sm text-slate-500">
                        {report.material_code}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-slate-500 mb-1">缺料数量</div>
                      <div className="font-medium text-red-600">
                        {report.shortage_qty || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500 mb-1">需求数量</div>
                      <div className="font-medium">
                        {report.required_qty || 0}
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-slate-400">
                    上报时间:{" "}
                    {report.report_time ? formatDate(report.report_time) : "-"}
                  </div>

                  {report.project_name && (
                    <div className="text-xs text-slate-400">
                      项目: {report.project_name}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
