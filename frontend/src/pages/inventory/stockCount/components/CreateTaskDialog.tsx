/**
 * 创建盘点任务对话框
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import InventoryAPI from '@/services/inventory';
import { CreateCountTaskRequest, CountTaskType } from '@/types/inventory';

interface CreateTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const CreateTaskDialog: React.FC<CreateTaskDialogProps> = ({
  open,
  onOpenChange,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<Partial<CreateCountTaskRequest>>({
    task_type: CountTaskType.FULL,
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!formData.task_name || !formData.scheduled_date) {
      alert('请填写必填项');
      return;
    }

    try {
      setLoading(true);
      await InventoryAPI.createCountTask(formData as CreateCountTaskRequest);
      onOpenChange(false);
      setFormData({ task_type: CountTaskType.FULL });
      onSuccess?.();
      alert('盘点任务创建成功！');
    } catch (error: any) {
      alert(`创建失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>创建盘点任务</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>任务名称 *</Label>
            <Input
              placeholder="例如：2026年2月月度盘点"
              value={formData.task_name || ''}
              onChange={(e) => setFormData({ ...formData, task_name: e.target.value })}
            />
          </div>

          <div>
            <Label>盘点类型 *</Label>
            <Select
              value={formData.task_type}
              onValueChange={(value) =>
                setFormData({ ...formData, task_type: value as CountTaskType })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={CountTaskType.FULL}>全盘</SelectItem>
                <SelectItem value={CountTaskType.SPOT}>抽盘</SelectItem>
                <SelectItem value={CountTaskType.CYCLE}>循环盘</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>盘点位置</Label>
            <Input
              placeholder="例如：仓库A（可选，留空表示全部）"
              value={formData.location || ''}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
          </div>

          <div>
            <Label>计划日期 *</Label>
            <Input
              type="date"
              value={formData.scheduled_date || ''}
              onChange={(e) =>
                setFormData({ ...formData, scheduled_date: e.target.value })
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

          <Button onClick={handleSubmit} disabled={loading} className="w-full">
            {loading ? '创建中...' : '创建任务'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CreateTaskDialog;
