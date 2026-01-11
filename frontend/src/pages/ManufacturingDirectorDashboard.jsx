/**
 * Manufacturing Director Dashboard - Executive dashboard for manufacturing director
 * Features: Manufacturing center management, Production planning approval, Resource coordination
 * Departments: Production, Customer Service, Warehouse, Shipping
 * Core Functions: Production plan approval, Resource coordination, Multi-department management
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Factory,
  Users,
  Package,
  Truck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Calendar,
  ClipboardCheck,
  Activity,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  ChevronRight,
  Wrench,
  Headphones,
  Warehouse,
  Ship,
  FileText,
  UserCheck,
  Box,
  PackageCheck,
  PackageX,
  MapPin,
  Timer,
  Award,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Input,
} from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  productionApi,
  shortageApi,
  serviceApi,
  materialApi,
  businessSupportApi,
} from "../services/api";
import CultureWallCarousel from "../components/culture/CultureWallCarousel";
import { ApiIntegrationError } from "../components/ui";

// Mock workshops data - 已移除，使用真实API

// Mock production plans pending approval - 已移除，使用真实API

// Mock customer service cases - 已移除，使用真实API

// Mock warehouse alerts - 已移除，使用真实API

// Mock shipping orders - 已移除，使用真实API

export default function ManufacturingDirectorDashboard() {
  // 状态定义
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTab, setSelectedTab] = useState("overview");
  const [productionStats, setProductionStats] = useState(null);
  const [serviceStats, setServiceStats] = useState(null);
  const [warehouseStats, setWarehouseStats] = useState(null);
  const [shippingStats, setShippingStats] = useState({
    pendingShipments: 0,
    shippedToday: 0,
    onTimeShippingRate: 0,
    inTransit: 0,
    avgShippingTime: 0,
  });
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [workshopCards, setWorkshopCards] = useState([]);
  const [dailyError, setDailyError] = useState(null);
  const [productionDaily, setProductionDaily] = useState(null);
  const [shortageDaily, setShortageDaily] = useState(null);
  const [loadingDaily, setLoadingDaily] = useState(false);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="制造总监工作台"
        description="制造中心全面管理 | 生产计划审批 | 资源协调"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              运营报表
            </Button>
            <Button className="flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4" />
              审批中心
            </Button>
          </motion.div>
        }
      />

      {/* 文化墙滚动播放 */}
      <motion.div variants={fadeIn}>
        <CultureWallCarousel
          autoPlay={true}
          interval={5000}
          showControls={true}
          showIndicators={true}
          height="400px"
          onItemClick={(item) => {
            // 点击项目时的处理，可以跳转到详情页或文化墙页面
            if (item.category === "GOAL") {
              // 跳转到个人目标页面
              window.location.href = "/personal-goals";
            } else {
              // 跳转到文化墙详情页
              window.location.href = `/culture-wall?item=${item.id}`;
            }
          }}
        />
      </motion.div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
        <div>
          {selectedDate
            ? `当前日期：${selectedDate}`
            : "显示最新生成的日报数据"}
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-slate-900/50 border-slate-700 text-sm"
          />
          {selectedDate && (
            <Button
              variant="ghost"
              className="text-slate-300"
              onClick={() => setSelectedDate("")}
            >
              清空
            </Button>
          )}
        </div>
      </div>

      {(dailyError || productionDaily || shortageDaily || loadingDaily) && (
        <div className="space-y-3">
          {dailyError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {dailyError}
            </div>
          )}
          {(productionDaily || shortageDaily) && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {productionDaily && (
                <Card className="bg-slate-900/60 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Activity className="w-5 h-5 text-emerald-400" />
                      今日生产日报
                    </CardTitle>
                    <p className="text-sm text-slate-400">
                      {productionDaily.date}
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-400">完成数量</p>
                        <p className="text-3xl font-semibold text-white">
                          {productionDaily.overall?.completed_qty ?? 0}
                        </p>
                        <p className="text-xs text-slate-500">
                          计划 {productionDaily.overall?.plan_qty ?? 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400">完成率</p>
                        <p className="text-3xl font-semibold text-emerald-400">
                          {(
                            productionDaily.overall?.completion_rate ?? 0
                          ).toFixed(1)}
                          %
                        </p>
                        <Progress
                          value={productionDaily.overall?.completion_rate || 0}
                          className="h-2 mt-2"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-400">
                          实工 / 计划工时
                        </p>
                        <p className="text-lg text-white">
                          {productionDaily.overall?.actual_hours ?? 0}h /{" "}
                          {productionDaily.overall?.plan_hours ?? 0}h
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400">到岗 / 应到</p>
                        <p className="text-lg text-white">
                          {productionDaily.overall?.actual_attend ?? 0} /{" "}
                          {productionDaily.overall?.should_attend ?? 0}
                        </p>
                      </div>
                    </div>
                    {productionDaily.overall?.summary && (
                      <p className="text-sm text-slate-300">
                        {productionDaily.overall.summary}
                      </p>
                    )}
                  </CardContent>
                </Card>
              )}
              {shortageDaily && (
                <Card className="bg-slate-900/60 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                      缺料日报
                    </CardTitle>
                    <p className="text-sm text-slate-400">
                      {shortageDaily.date}
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-400">新增预警</p>
                        <p className="text-3xl font-semibold text-amber-400">
                          {shortageDaily.alerts?.new ?? 0}
                        </p>
                        <p className="text-xs text-slate-500">
                          待处理 {shortageDaily.alerts?.pending ?? 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400">逾期预警</p>
                        <p className="text-3xl font-semibold text-red-400">
                          {shortageDaily.alerts?.overdue ?? 0}
                        </p>
                        <p className="text-xs text-slate-500">
                          已解决 {shortageDaily.alerts?.resolved ?? 0}
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm text-slate-300">
                      <div>
                        <p>齐套率</p>
                        <p className="text-lg text-white">
                          {shortageDaily.kit?.kit_rate ?? 0}%
                        </p>
                        <p className="text-xs text-slate-500">
                          {shortageDaily.kit?.complete_count ?? 0}/
                          {shortageDaily.kit?.total_work_orders ?? 0}{" "}
                          工单完成齐套
                        </p>
                      </div>
                      <div>
                        <p>准时到货率</p>
                        <p className="text-lg text-white">
                          {shortageDaily.arrivals?.on_time_rate ?? 0}%
                        </p>
                        <p className="text-xs text-slate-500">
                          实到 {shortageDaily.arrivals?.actual ?? 0} / 计划{" "}
                          {shortageDaily.arrivals?.expected ?? 0}
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-slate-500">
                      平均响应{" "}
                      {shortageDaily.response?.avg_response_minutes ?? 0} 分钟，
                      平均解决 {shortageDaily.response?.avg_resolve_hours ?? 0}{" "}
                      小时
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-xs text-slate-400">
                      {["level1", "level2", "level3", "level4"].map(
                        (levelKey, idx) => {
                          const labels = ["一级", "二级", "三级", "四级"];
                          return (
                            <div
                              key={levelKey}
                              className="rounded bg-slate-800/60 px-2 py-1 text-center"
                            >
                              <p>{labels[idx]}</p>
                              <p className="text-base text-white">
                                {shortageDaily.alerts?.levels?.[levelKey] ?? 0}
                              </p>
                            </div>
                          );
                        },
                      )}
                    </div>
                    <div className="text-xs text-slate-500">
                      停工 {shortageDaily.stoppage?.count ?? 0} 次 ·{" "}
                      {shortageDaily.stoppage?.hours ?? 0} 小时
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
          {loadingDaily && (
            <div className="text-sm text-slate-400">
              正在同步最新日报数据...
            </div>
          )}
        </div>
      )}

      {/* Key Statistics - 8 column grid for 4 departments */}
      {(productionStats || serviceStats || warehouseStats || shippingStats) && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-8"
        >
          {/* Production Department Stats */}
          {productionStats && (
            <>
              <StatCard
                title="生产项目"
                value={productionStats.inProductionProjects || 0}
                subtitle={`今日产出 ${productionStats.todayOutput || 0}`}
                trend={5.2}
                icon={Factory}
                color="text-blue-400"
                bg="bg-blue-500/10"
              />
              <StatCard
                title="完成率"
                value={`${productionStats.completionRate || 0}%`}
                subtitle="生产完成率"
                icon={Target}
                color="text-emerald-400"
                bg="bg-emerald-500/10"
              />
            </>
          )}

          {/* Customer Service Department Stats */}
          {serviceStats && (
            <>
              <StatCard
                title="服务案例"
                value={serviceStats.activeCases || 0}
                subtitle={`今日解决 ${serviceStats.resolvedToday || 0}`}
                trend={8.5}
                icon={Headphones}
                color="text-purple-400"
                bg="bg-purple-500/10"
              />
              <StatCard
                title="满意度"
                value={`${(serviceStats.customerSatisfaction || 0).toFixed(1)}%`}
                subtitle="客户满意度"
                icon={Award}
                color="text-amber-400"
                bg="bg-amber-500/10"
              />
            </>
          )}

          {/* Warehouse Department Stats */}
          {warehouseStats && (
            <>
              <StatCard
                title="库存SKU"
                value={warehouseStats.totalItems || 0}
                subtitle={`在库 ${warehouseStats.inStockItems || 0}`}
                trend={-2.3}
                icon={Warehouse}
                color="text-cyan-400"
                bg="bg-cyan-500/10"
              />
              <StatCard
                title="周转率"
                value={`${(warehouseStats.inventoryTurnover || 0).toFixed(1)}x`}
                subtitle="库存周转"
                icon={Activity}
                color="text-indigo-400"
                bg="bg-indigo-500/10"
              />
            </>
          )}

          {/* Shipping Department Stats */}
          <StatCard
            title="待发货"
            value={shippingStats.pendingShipments}
            subtitle={`今日已发 ${shippingStats.shippedToday}`}
            trend={12.5}
            icon={Ship}
            color="text-orange-400"
            bg="bg-orange-500/10"
          />
          <StatCard
            title="准时率"
            value={`${shippingStats.onTimeShippingRate.toFixed(1)}%`}
            subtitle="发货准时率"
            icon={CheckCircle2}
            color="text-green-400"
            bg="bg-green-500/10"
          />
        </motion.div>
      )}

      {/* Main Content Tabs */}
      <Tabs
        value={selectedTab}
        onValueChange={setSelectedTab}
        className="space-y-6"
      >
        <TabsList className="bg-surface-50 border-white/10">
          <TabsTrigger value="overview">综合概览</TabsTrigger>
          <TabsTrigger value="production">生产部</TabsTrigger>
          <TabsTrigger value="service">客服部</TabsTrigger>
          <TabsTrigger value="warehouse">仓储部</TabsTrigger>
          <TabsTrigger value="shipping">发货部</TabsTrigger>
          <TabsTrigger value="approvals">审批事项</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Production Overview */}
            {productionStats && (
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Factory className="w-5 h-5 text-blue-400" />
                    生产部概览
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">车间负荷</span>
                      <span className="text-white font-semibold">
                        {productionStats.workshopLoad || 0}%
                      </span>
                    </div>
                    <Progress
                      value={productionStats.workshopLoad || 0}
                      className="h-2"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                    <div>
                      <p className="text-xs text-slate-400 mb-1">在岗人员</p>
                      <p className="text-lg font-semibold text-white">
                        {productionStats.activeWorkers || 0}/
                        {productionStats.totalWorkers || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1">在用工位</p>
                      <p className="text-lg font-semibold text-white">
                        {productionStats.activeWorkstations || 0}/
                        {productionStats.totalWorkstations || 0}
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-4" size="sm">
                    <Eye className="w-4 h-4 mr-2" />
                    查看详情
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Customer Service Overview */}
            {serviceStats && (
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Headphones className="w-5 h-5 text-purple-400" />
                    客服部概览
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">平均响应时间</span>
                      <span className="text-white font-semibold">
                        {(serviceStats.avgResponseTime || 0).toFixed(1)} 小时
                      </span>
                    </div>
                    <Progress value={95} className="h-2" />
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                    <div>
                      <p className="text-xs text-slate-400 mb-1">待处理</p>
                      <p className="text-lg font-semibold text-white">
                        {serviceStats.pendingCases || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1">在岗工程师</p>
                      <p className="text-lg font-semibold text-white">
                        {serviceStats.activeEngineers || 0}/
                        {serviceStats.totalEngineers || 0}
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-4" size="sm">
                    <Eye className="w-4 h-4 mr-2" />
                    查看详情
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Warehouse & Shipping Overview */}
            {warehouseStats && shippingStats && (
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Package className="w-5 h-5 text-cyan-400" />
                    仓储&发货概览
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">仓储利用率</span>
                      <span className="text-white font-semibold">
                        {(warehouseStats.warehouseUtilization || 0).toFixed(1)}%
                      </span>
                    </div>
                    <Progress
                      value={warehouseStats.warehouseUtilization || 0}
                      className="h-2"
                    />
                    <div className="flex items-center justify-between text-sm pt-2 border-t border-white/10">
                      <span className="text-slate-400">在途订单</span>
                      <span className="text-white font-semibold">
                        {shippingStats.inTransit || 0}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                    <div>
                      <p className="text-xs text-slate-400 mb-1">待入库</p>
                      <p className="text-lg font-semibold text-white">
                        {warehouseStats.pendingInbound || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1">待出库</p>
                      <p className="text-lg font-semibold text-white">
                        {warehouseStats.pendingOutbound || 0}
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-4" size="sm">
                    <Eye className="w-4 h-4 mr-2" />
                    查看详情
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Pending Approvals Quick View */}
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ClipboardCheck className="w-5 h-5 text-amber-400" />
                  待审批事项
                </CardTitle>
                <Badge
                  variant="outline"
                  className="bg-amber-500/20 text-amber-400 border-amber-500/30"
                >
                  {/* 待审批事项数量 - 需要从API获取 */}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* 待审批事项 - 需要从API获取数据 */}
                <div className="text-center py-8 text-slate-500">
                  <p>待审批事项数据需要从API获取</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="production" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Workshop Load */}
            <Card className="lg:col-span-2 bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart3 className="w-5 h-5 text-primary" />
                  车间负荷情况
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {workshopCards.map((workshop, index) => (
                  <motion.div
                    key={workshop.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            "w-3 h-3 rounded-full",
                            workshop.status === "normal"
                              ? "bg-emerald-500"
                              : "bg-amber-500",
                          )}
                        />
                        <h4 className="font-semibold text-white">
                          {workshop.name}
                        </h4>
                        <Badge
                          className={cn(
                            "text-xs",
                            workshop.status === "normal"
                              ? "bg-emerald-500/20 text-emerald-400"
                              : "bg-amber-500/20 text-amber-400",
                          )}
                        >
                          {workshop.status === "normal" ? "正常" : "负荷高"}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-400">负荷率</p>
                        <p className="text-lg font-bold text-white">
                          {workshop.currentLoad}%
                        </p>
                      </div>
                    </div>
                    <Progress
                      value={workshop.currentLoad}
                      className="h-2 mb-3"
                    />
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-slate-400">工位</p>
                        <p className="text-white font-semibold">
                          {workshop.activeWorkstations}/
                          {workshop.totalWorkstations}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400">人员</p>
                        <p className="text-white font-semibold">
                          {workshop.activeWorkers}/{workshop.workers}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400">今日产出</p>
                        <p className="text-white font-semibold">
                          {workshop.todayOutput}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </CardContent>
            </Card>

            {/* Production Stats */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-primary" />
                  生产指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">完成率</p>
                    <p className="text-lg font-bold text-white">
                      {productionStats.completionRate}%
                    </p>
                  </div>
                  <Progress
                    value={productionStats.completionRate}
                    className="h-2"
                  />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">准时交付率</p>
                    <p className="text-lg font-bold text-white">
                      {productionStats.onTimeDeliveryRate}%
                    </p>
                  </div>
                  <Progress
                    value={productionStats.onTimeDeliveryRate}
                    className="h-2"
                  />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在岗人员</p>
                    <p className="text-lg font-bold text-white">
                      {productionStats.activeWorkers}/
                      {productionStats.totalWorkers}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Customer Service Department Tab */}
        <TabsContent value="service" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Active Cases */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Headphones className="w-5 h-5 text-purple-400" />
                  服务案例
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* 服务案例 - 需要从API获取数据 */}
                <div className="text-center text-slate-400 py-8">
                  <Headphones className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>服务案例数据加载中...</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-purple-400" />
                  服务指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">客户满意度</p>
                    <p className="text-lg font-bold text-white">
                      {(serviceStats?.customerSatisfaction || 0).toFixed(1)}%
                    </p>
                  </div>
                  <Progress
                    value={serviceStats.customerSatisfaction}
                    className="h-2"
                  />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">平均响应时间</p>
                    <p className="text-lg font-bold text-white">
                      {serviceStats.avgResponseTime.toFixed(1)} 小时
                    </p>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在岗工程师</p>
                    <p className="text-lg font-bold text-white">
                      {serviceStats.activeEngineers}/
                      {serviceStats.totalEngineers}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Warehouse Department Tab */}
        <TabsContent value="warehouse" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Warehouse Alerts */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  库存预警
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* 仓库预警 - 需要从API获取数据 */}
                <div className="text-center text-slate-400 py-8">
                  <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>仓库预警数据加载中...</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-cyan-400" />
                  仓储指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">仓储利用率</p>
                    <p className="text-lg font-bold text-white">
                      {(warehouseStats?.warehouseUtilization || 0).toFixed(1)}%
                    </p>
                  </div>
                  <Progress
                    value={warehouseStats.warehouseUtilization}
                    className="h-2"
                  />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">库存周转率</p>
                    <p className="text-lg font-bold text-white">
                      {warehouseStats.inventoryTurnover.toFixed(1)}x
                    </p>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在库SKU</p>
                    <p className="text-lg font-bold text-white">
                      {warehouseStats.inStockItems}/{warehouseStats.totalItems}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Shipping Department Tab */}
        <TabsContent value="shipping" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Shipping Orders */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Ship className="w-5 h-5 text-orange-400" />
                  发货订单
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* 发货订单 - 需要从API获取数据 */}
                <div className="text-center py-8 text-slate-500">
                  <p>发货订单数据需要从API获取</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-orange-400" />
                  发货指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {shippingStats ? (
                  <>
                    <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-slate-400">准时发货率</p>
                        <p className="text-lg font-bold text-white">
                          {(shippingStats.onTimeShippingRate || 0).toFixed(1)}%
                        </p>
                      </div>
                      <Progress
                        value={shippingStats.onTimeShippingRate || 0}
                        className="h-2"
                      />
                    </div>
                    <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-slate-400">平均发货时间</p>
                        <p className="text-lg font-bold text-white">
                          {(shippingStats.avgShippingTime || 0).toFixed(1)} 天
                        </p>
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-slate-400">在途订单</p>
                        <p className="text-lg font-bold text-white">
                          {shippingStats.inTransit || 0}
                        </p>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>发货数据需要从API获取</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Approvals Tab */}
        <TabsContent value="approvals" className="space-y-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ClipboardCheck className="w-5 h-5 text-amber-400" />
                  待审批事项
                </CardTitle>
                <Badge
                  variant="outline"
                  className="bg-amber-500/20 text-amber-400 border-amber-500/30"
                >
                  {/* 待审批事项数量 - 需要从API获取 */}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* 待审批事项 - 需要从API获取数据 */}
              {/* {pendingApprovals.map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            item.type === 'production_plan' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                            item.type === 'resource_allocation' && 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                            item.type === 'warehouse_expansion' && 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                          )}
                        >
                          {item.type === 'production_plan' ? '生产计划' : 
                           item.type === 'resource_allocation' ? '资源调配' : '仓储扩容'}
                        </Badge>
                        {item.priority === 'high' && (
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                            紧急
                          </Badge>
                        )}
                      </div>
                      <p className="font-medium text-white text-sm mb-1">
                        {item.projectName || item.title}
                      </p>
                      {item.planCode && (
                        <p className="text-xs text-slate-400 mb-1">
                          {item.planCode} · {item.workshop} · {item.startDate} ~ {item.endDate}
                        </p>
                      )}
                      {item.request && (
                        <p className="text-xs text-slate-400 mb-1">{item.request}</p>
                      )}
                      {item.amount && (
                        <p className="text-xs text-slate-400 mb-1">金额: {formatCurrency(item.amount)}</p>
                      )}
                      <p className="text-xs text-slate-400 mt-2">
                        {item.submitter} · {item.submitTime}
                      </p>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600">
                        审批
                      </Button>
                    </div>
                  </div>
                </div>
              ))} */}
              <div className="text-center py-8 text-slate-500">
                <p>待审批事项数据需要从API获取</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
