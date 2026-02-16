/**
 * 物料预留管理页面
 * 查看和管理物料预留
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Plus, X, Package } from 'lucide-react';
import InventoryAPI from '@/services/inventory';
import { Reservation, ReservationStatus, ReserveRequest } from '@/types/inventory';
import { format } from 'date-fns';

const MaterialReservation: React.FC = () => {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<ReserveRequest>>({});

  useEffect(() => {
    loadReservations();
  }, []);

  const loadReservations = async () => {
    try {
      setLoading(true);
      // TODO: 实现实际的预留列表API
      setReservations([]);
    } catch (error) {
      console.error('加载预留列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReservation = async () => {
    try {
      if (!formData.material_id || !formData.quantity) {
        alert('请填写必填项');
        return;
      }
      await InventoryAPI.reserveMaterial(formData as ReserveRequest);
      setDialogOpen(false);
      setFormData({});
      loadReservations();
      alert('预留成功！');
    } catch (error: any) {
      alert(`预留失败: ${error.message}`);
    }
  };

  const handleCancelReservation = async (id: number) => {
    if (!confirm('确定要取消这个预留吗？')) return;
    try {
      await InventoryAPI.cancelReservation(id, '用户取消');
      loadReservations();
      alert('预留已取消');
    } catch (error: any) {
      alert(`取消失败: ${error.message}`);
    }
  };

  const getStatusBadge = (status: ReservationStatus) => {
    const badges: Record<ReservationStatus, { label: string; className: string }> = {
      [ReservationStatus.ACTIVE]: {
        label: '有效',
        className: 'bg-green-100 text-green-800',
      },
      [ReservationStatus.USED]: { label: '已使用', className: 'bg-blue-100 text-blue-800' },
      [ReservationStatus.CANCELLED]: {
        label: '已取消',
        className: 'bg-gray-100 text-gray-800',
      },
      [ReservationStatus.EXPIRED]: {
        label: '已过期',
        className: 'bg-red-100 text-red-800',
      },
    };
    const badge = badges[status];
    return <Badge className={badge.className}>{badge.label}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">物料预留管理</h1>
          <p className="text-gray-500 mt-1">管理项目和工单的物料预留</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-500 hover:bg-blue-600">
              <Plus className="h-4 w-4 mr-2" />
              创建预留
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>创建物料预留</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>物料ID *</Label>
                <Input
                  type="number"
                  placeholder="输入物料ID"
                  value={formData.material_id || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, material_id: Number(e.target.value) })
                  }
                />
              </div>
              <div>
                <Label>预留数量 *</Label>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="输入数量"
                  value={formData.quantity || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, quantity: Number(e.target.value) })
                  }
                />
              </div>
              <div>
                <Label>项目ID</Label>
                <Input
                  type="number"
                  placeholder="输入项目ID（可选）"
                  value={formData.project_id || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, project_id: Number(e.target.value) })
                  }
                />
              </div>
              <div>
                <Label>预计使用日期</Label>
                <Input
                  type="date"
                  value={formData.expected_use_date || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, expected_use_date: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>备注</Label>
                <Textarea
                  placeholder="输入备注（可选）"
                  value={formData.remark || ''}
                  onChange={(e) => setFormData({ ...formData, remark: e.target.value })}
                />
              </div>
              <Button onClick={handleCreateReservation} className="w-full">
                确认预留
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>预留ID</TableHead>
              <TableHead>物料名称</TableHead>
              <TableHead className="text-right">预留数量</TableHead>
              <TableHead className="text-right">已用数量</TableHead>
              <TableHead className="text-right">剩余数量</TableHead>
              <TableHead>项目/工单</TableHead>
              <TableHead>预计使用日期</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reservations.length > 0 ? (
              reservations.map((res) => (
                <TableRow key={res.id}>
                  <TableCell className="font-medium">{res.id}</TableCell>
                  <TableCell>{res.material_name}</TableCell>
                  <TableCell className="text-right">{res.quantity}</TableCell>
                  <TableCell className="text-right text-blue-600">
                    {res.used_quantity}
                  </TableCell>
                  <TableCell className="text-right text-green-600 font-medium">
                    {res.remaining_quantity}
                  </TableCell>
                  <TableCell className="text-sm">
                    {res.project_name || res.work_order_no || '-'}
                  </TableCell>
                  <TableCell>
                    {res.expected_use_date
                      ? format(new Date(res.expected_use_date), 'yyyy-MM-dd')
                      : '-'}
                  </TableCell>
                  <TableCell>
                    {format(new Date(res.created_at), 'yyyy-MM-dd')}
                  </TableCell>
                  <TableCell>{getStatusBadge(res.status)}</TableCell>
                  <TableCell>
                    {res.status === ReservationStatus.ACTIVE && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCancelReservation(res.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={10} className="text-center py-12">
                  <Package className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-gray-500">暂无预留记录</p>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default MaterialReservation;
