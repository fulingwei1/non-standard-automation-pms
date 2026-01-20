import { useState, useEffect, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Download,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
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
import { fadeIn as _fadeIn, staggerContainer } from "../lib/animations";
import { projectApi, bomApi, purchaseApi, assemblyKitApi as _assemblyKitApi } from "../services/api";
import {
  MaterialStatsOverview,
  MATERIAL_STATUS,
  getMaterialStatus,
  calculateReadinessRate } from
"../components/material-analysis";

/**
 * 📦 材料分析管理系统 - 重构版
 * 项目材料齐套性分析、风险评估和性能监控
 */
export default function MaterialAnalysis() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [projectMaterials, setProjectMaterials] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [_trendData, setTrendData] = useState([]);
  const [trendPeriod, _setTrendPeriod] = useState("weekly");
  const [_loadingTrend, setLoadingTrend] = useState(false);
  const [_refreshKey, setRefreshKey] = useState(0);

  // 加载项目材料数据
  const loadProjectMaterials = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const projectMaterialsData = [];

      // 获取所有项目
      const projectsResponse = await projectApi.list({
        is_active: true,
        page_size: 1000
      });
      const projects = projectsResponse.data?.items || projectsResponse.data?.results || projectsResponse.data || [];

      for (const project of projects) {
        try {
          // 获取BOM数据
          const bomResponse = await bomApi.list({
            project: project.id,
            page_size: 1000
          });
          const bomItems = bomResponse.data?.items || bomResponse.data?.results || bomResponse.data || [];

          // 获取采购订单数据
          const purchaseResponse = await purchaseApi.orders.list({
            project_id: project.id,
            limit: 100
          });
          const purchaseOrders = purchaseResponse.data?.data || purchaseResponse.data?.items || purchaseResponse.data?.results || purchaseResponse.data || [];

          // 计算材料统计
          let stats = {
            total: 0,
            arrived: 0,
            inTransit: 0,
            delayed: 0,
            notOrdered: 0
          };

          bomItems.forEach((item) => {
            const totalQty = item.quantity || 0;
            stats.total += totalQty;

            // 查找对应的采购订单
            const relatedOrders = purchaseOrders.filter(
              (order) => order.material_item === item.id
            );

            if (relatedOrders.length === 0) {
              stats.notOrdered += totalQty;
            } else {
              let arrivedQty = 0;
              let inTransitQty = 0;
              let delayedQty = 0;

              relatedOrders.forEach((order) => {
                const orderQty = order.quantity || 0;
                const status = order.status;

                if (status === "delivered") {
                  arrivedQty += orderQty;
                } else if (status === "in_transit") {
                  // 检查是否延期
                  const deliveryDate = new Date(order.expected_delivery_date);
                  const today = new Date();
                  if (deliveryDate < today) {
                    delayedQty += orderQty;
                  } else {
                    inTransitQty += orderQty;
                  }
                }
              });

              const minQty = Math.min(
                arrivedQty + inTransitQty + delayedQty,
                totalQty
              );
              stats.arrived += Math.min(arrivedQty, minQty);
              stats.inTransit += Math.min(inTransitQty, minQty - arrivedQty);
              stats.delayed += Math.min(delayedQty, minQty - arrivedQty - inTransitQty);
            }
          });

          // 计算齐套率
          const readyRate = calculateReadinessRate(stats.arrived, stats.total);

          // 识别关键材料
          const criticalMaterials = bomItems.
          filter((item) => item.is_critical).
          map((item) => ({
            ...item,
            status: getItemStatus(item, purchaseOrders)
          }));

          // 计算计划装配日期
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
            id: project.project_code || project.id?.toString(),
            name: project.project_name || "",
            planAssemblyDate: planAssemblyDate.split("T")[0] || "",
            daysUntilAssembly,
            materialStats: stats,
            readyRate,
            criticalMaterials
          });
        } catch (fallbackErr) {
          console.error(
            `Failed to calculate materials for project ${project.id}:`,
            fallbackErr
          );
        }
      }

      setProjectMaterials(projectMaterialsData);
    } catch (err) {
      console.error("Failed to load project materials:", err);
      setError("加载物料数据失败");
      setProjectMaterials([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取材料状态
  const getItemStatus = (item, orders) => {
    const relatedOrders = orders.filter((order) => order.material_item === item.id);
    if (relatedOrders.length === 0) {return "not_ordered";}

    const hasDelivered = relatedOrders.some((order) => order.status === "delivered");
    const hasInTransit = relatedOrders.some((order) => order.status === "in_transit");
    const hasDelayed = relatedOrders.some(
      (order) =>
      order.status === "in_transit" &&
      new Date(order.expected_delivery_date) < new Date()
    );

    if (hasDelivered) {return "arrived";}
    if (hasDelayed) {return "delayed";}
    if (hasInTransit) {return "in_transit";}
    return "not_ordered";
  };

  // 加载趋势数据
  const loadTrendData = useCallback(async () => {
    try {
      setLoadingTrend(true);
      const response = await purchaseApi.kitRate.trend({
        group_by: trendPeriod
      });
      const trendResponse = response.data || {};
      setTrendData(trendResponse.trend_data || []);
    } catch (err) {
      console.error("Failed to load trend data:", err);
      // 使用模拟数据
      const days = trendPeriod === "daily" ? 7 : trendPeriod === "weekly" ? 8 : 12;
      const mockTrend = Array.from({ length: days }, (_, i) => ({
        period: new Date(Date.now() - (days - i - 1) * 24 * 60 * 60 * 1000).toLocaleDateString(),
        kit_rate: Math.floor(Math.random() * 20) + 75,
        on_time_rate: Math.floor(Math.random() * 25) + 70,
        quality_rate: Math.floor(Math.random() * 10) + 90
      }));
      setTrendData(mockTrend);
    } finally {
      setLoadingTrend(false);
    }
  }, [trendPeriod]);

  // 过滤后的项目
  const filteredProjects = useMemo(() => {
    let filtered = projectMaterials;

    if (searchQuery) {
      filtered = filtered.filter(
        (p) =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.id.toLowerCase().includes(searchQuery.toLowerCase())
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
    loadTrendData();
  }, [loadProjectMaterials, loadTrendData]);

  // 项目卡片组件
  function ProjectMaterialCard({ project }) {
    const [expanded, setExpanded] = useState(false);
    const stats = project.materialStats;
    const isAtRisk = project.readyRate < 80 || stats.delayed > 5;

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
              onClick={() => setExpanded(!expanded)}>

              {expanded ? "收起" : "详情"}
            </Button>
          </div>

          {expanded &&
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-4 pt-4 border-t border-slate-700">

              <h4 className="text-sm font-medium text-white mb-3">关键物料</h4>
              <div className="space-y-2">
                {project.criticalMaterials.map((material, index) =>
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-slate-900/50 rounded">

                    <span className="text-sm text-slate-300">
                      {material.name || material.part_number}
                    </span>
                    <Badge
                  variant="outline"
                  className={cn(
                    "border",
                    getMaterialStatus(material.status).borderColor,
                    getMaterialStatus(material.status).textColor
                  )}>

                      {getMaterialStatus(material.status).label}
                    </Badge>
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
        title="材料分析"
        description="项目材料齐套性分析、风险评估和性能监控"
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


      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="overview">统计概览</TabsTrigger>
          <TabsTrigger value="details">项目详情</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <MaterialStatsOverview
            projects={filteredProjects}
            materials={[]}
            loading={loading}
            onRefresh={() => setRefreshKey((prev) => prev + 1)} />

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