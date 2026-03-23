/**
 * TimeCostMarginFlow - 工时成本毛利集成视图
 * 显示工时填报 → 成本计算 → 毛利预测的数据流程
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Clock,
  DollarSign,
  TrendingUp,
} from "lucide-react";




import { projectApi } from "../services/api";
import { formatDate, formatCurrency, cn } from "../lib/utils";

// 流程节点配置
const FLOW_NODES = [
  {
    id: "timesheet",
    title: "工时填报",
    icon: Clock,
    color: "text-blue-400",
    bgColor: "bg-blue-500/20",
    borderColor: "border-blue-500/50",
    description: "工程师填报项目工时",
    link: "/workstation?tab=timesheet",
  },
  {
    id: "cost",
    title: "成本计算",
    icon: DollarSign,
    color: "text-amber-400",
    bgColor: "bg-amber-500/20",
    borderColor: "border-amber-500/50",
    description: "汇总人工成本与物料成本",
    link: "/project-list-with-cost",
  },
  {
    id: "margin",
    title: "毛利预测",
    icon: TrendingUp,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/20",
    borderColor: "border-emerald-500/50",
    description: "AI预测项目毛利率",
    link: "/margin-prediction",
  },
];

// 数据状态配置
const DATA_STATUS = {
  fresh: { label: "最新", color: "text-emerald-400", bgColor: "bg-emerald-500/20" },
  stale: { label: "需更新", color: "text-amber-400", bgColor: "bg-amber-500/20" },
  error: { label: "异常", color: "text-red-400", bgColor: "bg-red-500/20" },
  loading: { label: "加载中", color: "text-slate-400", bgColor: "bg-slate-500/20" },
};

// 流程节点组件
function FlowNode({ node, data, loading, onClick }) {
  const Icon = node.icon;
  const status = data?.status || "loading";
  const statusConfig = DATA_STATUS[status] || DATA_STATUS.loading;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative p-6 rounded-xl border-2 cursor-pointer transition-all",
        node.bgColor,
        node.borderColor,
        "hover:shadow-lg hover:scale-[1.02]"
      )}
      onClick={onClick}
    >
      {/* 状态徽章 */}
      <Badge
        className={cn("absolute -top-2 -right-2 text-xs", statusConfig.bgColor, statusConfig.color)}
      >
        {loading ? <RefreshCw className="h-3 w-3 animate-spin mr-1" /> : null}
        {statusConfig.label}
      </Badge>

      {/* 图标和标题 */}
      <div className="flex items-center gap-3 mb-4">
        <div className={cn("p-2 rounded-lg", node.bgColor)}>
          <Icon className={cn("h-6 w-6", node.color)} />
        </div>
        <div>
          <h3 className="font-semibold">{node.title}</h3>
          <p className="text-xs text-slate-400">{node.description}</p>
        </div>
      </div>

      {/* 数据内容 */}
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-4 w-full" />
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-2xl font-bold">{data?.value || "-"}</div>
          <div className="text-xs text-slate-400">{data?.subtext || ""}</div>
          {data?.lastUpdate && (
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <Calendar className="h-3 w-3" />
              更新于 {formatDate(data.lastUpdate)}
            </div>
          )}
        </div>
      )}

      {/* 详情链接 */}
      <div className="mt-4 flex items-center text-xs text-slate-400 hover:text-slate-200">
        查看详情
        <ChevronRight className="h-3 w-3 ml-1" />
      </div>
    </motion.div>
  );
}

// 箭头组件
function FlowArrow({ animated }) {
  return (
    <div className="flex items-center justify-center px-2 hidden lg:flex">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={cn("flex items-center", animated && "text-cyan-400")}
      >
        <div className={cn("w-12 h-px", animated ? "bg-cyan-400" : "bg-slate-600")} />
        <ArrowRight className="h-5 w-5" />
      </motion.div>
    </div>
  );
}

export default function TimeCostMarginFlow({ embedded = false }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const projectIdFromQuery = searchParams.get("project_id");

  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(
    projectIdFromQuery ? parseInt(projectIdFromQuery) : null
  );

  // 各节点数据
  const [timesheetData, setTimesheetData] = useState(null);
  const [costData, setCostData] = useState(null);
  const [marginData, setMarginData] = useState(null);

  // 加载项目列表
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const res = await projectApi.list({ page: 1, page_size: 100 });
        const items = res.data?.items || res.data || [];
        setProjects(Array.isArray(items) ? items : []);

        // 如果没有选中项目，选择第一个
        if (!selectedProjectId && items.length > 0) {
          setSelectedProjectId(items[0].id);
        }
      } catch (_error) {
        // 非关键操作失败时静默降级
      }
    };
    loadProjects();
  }, []);

  // 加载节点数据
  const fetchNodeData = useCallback(async () => {
    if (!selectedProjectId) return;

    setLoading(true);
    try {
      // 获取当前项目数据
      const selectedProject = projects.find(p => p.id === selectedProjectId);

      // 获取工时数据（使用 try-catch 以防 API 不存在）
      let timesheetRes = null;
      try {
        timesheetRes = await projectApi.getTimesheetSummary(selectedProjectId, {});
      } catch (_e) {
        // 非关键操作失败时静默降级
      }

      // 解析工时数据
      if (timesheetRes?.data || timesheetRes) {
        const data = timesheetRes?.data || timesheetRes || {};
        setTimesheetData({
          value: `${data.total_hours || 0} 小时`,
          subtext: `${data.record_count || 0} 条记录`,
          status: data.pending_sync_count > 0 ? "stale" : "fresh",
          lastUpdate: data.last_update_time,
          detail: data,
        });
      } else {
        setTimesheetData({
          value: "- 小时",
          subtext: "暂无数据",
          status: "stale",
        });
      }

      // 从项目数据直接计算毛利率（不调用 predict API）
      if (selectedProject) {
        const contractAmount = parseFloat(selectedProject.contract_amount) || 0;
        const actualCost = parseFloat(selectedProject.actual_cost) || 0;
        const budgetAmount = parseFloat(selectedProject.budget_amount) || 0;

        // 成本数据
        setCostData({
          value: formatCurrency(actualCost),
          subtext: `预算 ${formatCurrency(budgetAmount)}`,
          status: actualCost > 0 ? "fresh" : "stale",
          detail: { actual_cost: actualCost, budget_amount: budgetAmount },
        });

        // 毛利数据
        if (contractAmount > 0) {
          const margin = ((contractAmount - actualCost) / contractAmount) * 100;
          setMarginData({
            value: `${margin.toFixed(1)}%`,
            subtext: `合同 ${formatCurrency(contractAmount)}`,
            status: "fresh",
            detail: {
              predicted_margin: margin,
              contract_amount: contractAmount,
              actual_cost: actualCost,
              profit: contractAmount - actualCost,
            },
          });
        } else {
          setMarginData({
            value: "-%",
            subtext: "合同金额未设置",
            status: "stale",
          });
        }
      } else {
        setCostData({
          value: "¥ -",
          subtext: "暂无数据",
          status: "error",
        });
        setMarginData({
          value: "- %",
          subtext: "暂无数据",
          status: "error",
        });
      }
    } catch (_error) {
      // 非关键操作失败时静默降级
    } finally {
      setLoading(false);
    }
  }, [selectedProjectId, projects]);

  useEffect(() => {
    fetchNodeData();
  }, [fetchNodeData]);

  // 获取节点数据
  const getNodeData = (nodeId) => {
    switch (nodeId) {
      case "timesheet":
        return timesheetData;
      case "cost":
        return costData;
      case "margin":
        return marginData;
      default:
        return null;
    }
  };

  // 处理节点点击
  const handleNodeClick = (node) => {
    const link = selectedProjectId ? `${node.link}?project_id=${selectedProjectId}` : node.link;
    navigate(link);
  };

  // 获取当前项目
  const selectedProject = useMemo(() => {
    return projects.find((p) => p.id === selectedProjectId);
  }, [projects, selectedProjectId]);

  // 数据流是否完整
  const isFlowComplete = useMemo(() => {
    return (
      timesheetData?.status === "fresh" &&
      costData?.status === "fresh" &&
      marginData?.status === "fresh"
    );
  }, [timesheetData, costData, marginData]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {!embedded ? (
        <PageHeader
          title="工时成本毛利联动"
          description="查看工时填报 → 成本计算 → 毛利预测的数据流程"
          actions={
            <Button variant="outline" onClick={fetchNodeData}>
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新
            </Button>
          }
        />
      ) : null}

      {/* 项目选择和状态概览 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center justify-between">
              <span>项目选择</span>
              {isFlowComplete ? (
                <Badge className="bg-emerald-500/20 text-emerald-400">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  数据完整
                </Badge>
              ) : (
                <Badge className="bg-amber-500/20 text-amber-400">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  部分数据需更新
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Select
                value={selectedProjectId?.toString() || ""}
                onValueChange={(value) => setSelectedProjectId(parseInt(value))}
              >
                <SelectTrigger className="w-[300px]">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id?.toString()}>
                      {p.project_name || p.project_code || `项目#${p.id}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedProject && (
                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <span className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    {selectedProject.team_size || 0} 人
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="h-4 w-4" />
                    进度 {selectedProject.progress_percent || 0}%
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 同步状态 */}
        <SyncStatus projectId={selectedProjectId} onSyncComplete={fetchNodeData} />
      </div>

      {/* 数据流程图 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            数据流程
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 items-center">
            {FLOW_NODES.map((node, index) => (
              <>
                <FlowNode
                  key={node.id}
                  node={node}
                  data={getNodeData(node.id)}
                  loading={loading}
                  onClick={() => handleNodeClick(node)}
                />
                {index < FLOW_NODES.length - 1 && (
                  <FlowArrow key={`arrow-${index}`} animated={isFlowComplete} />
                )}
              </>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 详细数据卡片 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 工时统计 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Clock className="h-4 w-4 text-blue-400" />
              工时统计
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <>
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </>
            ) : (
              <>
                <div className="text-3xl font-bold">
                  {timesheetData?.detail?.total_hours || 0}
                  <span className="text-sm font-normal text-slate-400 ml-1">小时</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-slate-400">记录数</div>
                    <div className="font-medium">{timesheetData?.detail?.record_count || 0}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">人均工时</div>
                    <div className="font-medium">
                      {timesheetData?.detail?.avg_hours_per_person?.toFixed(1) || 0} h
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => navigate(`/workstation?tab=timesheet&project_id=${selectedProjectId}`)}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  填报工时
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* 成本汇总 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-amber-400" />
              成本汇总
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <>
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </>
            ) : (
              <>
                <div className="text-3xl font-bold">
                  {formatCurrency(costData?.detail?.total_cost || 0)}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">人工成本</span>
                    <span>{formatCurrency(costData?.detail?.labor_cost || 0)}</span>
                  </div>
                  <Progress
                    value={
                      costData?.detail?.total_cost
                        ? (costData?.detail?.labor_cost / costData?.detail?.total_cost) * 100
                        : 0
                    }
                    className="h-2"
                  />
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">物料成本</span>
                    <span>{formatCurrency(costData?.detail?.material_cost || 0)}</span>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => navigate(`/project-list-with-cost?project_id=${selectedProjectId}`)}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  成本明细
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* 毛利预测 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              毛利预测
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <>
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </>
            ) : (
              <>
                <div className="text-3xl font-bold">
                  <span
                    className={cn(
                      (marginData?.detail?.predicted_margin || 0) >= 20
                        ? "text-emerald-400"
                        : (marginData?.detail?.predicted_margin || 0) >= 10
                        ? "text-amber-400"
                        : "text-red-400"
                    )}
                  >
                    {(marginData?.detail?.predicted_margin || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-slate-400">目标毛利</div>
                    <div className="font-medium">{marginData?.detail?.target_margin || 25}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">置信度</div>
                    <div className="font-medium">
                      {(marginData?.detail?.confidence || 0).toFixed(0)}%
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => navigate(`/margin-prediction?project_id=${selectedProjectId}`)}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  毛利分析
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}
