/**
 * 库存统计卡片组件
 * 展示库存总览的关键指标
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, DollarSign, AlertTriangle, ClipboardCheck, TrendingUp } from 'lucide-react';
import { StockSummary } from '@/types/inventory';

interface StockSummaryCardsProps {
  summary: StockSummary;
  loading?: boolean;
}

const StockSummaryCards: React.FC<StockSummaryCardsProps> = ({ summary, loading }) => {
  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-gray-200 rounded" />
              <div className="h-4 w-4 bg-gray-200 rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-32 bg-gray-200 rounded mb-2" />
              <div className="h-3 w-20 bg-gray-200 rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: '总库存数量',
      value: summary.total_stock_quantity.toLocaleString(),
      icon: Package,
      description: '所有物料总数量',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: '库存总金额',
      value: `¥${summary.total_stock_value.toLocaleString()}`,
      icon: DollarSign,
      description: '库存资产总价值',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: '低库存物料',
      value: summary.low_stock_count.toString(),
      icon: AlertTriangle,
      description: '需要补货的物料',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: '盘点中任务',
      value: summary.counting_tasks.toString(),
      icon: ClipboardCheck,
      description: '进行中的盘点任务',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: '库存周转率',
      value: summary.turnover_rate.toFixed(2),
      icon: TrendingUp,
      description: '最近30天',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {card.title}
              </CardTitle>
              <div className={`p-2 rounded-full ${card.bgColor}`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
              <p className="text-xs text-gray-500 mt-1">{card.description}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default StockSummaryCards;
