/**
 * 快捷操作按钮组件
 * 提供常用的库存操作快捷入口
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  PackagePlus,
  PackageMinus,
  ArrowRightLeft,
  ClipboardCheck,
  BarChart3,
  Search,
} from 'lucide-react';

const QuickActions: React.FC = () => {
  const navigate = useNavigate();

  const actions = [
    {
      title: '领料出库',
      icon: PackageMinus,
      color: 'bg-red-500 hover:bg-red-600',
      onClick: () => navigate('/inventory/operations/issue'),
    },
    {
      title: '退料入库',
      icon: PackagePlus,
      color: 'bg-green-500 hover:bg-green-600',
      onClick: () => navigate('/inventory/operations/return'),
    },
    {
      title: '库存转移',
      icon: ArrowRightLeft,
      color: 'bg-blue-500 hover:bg-blue-600',
      onClick: () => navigate('/inventory/operations/transfer'),
    },
    {
      title: '库存盘点',
      icon: ClipboardCheck,
      color: 'bg-purple-500 hover:bg-purple-600',
      onClick: () => navigate('/inventory/stockCount/tasks'),
    },
    {
      title: '库存查询',
      icon: Search,
      color: 'bg-indigo-500 hover:bg-indigo-600',
      onClick: () => navigate('/inventory/stocks/list'),
    },
    {
      title: '库存分析',
      icon: BarChart3,
      color: 'bg-orange-500 hover:bg-orange-600',
      onClick: () => navigate('/inventory/analysis/turnover'),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">快捷操作</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {actions.map((action, index) => {
            const Icon = action.icon;
            return (
              <Button
                key={index}
                onClick={action.onClick}
                className={`${action.color} text-white flex flex-col items-center justify-center h-20 space-y-2`}
                variant="default"
              >
                <Icon className="h-6 w-6" />
                <span className="text-xs font-medium">{action.title}</span>
              </Button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default QuickActions;
