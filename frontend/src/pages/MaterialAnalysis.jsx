import { useState, useEffect, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Download,
  RefreshCw,
  AlertTriangle,
  BarChart3 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { cn } from "../lib/utils";
import { staggerContainer } from "../lib/animations";
import { purchaseApi } from "../services/api";
import {
  MaterialStatsOverview } from
"../components/material-analysis";

/**
 * 📦 材料分析管理系统 - 重构版
 * 项目材料齐套性分析、风险评估和性能监控
 */
export default function MaterialAnalysis() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [projectMaterials, setProjectMaterials] = useState([]);
  const [detailMap, setDetailMap] = useState({});
  const [detailLoading, setDetailLoading] = useState({});
  const [detailError, setDetailError] = useState({});
  const [stageKitMap, setStageKitMap] = useState({});
  const [stageKitLoading, setStageKitLoading] = useState({});
  const [stageKitError, setStageKitError] = useState({});
  const [activeTab, setActiveTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  const detailStatusMap = {
    fulfilled: {
      label: "已齐套",
      borderColor: "border-emerald-500/30",
      textColor: "text-emerald-400"
    },
    partial: {
      label: "部分齐套",
      borderColor: "border-amber-500/30",
      textColor: "text-amber-400"
    },
    shortage: {
      label: "缺料",
      borderColor: "border-red-500/30",
      textColor: "text-red-400"
    },
  };

  const getDetailStatus = (status) => {
    const key = String(status || "").toLowerCase();
    return detailStatusMap[key] || {
      label: status || "未知",
      borderColor: "border-slate-500/30",
      textColor: "text-slate-400"
    };
  };

  // 加载项目材料数据
  const loadProjectMaterials = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const projectMaterialsData = [];

      const kitRateResponse = await purchaseApi.kitRate.dashboard();
      const kitRateData = kitRateResponse?.data?.data || kitRateResponse?.data || {};
      const kitRateProjects = kitRateData.projects || [];
      kitRateProjects.forEach((project) => {
        const totalItems = project.total_items || 0;
        const fulfilledItems = project.fulfilled_items || 0;
        const shortageItems = project.shortage_items || 0;
        const inTransitItems = project.in_transit_items || Math.max(
          0,
          totalItems - fulfilledItems - shortageItems
        );
        const stats = {
          total: totalItems,
          arrived: fulfilledItems,
          inTransit: inTransitItems,
          delayed: 0,
          notOrdered: shortageItems,
        };
        const readyRate =
          totalItems > 0 ? Math.round(Number(project.kit_rate || 0)) : 100;
        const criticalMaterials = [];

        const planAssemblyDate = project.planned_end_date || "";
        const daysUntilAssembly = planAssemblyDate ?
        Math.max(
          0,
          Math.ceil(
            (new Date(planAssemblyDate) - new Date()) / (
            1000 * 60 * 60 * 24)
          )
        ) :
        0;

        projectMaterialsData.push({
          projectId: project.project_id,
          id: project.project_code || project.project_id?.toString(),
          name: project.project_name || "",
          planAssemblyDate: planAssemblyDate ? planAssemblyDate.split("T")[0] : "",
          daysUntilAssembly,
          materialStats: stats,
          readyRate,
          criticalMaterials
        });
      });

      setProjectMaterials(projectMaterialsData);
    } catch (err) {
      console.error("Failed to load project materials:", err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const message = err.response?.data?.message;
      const apiMessage =
        typeof detail === "string"
          ? detail
          : detail?.message || message || err.message;
      setError(status ? `加载物料数据失败 (${status}): ${apiMessage}` : `加载物料数据失败: ${apiMessage}`);
      setProjectMaterials([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadProjectDetail = useCallback(async (projectId) => {
    if (!projectId) {return;}
    if (detailLoading[projectId]) {return;}

    setDetailLoading((prev) => ({ ...prev, [projectId]: true }));
    setDetailError((prev) => ({ ...prev, [projectId]: "" }));

    try {
      const response = await purchaseApi.kitRate.getProjectMaterialStatus(projectId);
      const data = response?.data?.data || response?.data || {};
      setDetailMap((prev) => ({ ...prev, [projectId]: data }));
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const message = err.response?.data?.message;
      const apiMessage =
        typeof detail === "string"
          ? detail
          : detail?.message || message || err.message;
      const errorText = status
        ? `加载物料明细失败 (${status}): ${apiMessage}`
        : `加载物料明细失败: ${apiMessage}`;
      setDetailError((prev) => ({ ...prev, [projectId]: errorText }));
    } finally {
      setDetailLoading((prev) => ({ ...prev, [projectId]: false }));
    }
  }, [detailLoading]);

  const loadStageKitRate = useCallback(async (projectId) => {
    if (!projectId) {return;}
    if (stageKitLoading[projectId]) {return;}

    setStageKitLoading((prev) => ({ ...prev, [projectId]: true }));
    setStageKitError((prev) => ({ ...prev, [projectId]: "" }));

    try {
      const response = await purchaseApi.kitRate.unified(projectId);
      const data = response?.data?.data || response?.data || {};
      setStageKitMap((prev) => ({ ...prev, [projectId]: data }));
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const message = err.response?.data?.message;
      const apiMessage =
        typeof detail === "string"
          ? detail
          : detail?.message || message || err.message;
      const errorText = status
        ? `加载工艺齐套率失败 (${status}): ${apiMessage}`
        : `加载工艺齐套率失败: ${apiMessage}`;
      setStageKitError((prev) => ({ ...prev, [projectId]: errorText }));
    } finally {
      setStageKitLoading((prev) => ({ ...prev, [projectId]: false }));
    }
  }, [stageKitLoading]);

  // 过滤后的项目
  const filteredProjects = useMemo(() => {
    let filtered = projectMaterials;

    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
        (p.name || "").toLowerCase().includes(searchLower) ||
        (p.id || "").toLowerCase().includes(searchLower)
      );
    }

    if (filterStatus === "at_risk") {
      filtered = filtered.filter(
        (p) => p.readyRate < 80 || p.materialStats.delayed > 5
      );
    } else if (filterStatus === "upcoming") {
      filtered = filtered.filter(
        (p) => p.daysUntilAssembly <= 14 && p.daysUntilAssembly > 0
      );
    }

    return filtered;
  }, [projectMaterials, searchQuery, filterStatus]);

  // 总体统计
  const overallStats = useMemo(() => {
    return filteredProjects.reduce(
      (acc, project) => {
        acc.total += project.materialStats.total;
        acc.arrived += project.materialStats.arrived;
        acc.delayed += project.materialStats.delayed;
        return acc;
      },
      { total: 0, arrived: 0, delayed: 0 }
    );
  }, [filteredProjects]);

  const overallReadyRate = useMemo(() => {
    return overallStats.total > 0 ?
    Math.round(overallStats.arrived / overallStats.total * 100) :
    100;
  }, [overallStats]);

  // 初始化
  useEffect(() => {
    loadProjectMaterials();
  }, [loadProjectMaterials]);

  // 项目卡片组件
  function ProjectMaterialCard({ project }) {
    const [expanded, setExpanded] = useState(false);
    const stats = project.materialStats;
    const isAtRisk = project.readyRate < 80 || stats.delayed > 5;
    const detailData = detailMap[project.projectId];
    const detailIsLoading = detailLoading[project.projectId];
    const detailErrorText = detailError[project.projectId];
    const materialList = detailData?.materials || [];
    const stageKitData = stageKitMap[project.projectId];
    const stageIsLoading = stageKitLoading[project.projectId];
    const stageErrorText = stageKitError[project.projectId];
    const stageBased = stageKitData?.calculation_methods?.stage_based;
    const stageRates = stageBased?.stages || [];
    const shortageMaterials = [...materialList]
    .filter((material) => (material.shortage_qty || 0) > 0)
    .sort((a, b) => (b.shortage_qty || 0) - (a.shortage_qty || 0))
    .slice(0, 8);

    return (
      <motion.div
        layout
        className={cn(
          "rounded-xl border overflow-hidden transition-colors",
          isAtRisk ?
          "bg-red-500/5 border-red-500/30" :
          "bg-slate-800/50 border-slate-700/50"
        )}>

        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">
                {project.name}
              </h3>
              <p className="text-sm text-slate-400">{project.id}</p>
            </div>
            <div className="flex items-center gap-2">
              {isAtRisk &&
              <Badge variant="destructive" className="flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  风险
              </Badge>
              }
              <Badge
                variant={
                project.readyRate >= 90 ?
                "default" :
                project.readyRate >= 70 ?
                "secondary" :
                "destructive"
                }>

                {project.readyRate}% 齐套
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <div className="text-2xl font-bold text-white">{stats.total}</div>
              <div className="text-xs text-slate-400">总物料</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-400">
                {stats.arrived}
              </div>
              <div className="text-xs text-slate-400">已到货</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-400">
                {stats.inTransit}
              </div>
              <div className="text-xs text-slate-400">在途</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-400">
                {stats.delayed}
              </div>
              <div className="text-xs text-slate-400">延期</div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm text-slate-400">
              计划装配: {project.planAssemblyDate} ({project.daysUntilAssembly}天)
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const nextExpanded = !expanded;
                setExpanded(nextExpanded);
                if (nextExpanded && !detailData) {
                  loadProjectDetail(project.projectId);
                }
                if (nextExpanded && !stageKitData) {
                  loadStageKitRate(project.projectId);
                }
              }}>

              {expanded ? "收起" : "详情"}
            </Button>
          </div>

          {expanded &&
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-4 pt-4 border-t border-slate-700">

              <h4 className="text-sm font-medium text-white mb-3">缺料明细</h4>
              {detailIsLoading && (
                <div className="text-sm text-slate-400">正在加载物料明细...</div>
              )}
              {!detailIsLoading && detailErrorText && (
                <div className="text-sm text-red-400">{detailErrorText}</div>
              )}
              {!detailIsLoading && !detailErrorText && !detailData && (
                <div className="text-sm text-slate-400">暂无明细数据</div>
              )}
              {!detailIsLoading && !detailErrorText && detailData && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm text-slate-300">
                    <div>物料项数: {detailData.summary?.total_materials || 0}</div>
                    <div>缺料合计: {detailData.summary?.total_shortage_qty || 0}</div>
                  </div>
                  {shortageMaterials.length === 0 ? (
                    <div className="text-sm text-slate-400">暂无缺料明细</div>
                  ) : (
                    <div className="space-y-2">
                      {shortageMaterials.map((material) => {
                        const status = getDetailStatus(material.status);
                        return (
                          <div
                            key={material.material_code || material.material_id}
                            className="flex items-center justify-between p-2 bg-slate-900/50 rounded"
                          >
                            <div>
                              <div className="text-sm text-slate-200">
                                {material.material_name || material.material_code}
                              </div>
                              <div className="text-xs text-slate-500">
                                缺料 {material.shortage_qty || 0}
                              </div>
                            </div>
                            <Badge
                              variant="outline"
                              className={cn(
                                "border",
                                status.borderColor,
                                status.textColor
                              )}
                            >
                              {status.label}
                            </Badge>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              <div className="mt-6">
                <h4 className="text-sm font-medium text-white mb-3">工艺齐套率</h4>
                {stageIsLoading && (
                  <div className="text-sm text-slate-400">正在加载工艺齐套率...</div>
                )}
                {!stageIsLoading && stageErrorText && (
                  <div className="text-sm text-red-400">{stageErrorText}</div>
                )}
                {!stageIsLoading && !stageErrorText && !stageBased?.available && (
                  <div className="text-sm text-slate-400">
                    {stageBased?.message || "暂无工艺齐套数据"}
                  </div>
                )}
                {!stageIsLoading && !stageErrorText && stageBased?.available && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm text-slate-300">
                      <div>整体齐套率: {stageBased.overall_kit_rate}%</div>
                      <div>阻塞缺料: {stageBased.blocking_shortage_count || 0}</div>
                    </div>
                    {stageRates.length === 0 ? (
                      <div className="text-sm text-slate-400">暂无阶段明细</div>
                    ) : (
                      <div className="grid gap-2 md:grid-cols-2">
                        {stageRates.map((stage) => (
                          <div
                            key={stage.stage_code}
                            className="flex items-center justify-between p-2 bg-slate-900/50 rounded"
                          >
                            <div className="text-sm text-slate-200">
                              {stage.stage_name || stage.stage_code}
                            </div>
                            <Badge variant="outline" className="border-slate-600 text-slate-200">
                              {stage.kit_rate}%
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
          </motion.div>
          }
        </div>
      </motion.div>);

  }

  // 导出数据
  const exportData = () => {
    const csvData = filteredProjects.map((project) => ({
      项目编码: project.id,
      项目名称: project.name,
      计划装配日期: project.planAssemblyDate,
      总物料数: project.materialStats.total,
      已到货: project.materialStats.arrived,
      在途: project.materialStats.inTransit,
      延期: project.materialStats.delayed,
      未下单: project.materialStats.notOrdered,
      齐套率: `${project.readyRate}%`
    }));

    const csv = [
    Object.keys(csvData[0]).join(","),
    ...csvData.map((row) => Object.values(row).join(","))].
    join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `material_analysis_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>);

  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">加载失败</h3>
        <p className="text-slate-400 mb-4">{error}</p>
        <Button onClick={() => loadProjectMaterials()}>重试</Button>
      </div>);

  }

  return (
    <motion.div
      initial="initial"
      animate="animate"
      variants={staggerContainer}
      className="space-y-6">

      <PageHeader
        title="齐套缺料"
        description="项目齐套缺料分析、风险评估和性能监控"
        actions={
        <div className="flex items-center gap-3">
            <Button variant="outline" onClick={() => loadProjectMaterials()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
            <Button variant="outline" onClick={exportData}>
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
        </div>
        } />


      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="overview">统计概览</TabsTrigger>
          <TabsTrigger value="details">项目详情</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <MaterialStatsOverview
            projects={filteredProjects}
            materials={[]}
            loading={loading}
            onRefresh={loadProjectMaterials} />

        </TabsContent>

        <TabsContent value="details" className="space-y-6">
          {/* 搜索和过滤 */}
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <Input
                      placeholder="搜索项目名称或编码..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-900 border-slate-700 text-white" />

                  </div>
                </div>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger className="w-full md:w-48">
                    <SelectValue placeholder="过滤状态" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部项目</SelectItem>
                    <SelectItem value="at_risk">风险项目</SelectItem>
                    <SelectItem value="upcoming">近期装配</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* 总体统计 */}
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <BarChart3 className="w-5 h-5" />
                总体统计
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <div className="text-3xl font-bold text-white">
                    {filteredProjects.length}
                  </div>
                  <div className="text-sm text-slate-400">项目总数</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-blue-400">
                    {overallStats.total}
                  </div>
                  <div className="text-sm text-slate-400">总物料数</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-green-400">
                    {overallStats.arrived}
                  </div>
                  <div className="text-sm text-slate-400">已到货</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-amber-400">
                    {overallReadyRate}%
                  </div>
                  <div className="text-sm text-slate-400">整体齐套率</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 项目列表 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredProjects.map((project) =>
            <ProjectMaterialCard key={project.id} project={project} />
            )}
          </div>

          {filteredProjects.length === 0 &&
          <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="p-12 text-center">
                <div className="text-slate-400">没有找到匹配的项目</div>
              </CardContent>
          </Card>
          }
        </TabsContent>
      </Tabs>
    </motion.div>);

}
