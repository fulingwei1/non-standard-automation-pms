/**
 * 即时毛利率面板
 *
 * 显示项目的即时毛利率和成本去向，并与投标时的预估毛利率进行对比，
 * 帮助项目经理、技术负责人、销售和售前人员实时了解项目成本状况，便于成本控制。
 *
 * 核心指标：
 * - 即时毛利率 = (合同金额 - 累计实际成本) / 合同金额 × 100%
 * - 预估毛利率 = (合同金额 - 预估成本) / 合同金额 × 100%
 * - 成本偏差 = 实际成本 - 预估成本
 */

import { useState, useEffect, useMemo } from "react";
import { api } from "../../services/api/client";
import { formatCurrency } from "../../lib/utils";
import { usePermission, PERMISSIONS } from "../../hooks/usePermission";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Percent,
} from "lucide-react";

// 成本类别配置（非标自动化测试设备行业）
const COST_CATEGORY_CONFIG = {
  // 标准成本类别
  MECHANICAL: { label: "机械结构", color: "bg-blue-500", shortLabel: "机械" },
  ELECTRICAL: { label: "电气元件", color: "bg-yellow-500", shortLabel: "电气" },
  SOFTWARE: { label: "软件开发", color: "bg-purple-500", shortLabel: "软件" },
  OUTSOURCE: { label: "外协加工", color: "bg-orange-500", shortLabel: "外协" },
  LABOR: { label: "人工成本", color: "bg-green-500", shortLabel: "人工" },
  TRAVEL: { label: "差旅费用", color: "bg-cyan-500", shortLabel: "差旅" },
  OTHER: { label: "其他费用", color: "bg-gray-500", shortLabel: "其他" },
  // AI成本估算分类
  hardware_cost: { label: "硬件成本", color: "bg-blue-400", shortLabel: "硬件" },
  software_cost: { label: "软件成本", color: "bg-purple-400", shortLabel: "软件" },
  installation_cost: { label: "安装调试", color: "bg-teal-400", shortLabel: "安调" },
  service_cost: { label: "售后服务", color: "bg-pink-400", shortLabel: "服务" },
  risk_reserve: { label: "风险储备", color: "bg-red-400", shortLabel: "风险" },
  // 兼容旧数据
  purchase: { label: "采购成本", color: "bg-blue-400", shortLabel: "采购" },
  outsourcing: { label: "外协成本", color: "bg-orange-400", shortLabel: "外协" },
  bom: { label: "BOM成本", color: "bg-indigo-400", shortLabel: "BOM" },
  labor: { label: "人工成本", color: "bg-green-400", shortLabel: "人工" },
  travel: { label: "差旅费用", color: "bg-cyan-400", shortLabel: "差旅" },
};

// 毛利率阈值配置
const MARGIN_THRESHOLDS = {
  HEALTHY: 25, // 健康毛利率 >= 25%
  WARNING: 15, // 预警毛利率 15-25%
  DANGER: 0,   // 危险毛利率 < 15%
};

export default function RealTimeMarginPanel({ project, onRefresh }) {
  const [loading, setLoading] = useState(true);
  const [costData, setCostData] = useState(null);
  const [estimateData, setEstimateData] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  // 投标方案选择相关状态
  const [availableSolutions, setAvailableSolutions] = useState([]);
  const [selectedSolutionId, setSelectedSolutionId] = useState(null);

  // 权限检查
  const { hasAnyPermission } = usePermission();
  const canViewMargin = hasAnyPermission([
    PERMISSIONS.MARGIN?.READ,
    PERMISSIONS.MARGIN?.READ_ALL,
    PERMISSIONS.FINANCE?.REPORT_READ,
    'margin:read',
    'margin:read:all',
  ]);

  // 从项目对象获取关键财务字段
  const contractAmount = project?.contract_amount || 0;
  const budgetAmount = project?.budget_amount || project?.budget || 0;
  const opportunityId = project?.opportunity_id;

  useEffect(() => {
    if (project?.id) {
      fetchAllData();
    }
  }, [project?.id]);

  // 当选择的方案改变时，重新加载预估数据
  useEffect(() => {
    if (selectedSolutionId && availableSolutions.length > 0) {
      const selected = availableSolutions.find(s => s.id === selectedSolutionId);
      if (selected) {
        loadSolutionEstimate(selected);
      }
    }
  }, [selectedSolutionId]);

  const fetchAllData = async () => {
    setLoading(true);
    await Promise.all([fetchCostData(), fetchEstimateData()]);
    setLoading(false);
  };

  // 加载选定方案的预估数据
  const loadSolutionEstimate = async (solution) => {
    const response = await buildEstimateResponse(solution);
    if (response?.data) {
      setEstimateData(response.data);
    }
  };

  // 构建预估数据响应（从售前方案）
  const buildEstimateResponse = async (solution) => {
    const response = {
      data: {
        estimated_cost: parseFloat(solution.estimated_cost) || 0,
        suggested_price: parseFloat(solution.suggested_price) || 0,
        cost_breakdown: solution.cost_breakdown || {},
        solution_id: solution.id,
        solution_name: solution.name,
      },
    };

    // 获取详细成本明细
    try {
      const costItemsRes = await api.get(`/presale/solutions/${solution.id}/costs`);
      const costItems = costItemsRes.data?.data?.items || costItemsRes.data?.items || [];
      const byCategory = {};
      costItems.forEach(item => {
        const cat = item.category || "OTHER";
        byCategory[cat] = (byCategory[cat] || 0) + (parseFloat(item.amount) || 0);
      });
      response.data.by_category = byCategory;
    } catch {
      // 无详细明细，使用 cost_breakdown
    }

    return response;
  };

  // 获取实际成本数据
  const fetchCostData = async () => {
    try {
      const response = await api.get(`/projects/${project.id}/costs/summary`);
      setCostData(response.data?.data || response.data);
    } catch (error) {
      console.error("获取成本汇总失败:", error);
      // 备选方案：从成本列表计算
      try {
        const costsRes = await api.get(`/projects/${project.id}/costs`, {
          params: { page_size: 1000 },
        });
        const costs = costsRes.data?.data?.items || costsRes.data?.items || [];
        const totalCost = costs.reduce((sum, c) => sum + (parseFloat(c.amount) || 0), 0);
        const byType = {};
        costs.forEach(c => {
          const type = c.cost_type || c.cost_category || "OTHER";
          byType[type] = (byType[type] || 0) + (parseFloat(c.amount) || 0);
        });
        setCostData({ total_cost: totalCost, by_type: byType, budget: budgetAmount });
      } catch (e) {
        console.error("备选成本计算也失败:", e);
        setCostData({ total_cost: 0, by_type: {}, budget: budgetAmount });
      }
    }
  };

  // 获取投标时的预估成本数据
  const fetchEstimateData = async () => {
    try {
      let allSolutions = [];
      let estimateResponse = null;

      // 方式1：通过项目直接获取预估数据（如果有专用 API）
      try {
        estimateResponse = await api.get(`/projects/${project.id}/cost-estimate`);
      } catch {
        // API 可能不存在，继续尝试其他方式
      }

      // 方式2：通过项目 ID 获取关联的售前方案（一个项目可能有多个投标方案）
      if (!estimateResponse) {
        try {
          const solutionsRes = await api.get(`/presale/solutions`, {
            params: { project_id: project.id },
          });
          const solutions = solutionsRes.data?.data?.items || solutionsRes.data?.items || [];
          allSolutions = [...allSolutions, ...solutions];
        } catch {
          // 继续尝试其他方式
        }
      }

      // 方式3：通过商机 ID 获取售前方案（兼容历史数据）
      if (opportunityId) {
        try {
          const solutionsRes = await api.get(`/presale/solutions`, {
            params: { opportunity_id: opportunityId },
          });
          const solutions = solutionsRes.data?.data?.items || solutionsRes.data?.items || [];
          // 合并并去重（按 id）
          solutions.forEach(s => {
            if (!allSolutions.find(existing => existing.id === s.id)) {
              allSolutions.push(s);
            }
          });
        } catch (e) {
          console.error("获取售前方案失败:", e);
        }
      }

      // 按状态和时间排序：已批准的优先，然后按创建时间倒序
      allSolutions.sort((a, b) => {
        // 已批准的排前面
        if (a.review_status === "APPROVED" && b.review_status !== "APPROVED") return -1;
        if (b.review_status === "APPROVED" && a.review_status !== "APPROVED") return 1;
        // 同状态按创建时间倒序
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      });

      // 保存所有可用方案
      setAvailableSolutions(allSolutions);

      // 如果有方案，默认选中第一个（已批准的优先）
      if (allSolutions.length > 0 && !estimateResponse) {
        const defaultSolution = allSolutions[0];
        setSelectedSolutionId(defaultSolution.id);
        estimateResponse = await buildEstimateResponse(defaultSolution);
      }

      // 方式4：使用预算作为预估（最后的备选）
      if (!estimateResponse && allSolutions.length === 0 && budgetAmount > 0) {
        estimateResponse = {
          data: {
            estimated_cost: budgetAmount,
            suggested_price: contractAmount,
            cost_breakdown: {},
            source: "budget",
          },
        };
      }

      if (estimateResponse?.data) {
        setEstimateData(estimateResponse.data);
      }
    } catch (error) {
      console.error("获取预估数据失败:", error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAllData();
    setRefreshing(false);
    onRefresh?.();
  };

  // 计算即时毛利率和预估毛利率
  const marginData = useMemo(() => {
    const totalCost = costData?.total_cost || 0;
    const estimatedCost = estimateData?.estimated_cost || budgetAmount || 0;

    // 即时毛利金额 = 合同金额 - 累计成本
    const marginAmount = contractAmount - totalCost;

    // 即时毛利率 = (合同金额 - 累计成本) / 合同金额 × 100%
    const marginRate = contractAmount > 0
      ? ((contractAmount - totalCost) / contractAmount * 100)
      : null;

    // 预估毛利率 = (合同金额 - 预估成本) / 合同金额 × 100%
    const estimatedMarginRate = contractAmount > 0 && estimatedCost > 0
      ? ((contractAmount - estimatedCost) / contractAmount * 100)
      : null;

    // 毛利率偏差 = 即时毛利率 - 预估毛利率
    const marginVariance = (marginRate !== null && estimatedMarginRate !== null)
      ? marginRate - estimatedMarginRate
      : null;

    // 成本偏差 = 实际成本 - 预估成本
    const costVariance = estimatedCost > 0 ? totalCost - estimatedCost : null;
    const costVarianceRate = estimatedCost > 0
      ? ((totalCost - estimatedCost) / estimatedCost * 100)
      : null;

    // 确定毛利率健康状态
    let healthStatus = "unknown";
    if (marginRate !== null) {
      if (marginRate >= MARGIN_THRESHOLDS.HEALTHY) {
        healthStatus = "healthy";
      } else if (marginRate >= MARGIN_THRESHOLDS.WARNING) {
        healthStatus = "warning";
      } else {
        healthStatus = "danger";
      }
    }

    return {
      totalCost,
      estimatedCost,
      marginAmount,
      marginRate,
      estimatedMarginRate,
      marginVariance,
      costVariance,
      costVarianceRate,
      healthStatus,
    };
  }, [costData, estimateData, contractAmount, budgetAmount]);

  // 成本分类对比数据
  const costComparison = useMemo(() => {
    const actualByType = costData?.by_type || {};
    const estimatedByCategory = estimateData?.by_category || estimateData?.cost_breakdown || {};

    // 合并所有类别
    const allCategories = new Set([
      ...Object.keys(actualByType),
      ...Object.keys(estimatedByCategory),
    ]);

    const comparison = [];
    allCategories.forEach(category => {
      const actual = parseFloat(actualByType[category]) || 0;
      const estimated = parseFloat(estimatedByCategory[category]) || 0;
      const variance = actual - estimated;
      const varianceRate = estimated > 0 ? (variance / estimated * 100) : (actual > 0 ? 100 : 0);
      const config = COST_CATEGORY_CONFIG[category] || COST_CATEGORY_CONFIG.OTHER;

      comparison.push({
        category,
        label: config.label,
        shortLabel: config.shortLabel,
        color: config.color,
        actual,
        estimated,
        variance,
        varianceRate,
      });
    });

    // 按实际成本排序
    return comparison.sort((a, b) => b.actual - a.actual);
  }, [costData, estimateData]);

  // 获取毛利率状态的样式
  const getMarginStatusStyle = (status) => {
    switch (status) {
      case "healthy":
        return { color: "text-green-600", bg: "bg-green-100", icon: TrendingUp };
      case "warning":
        return { color: "text-yellow-600", bg: "bg-yellow-100", icon: AlertTriangle };
      case "danger":
        return { color: "text-red-600", bg: "bg-red-100", icon: TrendingDown };
      default:
        return { color: "text-gray-600", bg: "bg-gray-100", icon: Percent };
    }
  };

  // 获取偏差颜色
  const getVarianceColor = (variance) => {
    if (variance > 0) return "text-red-600"; // 超支
    if (variance < 0) return "text-green-600"; // 节约
    return "text-gray-600";
  };

  // 权限检查：无权限时显示提示
  if (!canViewMargin) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <PieChart className="h-5 w-5 text-blue-500" />
              即时毛利率
            </h3>
          </div>
          <div className="text-center py-4 text-gray-500">
            <Lock className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p>暂无查看权限</p>
            <p className="text-sm">如需查看毛利率数据，请联系管理员</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // 如果没有合同金额，显示提示
  if (!contractAmount) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <PieChart className="h-5 w-5 text-blue-500" />
              即时毛利率
            </h3>
          </div>
          <div className="text-center py-4 text-gray-500">
            <DollarSign className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p>暂无合同金额数据</p>
            <p className="text-sm">请先录入项目合同金额</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const statusStyle = getMarginStatusStyle(marginData.healthStatus);
  const StatusIcon = statusStyle.icon;

  return (
    <Card>
      <CardContent className="p-6">
        {/* 标题栏 */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <PieChart className="h-5 w-5 text-blue-500" />
            即时毛利率
          </h3>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="刷新数据"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* 核心指标卡片 */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* 即时毛利率 */}
          <div className={`p-4 rounded-lg ${statusStyle.bg}`}>
            <div className="flex items-center gap-2 mb-1">
              <StatusIcon className={`h-4 w-4 ${statusStyle.color}`} />
              <span className="text-xs text-gray-600">即时毛利率</span>
            </div>
            <div className={`text-2xl font-bold ${statusStyle.color}`}>
              {marginData.marginRate !== null
                ? `${marginData.marginRate.toFixed(1)}%`
                : "-"}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              毛利 {formatCurrency(marginData.marginAmount)}
            </div>
          </div>

          {/* 预估毛利率 */}
          <div className="p-4 rounded-lg bg-blue-50">
            <div className="flex items-center gap-2 mb-1">
              <Target className="h-4 w-4 text-blue-600" />
              <span className="text-xs text-gray-600">预估毛利率</span>
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {marginData.estimatedMarginRate !== null
                ? `${marginData.estimatedMarginRate.toFixed(1)}%`
                : "-"}
            </div>
            {marginData.marginVariance !== null && (
              <div className={`text-xs mt-1 ${marginData.marginVariance >= 0 ? "text-green-600" : "text-red-600"}`}>
                {marginData.marginVariance >= 0 ? "↑" : "↓"}
                偏差 {Math.abs(marginData.marginVariance).toFixed(1)}%
              </div>
            )}
          </div>
        </div>

        {/* 投标方案选择器（当有多个方案时显示） */}
        {availableSolutions.length > 1 && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-blue-700">
                <FileText className="h-4 w-4" />
                <span>对比方案</span>
                <Badge variant="secondary" className="text-xs">
                  {availableSolutions.length} 个方案
                </Badge>
              </div>
              <select
                value={selectedSolutionId || ""}
                onChange={(e) => setSelectedSolutionId(parseInt(e.target.value))}
                className="text-sm border border-blue-200 rounded px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableSolutions.map((sol) => (
                  <option key={sol.id} value={sol.id}>
                    {sol.name} ({sol.version || "V1.0"})
                    {sol.review_status === "APPROVED" ? " ✓" : ""}
                  </option>
                ))}
              </select>
            </div>
            {estimateData?.solution_name && (
              <div className="mt-2 text-xs text-blue-600">
                当前对比: {estimateData.solution_name}
                {estimateData.suggested_price > 0 && (
                  <span className="ml-2">
                    建议报价 {formatCurrency(estimateData.suggested_price)}
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* 成本对比条 */}
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between text-sm mb-2">
            <div className="flex items-center gap-4">
              <span className="text-gray-600">
                实际: <span className="font-medium text-gray-900">{formatCurrency(marginData.totalCost)}</span>
              </span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">
                预估: <span className="font-medium text-blue-600">{formatCurrency(marginData.estimatedCost)}</span>
              </span>
            </div>
            {marginData.costVariance !== null && (
              <span className={`font-medium ${getVarianceColor(marginData.costVariance)}`}>
                {marginData.costVariance > 0 ? "+" : ""}{formatCurrency(marginData.costVariance)}
                ({marginData.costVariance > 0 ? "+" : ""}{marginData.costVarianceRate?.toFixed(1)}%)
              </span>
            )}
          </div>

          {/* 双进度条对比 */}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-8">实际</span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    marginData.totalCost > contractAmount ? "bg-red-500" :
                    marginData.totalCost > marginData.estimatedCost ? "bg-yellow-500" : "bg-green-500"
                  }`}
                  style={{ width: `${Math.min((marginData.totalCost / contractAmount) * 100, 100)}%` }}
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-8">预估</span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-400 transition-all duration-500"
                  style={{ width: `${Math.min((marginData.estimatedCost / contractAmount) * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 展开/收起按钮 */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-center gap-1 text-sm text-gray-500 hover:text-gray-700 py-2"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-4 w-4" />
              收起详细对比
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4" />
              查看分类对比
            </>
          )}
        </button>

        {/* 展开的详细对比 */}
        {expanded && (
          <div className="mt-4 pt-4 border-t">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="overview" className="text-xs">
                  <BarChart3 className="h-3 w-3 mr-1" />
                  分类对比
                </TabsTrigger>
                <TabsTrigger value="detail" className="text-xs">
                  <FileText className="h-3 w-3 mr-1" />
                  偏差分析
                </TabsTrigger>
              </TabsList>

              {/* 分类对比视图 */}
              <TabsContent value="overview" className="space-y-3">
                {costComparison.length > 0 ? (
                  <>
                    {/* 表头 */}
                    <div className="flex items-center text-xs text-gray-500 px-2">
                      <span className="flex-1">成本类别</span>
                      <span className="w-20 text-right">预估</span>
                      <span className="w-20 text-right">实际</span>
                      <span className="w-20 text-right">偏差</span>
                    </div>
                    {/* 数据行 */}
                    {costComparison.map(({ category, label, shortLabel, color, actual, estimated, variance, varianceRate }) => (
                      <div key={category} className="flex items-center text-sm px-2 py-2 hover:bg-gray-50 rounded">
                        <span className="flex-1 flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${color}`} />
                          <span className="truncate">{shortLabel || label}</span>
                        </span>
                        <span className="w-20 text-right text-gray-600">
                          {estimated > 0 ? formatCurrency(estimated) : "-"}
                        </span>
                        <span className="w-20 text-right font-medium">
                          {actual > 0 ? formatCurrency(actual) : "-"}
                        </span>
                        <span className={`w-20 text-right ${getVarianceColor(variance)}`}>
                          {variance !== 0 ? (
                            <>
                              {variance > 0 ? "+" : ""}{varianceRate.toFixed(0)}%
                            </>
                          ) : "-"}
                        </span>
                      </div>
                    ))}
                  </>
                ) : (
                  <div className="text-center py-4 text-gray-500 text-sm">
                    暂无分类成本数据
                  </div>
                )}
              </TabsContent>

              {/* 偏差分析视图 */}
              <TabsContent value="detail" className="space-y-3">
                {/* 关键财务指标 */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">合同金额</div>
                    <div className="text-sm font-medium">{formatCurrency(contractAmount)}</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">项目预算</div>
                    <div className="text-sm font-medium">{formatCurrency(budgetAmount)}</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">投标预估成本</div>
                    <div className="text-sm font-medium text-blue-600">
                      {formatCurrency(marginData.estimatedCost)}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">累计实际成本</div>
                    <div className={`text-sm font-medium ${
                      marginData.totalCost > marginData.estimatedCost ? "text-red-600" : "text-green-600"
                    }`}>
                      {formatCurrency(marginData.totalCost)}
                    </div>
                  </div>
                </div>

                {/* 售前方案信息 */}
                {estimateData?.solution_name && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-2 text-xs text-blue-600 mb-1">
                      <FileText className="h-3 w-3" />
                      关联售前方案
                    </div>
                    <div className="text-sm font-medium text-blue-800">
                      {estimateData.solution_name}
                    </div>
                  </div>
                )}

                {/* 偏差分析图 */}
                {costComparison.filter(c => c.variance !== 0).length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs text-gray-500 mb-2">主要偏差项</div>
                    <div className="space-y-2">
                      {costComparison
                        .filter(c => Math.abs(c.variance) > 0)
                        .sort((a, b) => Math.abs(b.variance) - Math.abs(a.variance))
                        .slice(0, 5)
                        .map(({ category, label, variance, varianceRate, color }) => (
                          <div key={category} className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${color}`} />
                            <span className="text-xs flex-1">{label}</span>
                            <span className={`text-xs font-medium ${getVarianceColor(variance)}`}>
                              {variance > 0 ? "+" : ""}{formatCurrency(variance)}
                            </span>
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${variance > 0 ? "bg-red-400" : "bg-green-400"}`}
                                style={{
                                  width: `${Math.min(Math.abs(varianceRate), 100)}%`,
                                }}
                              />
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            {/* 成本控制建议 */}
            {marginData.healthStatus === "danger" && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-center gap-2 text-red-700 text-sm font-medium">
                  <AlertTriangle className="h-4 w-4" />
                  毛利率预警
                </div>
                <p className="text-xs text-red-600 mt-1">
                  当前毛利率 ({marginData.marginRate?.toFixed(1)}%) 低于预警线 ({MARGIN_THRESHOLDS.WARNING}%)。
                  成本超出预估 {formatCurrency(Math.abs(marginData.costVariance || 0))}。
                  建议立即审查超支项目，评估变更索赔可能性。
                </p>
              </div>
            )}
            {marginData.healthStatus === "warning" && (
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-center gap-2 text-yellow-700 text-sm font-medium">
                  <AlertTriangle className="h-4 w-4" />
                  成本关注
                </div>
                <p className="text-xs text-yellow-600 mt-1">
                  毛利率处于预警区间，较投标预估下降 {Math.abs(marginData.marginVariance || 0).toFixed(1)}%。
                  建议密切监控后续成本支出。
                </p>
              </div>
            )}
            {marginData.healthStatus === "healthy" && marginData.marginVariance !== null && marginData.marginVariance > 5 && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-2 text-green-700 text-sm font-medium">
                  <TrendingUp className="h-4 w-4" />
                  成本控制良好
                </div>
                <p className="text-xs text-green-600 mt-1">
                  毛利率高于预估 {marginData.marginVariance.toFixed(1)}%，
                  已节约成本 {formatCurrency(Math.abs(marginData.costVariance || 0))}。
                  可总结经验应用于类似项目。
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
