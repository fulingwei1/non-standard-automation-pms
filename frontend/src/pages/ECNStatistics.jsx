/**
 * ECN Statistics Page - ECN统计报表页面
 * Features: ECN统计概览、成本影响统计、工期影响统计、类型分布、趋势分析
 */
import { useState, useEffect } from "react";
import {
  TrendingUp,
  DollarSign,
  Clock,
  FileText,
  BarChart3,
  PieChart,
  Download,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  SimpleBarChart,
  SimpleLineChart,
  SimplePieChart,
  MonthlyTrendChart,
} from "../components/administrative/StatisticsCharts";
import { ecnApi } from "../services/api";
import { formatDate } from "../lib/utils";

const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500" },
  SUBMITTED: { label: "已提交", color: "bg-blue-500" },
  EVALUATING: { label: "评估中", color: "bg-amber-500" },
  EVALUATED: { label: "评估完成", color: "bg-cyan-500" },
  PENDING_APPROVAL: { label: "待审批", color: "bg-orange-500" },
  APPROVED: { label: "已批准", color: "bg-green-500" },
  REJECTED: { label: "已驳回", color: "bg-red-500" },
  EXECUTING: { label: "执行中", color: "bg-purple-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  CLOSED: { label: "已关闭", color: "bg-gray-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-400" },
};

const typeConfigs = {
  // 客户相关（3种）
  CUSTOMER_REQUIREMENT: { label: "客户需求变更", color: "bg-blue-500" },
  CUSTOMER_SPEC: { label: "客户规格调整", color: "bg-blue-400" },
  CUSTOMER_FEEDBACK: { label: "客户现场反馈", color: "bg-blue-600" },

  // 设计变更（5种）
  MECHANICAL_STRUCTURE: { label: "机械结构变更", color: "bg-cyan-500" },
  ELECTRICAL_SCHEME: { label: "电气方案变更", color: "bg-cyan-400" },
  SOFTWARE_FUNCTION: { label: "软件功能变更", color: "bg-cyan-600" },
  TECH_OPTIMIZATION: { label: "技术方案优化", color: "bg-teal-500" },
  DESIGN_FIX: { label: "设计缺陷修复", color: "bg-teal-600" },

  // 测试相关（4种）
  TEST_STANDARD: { label: "测试标准变更", color: "bg-purple-500" },
  TEST_FIXTURE: { label: "测试工装变更", color: "bg-purple-400" },
  CALIBRATION_SCHEME: { label: "校准方案变更", color: "bg-purple-600" },
  TEST_PROGRAM: { label: "测试程序变更", color: "bg-violet-500" },

  // 生产制造（4种）
  PROCESS_IMPROVEMENT: { label: "工艺改进", color: "bg-orange-500" },
  MATERIAL_SUBSTITUTE: { label: "物料替代", color: "bg-orange-400" },
  SUPPLIER_CHANGE: { label: "供应商变更", color: "bg-orange-600" },
  COST_OPTIMIZATION: { label: "成本优化", color: "bg-amber-500" },

  // 质量安全（3种）
  QUALITY_ISSUE: { label: "质量问题整改", color: "bg-red-500" },
  SAFETY_COMPLIANCE: { label: "安全合规变更", color: "bg-red-600" },
  RELIABILITY_IMPROVEMENT: { label: "可靠性改进", color: "bg-rose-500" },

  // 项目管理（3种）
  SCHEDULE_ADJUSTMENT: { label: "进度调整", color: "bg-green-500" },
  DOCUMENT_UPDATE: { label: "文档更新", color: "bg-green-400" },
  DRAWING_CHANGE: { label: "图纸变更", color: "bg-emerald-500" },

  // 兼容旧版本
  DESIGN: { label: "设计变更", color: "bg-blue-500" },
  REQUIREMENT: { label: "需求变更", color: "bg-green-500" },
  MATERIAL: { label: "物料替代", color: "bg-amber-500" },
  PROCESS: { label: "工艺变更", color: "bg-purple-500" },
  DOCUMENT: { label: "文档变更", color: "bg-slate-500" },
  SPECIFICATION: { label: "规格变更", color: "bg-green-500" },
  SCHEDULE: { label: "计划变更", color: "bg-orange-500" },
  OTHER: { label: "其他", color: "bg-slate-500" },
};

export default function ECNStatistics() {
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState(null);
  const [timeRange, setTimeRange] = useState("month");

  useEffect(() => {
    fetchStatistics();
  }, [timeRange]);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const params = { time_range: timeRange };
      const res = await ecnApi.getStatistics(params);
      setStatistics(res.data || res || {});
    } catch (error) {
      console.error("Failed to fetch ECN statistics:", error);
      alert(
        "获取统计信息失败: " + (error.response?.data?.detail || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader title="ECN统计报表" description="ECN变更管理统计分析" />
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader title="ECN统计报表" description="ECN变更管理统计分析" />
        <div className="text-center py-8 text-slate-400">暂无统计数据</div>
      </div>
    );
  }

  // 处理统计数据
  const totalCount = statistics.total_count || 0;
  const statusDistribution = statistics.status_distribution || {};
  const typeDistribution = statistics.type_distribution || {};
  const costImpact = statistics.cost_impact || { total: 0, average: 0 };
  const scheduleImpact = statistics.schedule_impact || { total: 0, average: 0 };
  const trends = statistics.trends || [];

  // 状态分布数据（用于饼图）
  const statusData = Object.entries(statusDistribution)
    .map(([status, count]) => ({
      label: statusConfigs[status]?.label || status,
      value: count,
      color: statusConfigs[status]?.color?.replace("bg-", "#") || "#6b7280",
    }))
    .filter((item) => item.value > 0);

  // 类型分布数据（用于饼图）
  const typeData = Object.entries(typeDistribution)
    .map(([type, count]) => ({
      label: typeConfigs[type]?.label || type,
      value: count,
      color: typeConfigs[type]?.color?.replace("bg-", "#") || "#6b7280",
    }))
    .filter((item) => item.value > 0);

  // 趋势数据（用于折线图）
  const trendData = trends.map((t) => ({
    label: t.period || t.date || "",
    value: t.count || 0,
  }));

  // 成本趋势数据
  const costTrendData = (statistics.cost_trends || []).map((t) => ({
    label: t.period || t.date || "",
    value: t.cost || 0,
  }));

  // 工期趋势数据
  const scheduleTrendData = (statistics.schedule_trends || []).map((t) => ({
    label: t.period || t.date || "",
    value: t.days || 0,
  }));

  // 导出统计报表
  const handleExport = () => {
    try {
      const timeRangeLabels = {
        week: "最近一周",
        month: "最近一月",
        quarter: "最近一季",
        year: "最近一年",
        all: "全部",
      };

      // 构建导出数据
      const exportData = [
        ["ECN统计报表"],
        ["统计周期", timeRangeLabels[timeRange] || timeRange],
        ["导出日期", new Date().toLocaleDateString("zh-CN")],
        [""],
        ["=== 统计概览 ==="],
        ["ECN总数", totalCount],
        ["总成本影响", `¥${costImpact.total?.toLocaleString() || 0}`],
        ["平均成本影响", `¥${costImpact.average?.toLocaleString() || 0}`],
        ["总工期影响", `${scheduleImpact.total || 0} 天`],
        ["平均工期影响", `${scheduleImpact.average?.toFixed(1) || 0} 天`],
        [""],
        ["=== 状态分布 ==="],
        ["状态", "数量"],
        ...Object.entries(statusDistribution).map(([status, count]) => [
          statusConfigs[status]?.label || status,
          count,
        ]),
        [""],
        ["=== 类型分布 ==="],
        ["类型", "数量"],
        ...Object.entries(typeDistribution).map(([type, count]) => [
          typeConfigs[type]?.label || type,
          count,
        ]),
        [""],
        ["=== 详细统计 ==="],
        ["已完成", statusDistribution.COMPLETED || 0],
        ["已关闭", statusDistribution.CLOSED || 0],
        ["已驳回", statusDistribution.REJECTED || 0],
        ["已取消", statusDistribution.CANCELLED || 0],
      ];

      // 转换为CSV格式
      const csvContent = exportData
        .map((row) => row.map((cell) => `"${cell}"`).join(","))
        .join("\n");

      // 添加BOM以支持中文
      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], {
        type: "text/csv;charset=utf-8;",
      });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute(
        "download",
        `ECN统计报表_${timeRange}_${new Date().toISOString().split("T")[0]}.csv`,
      );
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("导出失败:", error);
      alert("导出失败: " + error.message);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="ECN统计报表"
          description="ECN变更管理统计分析，包括数量、成本、工期、类型分布等"
        />
        <Button onClick={handleExport} variant="outline">
          <Download className="w-4 h-4 mr-2" />
          导出报表
        </Button>
      </div>

      {/* 时间范围选择 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="text-sm font-medium">时间范围：</div>
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">最近一周</SelectItem>
                <SelectItem value="month">最近一月</SelectItem>
                <SelectItem value="quarter">最近一季</SelectItem>
                <SelectItem value="year">最近一年</SelectItem>
                <SelectItem value="all">全部</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 统计概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">ECN总数</div>
                <div className="text-2xl font-bold">{totalCount}</div>
              </div>
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">总成本影响</div>
                <div className="text-2xl font-bold">
                  ¥{costImpact.total?.toLocaleString() || 0}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  平均: ¥{costImpact.average?.toLocaleString() || 0}
                </div>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">总工期影响</div>
                <div className="text-2xl font-bold">
                  {scheduleImpact.total || 0} 天
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  平均: {scheduleImpact.average?.toFixed(1) || 0} 天
                </div>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">进行中</div>
                <div className="text-2xl font-bold">
                  {(statusDistribution.EXECUTING || 0) +
                    (statusDistribution.EVALUATING || 0) +
                    (statusDistribution.PENDING_APPROVAL || 0)}
                </div>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 状态分布 */}
        <Card>
          <CardHeader>
            <CardTitle>状态分布</CardTitle>
            <CardDescription>ECN各状态数量分布</CardDescription>
          </CardHeader>
          <CardContent>
            {statusData.length > 0 ? (
              <div className="space-y-4">
                <SimplePieChart data={statusData} size={200} />
                <div className="space-y-2">
                  {Object.entries(statusDistribution).map(([status, count]) => (
                    <div
                      key={status}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <Badge
                          className={
                            statusConfigs[status]?.color || "bg-slate-500"
                          }
                        >
                          {statusConfigs[status]?.label || status}
                        </Badge>
                      </div>
                      <div className="font-medium">{count}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">暂无数据</div>
            )}
          </CardContent>
        </Card>

        {/* 类型分布 */}
        <Card>
          <CardHeader>
            <CardTitle>类型分布</CardTitle>
            <CardDescription>ECN各类型数量分布</CardDescription>
          </CardHeader>
          <CardContent>
            {typeData.length > 0 ? (
              <div className="space-y-4">
                <SimplePieChart data={typeData} size={200} />
                <div className="space-y-2">
                  {Object.entries(typeDistribution).map(([type, count]) => (
                    <div
                      key={type}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <Badge
                          className={typeConfigs[type]?.color || "bg-slate-500"}
                        >
                          {typeConfigs[type]?.label || type}
                        </Badge>
                      </div>
                      <div className="font-medium">{count}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">暂无数据</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 趋势分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* ECN数量趋势 */}
        <Card>
          <CardHeader>
            <CardTitle>ECN数量趋势</CardTitle>
            <CardDescription>ECN数量变化趋势</CardDescription>
          </CardHeader>
          <CardContent>
            {trendData.length > 0 ? (
              <SimpleLineChart
                data={trendData}
                height={200}
                color="text-blue-400"
              />
            ) : (
              <div className="text-center py-8 text-slate-400">暂无数据</div>
            )}
          </CardContent>
        </Card>

        {/* 成本影响趋势 */}
        <Card>
          <CardHeader>
            <CardTitle>成本影响趋势</CardTitle>
            <CardDescription>ECN成本影响变化趋势</CardDescription>
          </CardHeader>
          <CardContent>
            {costTrendData.length > 0 ? (
              <MonthlyTrendChart
                data={costTrendData.map((d) => ({
                  month: d.label,
                  amount: d.value,
                }))}
                valueKey="amount"
                labelKey="month"
                height={200}
              />
            ) : (
              <div className="text-center py-8 text-slate-400">暂无数据</div>
            )}
          </CardContent>
        </Card>

        {/* 工期影响趋势 */}
        <Card>
          <CardHeader>
            <CardTitle>工期影响趋势</CardTitle>
            <CardDescription>ECN工期影响变化趋势</CardDescription>
          </CardHeader>
          <CardContent>
            {scheduleTrendData.length > 0 ? (
              <MonthlyTrendChart
                data={scheduleTrendData.map((d) => ({
                  month: d.label,
                  amount: d.value,
                }))}
                valueKey="amount"
                labelKey="month"
                height={200}
              />
            ) : (
              <div className="text-center py-8 text-slate-400">暂无数据</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 详细统计表格 */}
      <Card>
        <CardHeader>
          <CardTitle>详细统计</CardTitle>
          <CardDescription>ECN详细统计数据</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-slate-400">已完成</div>
              <div className="text-xl font-bold">
                {statusDistribution.COMPLETED || 0}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400">已关闭</div>
              <div className="text-xl font-bold">
                {statusDistribution.CLOSED || 0}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400">已驳回</div>
              <div className="text-xl font-bold">
                {statusDistribution.REJECTED || 0}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400">已取消</div>
              <div className="text-xl font-bold">
                {statusDistribution.CANCELLED || 0}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
