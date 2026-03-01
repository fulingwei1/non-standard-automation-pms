/**
 * Delivery Overview
 * 交付概览组件：用于展示交付总体统计与关键提醒
 * Refactored to shadcn/Tailwind Dark Theme
 */

import { useMemo } from "react";
import { Card, CardContent, Badge, Progress, EmptyState } from "../ui";
import { PackageCheck, Truck, Clock, AlertCircle, BarChart3, AlertTriangle, Percent } from "lucide-react";
import { cn } from "../../lib/utils";
import { MonthlyTrendChart } from "../administrative/StatisticsCharts";

import { DELIVERY_STATUS, DELIVERY_PRIORITY, SHIPPING_METHODS } from "@/lib/constants/service";

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c" };
};

const countBy = (items, predicate) => (items || []).reduce((acc, item) => acc + (predicate(item) ? 1 : 0), 0);

const DeliveryOverview = ({ data, _loading, statistics }) => {
  const deliveries = Array.isArray(data) ? data : data?.deliveries || [];

  const total = deliveries?.length;
  const preparingCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.PREPARING.value);
  const pendingCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.PENDING.value);
  const inTransitCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.IN_TRANSIT.value);
  const deliveredCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.DELIVERED.value);
  const cancelledCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.CANCELLED.value);

  const urgentCount = countBy(deliveries, (d) => d.priority === DELIVERY_PRIORITY.URGENT.value);
  const highPriorityCount = countBy(deliveries, (d) => d.priority === DELIVERY_PRIORITY.HIGH.value);

  const shippedOrInTransit = (deliveries || []).filter(
    (d) => d.status === DELIVERY_STATUS.SHIPPED.value || d.status === DELIVERY_STATUS.IN_TRANSIT.value
  );

  const completionRate = total > 0 ? Math.round((deliveredCount / total) * 100) : 0;

  // 发货异常统计：审批拒绝、退回、延迟发货（实际发货日晚于计划发货日）
  const exceptionStats = useMemo(() => {
    const rejected = countBy(deliveries, (d) => (d.approvalStatus || "").toLowerCase() === "rejected");
    const returned = countBy(deliveries, (d) => (d.deliveryStatusRaw || "").toLowerCase() === "returned");
    let delayed = 0;
    (deliveries || []).forEach((d) => {
      const plan = d.deliveryDate || d.scheduledDate;
      const actual = d.shipDate;
      if (!plan || !actual) return;
      const planDate = new Date(plan);
      const actualDate = new Date(actual);
      if (actualDate > planDate) delayed += 1;
    });
    return { rejected, returned, delayed, total: rejected + returned + delayed };
  }, [deliveries]);

  // 发货及时率：优先用接口 on_time_shipping_rate，否则用列表估算（已发货且实际≤计划的数量/已发货总数）
  const onTimeRate = useMemo(() => {
    if (statistics != null && typeof statistics.on_time_shipping_rate === "number") {
      return Math.round(statistics.on_time_shipping_rate * 10) / 10;
    }
    const withShipAndPlan = (deliveries || []).filter(
      (d) => (d.deliveryStatusRaw === "shipped" || d.deliveryStatusRaw === "received") && d.shipDate && (d.deliveryDate || d.scheduledDate)
    );
    if (withShipAndPlan.length === 0) return null;
    const onTime = withShipAndPlan.filter((d) => {
      const plan = new Date(d.deliveryDate || d.scheduledDate);
      const actual = new Date(d.shipDate);
      return actual <= plan;
    }).length;
    return Math.round((onTime / withShipAndPlan.length) * 1000) / 10;
  }, [deliveries, statistics]);

  // 每月累计发货金额：按 deliveryDate 的 YYYY-MM 聚合
  const monthlyAmountData = useMemo(() => {
    const map = new Map();
    (deliveries || []).forEach((d) => {
      const amount = d.deliveryAmount != null ? Number(d.deliveryAmount) : 0;
      if (amount <= 0) return;
      const raw = d.deliveryDate || d.scheduledDate || d.actualDate;
      if (!raw) return;
      const str = typeof raw === "string" ? raw : (raw.toISOString ? raw.toISOString().slice(0, 7) : "");
      const month = str.slice(0, 7);
      if (!month || month.length < 7) return;
      map.set(month, (map.get(month) || 0) + amount);
    });
    const list = Array.from(map.entries())
      .map(([month, value]) => ({ month, value }))
      .sort((a, b) => a.month.localeCompare(b.month));
    return list;
  }, [deliveries]);

  const StatCard = ({ icon: Icon, title, value, iconBgClass, _textClass }) => (
    <Card className="bg-surface-100/50">
      <CardContent className="p-4 flex items-center gap-4">
        <div className={cn("p-2 rounded-lg", iconBgClass)}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-xs text-slate-400">{title}</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-4">
      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={PackageCheck}
          title="总发货单"
          value={total || 0}
          iconBgClass="bg-blue-500/20"
          _textClass="text-blue-400"
        />
        <StatCard
          icon={Clock}
          title="待处理（待发货/准备中）"
          value={pendingCount + preparingCount}
          iconBgClass="bg-amber-500/20"
          _textClass="text-amber-400"
        />
        <StatCard
          icon={Truck}
          title="在途/已发货"
          value={shippedOrInTransit.length}
          iconBgClass="bg-emerald-500/20"
          _textClass="text-emerald-400"
        />
        <StatCard
          icon={PackageCheck}
          title="已送达"
          value={deliveredCount || "unknown"}
          iconBgClass="bg-slate-500/20"
          _textClass="text-slate-400"
        />
      </div>

      {/* 发货异常统计 & 发货及时率统计 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              发货异常统计
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-center">
                <p className="text-xl font-bold text-red-400">{exceptionStats.rejected}</p>
                <p className="text-xs text-slate-400">审批拒绝</p>
              </div>
              <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 text-center">
                <p className="text-xl font-bold text-amber-400">{exceptionStats.returned}</p>
                <p className="text-xs text-slate-400">退回</p>
              </div>
              <div className="rounded-lg bg-orange-500/10 border border-orange-500/20 p-3 text-center">
                <p className="text-xl font-bold text-orange-400">{exceptionStats.delayed}</p>
                <p className="text-xs text-slate-400">延迟发货</p>
              </div>
            </div>
            {exceptionStats.total > 0 && (
              <p className="text-xs text-slate-500 mt-2">合计异常 {exceptionStats.total} 单</p>
            )}
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
              <Percent className="w-4 h-4" />
              发货及时率统计
            </h3>
            {onTimeRate != null ? (
              <>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-white">{onTimeRate}%</span>
                  <span className="text-sm text-slate-400">计划发货日内发货占比</span>
                </div>
                <Progress value={Math.min(100, onTimeRate)} className="h-2 mt-3" />
                <p className="text-xs text-slate-500 mt-2">基于已发货且有计划/实际日期的订单计算</p>
              </>
            ) : (
              <EmptyState
                icon={Percent}
                title="暂无及时率数据"
                message="有已发货且计划发货日、实际发货日的订单后将显示及时率"
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Progress & Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 space-y-3">
            <h3 className="text-sm font-medium text-slate-400">完成率</h3>
            <Progress value={completionRate || "unknown"} className="h-2" />
            <p className="text-xs text-slate-500">
              已送达 {deliveredCount} / {total}（取消 {cancelledCount}）
            </p>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 space-y-3">
            <h3 className="text-sm font-medium text-slate-400">风险提醒</h3>
            <div className="flex flex-wrap gap-2">
              <Badge 
                variant="outline" 
                className={cn(
                  "flex items-center gap-1",
                  urgentCount > 0 
                    ? "bg-red-500/20 text-red-400 border-red-500/30" 
                    : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                )}
              >
                <AlertCircle size={14} />
                紧急 {urgentCount}
              </Badge>
              <Badge 
                variant="outline"
                className={cn(
                  highPriorityCount > 0 
                    ? "bg-amber-500/20 text-amber-400 border-amber-500/30" 
                    : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                )}
              >
                高优先级 {highPriorityCount}
              </Badge>
              <Badge variant="outline" className="bg-slate-500/20 text-slate-400 border-slate-500/30">
                在途 {inTransitCount}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 每月累计发货金额 - 柱状图 */}
      <Card className="bg-surface-100/50">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            每月累计发货金额
          </h3>
          {monthlyAmountData.length === 0 ? (
            <EmptyState
              icon={BarChart3}
              title="暂无发货金额数据"
              message="有发货日期与金额的发货单将在此按月份汇总展示"
            />
          ) : (
            <MonthlyTrendChart
              data={monthlyAmountData}
              valueKey="value"
              labelKey="month"
              height={220}
            />
          )}
        </CardContent>
      </Card>

      {/* Recent Shipments List */}
      <Card className="bg-surface-100/50">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-4">在途/已发货清单（最近）</h3>
          {shippedOrInTransit.length === 0 ? (
            <EmptyState 
              icon={PackageCheck}
              title="暂无在途/已发货数据"
              message="当前没有在途或已发货的订单"
            />
          ) : (
            <div className="space-y-2">
              {shippedOrInTransit.slice(0, 8).map((d) => {
                const status = getConfigByValue(DELIVERY_STATUS, d.status, d.status);
                const method = getConfigByValue(SHIPPING_METHODS, d.shippingMethod, d.shippingMethod);
                const priority = getConfigByValue(DELIVERY_PRIORITY, d.priority, d.priority);

                return (
                  <div 
                    key={d.id} 
                    className="p-3 bg-surface-100 rounded-lg border border-white/5"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-white truncate">{d.orderNumber}</p>
                        <p className="text-xs text-slate-400">{d.customerName}</p>
                      </div>
                      <div className="flex flex-wrap gap-1 justify-end">
                        <Badge 
                          variant="outline" 
                          className="text-xs"
                          style={{ borderColor: status.color, color: status.color }}
                        >
                          {status.label}
                        </Badge>
                        <Badge 
                          variant="outline" 
                          className="text-xs"
                          style={{ borderColor: priority.color, color: priority.color }}
                        >
                          {priority.label}
                        </Badge>
                        <Badge variant="outline" className="text-xs border-slate-500/30 text-slate-400">
                          {method.label}
                        </Badge>
                        {d.scheduledDate && (
                          <Badge variant="outline" className="text-xs border-slate-500/30 text-slate-400">
                            计划 {d.scheduledDate}
                          </Badge>
                        )}
                        {d.trackingNumber && (
                          <Badge variant="outline" className="text-xs border-slate-500/30 text-slate-400">
                            单号 {d.trackingNumber}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DeliveryOverview;
