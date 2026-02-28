import React from "react";
import { motion } from "framer-motion";
import {
  Package,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  Truck,
  BarChart3,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { PurchaseOrderUtils, ORDER_STATUS_CONFIGS } from "@/lib/constants/procurement";

export default function PurchaseOrdersOverview({ orders = [] }) {
  // 计算统计数据
  const stats = {
    total: orders?.length || 0,
    pending: (orders || []).filter(o => o.status === 'pending').length || 0,
    completed: (orders || []).filter(o => o.status === 'completed').length || 0,
    delayed: (orders || []).filter(o => o.status === 'delayed').length || 0,
    totalAmount: (orders || []).reduce((sum, o) => sum + (o.totalAmount || 0), 0) || 0,
    averageAmount: orders?.length > 0 
      ? ((orders || []).reduce((sum, o) => sum + (o.totalAmount || 0), 0) / orders?.length).toFixed(2)
      : 0,
  };

  // 计算状态分布
  const statusDistribution = Object.keys(ORDER_STATUS_CONFIGS).map(status => {
    const count = (orders || []).filter(o => o.status === status).length;
    const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;
    return {
      status,
      label: ORDER_STATUS_CONFIGS[status].label,
      color: ORDER_STATUS_CONFIGS[status].color,
      count,
      percentage,
    };
  }).filter(item => item.count > 0);

  // 获取最近延期订单
  const delayedOrders = orders
    .filter(o => o.status === 'delayed')
    .slice(0, 5)
    .map(order => ({
      id: order.id,
      supplierName: order.supplierName,
      expectedDate: order.expected_date,
      delayedDays: PurchaseOrderUtils.getDelayedDays(order.expected_date),
      totalAmount: order.totalAmount,
    }));

  // 获取今日到期订单
  const todayOrders = (orders || []).filter(order => {
    const expectedDate = new Date(order.expected_date);
    const today = new Date();
    return expectedDate.toDateString() === today.toDateString();
  });

  return (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">总订单数</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
            </div>
            <div className="bg-blue-500/20 p-3 rounded-lg">
              <Package className="h-6 w-6 text-blue-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">待收货</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.pending}</p>
            </div>
            <div className="bg-amber-500/20 p-3 rounded-lg">
              <Clock className="h-6 w-6 text-amber-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">已完成</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.completed}</p>
            </div>
            <div className="bg-emerald-500/20 p-3 rounded-lg">
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">总金额</p>
              <p className="text-2xl font-bold text-white mt-1">
                ¥{Number(stats.totalAmount).toLocaleString()}
              </p>
            </div>
            <div className="bg-green-500/20 p-3 rounded-lg">
              <DollarSign className="h-6 w-6 text-green-400" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* 状态分布 */}
      <Card className="bg-surface-1 border-border">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            订单状态分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {(statusDistribution || []).map((item) => (
              <motion.div
                key={item.status}
                whileHover={{ scale: 1.05 }}
                className="text-center"
              >
                <div className={`w-12 h-12 ${item.color} rounded-lg mx-auto mb-2 flex items-center justify-center`}>
                  <span className="text-white font-semibold text-sm">{item.count}</span>
                </div>
                <p className="text-xs text-text-secondary">{item.label}</p>
                <p className="text-xs text-white font-semibold">{item.percentage}%</p>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 延期订单 */}
        <Card className="bg-surface-1 border-border">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              延期订单 ({delayedOrders.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {delayedOrders.length > 0 ? (
              <div className="space-y-3">
                {(delayedOrders || []).map((order) => (
                  <div
                    key={order.id}
                    className="flex items-center justify-between p-3 bg-surface-2 rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{order.id}</p>
                      <p className="text-xs text-text-secondary">{order.supplierName}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant="destructive" className="text-xs">
                        延期 {order.delayedDays} 天
                      </Badge>
                      <p className="text-xs text-text-secondary mt-1">
                        {PurchaseOrderUtils.formatDate(order.expectedDate)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto mb-2" />
                <p className="text-text-secondary">暂无延期订单</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 今日到期 */}
        <Card className="bg-surface-1 border-border">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-400" />
              今日到期 ({todayOrders.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {todayOrders.length > 0 ? (
              <div className="space-y-3">
                {todayOrders.slice(0, 5).map((order) => (
                  <div
                    key={order.id}
                    className="flex items-center justify-between p-3 bg-surface-2 rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{order.id}</p>
                      <p className="text-xs text-text-secondary">{order.supplierName}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-white">
                        ¥{PurchaseOrderUtils.formatCurrency(order.totalAmount)}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {PurchaseOrderUtils.getStatusConfig(order.status).label}
                      </Badge>
                    </div>
                  </div>
                ))}
                {todayOrders.length > 5 && (
                  <p className="text-xs text-text-secondary text-center">
                    还有 {todayOrders.length - 5} 个订单今日到期
                  </p>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Clock className="h-12 w-12 text-blue-400 mx-auto mb-2" />
                <p className="text-text-secondary">今日无到期订单</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 快速统计 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-surface-1 border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="bg-blue-500/20 p-2 rounded-lg">
                <TrendingUp className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-text-secondary">平均订单金额</p>
                <p className="text-lg font-semibold text-white">
                  ¥{PurchaseOrderUtils.formatCurrency(stats.averageAmount)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-1 border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="bg-emerald-500/20 p-2 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-text-secondary">完成率</p>
                <p className="text-lg font-semibold text-white">
                  {stats.total > 0 ? (stats.completed / stats.total * 100).toFixed(1) : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-1 border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="bg-red-500/20 p-2 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-text-secondary">延期率</p>
                <p className="text-lg font-semibold text-white">
                  {stats.total > 0 ? (stats.delayed / stats.total * 100).toFixed(1) : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}