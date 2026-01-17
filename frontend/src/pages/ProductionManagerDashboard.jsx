/**
 * Production Manager Dashboard - Refactored
 * 生产经理仪表板 - 重构版本
 * Features: Production overview, workshop management, production plans, work orders, team management
 */

import { useState, useEffect, useCallback, useMemo as _useMemo } from "react";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Factory,
  Calendar,
  Users,
  Wrench,
  AlertTriangle,
  BarChart3,
  Settings,
  TrendingUp,
  Package,
  Target,
  Activity,
  Zap } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button } from
"../components/ui";
import {
  productionApi,
  projectApi as _projectApi,
  materialApi as _materialApi,
  alertApi } from
"../services/api";
import { ApiIntegrationError } from "../components/ui";
import {
  ProductionStatsOverview,
  ProductionLineManager,
  PRODUCTION_PLAN_STATUS,
  WORK_ORDER_STATUS,
  ALERT_LEVEL,
  ALERT_STATUS,
  RANKING_TYPE,
  TIME_RANGE_FILTERS,
  getStatusColor as _getStatusColor,
  getStatusLabel as _getStatusLabel,
  getPriorityColor as _getPriorityColor,
  getAlertLevelConfig,
  getAlertStatusConfig } from
"../components/production";

export default function ProductionManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // API数据状态
  const [productionStats, setProductionStats] = useState({
    inProductionProjects: 0,
    todayOutput: 0,
    completionRate: 0,
    onTimeDeliveryRate: 0,
    totalWorkers: 0,
    activeWorkers: 0,
    totalWorkstations: 0,
    activeWorkstations: 0
  });
  const [workshops, setWorkshops] = useState([]);
  const [_productionPlans, setProductionPlans] = useState([]);
  const [_workOrders, setWorkOrders] = useState([]);
  const [productionDaily, setProductionDaily] = useState(null);
  const [alerts, setAlerts] = useState([]);

  // 数据加载函数
  const loadProductionStats = useCallback(async () => {
    try {
      const response = await productionApi.getProductionStats();
      setProductionStats(response.data);
    } catch (err) {
      console.error('Failed to load production stats:', err);
    }
  }, []);

  const loadWorkshops = useCallback(async () => {
    try {
      const response = await productionApi.getWorkshops();
      setWorkshops(response.data || []);
    } catch (err) {
      console.error('Failed to load workshops:', err);
      setWorkshops([]);
    }
  }, []);

  const loadProductionPlans = useCallback(async () => {
    try {
      const response = await productionApi.getProductionPlans();
      setProductionPlans(response.data || []);
    } catch (err) {
      console.error('Failed to load production plans:', err);
      setProductionPlans([]);
    }
  }, []);

  const loadWorkOrders = useCallback(async () => {
    try {
      const response = await productionApi.getWorkOrders();
      setWorkOrders(response.data || []);
    } catch (err) {
      console.error('Failed to load work orders:', err);
      setWorkOrders([]);
    }
  }, []);

  const loadProductionDaily = useCallback(async () => {
    try {
      const response = await productionApi.getProductionDaily();
      setProductionDaily(response.data);
    } catch (err) {
      console.error('Failed to load production daily:', err);
    }
  }, []);

  const loadAlerts = useCallback(async () => {
    try {
      const response = await alertApi.getAlerts({ type: 'production' });
      setAlerts(response.data || []);
    } catch (err) {
      console.error('Failed to load alerts:', err);
      setAlerts([]);
    }
  }, []);

  // 初始数据加载
  useEffect(() => {
    const loadAllData = async () => {
      setLoading(true);
      try {
        await Promise.all([
        loadProductionStats(),
        loadWorkshops(),
        loadProductionPlans(),
        loadWorkOrders(),
        loadProductionDaily(),
        loadAlerts()]
        );
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadAllData();
  }, [
  loadProductionStats,
  loadWorkshops,
  loadProductionPlans,
  loadWorkOrders,
  loadProductionDaily,
  loadAlerts]
  );

  // 定时刷新数据
  useEffect(() => {
    const interval = setInterval(() => {
      loadProductionStats();
      loadProductionDaily();
      loadAlerts();
    }, 300000); // 5分钟刷新一次

    return () => clearInterval(interval);
  }, [loadProductionStats, loadProductionDaily, loadAlerts]);

  // 刷新所有数据
  const handleRefresh = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
      loadProductionStats(),
      loadWorkshops(),
      loadProductionPlans(),
      loadWorkOrders(),
      loadProductionDaily(),
      loadAlerts()]
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [
  loadProductionStats,
  loadWorkshops,
  loadProductionPlans,
  loadWorkOrders,
  loadProductionDaily,
  loadAlerts]
  );

  // 处理生产线操作
  const handleLineAction = useCallback(async (lineId, action) => {
    try {
      await productionApi.updateWorkshopStatus(lineId, action);
      await loadWorkshops(); // 刷新生产线数据
    } catch (err) {
      console.error('Failed to update workshop status:', err);
      setError(err.message);
    }
  }, [loadWorkshops]);

  // 处理生产线编辑
  const handleEditLine = useCallback((workshop) => {
    // TODO: 打开编辑对话框
    console.log('Edit workshop:', workshop);
  }, []);

  // Tab配置
  const tabs = [
  { value: "overview", label: "生产概览", icon: LayoutDashboard },
  { value: "workshops", label: "生产线管理", icon: Factory },
  { value: "plans", label: "生产计划", icon: Calendar },
  { value: "orders", label: "工单管理", icon: Wrench },
  { value: "alerts", label: "生产预警", icon: AlertTriangle }];


  // 渲染错误状态
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ApiIntegrationError
          title="生产系统加载失败"
          description="无法连接到生产管理系统，请检查网络连接或联系管理员。"
          onRetry={handleRefresh} />

      </div>);

  }

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* 页面头部 */}
      <PageHeader
        title="生产管理"
        subtitle="实时监控和管理生产活动"
        icon={Factory}
        actions={[
        {
          label: "刷新数据",
          icon: Activity,
          onClick: handleRefresh,
          loading: loading
        },
        {
          label: "生产设置",
          icon: Settings,
          onClick: () => console.log('Open settings')
        }]
        } />


      {/* 主要内容区域 */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <TabsTrigger key={tab.value} value={tab.value} className="flex items-center gap-2">
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </TabsTrigger>);

          })}
        </TabsList>

        {/* 生产概览 */}
        <TabsContent value="overview" className="space-y-6">
          <ProductionStatsOverview
            productionStats={productionStats}
            productionDaily={productionDaily}
            loading={loading}
            onRefresh={handleRefresh} />

        </TabsContent>

        {/* 生产线管理 */}
        <TabsContent value="workshops" className="space-y-6">
          <ProductionLineManager
            workshops={workshops}
            loading={loading}
            onLineAction={handleLineAction}
            onEditLine={handleEditLine}
            onViewDetails={(workshop) => console.log('View details:', workshop)} />

        </TabsContent>

        {/* 生产计划 */}
        <TabsContent value="plans" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-blue-600" />
                生产计划管理
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">生产计划组件</h3>
                <p className="text-gray-600">生产计划管理功能正在开发中...</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 工单管理 */}
        <TabsContent value="orders" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="w-5 h-5 text-green-600" />
                工单管理
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Wrench className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">工单管理组件</h3>
                <p className="text-gray-600">工单管理功能正在开发中...</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 生产预警 */}
        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                生产预警
              </CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length > 0 ?
              <div className="space-y-3">
                  {alerts.slice(0, 10).map((alert) => {
                  const levelConfig = getAlertLevelConfig(alert.level);
                  const statusConfig = getAlertStatusConfig(alert.status);

                  return (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center justify-between p-4 border rounded-lg">

                        <div className="flex items-center gap-3">
                          <span className="text-xl">{levelConfig.icon}</span>
                          <div>
                            <div className="font-medium">{alert.title}</div>
                            <div className="text-sm text-gray-600">{alert.message}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={statusConfig.className}>
                            {statusConfig.label}
                          </Badge>
                          <Badge className={levelConfig.color.replace('bg-', 'bg-') + ' text-white'}>
                            {levelConfig.label}
                          </Badge>
                        </div>
                      </motion.div>);

                })}
                </div> :

              <div className="text-center py-8">
                  <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">暂无预警信息</h3>
                  <p className="text-gray-600">当前没有生产预警信息</p>
                </div>
              }
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>);

}