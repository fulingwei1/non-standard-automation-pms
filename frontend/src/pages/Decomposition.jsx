/**
 * 战略目标分解页面
 * 战略 CSF → 部门目标 (OKR) → 个人 KPI 三层树形结构
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ChevronRight,
  ChevronDown,
  Target,
  Users,
  User,
  TrendingUp,
  Award,
  Star,
  RefreshCw,
  Plus,
  Edit2,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Label,
  Input,
  Textarea,
} from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import { decompositionApi, strategyApi } from "@/services/api/strategy";

const STATUS_CONFIG = {
  ON_TRACK: { label: "正常", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  AT_RISK: { label: "预警", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  OFF_TRACK: { label: "落后", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  COMPLETED: { label: "已完成", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
};

// BSC 维度颜色
const DIMENSION_COLORS = {
  financial: "#22c55e",
  customer: "#3b82f6",
  internal: "#f59e0b",
  learning: "#a855f7",
};

export default function Decomposition() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [treeData, setTreeData] = useState(null);
  const [expandedCsfs, setExpandedCsfs] = useState({});
  const [expandedDepts, setExpandedDepts] = useState({});
  const [selectedKpi, setSelectedKpi] = useState(null);
  const [isRatingModalOpen, setIsRatingModalOpen] = useState(false);
  const [ratingType, setRatingType] = useState("self"); // self or manager
  const [ratingForm, setRatingForm] = useState({
    score: 5,
    comment: "",
  });

  // 获取战略列表
  useEffect(() => {
    fetchStrategies();
  }, []);

  // 获取分解树
  useEffect(() => {
    if (selectedStrategyId) {
      fetchTree();
    }
  }, [selectedStrategyId]);

  const fetchStrategies = async () => {
    try {
      const { data } = await strategyApi.list();
      setStrategies(data.items || data || []);
      if (data.items?.length > 0 && !selectedStrategyId) {
        setSelectedStrategyId(data.items[0].id);
      }
    } catch (error) {
      console.error("获取战略列表失败:", error);
    }
  };

  const fetchTree = async () => {
    setLoading(true);
    try {
      const { data } = await decompositionApi.getTree(selectedStrategyId);
      setTreeData(data);
    } catch (error) {
      console.error("获取分解树失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchTree();
    setRefreshing(false);
  };

  const toggleCsf = (csfId) => {
    setExpandedCsfs((prev) => ({
      ...prev,
      [csfId]: !prev[csfId],
    }));
  };

  const toggleDept = (deptId) => {
    setExpandedDepts((prev) => ({
      ...prev,
      [deptId]: !prev[deptId],
    }));
  };

  const handleOpenRating = (kpi, type) => {
    setSelectedKpi(kpi);
    setRatingType(type);
    setRatingForm({
      score: type === "self" ? kpi.self_rating_score : kpi.manager_rating_score,
      comment: type === "self" ? kpi.self_rating_comment : kpi.manager_rating_comment,
    });
    setIsRatingModalOpen(true);
  };

  const handleSubmitRating = async () => {
    try {
      if (ratingType === "self") {
        await decompositionApi.selfRating(selectedKpi.id, {
          score: ratingForm.score,
          comment: ratingForm.comment,
        });
      } else {
        await decompositionApi.managerRating(selectedKpi.id, {
          score: ratingForm.score,
          comment: ratingForm.comment,
        });
      }
      setIsRatingModalOpen(false);
      await fetchTree();
    } catch (error) {
      console.error("提交评分失败:", error);
    }
  };

  const parseKeyResults = (jsonStr) => {
    try {
      return JSON.parse(jsonStr);
    } catch {
      return [];
    }
  };

  const getCompletionRate = (kpi) => {
    if (!kpi.target_value || !kpi.actual_value) return 0;
    return Math.min(100, (kpi.actual_value / kpi.target_value) * 100);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="战略目标分解"
        description="战略 CSF → 部门 OKR → 个人 KPI 三层分解视图"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Select
              value={selectedStrategyId?.toString()}
              onValueChange={(val) => setSelectedStrategyId(parseInt(val))}
            >
              <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="选择战略" />
              </SelectTrigger>
              <SelectContent>
                {strategies.map((s) => (
                  <SelectItem key={s.id} value={s.id.toString()}>
                    {s.name} ({s.year})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
              刷新
            </Button>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              新增分解
            </Button>
          </motion.div>
        }
      />

      {/* 统计概览 */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Target className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {treeData?.csfs?.length || 0}
                </p>
                <p className="text-xs text-slate-400">战略 CSF</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Users className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {treeData?.total_departments || 0}
                </p>
                <p className="text-xs text-slate-400">部门目标</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/20">
                <User className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {treeData?.total_kpis || 0}
                </p>
                <p className="text-xs text-slate-400">个人 KPI</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <Award className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {treeData?.avg_completion_rate?.toFixed(1) || 0}%
                </p>
                <p className="text-xs text-slate-400">平均完成率</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 分解树 */}
      <motion.div variants={staggerContainer} className="space-y-4">
        {(treeData?.csfs || []).map((csf) => {
          const isExpanded = expandedCsfs[csf.id];
          const dimensionColor = DIMENSION_COLORS[csf.dimension] || "#64748b";

          return (
            <motion.div key={csf.id} variants={fadeIn}>
              <Card className="bg-slate-800/40 border-slate-700/50 overflow-hidden">
                {/* CSF 层 */}
                <CardHeader
                  className="cursor-pointer hover:bg-slate-700/30 transition-colors"
                  onClick={() => toggleCsf(csf.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-1 h-8 rounded"
                        style={{ backgroundColor: dimensionColor }}
                      />
                      <div>
                        <CardTitle className="text-base text-white flex items-center gap-2">
                          <ChevronRight
                            className={`w-4 h-4 transition-transform ${
                              isExpanded ? "rotate-90" : ""
                            }`}
                          />
                          <Target className="w-4 h-4" style={{ color: dimensionColor }} />
                          CSF: {csf.name}
                        </CardTitle>
                        <p className="text-sm text-slate-400 mt-1">
                          {csf.description}
                        </p>
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={
                        csf.dimension === "financial"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : csf.dimension === "customer"
                          ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                          : csf.dimension === "internal"
                          ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                          : "bg-purple-500/20 text-purple-400 border-purple-500/30"
                      }
                    >
                      {csf.dimension === "financial"
                        ? "财务"
                        : csf.dimension === "customer"
                        ? "客户"
                        : csf.dimension === "internal"
                        ? "内部流程"
                        : "学习成长"}
                    </Badge>
                  </div>
                </CardHeader>

                {/* 部门目标层 */}
                {isExpanded && csf.departments && csf.departments.length > 0 && (
                  <CardContent className="space-y-3 pt-0">
                    {csf.departments.map((dept) => {
                      const isDeptExpanded = expandedDepts[dept.id];
                      const statusCfg = STATUS_CONFIG[dept.status] || STATUS_CONFIG.ON_TRACK;

                      return (
                        <div
                          key={dept.id}
                          className="ml-4 border-l-2 border-slate-700 pl-4"
                        >
                          <div
                            className="flex items-center gap-2 py-2 cursor-pointer hover:text-white transition-colors"
                            onClick={() => toggleDept(dept.id)}
                          >
                            <ChevronRight
                              className={`w-4 h-4 transition-transform ${
                                isDeptExpanded ? "rotate-90" : ""
                              }`}
                            />
                            <Users className="w-4 h-4 text-blue-400" />
                            <span className="font-medium text-white">{dept.department_name}</span>
                            <Badge variant="outline" className={statusCfg.color}>
                              {statusCfg.label}
                            </Badge>
                          </div>

                          {/* 部门目标详情 */}
                          {isDeptExpanded && (
                            <div className="ml-6 space-y-3">
                              <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                                <p className="text-sm text-slate-400 mb-1">部门目标</p>
                                <p className="text-white">{dept.objective}</p>
                              </div>

                              {/* 关键结果 */}
                              {dept.key_results && (
                                <div className="space-y-2">
                                  <p className="text-sm text-slate-400">关键结果</p>
                                  {parseKeyResults(dept.key_results).map((kr, idx) => (
                                    <div
                                      key={idx}
                                      className="flex items-start gap-2 text-sm"
                                    >
                                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5" />
                                      <span className="text-slate-300">{kr}</span>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* 个人 KPI 列表 */}
                              {dept.kpis && dept.kpis.length > 0 && (
                                <div className="space-y-2 mt-3">
                                  <p className="text-sm text-slate-400 flex items-center gap-2">
                                    <User className="w-4 h-4" />
                                    个人 KPI ({dept.kpis.length})
                                  </p>
                                  {dept.kpis.map((kpi) => {
                                    const completionRate = getCompletionRate(kpi);
                                    const kpiStatusCfg = STATUS_CONFIG[kpi.status] || STATUS_CONFIG.ON_TRACK;

                                    return (
                                      <div
                                        key={kpi.id}
                                        className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/50"
                                      >
                                        <div className="flex items-start justify-between mb-2">
                                          <div>
                                            <p className="text-white font-medium">{kpi.name}</p>
                                            <p className="text-xs text-slate-400">
                                              {kpi.employee_name}
                                            </p>
                                          </div>
                                          <Badge variant="outline" className={kpiStatusCfg.color}>
                                            {kpiStatusCfg.label}
                                          </Badge>
                                        </div>

                                        {/* 完成率进度条 */}
                                        <div className="space-y-1 mb-3">
                                          <div className="flex items-center justify-between text-xs">
                                            <span className="text-slate-400">
                                              {kpi.actual_value} / {kpi.target_value}
                                            </span>
                                            <span className="text-white font-medium">
                                              {completionRate.toFixed(1)}%
                                            </span>
                                          </div>
                                          <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                              className={`h-full transition-all ${
                                                completionRate >= 100
                                                  ? "bg-emerald-500"
                                                  : completionRate >= 80
                                                  ? "bg-blue-500"
                                                  : completionRate >= 60
                                                  ? "bg-amber-500"
                                                  : "bg-red-500"
                                              }`}
                                              style={{ width: `${completionRate}%` }}
                                            />
                                          </div>
                                        </div>

                                        {/* 评分 */}
                                        <div className="flex items-center justify-between">
                                          <div className="flex items-center gap-4 text-sm">
                                            <div className="flex items-center gap-1">
                                              <Star className="w-3 h-3 text-amber-400" />
                                              <span className="text-slate-400">自评:</span>
                                              <span className="text-white">
                                                {kpi.self_rating_score || "-"}
                                              </span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                              <Award className="w-3 h-3 text-purple-400" />
                                              <span className="text-slate-400">上级:</span>
                                              <span className="text-white">
                                                {kpi.manager_rating_score || "-"}
                                              </span>
                                            </div>
                                          </div>
                                          <div className="flex gap-2">
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              onClick={() => handleOpenRating(kpi, "self")}
                                            >
                                              自评
                                            </Button>
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              onClick={() => handleOpenRating(kpi, "manager")}
                                            >
                                              上级评分
                                            </Button>
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </CardContent>
                )}

                {/* 无部门数据提示 */}
                {isExpanded && (!csf.departments || csf.departments.length === 0) && (
                  <CardContent className="py-6 text-center text-slate-500">
                    <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>暂无部门目标分解</p>
                  </CardContent>
                )}
              </Card>
            </motion.div>
          );
        })}

        {/* 无数据提示 */}
        {(!treeData?.csfs || treeData.csfs.length === 0) && (
          <div className="text-center py-12 text-slate-500">
            <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>暂无战略分解数据</p>
            <p className="text-sm">请先创建战略 CSF 并进行目标分解</p>
          </div>
        )}
      </motion.div>

      {/* 评分弹窗 */}
      <Dialog open={isRatingModalOpen} onOpenChange={setIsRatingModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle>
              {ratingType === "self" ? "自我评分" : "上级评分"} - {selectedKpi?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>评分 (1-10)</Label>
              <div className="flex items-center gap-4 mt-2">
                <Input
                  type="number"
                  min="1"
                  max="10"
                  value={ratingForm.score}
                  onChange={(e) =>
                    setRatingForm({ ...ratingForm, score: parseInt(e.target.value) || 0 })
                  }
                  className="w-24 bg-slate-800 border-slate-700"
                />
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((s) => (
                    <button
                      key={s}
                      onClick={() => setRatingForm({ ...ratingForm, score: s })}
                      className={`w-6 h-6 rounded text-xs ${
                        ratingForm.score >= s
                          ? "bg-amber-500 text-white"
                          : "bg-slate-700 text-slate-400"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div>
              <Label>评语</Label>
              <Textarea
                value={ratingForm.comment}
                onChange={(e) =>
                  setRatingForm({ ...ratingForm, comment: e.target.value })
                }
                placeholder="请输入评分说明..."
                className="bg-slate-800 border-slate-700 min-h-[100px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRatingModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitRating}>
              <Star className="w-4 h-4 mr-2" />
              提交评分
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
