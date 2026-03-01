/**
 * Office Supplies Management - Administrative office supplies management
 * Features: Inventory management, purchase orders, supplier management, low stock alerts
 */

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  Search,
  Filter,
  Plus,
  Package,
  AlertTriangle,
  ShoppingCart,
  TrendingUp,
  TrendingDown,
  Edit,
  Eye,
  Trash2,
  Download,
  Upload,
  BarChart3,
  Calendar,
  Building2 } from
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
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody } from
"../components/ui";
import { cn, formatCurrency, formatDate as _formatDate } from "../lib/utils";
import { fadeIn as _fadeIn, staggerContainer } from "../lib/animations";
import {
  SimpleBarChart,
  MonthlyTrendChart,
  CategoryBreakdownCard } from
"../components/administrative/StatisticsCharts";
import { adminApi } from "../services/api";

// Mock data - 已移除，使用真实API

export default function OfficeSuppliesManagement() {
  const [selectedItem, setSelectedItem] = useState(null);
  const [showItemDetail, setShowItemDetail] = useState(false);
  const mockPurchaseOrders = [];
  const [searchText, setSearchText] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [_loading, setLoading] = useState(false);
  const [_error, _setError] = useState(null);
  const [supplies, setSupplies] = useState([]);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await adminApi.supplies.list();
        if (res.data?.items) {
          setSupplies(res.data.items);
        } else if (Array.isArray(res.data)) {
          setSupplies(res.data);
        }
      } catch (_err) {
        console.log("Office supplies API unavailable, using mock data");
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const filteredSupplies = useMemo(() => {
    return (supplies || []).filter((item) => {
      const matchSearch = item.name.
      toLowerCase().
      includes(searchText.toLowerCase());
      const matchCategory =
      categoryFilter === "all" || item.category === categoryFilter;
      const matchStatus =
      statusFilter === "all" || item.status === statusFilter;
      return matchSearch && matchCategory && matchStatus;
    });
  }, [supplies, searchText, categoryFilter, statusFilter]);

  const stats = useMemo(() => {
    const totalItems = supplies.length;
    const lowStockItems = (supplies || []).filter((s) => s.status === "low").length;
    const totalValue = (supplies || []).reduce((sum, s) => sum + s.totalValue, 0);
    return { totalItems, lowStockItems, totalValue };
  }, [supplies]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="办公用品管理"
        description="办公用品库存管理、采购订单、供应商管理"
        actions={
        <div className="flex gap-2">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
            <Button variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              导入
            </Button>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              新建采购订单
            </Button>
        </div>
        } />


      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">物品总数</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {stats.totalItems}
                </p>
              </div>
              <Package className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">低库存物品</p>
                <p className="text-2xl font-bold text-red-400 mt-1">
                  {stats.lowStockItems}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">库存总值</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(stats.totalValue)}
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">待处理订单</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {mockPurchaseOrders.length}
                </p>
              </div>
              <ShoppingCart className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="inventory" className="space-y-4">
        <TabsList>
          <TabsTrigger value="inventory">库存管理</TabsTrigger>
          <TabsTrigger value="orders">采购订单</TabsTrigger>
          <TabsTrigger value="suppliers">供应商</TabsTrigger>
        </TabsList>

        <TabsContent value="inventory" className="space-y-4">
          {/* Statistics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>分类库存价值分布</CardTitle>
              </CardHeader>
              <CardContent>
                <CategoryBreakdownCard
                  title="库存价值"
                  data={[
                  {
                    label: "办公耗材",
                    value: supplies.
                    filter((s) => s.category === "办公耗材").
                    reduce((sum, s) => sum + s.totalValue, 0),
                    color: "#3b82f6"
                  },
                  {
                    label: "办公文具",
                    value: supplies.
                    filter((s) => s.category === "办公文具").
                    reduce((sum, s) => sum + s.totalValue, 0),
                    color: "#10b981"
                  }]
                  }
                  total={stats.totalValue}
                  formatValue={formatCurrency} />

              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>月度采购趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <MonthlyTrendChart
                  data={[
                  { month: "2024-10", amount: 42000 },
                  { month: "2024-11", amount: 38000 },
                  { month: "2024-12", amount: 45000 },
                  { month: "2025-01", amount: 45000 }]
                  }
                  valueKey="amount"
                  labelKey="month"
                  height={150} />

              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-4">
                <Input
                  placeholder="搜索物品名称..."
                  value={searchText || "unknown"}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="flex-1" />

                <select
                  value={categoryFilter || "unknown"}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">

                  <option value="all">全部分类</option>
                  <option value="办公耗材">办公耗材</option>
                  <option value="办公文具">办公文具</option>
                </select>
                <select
                  value={statusFilter || "unknown"}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">

                  <option value="all">全部状态</option>
                  <option value="low">低库存</option>
                  <option value="normal">正常</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Items List */}
          <div className="grid grid-cols-1 gap-4">
            {(filteredSupplies || []).map((item) =>
            <Card key={item.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {item.name}
                        </h3>
                        <Badge
                        variant="outline"
                        className={cn(
                          item.status === "low" &&
                          "bg-red-500/20 text-red-400 border-red-500/30",
                          item.status === "normal" && "bg-slate-700/40"
                        )}>

                          {item.status === "low" ? "库存不足" : "正常"}
                        </Badge>
                        <Badge variant="outline">{item.category}</Badge>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">当前库存</p>
                          <p className="text-white font-medium">
                            {item.currentStock} {item.unit}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">最低库存</p>
                          <p className="text-white font-medium">
                            {item.minStock} {item.unit}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">单价</p>
                          <p className="text-white font-medium">
                            {formatCurrency(item.unitPrice)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">库存价值</p>
                          <p className="text-white font-medium">
                            {formatCurrency(item.totalValue)}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-slate-400">库存率</span>
                          <span className="text-slate-300">
                            {(
                          item.currentStock / item.minStock *
                          100).
                          toFixed(0)}
                            %
                          </span>
                        </div>
                        <Progress
                        value={item.currentStock / item.minStock * 100}
                        className={cn(
                          "h-2",
                          item.status === "low" && "bg-red-500/20"
                        )} />

                      </div>
                      <div className="mt-3 text-xs text-slate-500">
                        供应商: {item.supplier} · 最后采购: {item.lastPurchase}
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedItem(item);
                        setShowItemDetail(true);
                      }}>

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

        <TabsContent value="orders" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>采购订单</CardTitle>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  新建订单
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(mockPurchaseOrders || []).map((order) =>
                <div
                  key={order.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">

                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-medium text-white">
                            {order.orderNo}
                          </span>
                          <Badge
                          variant="outline"
                          className={cn(
                            order.status === "pending" &&
                            "bg-amber-500/20 text-amber-400 border-amber-500/30",
                            order.status === "approved" &&
                            "bg-green-500/20 text-green-400 border-green-500/30",
                            order.status === "completed" &&
                            "bg-blue-500/20 text-blue-400 border-blue-500/30"
                          )}>

                            {order.status === "pending" ?
                          "待审批" :
                          order.status === "approved" ?
                          "已批准" :
                          "已完成"}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-slate-400">供应商</p>
                            <p className="text-white font-medium">
                              {order.supplier}
                            </p>
                          </div>
                          <div>
                            <p className="text-slate-400">订单金额</p>
                            <p className="text-white font-medium">
                              {formatCurrency(order.totalAmount)}
                            </p>
                          </div>
                          <div>
                            <p className="text-slate-400">物品数量</p>
                            <p className="text-white font-medium">
                              {order.items} 项
                            </p>
                          </div>
                        </div>
                        <div className="text-xs text-slate-500 mt-2">
                          创建时间: {order.createDate}
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
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="suppliers" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>供应商管理</CardTitle>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  新增供应商
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(supplies || []).map((item) =>
                <div
                  key={item.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">

                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-white mb-1">
                          {item.supplier}
                        </h3>
                        <div className="text-sm text-slate-400 space-y-1">
                          <p>主要供应: {item.category}</p>
                          <p>最后采购: {item.lastPurchase}</p>
                        </div>
                      </div>
                      <Badge
                      variant="outline"
                      className="bg-green-500/20 text-green-400 border-green-500/30">

                        合作中
                      </Badge>
                    </div>
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Item Detail Dialog */}
      <Dialog open={showItemDetail} onOpenChange={setShowItemDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>物品详情</DialogTitle>
            <DialogDescription>
              {selectedItem?.category} · {selectedItem?.name}
            </DialogDescription>
          </DialogHeader>
          <DialogBody>
            {selectedItem &&
            <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge
                  variant="outline"
                  className={cn(
                    selectedItem.status === "low" &&
                    "bg-red-500/20 text-red-400 border-red-500/30",
                    selectedItem.status === "normal" && "bg-slate-700/40"
                  )}>

                    {selectedItem.status === "low" ? "库存不足" : "正常"}
                  </Badge>
                  <Badge variant="outline">{selectedItem.category}</Badge>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    {selectedItem.name}
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-400 mb-1">当前库存</p>
                      <p className="text-white font-medium">
                        {selectedItem.currentStock} {selectedItem.unit}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">最低库存</p>
                      <p className="text-white font-medium">
                        {selectedItem.minStock} {selectedItem.unit}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">单价</p>
                      <p className="text-white font-medium">
                        {formatCurrency(selectedItem.unitPrice)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">库存价值</p>
                      <p className="text-white font-medium">
                        {formatCurrency(selectedItem.totalValue)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">供应商</p>
                      <p className="text-white">{selectedItem.supplier}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">最后采购</p>
                      <p className="text-white">{selectedItem.lastPurchase}</p>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">库存率</span>
                      <span className="text-slate-300">
                        {(
                      selectedItem.currentStock / selectedItem.minStock *
                      100).
                      toFixed(0)}
                        %
                      </span>
                    </div>
                    <Progress
                    value={
                    selectedItem.currentStock / selectedItem.minStock *
                    100
                    }
                    className={cn(
                      "h-2",
                      selectedItem.status === "low" && "bg-red-500/20"
                    )} />

                  </div>
                </div>
                <div className="pt-4 border-t border-slate-700/50 flex gap-2">
                  <Button className="flex-1">创建采购订单</Button>
                  <Button variant="outline" className="flex-1">
                    编辑信息
                  </Button>
                </div>
            </div>
            }
          </DialogBody>
        </DialogContent>
      </Dialog>
    </motion.div>);

}
