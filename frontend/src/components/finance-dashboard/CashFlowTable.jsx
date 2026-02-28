/**
 * Cash Flow Table Component
 * 现金流表格组件
 * 用于展示现金流明细和分析
 */

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Badge } from "../../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Input } from "../../components/ui/input";
import { cn } from "../../lib/utils";
import {
  formatCurrency,
  formatPercentage,
  timePeriods } from
"@/lib/constants/finance";

// 现金流汇总卡片
const CashFlowSummaryCard = ({ cashFlowData, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) =>
        <Card key={i} className="bg-surface-50 border-white/10">
            <CardContent className="p-6">
              <div className="animate-pulse space-y-3">
                <div className="w-8 h-8 bg-slate-700 rounded" />
                <div className="h-6 bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-700 rounded w-1/2" />
              </div>
            </CardContent>
        </Card>
        )}
      </div>);

  }

  const cashFlowTypes = [
  {
    type: 'operating',
    label: '经营活动现金流',
    value: cashFlowData.operating,
    icon: '💰',
    color: cashFlowData.operating >= 0 ? 'text-green-400' : 'text-red-400',
    bgColor: cashFlowData.operating >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'
  },
  {
    type: 'investing',
    label: '投资活动现金流',
    value: cashFlowData.investing,
    icon: '📈',
    color: cashFlowData.investing >= 0 ? 'text-green-400' : 'text-red-400',
    bgColor: cashFlowData.investing >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'
  },
  {
    type: 'financing',
    label: '筹资活动现金流',
    value: cashFlowData.financing,
    icon: '🏦',
    color: cashFlowData.financing >= 0 ? 'text-green-400' : 'text-red-400',
    bgColor: cashFlowData.financing >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'
  },
  {
    type: 'net',
    label: '现金流量净额',
    value: cashFlowData.net,
    icon: '💧',
    color: cashFlowData.net >= 0 ? 'text-green-400' : 'text-red-400',
    bgColor: cashFlowData.net >= 0 ? 'bg-green-500/10' : 'bg-red-500/10'
  }];


  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cashFlowTypes.map((item, index) =>
      <Card key={index} className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", item.bg)}>
                <span className="text-xl">{item.icon}</span>
              </div>
            </div>
            <div>
              <div className={cn("text-2xl font-bold mb-1", item.color)}>
                {formatCurrency(item.value)}
              </div>
              <div className="text-sm text-slate-400">{item.label}</div>
            </div>
          </CardContent>
      </Card>
      )}
    </div>);

};

// 现金流趋势图
const CashFlowTrendChart = ({ cashFlowByMonth, loading }) => {
  const chartData = useMemo(() => {
    if (!cashFlowByMonth || cashFlowByMonth.length === 0) {return [];}
    return cashFlowByMonth.map((item) => ({
      month: item.month,
      operating: item.operating,
      investing: item.investing,
      financing: item.financing,
      net: item.net
    }));
  }, [cashFlowByMonth]);

  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            <div className="h-64 bg-slate-700 rounded" />
          </div>
        </CardContent>
      </Card>);

  }

  if (!chartData || chartData.length === 0) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64 text-slate-400">
            暂无现金流趋势数据
          </div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">现金流趋势</h3>

        <div className="h-80 flex items-center justify-center text-slate-400">
          {/* TODO: 实现 LineChart 组件 - 需要从 recharts 导入并重构 */}
          <p>现金流趋势图表 (开发中)</p>
          {/* 
          <LineChart
            data={chartData}
            xField="month"
            yField="net"
            seriesField="type"
            height={300}
            showPoint
            showArea
            formatter={formatter}
            colors={['#4ade80', '#ef4444', '#60a5fa', '#a78bfa']}
            tooltip={{
              showMarkers: true,
              shared: true,
              showCrosshairs: true,
              crosshairs: {
                type: 'xy'
              },
              formatter: (datum) => ({
                name: datum.operating !== undefined ? '现金流量净额' : datum.type,
                value: formatter(datum.net || datum.value)
              })
            }} />
          */}

        </div>
      </CardContent>
    </Card>);

};

// 现金流明细表格
const CashFlowDetailTable = ({
  cashFlowDetails,
  loading,
  searchTerm,
  setSearchTerm,
  selectedType,
  setSelectedType,
  period,
  setPeriod
}) => {
  const filteredData = useMemo(() => {
    if (!cashFlowDetails) {return [];}

    return cashFlowDetails.
    filter((item) => {
      const matchesSearch = item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = !selectedType || item.type === selectedType;
      return matchesSearch && matchesType;
    }).
    sort((a, b) => {
      // 先按类型排序，再按金额排序
      if (a.type !== b.type) {
        const typeOrder = ['operating', 'investing', 'financing'];
        return typeOrder.indexOf(a.type) - typeOrder.indexOf(b.type);
      }
      return Math.abs(b.amount) - Math.abs(a.amount);
    });
  }, [cashFlowDetails, searchTerm, selectedType]);

  const getTypeConfig = (type) => {
    switch (type) {
      case 'operating':
        return { color: 'text-green-400', bgColor: 'bg-green-500/10', label: '经营' };
      case 'investing':
        return { color: 'text-blue-400', bgColor: 'bg-blue-500/10', label: '投资' };
      case 'financing':
        return { color: 'text-purple-400', bgColor: 'bg-purple-500/10', label: '筹资' };
      default:
        return { color: 'text-slate-400', bgColor: 'bg-slate-500/10', label: '其他' };
    }
  };

  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            <div className="space-y-2">
              {[...Array(5)].map((_, i) =>
              <div key={i} className="h-3 bg-slate-700 rounded w-full" />
              )}
            </div>
          </div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        {/* 筛选区域 */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <Input
              placeholder="搜索现金流项目..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-800 border-slate-700 text-white" />

          </div>

          <Select value={selectedType || '__all__'} onValueChange={(value) => setSelectedType(value === '__all__' ? '' : value)}>
            <SelectTrigger className="w-32 bg-slate-800 border-slate-700 text-white">
              <SelectValue placeholder="全部类型" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800">
              <SelectItem value="__all__">全部类型</SelectItem>
              <SelectItem value="operating">经营活动</SelectItem>
              <SelectItem value="investing">投资活动</SelectItem>
              <SelectItem value="financing">筹资活动</SelectItem>
            </SelectContent>
          </Select>

          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-32 bg-slate-800 border-slate-700 text-white">
              <SelectValue placeholder="选择期间" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800">
              {Object.entries(timePeriods).map(([key, value]) =>
              <SelectItem key={key} value={key}>{value.label}</SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        {/* 表格 */}
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-slate-400 text-left">日期</TableHead>
                <TableHead className="text-slate-400 text-left">类型</TableHead>
                <TableHead className="text-slate-400 text-left">类别</TableHead>
                <TableHead className="text-slate-400 text-left">描述</TableHead>
                <TableHead className="text-slate-400 text-right">金额</TableHead>
                <TableHead className="text-slate-400 text-right">累计</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((item, index) => {
                const typeConfig = getTypeConfig(item.type);
                const isPositive = item.amount >= 0;
                const cumulative = filteredData.
                slice(0, index + 1).
                reduce((sum, d) => sum + d.amount, 0);

                return (
                  <TableRow key={index} className="border-b border-slate-800/50">
                    <TableCell className="text-sm text-slate-300">
                      {item.date}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={cn(
                        "text-xs",
                        typeConfig.borderColor.replace("border-", "text-")
                      )}>
                        {typeConfig.label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-slate-400">
                      {item.category}
                    </TableCell>
                    <TableCell className="text-sm text-white max-w-xs">
                      {item.description}
                    </TableCell>
                    <TableCell className={cn(
                      "text-sm font-medium text-right",
                      isPositive ? "text-green-400" : "text-red-400"
                    )}>
                      {isPositive ? "+" : ""}{formatCurrency(item.amount)}
                    </TableCell>
                    <TableCell className={cn(
                      "text-sm font-medium text-right",
                      cumulative >= 0 ? "text-green-400" : "text-red-400"
                    )}>
                      {formatCurrency(cumulative)}
                    </TableCell>
                  </TableRow>);

              })}
            </TableBody>
          </Table>
        </div>

        {filteredData.length === 0 &&
        <div className="text-center py-8 text-slate-400">
            暂无现金流数据
        </div>
        }

        {/* 汇总行 */}
        {filteredData.length > 0 &&
        <div className="mt-4 pt-4 border-t border-slate-700">
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-400">
                共 {filteredData.length} 条记录
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-400">现金流量净额</div>
                <div className="text-xl font-bold text-white">
                  {formatCurrency(filteredData.reduce((sum, item) => sum + item.amount, 0))}
                </div>
              </div>
            </div>
        </div>
        }
      </CardContent>
    </Card>);

};

// 现金流分析卡片
const CashFlowAnalysisCard = ({ analysisData, loading }) => {
  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            <div className="space-y-2">
              {[...Array(4)].map((_, i) =>
              <div key={i} className="h-3 bg-slate-700 rounded w-full" />
              )}
            </div>
          </div>
        </CardContent>
      </Card>);

  }

  const metrics = [
  {
    label: '现金流入',
    value: analysisData.totalInflow,
    trend: analysisData.inflowGrowth,
    positive: true
  },
  {
    label: '现金流出',
    value: analysisData.totalOutflow,
    trend: analysisData.outflowGrowth,
    positive: false
  },
  {
    label: '现金转换周期',
    value: `${analysisData.cashConversionCycle}天`,
    trend: analysisData.cycleTrend,
    positive: analysisData.cycleTrend <= 0
  },
  {
    label: '自由现金流',
    value: analysisData.freeCashFlow,
    trend: analysisData.freeCashFlowGrowth,
    positive: analysisData.freeCashFlow >= 0
  }];


  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">现金流分析</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {metrics.map((metric, index) =>
          <div key={index} className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-slate-400">{metric.label}</div>
                {metric.trend !== undefined &&
              <div className={cn(
                "text-xs font-medium",
                metric.positive ? "text-green-400" : "text-red-400"
              )}>
                    {metric.trend >= 0 ? "↑" : "↓"}
                    {Math.abs(metric.trend)}%
              </div>
              }
              </div>
              <div className={cn(
              "text-xl font-bold",
              metric.positive ? "text-green-400" : "text-red-400"
            )}>
                {metric.value}
              </div>
          </div>
          )}
        </div>

        <div className="mt-4 space-y-3">
          <div className="text-sm text-slate-400">
            经营活动现金流占比
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-green-400 to-emerald-500 h-2 rounded-full"
                style={{
                  width: `${Math.abs(analysisData.operatingRatio)}%`
                }} />
            </div>
            <span className="text-sm font-medium text-white">
              {analysisData.operatingRatio >= 0 ? '+' : ''}
              {formatPercentage(analysisData.operatingRatio)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>);

};

export function CashFlowTable({
  cashFlowData,
  loading = false
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [period, setPeriod] = useState("CURRENT_MONTH");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6">

      {/* 现金流汇总 */}
      <CashFlowSummaryCard
        cashFlowData={cashFlowData}
        loading={loading} />


      {/* 现金流分析 */}
      <CashFlowAnalysisCard
        analysisData={cashFlowData?.analysis}
        loading={loading} />


      {/* 现金流趋势 */}
      <CashFlowTrendChart
        cashFlowByMonth={cashFlowData?.byMonth}
        loading={loading} />


      {/* 现金流明细 */}
      <CashFlowDetailTable
        cashFlowDetails={cashFlowData?.details}
        loading={loading}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        selectedType={selectedType}
        setSelectedType={setSelectedType}
        period={period}
        setPeriod={setPeriod} />

    </motion.div>);

}

export default CashFlowTable;