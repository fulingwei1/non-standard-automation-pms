/**
 * ProjectHealthMonitor - 项目健康监控整合视图
 * 整合项目列表 + 齐套率 + 健康度 + 毛利率
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Package,
  RefreshCw,
  Search,
  Eye,
  ChevronDown,
  ChevronRight,
  Filter,
  BarChart3,
  DollarSign,
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
import { Skeleton } from "../components/ui/skeleton";
import { toast } from "../components/ui/toast";
import { projectApi, marginPredictionApi } from "../services/api";
import { materialReadinessApi } from "../services/api/materialReadiness";
import { PROJECT_STAGES, HEALTH_CONFIG, getHealthConfig } from "../lib/constants/common";
import { formatDate, formatCurrency, cn } from "../lib/utils";

// 健康度筛选选项
const HEALTH_FILTER_OPTIONS = [
  { value: "all", label: "全部健康度" },
  { value: "H1", label: "正常" },
  { value: "H2", label: "有风险" },
  { value: "H3", label: "阻塞" },
  { value: "H4", label: "已完结" },
];

// 齐套率筛选选项
const KIT_RATE_FILTER_OPTIONS = [
  { value: "all", label: "全部齐套率" },
  { value: "critical", label: "严重不足 (<60%)" },
  { value: "warning", label: "警告 (60-80%)" },
  { value: "good", label: "良好 (80-95%)" },
  { value: "excellent", label: "齐套 (≥95%)" },
];

// 获取齐套率级别
const getKitRateLevel = (rate) => {
  if (rate >= 95) return { level: "excellent", color: "text-emerald-400", bgColor: "bg-emerald-500/20" };
  if (rate >= 80) return { level: "good", color: "text-blue-400", bgColor: "bg-blue-500/20" };
  if (rate >= 60) return { level: "warning", color: "text-amber-400", bgColor: "bg-amber-500/20" };
  return { level: "critical", color: "text-red-400", bgColor: "bg-red-500/20" };
};

// 获取毛利率级别
const getMarginLevel = (margin) => {
  if (margin >= 30) return { level: "excellent", color: "text-emerald-400" };
  if (margin >= 20) return { level: "good", color: "text-blue-400" };
  if (margin >= 10) return { level: "warning", color: "text-amber-400" };
  return { level: "critical", color: "text-red-400" };
};

export default function ProjectHealthMonitor({ embedded = false }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [kitRates, setKitRates] = useState({});
  const [margins, setMargins] = useState({});
  const [expandedRows, setExpandedRows] = useState(new Set());

  // 筛选状态
  const [searchQuery, setSearchQuery] = useState("");
  const [healthFilter, setHealthFilter] = useState("all");
  const [kitRateFilter, setKitRateFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");

  // 计算项目毛利率（从项目数据直接计算，无需调用 API）
  const calculateMargins = useCallback((projectList) => {
    const marginData = {};
    projectList.forEach(project => {
      const contractAmount = parseFloat(project.contract_amount) || 0;
      const actualCost = parseFloat(project.actual_cost) || 0;

      if (contractAmount > 0) {
        const margin = ((contractAmount - actualCost) / contractAmount) * 100;
        marginData[project.id] = {
          predicted_margin: Math.round(margin * 100) / 100,
          contract_amount: contractAmount,
          actual_cost: actualCost,
          profit: contractAmount - actualCost,
        };
      }
    });
    setMargins(marginData);
  }, []);

  // 获取项目列表
  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const res = await projectApi.list({ page_size: 100 });
      const items = res.data?.items || res.data || [];
      setProjects(Array.isArray(items) ? items : []);

      // 批量获取齐套率数据
      if (items.length > 0) {
        const projectIds = items.map(p => p.id);
        await fetchBatchKitRates(projectIds);
        // 直接从项目数据计算毛利率，无需调用 API
        calculateMargins(items);
      }
    } catch (error) {
      console.error("Failed to fetch projects:", error);
      toast.error("加载项目列表失败");
    } finally {
      setLoading(false);
    }
  }, [calculateMargins]);

  // 批量获取齐套率
  const fetchBatchKitRates = async (projectIds) => {
    try {
      const res = await materialReadinessApi.getBatchKitRate(projectIds);
      const data = res.data || res || {};
      setKitRates(data.kit_rates || {});
    } catch (error) {
      console.warn("Failed to fetch kit rates:", error);
      // 降级：为每个项目设置默认值
      const defaultRates = {};
      projectIds.forEach(id => {
        defaultRates[id] = { rate: 0, status: "unknown" };
      });
      setKitRates(defaultRates);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // 筛选后的项目列表
  const filteredProjects = useMemo(() => {
    return projects.filter(project => {
      // 搜索筛选
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchName = (project.project_name || "").toLowerCase().includes(query);
        const matchCode = (project.project_code || "").toLowerCase().includes(query);
        if (!matchName && !matchCode) return false;
      }

      // 健康度筛选
      if (healthFilter !== "all" && project.health_status !== healthFilter) {
        return false;
      }

      // 阶段筛选
      if (stageFilter !== "all" && project.current_stage !== stageFilter) {
        return false;
      }

      // 齐套率筛选
      if (kitRateFilter !== "all") {
        const kitRate = kitRates[project.id]?.rate || 0;
        switch (kitRateFilter) {
          case "critical":
            if (kitRate >= 60) return false;
            break;
          case "warning":
            if (kitRate < 60 || kitRate >= 80) return false;
            break;
          case "good":
            if (kitRate < 80 || kitRate >= 95) return false;
            break;
          case "excellent":
            if (kitRate < 95) return false;
            break;
        }
      }

      return true;
    });
  }, [projects, searchQuery, healthFilter, stageFilter, kitRateFilter, kitRates]);

  // 统计数据
  const stats = useMemo(() => {
    const total = projects.length;
    const healthCounts = { H1: 0, H2: 0, H3: 0, H4: 0 };
    let totalKitRate = 0;
    let kitRateCount = 0;
    let totalMargin = 0;
    let marginCount = 0;

    projects.forEach(project => {
      // 健康度统计
      const health = project.health_status || "H1";
      if (healthCounts[health] !== undefined) {
        healthCounts[health]++;
      }

      // 齐套率统计
      const kitRate = kitRates[project.id]?.rate;
      if (kitRate !== undefined) {
        totalKitRate += kitRate;
        kitRateCount++;
      }

      // 毛利统计
      const margin = margins[project.id]?.predicted_margin;
      if (margin !== undefined) {
        totalMargin += margin;
        marginCount++;
      }
    });

    return {
      total,
      healthCounts,
      avgKitRate: kitRateCount > 0 ? Math.round(totalKitRate / kitRateCount) : 0,
      avgMargin: marginCount > 0 ? (totalMargin / marginCount).toFixed(1) : 0,
      blocked: healthCounts.H3,
      atRisk: healthCounts.H2,
    };
  }, [projects, kitRates, margins]);

  // 切换行展开
  const toggleRowExpand = (projectId) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      return next;
    });
  };

  // 获取健康度徽章
  const getHealthBadge = (healthStatus) => {
    const config = getHealthConfig(healthStatus);
    return (
      <Badge className={cn("border-0", config.bgColor, config.textColor)}>
        {config.label}
      </Badge>
    );
  };

  // 获取阶段名称
  const getStageName = (stageCode) => {
    const stage = PROJECT_STAGES.find(s => s.code === stageCode);
    return stage?.name || stageCode || "-";
  };

  // 渲染展开的详情行
  const renderExpandedRow = (project) => {
    const kitRate = kitRates[project.id] || {};
    const margin = margins[project.id] || {};

    return (
      <TableRow className="bg-slate-900/50">
        <TableCell colSpan={7} className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 齐套率详情 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  齐套率详情
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">整体齐套率</span>
                  <span className={cn("font-bold", getKitRateLevel(kitRate.rate || 0).color)}>
                    {kitRate.rate || 0}%
                  </span>
                </div>
                <Progress value={kitRate.rate || 0} className="h-2" />
                <div className="flex justify-between text-xs text-slate-500">
                  <span>可用物料: {kitRate.available || 0}</span>
                  <span>缺料: {kitRate.shortage || 0}</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => navigate(`/material-readiness?project_id=${project.id}`)}
                >
                  查看物料详情
                </Button>
              </CardContent>
            </Card>

            {/* 毛利预测详情 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  毛利预测
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">预测毛利率</span>
                  <span className={cn("font-bold", getMarginLevel(margin.predicted_margin || 0).color)}>
                    {margin.predicted_margin?.toFixed(1) || "-"}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">目标毛利率</span>
                  <span className="text-slate-300">
                    {margin.target_margin?.toFixed(1) || 25}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">预测置信度</span>
                  <span className="text-slate-300">
                    {margin.confidence?.toFixed(0) || "-"}%
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => navigate(`/margin-prediction?project_id=${project.id}`)}
                >
                  查看毛利分析
                </Button>
              </CardContent>
            </Card>

            {/* 项目进度详情 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  项目进度
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">当前阶段</span>
                  <Badge variant="outline">{getStageName(project.current_stage)}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">计划交付</span>
                  <span className="text-slate-300">{formatDate(project.planned_end_date)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">完成进度</span>
                  <span className="text-slate-300">{project.progress_percent || 0}%</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => navigate(`/projects/${project.id}`)}
                >
                  查看项目详情
                </Button>
              </CardContent>
            </Card>
          </div>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {!embedded ? (
        <PageHeader
          title="项目健康监控"
          description="整合齐套率、健康度、毛利率的项目全景视图"
          actions={
            <Button variant="outline" onClick={fetchProjects}>
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新
            </Button>
          }
        />
      ) : null}

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">项目总数</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">
              阻塞: {stats.blocked} | 风险: {stats.atRisk}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均齐套率</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={cn("text-2xl font-bold", getKitRateLevel(stats.avgKitRate).color)}>
              {stats.avgKitRate}%
            </div>
            <Progress value={stats.avgKitRate} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均毛利率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={cn("text-2xl font-bold", getMarginLevel(parseFloat(stats.avgMargin)).color)}>
              {stats.avgMargin}%
            </div>
            <p className="text-xs text-muted-foreground">
              基于 AI 毛利预测
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">健康分布</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <div className="flex h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="bg-emerald-500"
                    style={{ width: `${(stats.healthCounts.H1 / stats.total) * 100}%` }}
                  />
                  <div
                    className="bg-amber-500"
                    style={{ width: `${(stats.healthCounts.H2 / stats.total) * 100}%` }}
                  />
                  <div
                    className="bg-red-500"
                    style={{ width: `${(stats.healthCounts.H3 / stats.total) * 100}%` }}
                  />
                  <div
                    className="bg-slate-500"
                    style={{ width: `${(stats.healthCounts.H4 / stats.total) * 100}%` }}
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
              <span className="text-emerald-400">正常 {stats.healthCounts.H1}</span>
              <span className="text-amber-400">风险 {stats.healthCounts.H2}</span>
              <span className="text-red-400">阻塞 {stats.healthCounts.H3}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选条件 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索项目名称或编号..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select value={healthFilter} onValueChange={setHealthFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="健康度" />
              </SelectTrigger>
              <SelectContent>
                {HEALTH_FILTER_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={kitRateFilter} onValueChange={setKitRateFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="齐套率" />
              </SelectTrigger>
              <SelectContent>
                {KIT_RATE_FILTER_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={stageFilter} onValueChange={setStageFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="项目阶段" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部阶段</SelectItem>
                {PROJECT_STAGES.map((stage) => (
                  <SelectItem key={stage.code} value={stage.code}>
                    {stage.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 项目列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>项目列表</span>
            <Badge variant="outline">{filteredProjects.length} 个项目</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-slate-800">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[40px]"></TableHead>
                  <TableHead>项目名称</TableHead>
                  <TableHead>阶段</TableHead>
                  <TableHead>健康度</TableHead>
                  <TableHead>齐套率</TableHead>
                  <TableHead>毛利率</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  // 加载骨架屏
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell colSpan={7}>
                        <Skeleton className="h-12 w-full" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : filteredProjects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-slate-400">
                      暂无符合条件的项目
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredProjects.map((project) => {
                    const isExpanded = expandedRows.has(project.id);
                    const kitRate = kitRates[project.id]?.rate || 0;
                    const margin = margins[project.id]?.predicted_margin;
                    const kitRateLevel = getKitRateLevel(kitRate);

                    return (
                      <>
                        <TableRow
                          key={project.id}
                          className="cursor-pointer hover:bg-slate-800/50"
                          onClick={() => toggleRowExpand(project.id)}
                        >
                          <TableCell>
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{project.project_name}</div>
                              <div className="text-xs text-slate-500">{project.project_code}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{getStageName(project.current_stage)}</Badge>
                          </TableCell>
                          <TableCell>{getHealthBadge(project.health_status)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress value={kitRate} className="w-16 h-2" />
                              <span className={cn("text-sm font-medium", kitRateLevel.color)}>
                                {kitRate}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {margin !== undefined ? (
                              <span className={cn("font-medium", getMarginLevel(margin).color)}>
                                {margin.toFixed(1)}%
                              </span>
                            ) : (
                              <span className="text-slate-500">-</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/projects/${project.id}`);
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                        {isExpanded && renderExpandedRow(project)}
                      </>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
