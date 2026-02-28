/**
 * 趋势图表组件 (Trend Chart) - Dashboard Widget
 *
 * 显示关键指标的趋势变化
 *
 * NOTE: An assessment-oriented TrendChart exists at:
 * components/assessment/TrendChart.jsx
 * That component is a raw SVG chart for assessment score trends.
 * This component is a dashboard card widget with KPI indicators.
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { cn } from '../../../lib/utils';

// 默认趋势数据
const defaultTrendData = {
  revenue: {
    title: '营收趋势',
    current: '¥1,250,000',
    change: 12.5,
    data: [65, 72, 68, 85, 92, 88, 95, 100, 105, 98, 110, 125],
    labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  },
  'project-health': {
    title: '项目健康度',
    current: '85%',
    change: 5.2,
    data: [75, 78, 80, 76, 82, 85, 83, 88, 86, 90, 87, 85],
    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
  },
  'production-output': {
    title: '产出趋势',
    current: '320台',
    change: 8.3,
    data: [250, 265, 280, 270, 295, 300, 285, 310, 320, 305, 325, 320],
    labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  },
  'procurement-spend': {
    title: '采购支出',
    current: '¥850,000',
    change: -3.2,
    data: [900, 920, 880, 910, 870, 890, 860, 880, 840, 870, 850, 850],
    labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  },
  financial: {
    title: '财务指标',
    current: '¥2,100,000',
    change: 15.8,
    data: [1500, 1600, 1750, 1680, 1820, 1900, 1850, 1980, 2050, 2000, 2150, 2100],
    labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  },
  'company-kpi': {
    title: '公司KPI',
    current: '92分',
    change: 6.5,
    data: [78, 82, 85, 80, 88, 90, 86, 92, 89, 94, 91, 92],
    labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  },
};

/**
 * 简易折线图
 */
function SimpleLine({ data, className }) {
  if (!data || data?.length === 0) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const height = 60;
  const width = 100;

  const points = (data || []).map((value, index) => {
    const x = (index / (data?.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  const areaPoints = `0,${height} ${points} ${width},${height}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className={cn('w-full h-16', className)}>
      {/* 渐变填充 */}
      <defs>
        <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.3" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon
        points={areaPoints}
        fill="url(#areaGradient)"
        className="text-primary"
      />
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-primary"
      />
    </svg>
  );
}

/**
 * 趋势图表主组件
 */
export default function TrendChart({ type = 'revenue', data }) {
  const [trendData, setTrendData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        if (data) {
          setTrendData(data);
          return;
        }

        // 使用默认数据
        setTrendData(defaultTrendData[type] || defaultTrendData.revenue);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [type, data]);

  const isPositive = trendData?.change > 0;
  const isNegative = trendData?.change < 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">
          {loading ? '加载中...' : trendData?.title || '趋势图表'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-32 bg-white/5 rounded-lg animate-pulse" />
        ) : (
          <div>
            {/* 当前值和变化 */}
            <div className="flex items-end justify-between mb-4">
              <div>
                <p className="text-2xl font-bold">{trendData?.current}</p>
                <div className={cn(
                  'flex items-center text-sm',
                  isPositive && 'text-emerald-400',
                  isNegative && 'text-red-400',
                  !isPositive && !isNegative && 'text-slate-400'
                )}>
                  {isPositive ? (
                    <TrendingUp className="h-4 w-4 mr-1" />
                  ) : isNegative ? (
                    <TrendingDown className="h-4 w-4 mr-1" />
                  ) : (
                    <Minus className="h-4 w-4 mr-1" />
                  )}
                  {isPositive ? '+' : ''}{trendData?.change}%
                  <span className="text-muted-foreground ml-1">较上期</span>
                </div>
              </div>
            </div>

            {/* 折线图 */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <SimpleLine data={trendData?.data} />
            </motion.div>

            {/* X轴标签 */}
            {trendData?.labels && (
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>{trendData.labels[0]}</span>
                <span>{trendData.labels[Math.floor(trendData.labels?.length / 2)]}</span>
                <span>{trendData.labels[trendData.labels?.length - 1]}</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
