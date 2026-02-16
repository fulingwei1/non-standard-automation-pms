/**
 * 库存总览仪表板
 * 展示库存关键指标和快捷操作
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, Clock } from 'lucide-react';
import StockSummaryCards from './components/StockSummaryCards';
import QuickActions from './components/QuickActions';
import InventoryAPI from '@/services/inventory';
import { StockSummary, Transaction, StockAlert } from '@/types/inventory';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<StockSummary | null>(null);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [alerts, setAlerts] = useState<StockAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // 加载统计数据
      const summaryData = await InventoryAPI.getDashboardSummary();
      setSummary(summaryData);

      // 加载最近交易（模拟，实际应该从API获取）
      // TODO: 添加实际的最近交易API
      setRecentTransactions([]);

      // 加载库存预警（模拟，实际应该从API获取）
      // TODO: 添加实际的预警API
      setAlerts([]);
    } catch (error) {
      console.error('加载仪表板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      PURCHASE_IN: '采购入库',
      RETURN_IN: '退料入库',
      ISSUE: '领料出库',
      TRANSFER: '库存转移',
      SCRAP: '报废',
      ADJUSTMENT: '库存调整',
    };
    return labels[type] || type;
  };

  const getTransactionTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      PURCHASE_IN: 'text-green-600',
      RETURN_IN: 'text-blue-600',
      ISSUE: 'text-red-600',
      TRANSFER: 'text-purple-600',
      SCRAP: 'text-gray-600',
      ADJUSTMENT: 'text-orange-600',
    };
    return colors[type] || 'text-gray-600';
  };

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">库存总览</h1>
        <p className="text-gray-500 mt-1">实时监控库存状态和关键指标</p>
      </div>

      {/* 统计卡片 */}
      <StockSummaryCards summary={summary!} loading={loading} />

      {/* 快捷操作 */}
      <QuickActions />

      <div className="grid gap-6 md:grid-cols-2">
        {/* 库存预警 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              库存预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
                ))}
              </div>
            ) : alerts.length > 0 ? (
              <div className="space-y-2">
                {alerts.map((alert, index) => (
                  <Alert key={index} variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <span className="font-medium">{alert.material_name}</span>
                      <br />
                      {alert.alert_message}
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <AlertTriangle className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>暂无预警信息</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 最近交易记录 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-500" />
              最近交易
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex justify-between items-center">
                    <div className="space-y-1 flex-1">
                      <div className="h-4 w-40 bg-gray-200 rounded animate-pulse" />
                      <div className="h-3 w-24 bg-gray-100 rounded animate-pulse" />
                    </div>
                    <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                  </div>
                ))}
              </div>
            ) : recentTransactions.length > 0 ? (
              <div className="space-y-3">
                {recentTransactions.map((transaction, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center border-b pb-2 last:border-0"
                  >
                    <div>
                      <p className="font-medium text-sm">{transaction.material_name}</p>
                      <p className="text-xs text-gray-500">
                        {getTransactionTypeLabel(transaction.transaction_type)} ·{' '}
                        {transaction.operator} ·{' '}
                        {formatDistanceToNow(new Date(transaction.transaction_date), {
                          addSuffix: true,
                          locale: zhCN,
                        })}
                      </p>
                    </div>
                    <span
                      className={`text-sm font-medium ${getTransactionTypeColor(
                        transaction.transaction_type
                      )}`}
                    >
                      {transaction.quantity > 0 ? '+' : ''}
                      {transaction.quantity}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Clock className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>暂无交易记录</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
