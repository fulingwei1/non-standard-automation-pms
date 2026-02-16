/**
 * 交易记录页面
 * 查看库存交易历史记录
 */

import React, { useEffect, useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { Search, RefreshCw, FileText } from 'lucide-react';
import InventoryAPI from '@/services/inventory';
import { Transaction, TransactionType } from '@/types/inventory';
import { format } from 'date-fns';

const TransactionHistory: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      // TODO: 实现实际的交易记录API查询
      // const data = await InventoryAPI.getTransactions(filters);
      setTransactions([]);
    } catch (error) {
      console.error('加载交易记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeBadge = (type: TransactionType) => {
    const badges: Record<TransactionType, { label: string; className: string }> = {
      [TransactionType.PURCHASE_IN]: {
        label: '采购入库',
        className: 'bg-green-100 text-green-800',
      },
      [TransactionType.RETURN_IN]: {
        label: '退料入库',
        className: 'bg-blue-100 text-blue-800',
      },
      [TransactionType.TRANSFER_IN]: {
        label: '调拨入库',
        className: 'bg-purple-100 text-purple-800',
      },
      [TransactionType.ISSUE]: {
        label: '领料出库',
        className: 'bg-red-100 text-red-800',
      },
      [TransactionType.SCRAP]: {
        label: '报废',
        className: 'bg-gray-100 text-gray-800',
      },
      [TransactionType.TRANSFER_OUT]: {
        label: '调拨出库',
        className: 'bg-orange-100 text-orange-800',
      },
      [TransactionType.ADJUSTMENT]: {
        label: '库存调整',
        className: 'bg-yellow-100 text-yellow-800',
      },
    };
    const badge = badges[type];
    return <Badge className={badge.className}>{badge.label}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">交易记录</h1>
        <p className="text-gray-500 mt-1">查看所有库存交易历史</p>
      </div>

      {/* 筛选栏 */}
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            placeholder="物料名称或编码"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <DatePickerWithRange value={dateRange} onChange={setDateRange} />
          <div className="flex gap-2">
            <Button onClick={loadTransactions} className="flex-1">
              <Search className="h-4 w-4 mr-2" />
              查询
            </Button>
            <Button variant="outline" onClick={() => setSearchText('')}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* 交易列表 */}
      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>交易时间</TableHead>
              <TableHead>交易类型</TableHead>
              <TableHead>物料名称</TableHead>
              <TableHead className="text-right">数量</TableHead>
              <TableHead className="text-right">单价</TableHead>
              <TableHead className="text-right">金额</TableHead>
              <TableHead>源位置</TableHead>
              <TableHead>目标位置</TableHead>
              <TableHead>批次号</TableHead>
              <TableHead>操作人</TableHead>
              <TableHead>备注</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.length > 0 ? (
              transactions.map((tx) => (
                <TableRow key={tx.id}>
                  <TableCell>
                    {format(new Date(tx.transaction_date), 'yyyy-MM-dd HH:mm')}
                  </TableCell>
                  <TableCell>{getTransactionTypeBadge(tx.transaction_type)}</TableCell>
                  <TableCell className="font-medium">{tx.material_name}</TableCell>
                  <TableCell className="text-right">{tx.quantity}</TableCell>
                  <TableCell className="text-right">¥{tx.unit_price.toFixed(2)}</TableCell>
                  <TableCell className="text-right font-medium">
                    ¥{tx.total_amount.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-sm">{tx.source_location || '-'}</TableCell>
                  <TableCell className="text-sm">{tx.target_location || '-'}</TableCell>
                  <TableCell className="text-sm">{tx.batch_number || '-'}</TableCell>
                  <TableCell>{tx.operator}</TableCell>
                  <TableCell className="text-sm text-gray-500">{tx.remark || '-'}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={11} className="text-center py-12">
                  <FileText className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-gray-500">暂无交易记录</p>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default TransactionHistory;
