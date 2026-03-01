import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Activity, BarChart3, RefreshCw, TrendingUp } from "lucide-react";

import { PageHeader } from "../components/layout";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  LoadingSpinner,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui";
import { fadeIn, staggerContainer } from "../lib/animations";
import { cn, formatCurrency } from "../lib/utils";
import { supplierPriceTrendApi } from "../services/api";

function unwrapApiData(response) {
  return response?.formatted || response?.data?.data || response?.data || null;
}

function getVolatilityMeta(stddevAmount, maxStddevAmount) {
  if (!maxStddevAmount) {
    return {
      label: "低波动",
      className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    };
  }

  const ratio = stddevAmount / maxStddevAmount;
  if (ratio >= 0.66) {
    return {
      label: "高波动",
      className: "bg-rose-500/15 text-rose-300 border-rose-500/40",
    };
  }
  if (ratio >= 0.33) {
    return {
      label: "中波动",
      className: "bg-amber-500/15 text-amber-300 border-amber-500/40",
    };
  }
  return {
    label: "低波动",
    className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  };
}

export default function SupplierPriceTrend() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [trendData, setTrendData] = useState({ periods: [], series: [] });
  const [comparisonData, setComparisonData] = useState([]);
  const [volatilityData, setVolatilityData] = useState([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [trendRes, comparisonRes, volatilityRes] = await Promise.all([
        supplierPriceTrendApi.getTrends(),
        supplierPriceTrendApi.getComparison(),
        supplierPriceTrendApi.getVolatility({ limit: 12 }),
      ]);

      setTrendData(unwrapApiData(trendRes) || { periods: [], series: [] });
      setComparisonData(unwrapApiData(comparisonRes) || []);
      setVolatilityData(unwrapApiData(volatilityRes) || []);
    } catch (loadError) {
      console.error("加载供应商价格趋势失败:", loadError);
      setError("供应商价格趋势数据加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const periods = trendData?.periods || [];
  const trendSeries = trendData?.series || [];

  const volatilityList = useMemo(() => {
    if (Array.isArray(volatilityData)) return volatilityData;
    if (volatilityData && typeof volatilityData === "object") {
      const list = volatilityData.items ?? volatilityData.data ?? volatilityData.list ?? volatilityData.results;
      return Array.isArray(list) ? list : [];
    }
    return [];
  }, [volatilityData]);

  const comparisonList = useMemo(() => {
    if (Array.isArray(comparisonData)) return comparisonData;
    if (comparisonData && typeof comparisonData === "object") {
      const list = comparisonData.items ?? comparisonData.data ?? comparisonData.list ?? comparisonData.results;
      return Array.isArray(list) ? list : [];
    }
    return [];
  }, [comparisonData]);

  const maxTrendAmount = useMemo(() => {
    let maxValue = 0;
    for (const supplier of trendSeries) {
      for (const point of supplier.trend || []) {
        const amount = Number(point.total_amount || 0);
        if (amount > maxValue) {
          maxValue = amount;
        }
      }
    }
    return maxValue || 1;
  }, [trendSeries]);

  const maxVolatilityAmount = useMemo(() => {
    const values = volatilityList.map((item) => Number(item.stddev_amount || 0));
    return Math.max(...values, 0);
  }, [volatilityList]);

  const totalPurchaseAmount = useMemo(() => {
    return trendSeries.reduce(
      (sum, supplier) => sum + Number(supplier.total_amount || 0),
      0,
    );
  }, [trendSeries]);

  const renderHeader = (
    <PageHeader
      title="供应商价格趋势"
      description="跟踪供应商订单金额趋势、横向对比和价格波动风险"
      actions={[
        {
          label: "刷新",
          icon: RefreshCw,
          onClick: loadData,
          className: "bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-200",
        },
      ]}
    />
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="mx-auto max-w-7xl">
          {renderHeader}
          <Card className="border-slate-800 bg-slate-900/70">
            <CardContent className="py-16">
              <div className="flex items-center justify-center gap-3 text-slate-300">
                <LoadingSpinner className="h-5 w-5" />
                <span>正在加载供应商价格趋势...</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-6">
        <div className="mx-auto max-w-7xl">
          {renderHeader}
          <Card className="border-rose-500/40 bg-rose-950/30">
            <CardContent className="py-10 text-center">
              <p className="text-rose-200">{error}</p>
              <Button
                onClick={loadData}
                className="mt-4 bg-rose-600 hover:bg-rose-500 text-white"
              >
                重新加载
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {renderHeader}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
          className="space-y-6"
        >
          <motion.div
            variants={fadeIn}
            className="grid gap-4 md:grid-cols-3"
          >
            <Card className="border-slate-800 bg-slate-900/80">
              <CardHeader>
                <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-cyan-400" />
                  供应商数量
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold text-white">{trendSeries.length}</p>
              </CardContent>
            </Card>
            <Card className="border-slate-800 bg-slate-900/80">
              <CardHeader>
                <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-indigo-400" />
                  累计采购金额
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold text-white">
                  {formatCurrency(totalPurchaseAmount)}
                </p>
              </CardContent>
            </Card>
            <Card className="border-slate-800 bg-slate-900/80">
              <CardHeader>
                <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                  <Activity className="h-4 w-4 text-amber-400" />
                  分析期间
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold text-white">
                  {periods.length ? `${periods[0]} ~ ${periods[periods.length - 1]}` : "-"}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="border-slate-800 bg-slate-900/80">
              <CardHeader>
                <CardTitle className="text-slate-100">供应商趋势柱状图</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {trendSeries.length === 0 ? (
                  <p className="text-sm text-slate-400">暂无趋势数据</p>
                ) : (
                  trendSeries.map((supplier) => {
                    const trendMap = new Map(
                      (supplier.trend || []).map((point) => [point.period, point]),
                    );
                    return (
                      <div
                        key={supplier.supplier_id}
                        className="rounded-lg border border-slate-800 bg-slate-950/50 p-4"
                      >
                        <div className="mb-4 flex items-center justify-between gap-2">
                          <p className="text-slate-100 font-medium">{supplier.supplier_name}</p>
                          <span className="text-sm text-slate-300">
                            总额 {formatCurrency(supplier.total_amount || 0)}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
                          {periods.map((period) => {
                            const point = trendMap.get(period);
                            const amount = Number(point?.total_amount || 0);
                            const heightPercent = amount
                              ? Math.max((amount / maxTrendAmount) * 100, 8)
                              : 0;
                            return (
                              <div key={`${supplier.supplier_id}-${period}`} className="space-y-2">
                                <p className="text-xs text-slate-500">{period}</p>
                                <div className="h-20 rounded-md border border-slate-800 bg-slate-900/60 p-1">
                                  <div className="relative h-full w-full overflow-hidden rounded-sm">
                                    <div
                                      className="absolute bottom-0 left-0 right-0 rounded-sm bg-gradient-to-t from-cyan-500 to-blue-400 transition-all"
                                      style={{ height: `${heightPercent}%` }}
                                    />
                                  </div>
                                </div>
                                <p className="text-xs text-slate-400">{formatCurrency(amount)}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="border-slate-800 bg-slate-900/80">
              <CardHeader>
                <CardTitle className="text-slate-100">供应商价格对比</CardTitle>
              </CardHeader>
              <CardContent>
                <Table className="text-slate-200">
                  <TableHeader>
                    <TableRow className="border-slate-800">
                      <TableHead className="text-slate-400">供应商</TableHead>
                      <TableHead className="text-right text-slate-400">平均订单金额</TableHead>
                      <TableHead className="text-right text-slate-400">订单数</TableHead>
                      <TableHead className="text-right text-slate-400">最低订单金额</TableHead>
                      <TableHead className="text-right text-slate-400">最高订单金额</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {comparisonList.length === 0 ? (
                      <TableRow className="border-slate-800">
                        <TableCell colSpan={5} className="text-center text-slate-400 py-8">
                          暂无对比数据
                        </TableCell>
                      </TableRow>
                    ) : (
                      comparisonList.map((item) => (
                        <TableRow key={item.supplier_id} className="border-slate-800">
                          <TableCell className="font-medium text-slate-100">
                            {item.supplier_name}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(item.avg_order_amount || 0)}
                          </TableCell>
                          <TableCell className="text-right text-slate-300">
                            {item.order_count || 0}
                          </TableCell>
                          <TableCell className="text-right text-slate-300">
                            {formatCurrency(item.min_order_amount || 0)}
                          </TableCell>
                          <TableCell className="text-right text-slate-300">
                            {formatCurrency(item.max_order_amount || 0)}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="border-slate-800 bg-slate-900/80">
              <CardHeader>
                <CardTitle className="text-slate-100">价格波动风险</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {volatilityList.length === 0 ? (
                    <p className="text-sm text-slate-400">暂无波动数据</p>
                  ) : (
                    volatilityList.map((item) => {
                      const meta = getVolatilityMeta(
                        Number(item.stddev_amount || 0),
                        maxVolatilityAmount,
                      );
                      return (
                        <div
                          key={item.supplier_id}
                          className="rounded-lg border border-slate-800 bg-slate-950/50 p-4"
                        >
                          <div className="mb-3 flex items-center justify-between">
                            <p className="text-slate-100 font-medium">{item.supplier_name}</p>
                            <Badge className={cn("border", meta.className)}>{meta.label}</Badge>
                          </div>
                          <div className="space-y-1 text-sm">
                            <p className="text-slate-400">
                              标准差:
                              <span className="ml-2 text-slate-200">
                                {formatCurrency(item.stddev_amount || 0)}
                              </span>
                            </p>
                            <p className="text-slate-400">
                              波动区间:
                              <span className="ml-2 text-slate-200">
                                {formatCurrency(item.range_amount || 0)}
                              </span>
                            </p>
                            <p className="text-slate-400">
                              订单数:
                              <span className="ml-2 text-slate-200">
                                {item.order_count || 0}
                              </span>
                            </p>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
