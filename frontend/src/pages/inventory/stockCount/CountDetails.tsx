/**
 * 盘点明细页面
 * 录入实盘数量并显示差异
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, CheckCircle, AlertTriangle } from 'lucide-react';
import InventoryAPI from '@/services/inventory';
import { CountTask, CountDetail } from '@/types/inventory';

const CountDetailsPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<CountTask | null>(null);
  const [details, setDetails] = useState<CountDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [inputValue, setInputValue] = useState('');

  useEffect(() => {
    if (taskId) {
      loadTaskDetails();
    }
  }, [taskId]);

  const loadTaskDetails = async () => {
    try {
      setLoading(true);
      const [taskData, detailsData] = await Promise.all([
        InventoryAPI.getCountTaskById(Number(taskId)),
        InventoryAPI.getCountDetails(Number(taskId)),
      ]);
      setTask(taskData);
      setDetails(detailsData);
    } catch (error) {
      console.error('加载盘点明细失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartEdit = (detail: CountDetail) => {
    setEditingId(detail.id);
    setInputValue(detail.actual_quantity?.toString() || '');
  };

  const handleSaveEdit = async (detailId: number) => {
    try {
      const actualQty = parseFloat(inputValue);
      if (isNaN(actualQty)) {
        alert('请输入有效数字');
        return;
      }
      await InventoryAPI.updateCountDetail(detailId, { actual_quantity: actualQty });
      setEditingId(null);
      loadTaskDetails();
    } catch (error: any) {
      alert(`保存失败: ${error.message}`);
    }
  };

  const handleApprove = async () => {
    if (!confirm('确定批准此盘点任务并调整库存吗？')) return;
    try {
      await InventoryAPI.approveCountTask(Number(taskId));
      alert('盘点任务已批准，库存已调整');
      navigate('/inventory/stockCount/tasks');
    } catch (error: any) {
      alert(`批准失败: ${error.message}`);
    }
  };

  const getDifferenceCell = (difference?: number, differenceValue?: number) => {
    if (difference === undefined) return '-';
    if (difference === 0) {
      return <span className="text-gray-500">0</span>;
    }
    const color = difference > 0 ? 'text-green-600' : 'text-red-600';
    return (
      <div className={`font-medium ${color}`}>
        <div>{difference > 0 ? '+' : ''}{difference}</div>
        {differenceValue !== undefined && (
          <div className="text-xs">
            ¥{differenceValue > 0 ? '+' : ''}{differenceValue.toFixed(2)}
          </div>
        )}
      </div>
    );
  };

  const totalDifference = details.reduce(
    (sum, d) => sum + (d.difference_value || 0),
    0
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              盘点明细 - {task?.task_name}
            </h1>
            <p className="text-gray-500 mt-1">任务编号: {task?.task_no}</p>
          </div>
        </div>
        {task?.status === 'COMPLETED' && (
          <Button onClick={handleApprove} className="bg-green-500 hover:bg-green-600">
            <CheckCircle className="h-4 w-4 mr-2" />
            批准调整
          </Button>
        )}
      </div>

      {/* 汇总信息 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600">盘点物料数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{details.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600">已录入数量</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {details.filter((d) => d.actual_quantity !== null).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600">差异项目数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {details.filter((d) => d.difference && d.difference !== 0).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600">差异金额</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                totalDifference >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              ¥{totalDifference >= 0 ? '+' : ''}
              {totalDifference.toFixed(2)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 盘点明细表 */}
      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>物料编码</TableHead>
              <TableHead>物料名称</TableHead>
              <TableHead>位置</TableHead>
              <TableHead>批次号</TableHead>
              <TableHead className="text-right">账面数量</TableHead>
              <TableHead className="text-right">实盘数量</TableHead>
              <TableHead className="text-right">差异</TableHead>
              <TableHead className="text-right">单价</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {details.map((detail) => (
              <TableRow
                key={detail.id}
                className={
                  detail.difference && detail.difference !== 0 ? 'bg-orange-50' : ''
                }
              >
                <TableCell className="font-medium">{detail.material_code}</TableCell>
                <TableCell>{detail.material_name}</TableCell>
                <TableCell className="text-sm">{detail.location}</TableCell>
                <TableCell className="text-sm">{detail.batch_number || '-'}</TableCell>
                <TableCell className="text-right font-medium">
                  {detail.book_quantity}
                </TableCell>
                <TableCell className="text-right">
                  {editingId === detail.id ? (
                    <Input
                      type="number"
                      step="0.01"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      className="w-24"
                      autoFocus
                    />
                  ) : detail.actual_quantity !== null ? (
                    <span className="font-medium text-blue-600">
                      {detail.actual_quantity}
                    </span>
                  ) : (
                    <span className="text-gray-400">未录入</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {getDifferenceCell(detail.difference, detail.difference_value)}
                </TableCell>
                <TableCell className="text-right">
                  ¥{detail.unit_price.toFixed(2)}
                </TableCell>
                <TableCell>
                  {editingId === detail.id ? (
                    <div className="flex gap-1">
                      <Button size="sm" onClick={() => handleSaveEdit(detail.id)}>
                        保存
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingId(null)}
                      >
                        取消
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleStartEdit(detail)}
                    >
                      录入
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default CountDetailsPage;
