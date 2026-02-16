/**
 * 盘点录入表单组件
 * 用于批量录入实盘数量
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CountDetail } from '@/types/inventory';

interface CountInputFormProps {
  details: CountDetail[];
  onBatchUpdate: (updates: Array<{ id: number; actual_quantity: number }>) => Promise<void>;
}

const CountInputForm: React.FC<CountInputFormProps> = ({ details, onBatchUpdate }) => {
  const [inputs, setInputs] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(false);

  const handleInputChange = (detailId: number, value: string) => {
    setInputs({ ...inputs, [detailId]: value });
  };

  const handleBatchSubmit = async () => {
    const updates = Object.entries(inputs)
      .map(([id, value]) => ({
        id: Number(id),
        actual_quantity: parseFloat(value),
      }))
      .filter((u) => !isNaN(u.actual_quantity));

    if (updates.length === 0) {
      alert('请至少录入一项数据');
      return;
    }

    try {
      setLoading(true);
      await onBatchUpdate(updates);
      setInputs({});
      alert(`成功录入 ${updates.length} 项数据`);
    } catch (error: any) {
      alert(`批量录入失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-2">
        {details.map((detail) => (
          <div key={detail.id} className="flex items-center gap-2">
            <span className="text-sm w-48 truncate">{detail.material_name}</span>
            <span className="text-sm text-gray-500 w-24">
              账面: {detail.book_quantity}
            </span>
            <Input
              type="number"
              step="0.01"
              placeholder="实盘数量"
              className="w-32"
              value={inputs[detail.id] || ''}
              onChange={(e) => handleInputChange(detail.id, e.target.value)}
            />
          </div>
        ))}
      </div>
      <Button onClick={handleBatchSubmit} disabled={loading} className="w-full">
        {loading ? '提交中...' : '批量提交'}
      </Button>
    </div>
  );
};

export default CountInputForm;
