/**
 * Fixed Assets Management - Administrative fixed assets management
 * Features: Asset inventory, depreciation calculation, maintenance tracking, asset allocation
 */

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Plus,
  Building2,
  TrendingDown,
  Wrench,
  MapPin,
  User,
  DollarSign,
  Calendar,
  Edit,
  Eye,
  Download } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";
import { cn, formatCurrency } from "../lib/utils";
import { staggerContainer } from "../lib/animations";
import {
  SimpleBarChart,
  MonthlyTrendChart,
  SimplePieChart,
  CategoryBreakdownCard,
  TrendComparisonCard } from
"../components/administrative/StatisticsCharts";
import { adminApi } from "../services/api";

// Mock data - 已移除，使用真实API

export default function FixedAssetsManagement() {
  const [searchText, setSearchText] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [_loading, setLoading] = useState(false);
  const [_error, setError] = useState(null);
  const [assets, setAssets] = useState([]);

  // Fetch assets from API
  useEffect(() => {
    const fetchAssets = async () => {
      setLoading(true);
      try {
        const res = await adminApi.assets.list();
        if (res.data?.items) {
          setAssets(res.data.items);
        } else if (Array.isArray(res.data)) {
          setAssets(res.data);
        }
      } catch (_err) {
        console.log("Assets API unavailable");
        setError("加载固定资产数据失败");
      }
      setLoading(false);
    };
    fetchAssets();
  }, []);

  const filteredAssets = useMemo(() => {
    return (assets || []).filter((asset) => {
      const matchSearch =
      asset.name?.toLowerCase().includes(searchText.toLowerCase()) ||
      asset.assetNo?.includes(searchText);
      const matchCategory =
      categoryFilter === "all" || asset.category === categoryFilter;
      const matchStatus =
      statusFilter === "all" || asset.status === statusFilter;
      return matchSearch && matchCategory && matchStatus;
    });
  }, [assets, searchText, categoryFilter, statusFilter]);

  const stats = useMemo(() => {
    const total = assets.length;
    const totalValue = (assets || []).reduce((sum, a) => sum + (a.currentValue || 0), 0);
    const totalDepreciation = (assets || []).reduce(
      (sum, a) => sum + (a.depreciation || 0),
      0
    );
    const maintenance = (assets || []).filter(
      (a) => a.status === "maintenance"
    ).length;
    return { total, totalValue, totalDepreciation, maintenance };
  }, [assets]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="固定资产管理"
        description="固定资产清单、折旧计算、维护跟踪、资产分配"
        actions={
        <div className="flex gap-2">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              新增资产
            </Button>
        </div>
        } />


      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">资产总数</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {stats.total}
                </p>
              </div>
              <Building2 className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">资产总值</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(stats.totalValue)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">累计折旧</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {formatCurrency(stats.totalDepreciation)}
                </p>
              </div>
              <TrendingDown className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">维护中</p>
                <p className="text-2xl font-bold text-red-400 mt-1">
                  {stats.maintenance}
                </p>
              </div>
              <Wrench className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="assets" className="space-y-4">
        <TabsList>
          <TabsTrigger value="assets">资产清单</TabsTrigger>
          <TabsTrigger value="depreciation">折旧管理</TabsTrigger>
          <TabsTrigger value="maintenance">维护记录</TabsTrigger>
          <TabsTrigger value="allocation">资产分配</TabsTrigger>
        </TabsList>

        <TabsContent value="assets" className="space-y-4">
          {/* Statistics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>资产分类价值分布</CardTitle>
              </CardHeader>
              <CardContent>
                <CategoryBreakdownCard
                  title="资产价值"
                  data={[
                  {
                    label: "办公家具",
                    value: assets.
                    filter((a) => a.category === "办公家具").
                    reduce((sum, a) => sum + a.currentValue, 0),
                    color: "#3b82f6"
                  },
                  {
                    label: "办公设备",
                    value: assets.
                    filter((a) => a.category === "办公设备").
                    reduce((sum, a) => sum + a.currentValue, 0),
                    color: "#10b981"
                  }]
                  }
                  total={stats.totalValue}
                  formatValue={formatCurrency} />

              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>资产价值趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <MonthlyTrendChart
                  data={[
                  { month: "2024-10", amount: 12000000 },
                  { month: "2024-11", amount: 12200000 },
                  { month: "2024-12", amount: 12350000 },
                  { month: "2025-01", amount: stats.totalValue }]
                  }
                  valueKey="amount"
                  labelKey="month"
                  height={150} />

              </CardContent>
            </Card>
          </div>

          {/* Trend Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TrendComparisonCard
              title="资产总值"
              current={stats.totalValue}
              previous={12350000}
              formatValue={formatCurrency} />

            <TrendComparisonCard
              title="累计折旧"
              current={stats.totalDepreciation}
              previous={1200000}
              formatValue={formatCurrency} />

            <TrendComparisonCard
              title="维护中资产"
              current={stats.maintenance}
              previous={12} />

          </div>

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-4">
                <Input
                  placeholder="搜索资产名称、编号..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="flex-1" />

                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">

                  <option value="all">全部分类</option>
                  <option value="办公家具">办公家具</option>
                  <option value="办公设备">办公设备</option>
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">

                  <option value="all">全部状态</option>
                  <option value="in_use">使用中</option>
                  <option value="maintenance">维护中</option>
                  <option value="idle">闲置</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Assets List */}
          <div className="grid grid-cols-1 gap-4">
            {(filteredAssets || []).map((asset) =>
            <Card key={asset.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {asset.name}
                        </h3>
                        <Badge variant="outline">{asset.category}</Badge>
                        <Badge
                        variant="outline"
                        className={cn(
                          asset.status === "in_use" &&
                          "bg-green-500/20 text-green-400 border-green-500/30",
                          asset.status === "maintenance" &&
                          "bg-amber-500/20 text-amber-400 border-amber-500/30"
                        )}>

                          {asset.status === "in_use" ? "使用中" : "维护中"}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                        <div>
                          <p className="text-slate-400">资产编号</p>
                          <p className="text-white font-medium">
                            {asset.assetNo}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">位置</p>
                          <p className="text-white font-medium">
                            {asset.location}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">负责人</p>
                          <p className="text-white font-medium">
                            {asset.responsible}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">部门</p>
                          <p className="text-white font-medium">
                            {asset.department}
                          </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">购置价格</p>
                          <p className="text-white font-medium">
                            {formatCurrency(asset.purchasePrice)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">当前价值</p>
                          <p className="text-emerald-400 font-medium">
                            {formatCurrency(asset.currentValue)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">累计折旧</p>
                          <p className="text-amber-400 font-medium">
                            {formatCurrency(asset.depreciation)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">购置日期</p>
                          <p className="text-white font-medium">
                            {asset.purchaseDate}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
            </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="depreciation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>折旧管理</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(assets || []).map((asset) => {
                  const yearsInUse = Math.floor(
                    (new Date() - new Date(asset.purchaseDate)) / (
                    365 * 24 * 60 * 60 * 1000)
                  );
                  const annualDepreciation =
                  asset.purchasePrice * (asset.depreciationRate / 100);
                  return (
                    <div
                      key={asset.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">

                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-medium text-white mb-1">
                            {asset.name}
                          </h3>
                          <p className="text-sm text-slate-400">
                            {asset.assetNo}
                          </p>
                        </div>
                        <Badge variant="outline">{asset.category}</Badge>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                        <div>
                          <p className="text-slate-400">购置价格</p>
                          <p className="text-white font-medium">
                            {formatCurrency(asset.purchasePrice)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">当前价值</p>
                          <p className="text-emerald-400 font-medium">
                            {formatCurrency(asset.currentValue)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">累计折旧</p>
                          <p className="text-amber-400 font-medium">
                            {formatCurrency(asset.depreciation)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">使用年限</p>
                          <p className="text-white font-medium">
                            {yearsInUse} 年
                          </p>
                        </div>
                      </div>
                      <div className="text-xs text-slate-500">
                        折旧率: {asset.depreciationRate}% · 年折旧额:{" "}
                        {formatCurrency(annualDepreciation)}
                      </div>
                    </div>);

                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="maintenance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>维护记录</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {assets.
                filter((a) => a.status === "maintenance").
                map((asset) =>
                <div
                  key={asset.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">

                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="font-medium text-white">
                              {asset.name}
                            </span>
                            <Badge
                          variant="outline"
                          className="bg-amber-500/20 text-amber-400 border-amber-500/30">

                              维护中
                            </Badge>
                          </div>
                          <div className="text-sm text-slate-400">
                            资产编号: {asset.assetNo} · 位置: {asset.location}
                          </div>
                          <div className="text-xs text-slate-500 mt-2">
                            负责人: {asset.responsible} · 部门:{" "}
                            {asset.department}
                          </div>
                        </div>
                      </div>
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="allocation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>资产分配</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(assets || []).map((asset) =>
                <div
                  key={asset.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">

                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-medium text-white">
                            {asset.name}
                          </span>
                          <Badge variant="outline">{asset.category}</Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-slate-400">分配位置</p>
                            <p className="text-white font-medium">
                              {asset.location}
                            </p>
                          </div>
                          <div>
                            <p className="text-slate-400">负责人</p>
                            <p className="text-white font-medium">
                              {asset.responsible}
                            </p>
                          </div>
                          <div>
                            <p className="text-slate-400">所属部门</p>
                            <p className="text-white font-medium">
                              {asset.department}
                            </p>
                          </div>
                        </div>
                        <div className="text-xs text-slate-500 mt-2">
                          资产编号: {asset.assetNo} · 分配日期:{" "}
                          {asset.purchaseDate}
                        </div>
                      </div>
                    </div>
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>);

}