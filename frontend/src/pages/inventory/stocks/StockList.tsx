/**
 * 库存查询页面
 * 提供库存列表查询、筛选、批次追溯等功能
 */

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Eye, Package } from 'lucide-react';
import StockFilterBar from './components/StockFilterBar';
import BatchTraceDialog from './components/BatchTraceDialog';
import InventoryAPI from '@/services/inventory';
import { Stock, StockStatus } from '@/types/inventory';

const StockList: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<any>({});
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
  });
  const [traceDialogOpen, setTraceDialogOpen] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState('');

  useEffect(() => {
    loadStocks();
  }, [pagination.page]);

  const loadStocks = async () => {
    try {
      setLoading(true);
      const response = await InventoryAPI.getStocks({
        ...filters,
        page: pagination.page,
        page_size: pagination.page_size,
      });
      setStocks(response.items);
      setPagination((prev) => ({
        ...prev,
        total: response.total,
      }));
    } catch (error) {
      console.error('加载库存数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPagination((prev) => ({ ...prev, page: 1 }));
    loadStocks();
  };

  const handleReset = () => {
    setFilters({});
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleExport = async () => {
    try {
      const blob = await InventoryAPI.exportStocks(filters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `库存数据_${new Date().toISOString().split('T')[0]}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出失败:', error);
    }
  };

  const handleBatchTrace = (batchNumber: string) => {
    setSelectedBatch(batchNumber);
    setTraceDialogOpen(true);
  };

  const getStatusBadge = (status: StockStatus) => {
    const badges: Record<StockStatus, { label: string; className: string }> = {
      [StockStatus.NORMAL]: { label: '正常', className: 'bg-green-100 text-green-800' },
      [StockStatus.LOW]: { label: '低库存', className: 'bg-orange-100 text-orange-800' },
      [StockStatus.EXPIRED]: { label: '已过期', className: 'bg-red-100 text-red-800' },
      [StockStatus.RESERVED]: { label: '已预留', className: 'bg-blue-100 text-blue-800' },
    };
    const badge = badges[status] || badges[StockStatus.NORMAL];
    return <Badge className={badge.className}>{badge.label}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">库存查询</h1>
        <p className="text-gray-500 mt-1">查询和管理库存信息</p>
      </div>

      {/* 筛选栏 */}
      <StockFilterBar
        filters={filters}
        onFilterChange={setFilters}
        onSearch={handleSearch}
        onReset={handleReset}
        onExport={handleExport}
        loading={loading}
      />

      {/* 库存列表 */}
      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>物料编码</TableHead>
              <TableHead>物料名称</TableHead>
              <TableHead>规格</TableHead>
              <TableHead className="text-right">库存数量</TableHead>
              <TableHead className="text-right">可用数量</TableHead>
              <TableHead className="text-right">预留数量</TableHead>
              <TableHead>单位</TableHead>
              <TableHead>批次号</TableHead>
              <TableHead>位置</TableHead>
              <TableHead className="text-right">单价</TableHead>
              <TableHead className="text-right">库存金额</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={13} className="text-center py-12">
                  <Package className="h-12 w-12 mx-auto mb-2 text-gray-300 animate-pulse" />
                  <p className="text-gray-500">加载中...</p>
                </TableCell>
              </TableRow>
            ) : stocks.length > 0 ? (
              stocks.map((stock) => (
                <TableRow key={stock.id}>
                  <TableCell className="font-medium">{stock.material_code}</TableCell>
                  <TableCell>{stock.material_name}</TableCell>
                  <TableCell className="text-gray-500 text-sm">
                    {stock.specification || '-'}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {stock.quantity.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right text-green-600 font-medium">
                    {stock.available_quantity.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right text-orange-600">
                    {stock.reserved_quantity.toLocaleString()}
                  </TableCell>
                  <TableCell>{stock.unit}</TableCell>
                  <TableCell>
                    {stock.batch_number ? (
                      <Button
                        variant="link"
                        className="p-0 h-auto text-blue-600"
                        onClick={() => handleBatchTrace(stock.batch_number!)}
                      >
                        {stock.batch_number}
                      </Button>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell className="text-sm">{stock.location}</TableCell>
                  <TableCell className="text-right">
                    ¥{stock.unit_price.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    ¥{stock.total_value.toLocaleString()}
                  </TableCell>
                  <TableCell>{getStatusBadge(stock.status)}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        // TODO: 查看详情
                      }}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={13} className="text-center py-12">
                  <Package className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-gray-500">暂无库存数据</p>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>

        {/* 分页 */}
        {pagination.total > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <div className="text-sm text-gray-500">
              共 {pagination.total} 条记录，第 {pagination.page} /{' '}
              {Math.ceil(pagination.total / pagination.page_size)} 页
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setPagination((prev) => ({ ...prev, page: prev.page - 1 }))
                }
                disabled={pagination.page === 1 || loading}
              >
                上一页
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setPagination((prev) => ({ ...prev, page: prev.page + 1 }))
                }
                disabled={
                  pagination.page >= Math.ceil(pagination.total / pagination.page_size) ||
                  loading
                }
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* 批次追溯对话框 */}
      <BatchTraceDialog
        open={traceDialogOpen}
        onOpenChange={setTraceDialogOpen}
        batchNumber={selectedBatch}
      />
    </div>
  );
};

export default StockList;
