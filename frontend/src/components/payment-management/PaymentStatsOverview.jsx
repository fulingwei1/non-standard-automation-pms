import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
  PieChart,
  Calendar,
  Bell } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { SimpleBarChart, SimplePieChart, SimpleLineChart } from "../../components/administrative/StatisticsCharts";
import {
  COLLECTION_LEVELS,
  getPaymentStatus,
  getPaymentType,
  getAgingPeriod,
  getCollectionLevel,
  calculateCollectionRate,
  calculateDSO,
  formatCurrency,
  formatPercentage } from
"@/lib/constants/finance";
import { cn } from "../../lib/utils";

const calculateAging = (dueDate) => {
  if (!dueDate) {return 0;}
  const due = new Date(dueDate);
  if (Number.isNaN(due.getTime())) {return 0;}
  const now = new Date();
  const diffMs = now.getTime() - due.getTime();
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
};

const getCollectionRecommendation = (daysOverdue, amount, customerCreditRating) => {
  const credit = String(customerCreditRating || "").toUpperCase();

  if (daysOverdue >= 90 || amount >= 100000 || ["D", "E"].includes(credit)) {
    return { level: COLLECTION_LEVELS.CRITICAL.key };
  }
  if (daysOverdue >= 60 || amount >= 50000) {
    return { level: COLLECTION_LEVELS.URGENT.key };
  }
  if (daysOverdue >= 30 || amount >= 20000) {
    return { level: COLLECTION_LEVELS.WARNING.key };
  }
  return { level: COLLECTION_LEVELS.NORMAL.key };
};

/**
 * 💰 支付统计概览组件
 * 展示支付管理的关键指标、账龄分析、催收情况等统计信息
 */
export function PaymentStatsOverview({
  payments = [],
  invoices = [],
  reminders = [],
  loading = false,
  refreshInterval = 30000,
  onRefresh: _onRefresh
}) {
  const [_selectedPeriod, _setSelectedPeriod] = useState('month');
  const [lastRefreshTime, _setLastRefreshTime] = useState(new Date());

  // 计算总体统计数据
  const overallStats = useMemo(() => {
    if (payments?.length === 0) {
      return {
        totalReceivables: 0,
        overdueAmount: 0,
        collectionRate: 0,
        dso: 0,
        paidAmount: 0,
        pendingAmount: 0,
        invoiceCount: 0,
        reminderCount: 0
      };
    }

    const totalReceivables = (payments || []).reduce((sum, p) => sum + p.amount, 0);
    const overdueAmount = payments.
    filter((p) => p.status === 'overdue').
    reduce((sum, p) => sum + p.amount, 0);
    const paidAmount = payments.
    filter((p) => p.status === 'paid').
    reduce((sum, p) => sum + p.amount, 0);
    const pendingAmount = payments.
    filter((p) => p.status === 'pending').
    reduce((sum, p) => sum + p.amount, 0);

    // 计算DSO（假设月收入为totalReceivables的1/12）
    const monthlyRevenue = totalReceivables / 12;
    const dso = calculateDSO(totalReceivables - paidAmount, monthlyRevenue);

    const collectionRate = calculateCollectionRate(paidAmount, totalReceivables);

    return {
      totalReceivables,
      overdueAmount,
      collectionRate,
      dso,
      paidAmount,
      pendingAmount,
      invoiceCount: invoices.length,
      reminderCount: reminders.length
    };
  }, [payments, invoices]);

  // 支付状态分布
  const statusDistribution = useMemo(() => {
    const statusCount = {};

    (payments || []).forEach((payment) => {
      const status = getPaymentStatus(payment.status);
      statusCount[status.key] = (statusCount[status.key] || 0) + 1;
    });

    return Object.entries(statusCount).map(([statusKey, count]) => {
      const status = getPaymentStatus(statusKey);
      return {
        name: status.label,
        value: count,
        color: status.color.replace('bg-', '#').replace('500', '')
      };
    });
  }, [payments]);

  // 支付类型分布
  const _typeDistribution = useMemo(() => {
    const typeCount = {};

    (payments || []).forEach((payment) => {
      const type = getPaymentType(payment.type);
      typeCount[type.label] = (typeCount[type.label] || 0) + 1;
    });

    return Object.entries(typeCount).map(([typeLabel, count]) => ({
      name: typeLabel,
      value: count,
      color: getPaymentType(typeLabel).color.replace('bg-', '#').replace('500', '')
    }));
  }, [payments]);

  // 账龄分析
  const agingAnalysis = useMemo(() => {
    const agingData = {};

    (payments || []).forEach((payment) => {
      if (payment.status === 'paid') {return;}

      const daysOverdue = Math.max(0, calculateAging(payment.due_date));
      const period = getAgingPeriod(daysOverdue);
      const amount = payment.amount;

      agingData[period.key] = (agingData[period.key] || 0) + amount;
    });

    return Object.entries(agingData).map(([periodKey, amount]) => {
      const period = getAgingPeriod(periodKey);
      return {
        name: period.label,
        value: amount,
        color: period.color.replace('bg-', '#').replace('500', ''),
        riskLevel: period.riskLevel
      };
    });
  }, [payments]);

  // 催收级别分析
  const collectionAnalysis = useMemo(() => {
    const collectionData = {};

    (payments || []).forEach((payment) => {
      if (payment.status === 'paid') {return;}

      const daysOverdue = Math.max(0, calculateAging(payment.due_date));
      const collection = getCollectionRecommendation(daysOverdue, payment.amount, payment.customer_credit_rating);

      collectionData[collection.level] = (collectionData[collection.level] || 0) + 1;
    });

    return Object.entries(collectionData).map(([level, count]) => {
      const config = getCollectionLevel(level);
      return {
        level,
        count,
        label: config.label,
        color: config.color.replace('bg-', '#').replace('500', ''),
        priority: config.priority
      };
    }).sort((a, b) => {
      const priorityOrder = { critical: 4, urgent: 3, warning: 2, normal: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }, [payments]);

  // 最近回款趋势
  const recentCollections = useMemo(() => {
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (29 - i));
      return date.toISOString().split('T')[0];
    });

    return (last30Days || []).map((date) => {
      const dayPayments = (payments || []).filter((p) =>
      p.status === 'paid' && p.paid_date === date
      );

      return {
        date,
        amount: (dayPayments || []).reduce((sum, p) => sum + p.amount, 0),
        count: dayPayments.length
      };
    });
  }, [payments]);

  // 关键指标卡片
  const MetricCard = ({ title, value, icon: Icon, trend, trendValue, color, description }) =>
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ scale: 1.02 }}
    className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className={cn("p-2 rounded-lg", color)}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-400">{title}</h3>
              <p className="text-2xl font-bold text-white">{value}</p>
            </div>
          </div>
          {trend &&
        <div className="flex items-center gap-1 mt-2">
              {trendValue > 0 ?
          <TrendingUp className="w-4 h-4 text-green-400" /> :

          <TrendingDown className="w-4 h-4 text-red-400" />
          }
              <span className={cn(
            "text-sm font-medium",
            trendValue > 0 ? 'text-green-400' : 'text-red-400'
          )}>
                {Math.abs(trendValue)}%
              </span>
        </div>
        }
          {description &&
        <p className="text-xs text-slate-500 mt-2">{description}</p>
        }
        </div>
      </div>
  </motion.div>;


  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) =>
        <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 animate-pulse">
            <div className="h-20 bg-slate-700/50 rounded-lg" />
        </div>
        )}
      </div>);

  }

  return (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="应收账款"
          value={formatCurrency(overallStats.totalReceivables)}
          icon={DollarSign}
          color="bg-blue-500"
          description="未收回的款项总额" />

        <MetricCard
          title="逾期金额"
          value={formatCurrency(overallStats.overdueAmount)}
          icon={AlertTriangle}
          color="bg-red-500"
          description="已逾期的款项金额" />

        <MetricCard
          title="回款率"
          value={formatPercentage(overallStats.collectionRate)}
          icon={CheckCircle2}
          color="bg-green-500"
          description="本期回款完成率" />

        <MetricCard
          title="DSO天数"
          value={`${overallStats.dso}天`}
          icon={Clock}
          color="bg-amber-500"
          description="应收账款周转天数" />

      </div>

      {/* 详细的统计信息 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 支付状态分布 */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <PieChart className="w-5 h-5" />
              支付状态分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <SimplePieChart
                data={statusDistribution}
                valueKey="value"
                nameKey="name"
                colors={(statusDistribution || []).map((d) => d.color)} />

            </div>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {(statusDistribution || []).map((item, index) =>
              <div key={index} className="flex items-center gap-2">
                  <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }} />

                  <span className="text-sm text-slate-300">
                    {item.name}: {item.value}
                  </span>
              </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 账龄分析 */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <BarChart3 className="w-5 h-5" />
              账龄分析
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <SimpleBarChart
                data={agingAnalysis}
                xAxisKey="name"
                yAxisKey="value"
                color="#f59e0b" />

            </div>
            <div className="space-y-2 mt-4">
              {(agingAnalysis || []).map((item, index) =>
              <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">{item.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">
                      {formatCurrency(item.value)}
                    </span>
                    <Badge
                    variant={item.riskLevel === 'critical' ? 'destructive' : 'secondary'}
                    className="text-xs">

                      {item.riskLevel}
                    </Badge>
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 催收级别分析 */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Bell className="w-5 h-5" />
              催收级别分析
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {(collectionAnalysis || []).map((item, index) =>
              <div key={index} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }} />

                    <div>
                      <span className="text-sm font-medium text-white">{item.label}</span>
                      <div className="text-xs text-slate-400">
                        优先级: {item.priority}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white">{item.count}</div>
                    <div className="text-xs text-slate-400">个付款</div>
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 回款趋势图 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-white">
              <Calendar className="w-5 h-5" />
              最近30天回款趋势
            </CardTitle>
            <div className="text-sm text-slate-400">
              更新时间: {lastRefreshTime.toLocaleTimeString()}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <SimpleLineChart
              data={recentCollections}
              xAxisKey="date"
              yAxisKeys={['amount']}
              colors={['#10b981']}
              labels={['回款金额']}
              formatLabel={(value) => formatCurrency(value)} />

          </div>
          <div className="flex items-center justify-between mt-4 text-xs text-slate-400">
            <span>自动刷新间隔: {refreshInterval / 1000}秒</span>
            <span>
              总回款: {formatCurrency(
                (recentCollections || []).reduce((sum, r) => sum + r.amount, 0)
              )}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>);

}

export default PaymentStatsOverview;
