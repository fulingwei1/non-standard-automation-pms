/**
 * 批次追溯对话框组件
 * 显示批次的完整追溯链
 */

import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, ArrowRight } from 'lucide-react';
import InventoryAPI from '@/services/inventory';
import { Transaction } from '@/types/inventory';
import { format } from 'date-fns';

interface BatchTraceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  batchNumber: string;
}

const BatchTraceDialog: React.FC<BatchTraceDialogProps> = ({
  open,
  onOpenChange,
  batchNumber,
}) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && batchNumber) {
      loadBatchTrace();
    }
  }, [open, batchNumber]);

  const loadBatchTrace = async () => {
    try {
      setLoading(true);
      const data = await InventoryAPI.traceBatch(batchNumber);
      setTransactions(data);
    } catch (error) {
      console.error('加载批次追溯失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      PURCHASE_IN: '采购入库',
      RETURN_IN: '退料入库',
      TRANSFER_IN: '调拨入库',
      ISSUE: '领料出库',
      SCRAP: '报废出库',
      TRANSFER_OUT: '调拨出库',
      ADJUSTMENT: '库存调整',
    };
    return labels[type] || type;
  };

  const getTransactionTypeBadge = (type: string) => {
    const variants: Record<string, any> = {
      PURCHASE_IN: { variant: 'default', className: 'bg-green-100 text-green-800' },
      RETURN_IN: { variant: 'default', className: 'bg-blue-100 text-blue-800' },
      TRANSFER_IN: { variant: 'default', className: 'bg-purple-100 text-purple-800' },
      ISSUE: { variant: 'default', className: 'bg-red-100 text-red-800' },
      SCRAP: { variant: 'default', className: 'bg-gray-100 text-gray-800' },
      TRANSFER_OUT: { variant: 'default', className: 'bg-orange-100 text-orange-800' },
      ADJUSTMENT: { variant: 'default', className: 'bg-yellow-100 text-yellow-800' },
    };
    return variants[type] || { variant: 'secondary' };
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>批次追溯</DialogTitle>
          <DialogDescription>批次号: {batchNumber}</DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : (
          <ScrollArea className="max-h-[500px] pr-4">
            <div className="space-y-4">
              {transactions.length > 0 ? (
                transactions.map((transaction, index) => {
                  const badgeProps = getTransactionTypeBadge(transaction.transaction_type);
                  return (
                    <div key={transaction.id} className="relative">
                      {/* 连接线 */}
                      {index < transactions.length - 1 && (
                        <div className="absolute left-6 top-12 bottom-0 w-0.5 bg-gray-200" />
                      )}

                      <div className="flex gap-4">
                        {/* 时间轴圆点 */}
                        <div className="flex flex-col items-center">
                          <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold z-10">
                            {index + 1}
                          </div>
                        </div>

                        {/* 交易详情卡片 */}
                        <div className="flex-1 bg-gray-50 rounded-lg p-4 border border-gray-200">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <Badge {...badgeProps} className={badgeProps.className}>
                                {getTransactionTypeLabel(transaction.transaction_type)}
                              </Badge>
                              <p className="text-sm text-gray-600 mt-1">
                                {format(new Date(transaction.transaction_date), 'yyyy-MM-dd HH:mm:ss')}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-medium">
                                数量: {transaction.quantity} {transaction.material_name}
                              </p>
                              <p className="text-xs text-gray-500">
                                金额: ¥{transaction.total_amount.toFixed(2)}
                              </p>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-2 text-sm mt-3">
                            {transaction.source_location && (
                              <div>
                                <span className="text-gray-500">源位置:</span>
                                <span className="ml-2 font-medium">
                                  {transaction.source_location}
                                </span>
                              </div>
                            )}
                            {transaction.target_location && (
                              <div>
                                <span className="text-gray-500">目标位置:</span>
                                <span className="ml-2 font-medium">
                                  {transaction.target_location}
                                </span>
                              </div>
                            )}
                            {transaction.work_order_no && (
                              <div>
                                <span className="text-gray-500">工单号:</span>
                                <span className="ml-2 font-medium">
                                  {transaction.work_order_no}
                                </span>
                              </div>
                            )}
                            {transaction.project_name && (
                              <div>
                                <span className="text-gray-500">项目:</span>
                                <span className="ml-2 font-medium">
                                  {transaction.project_name}
                                </span>
                              </div>
                            )}
                            <div className="col-span-2">
                              <span className="text-gray-500">操作人:</span>
                              <span className="ml-2 font-medium">{transaction.operator}</span>
                            </div>
                            {transaction.remark && (
                              <div className="col-span-2">
                                <span className="text-gray-500">备注:</span>
                                <span className="ml-2">{transaction.remark}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>暂无追溯记录</p>
                </div>
              )}
            </div>
          </ScrollArea>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default BatchTraceDialog;
