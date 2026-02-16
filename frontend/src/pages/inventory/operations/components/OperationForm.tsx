/**
 * 物料操作表单组件（共享）
 * 用于领料、退料、转移等操作
 */

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { CostMethod } from '@/types/inventory';

const issueSchema = z.object({
  material_id: z.number().min(1, '请选择物料'),
  quantity: z.number().min(0.01, '数量必须大于0'),
  location: z.string().min(1, '请输入仓库位置'),
  work_order_no: z.string().optional(),
  project_id: z.number().optional(),
  cost_method: z.nativeEnum(CostMethod).optional(),
  reservation_id: z.number().optional(),
  remark: z.string().optional(),
});

const returnSchema = z.object({
  material_id: z.number().min(1, '请选择物料'),
  quantity: z.number().min(0.01, '数量必须大于0'),
  location: z.string().min(1, '请输入仓库位置'),
  batch_number: z.string().optional(),
  work_order_id: z.number().optional(),
  remark: z.string().optional(),
});

const transferSchema = z.object({
  material_id: z.number().min(1, '请选择物料'),
  quantity: z.number().min(0.01, '数量必须大于0'),
  from_location: z.string().min(1, '请输入源位置'),
  to_location: z.string().min(1, '请输入目标位置'),
  batch_number: z.string().optional(),
  remark: z.string().optional(),
});

type OperationType = 'issue' | 'return' | 'transfer';

interface OperationFormProps {
  type: OperationType;
  onSubmit: (data: any) => Promise<void>;
  loading?: boolean;
}

const OperationForm: React.FC<OperationFormProps> = ({ type, onSubmit, loading }) => {
  const getSchema = () => {
    switch (type) {
      case 'issue':
        return issueSchema;
      case 'return':
        return returnSchema;
      case 'transfer':
        return transferSchema;
      default:
        return issueSchema;
    }
  };

  const form = useForm({
    resolver: zodResolver(getSchema()),
    defaultValues: {
      material_id: 0,
      quantity: 0,
      location: '',
      remark: '',
    },
  });

  const getTitle = () => {
    const titles = {
      issue: '领料出库',
      return: '退料入库',
      transfer: '库存转移',
    };
    return titles[type];
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* 物料选择 */}
        <FormField
          control={form.control}
          name="material_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>物料 *</FormLabel>
              <Select
                onValueChange={(value) => field.onChange(Number(value))}
                value={field.value?.toString()}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="选择物料" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {/* TODO: 从API加载物料列表 */}
                  <SelectItem value="1">示例物料 1</SelectItem>
                  <SelectItem value="2">示例物料 2</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* 数量 */}
        <FormField
          control={form.control}
          name="quantity"
          render={({ field }) => (
            <FormItem>
              <FormLabel>数量 *</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="输入数量"
                  {...field}
                  onChange={(e) => field.onChange(parseFloat(e.target.value))}
                />
              </FormControl>
              <FormDescription>请输入{getTitle()}数量</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* 位置字段 */}
        {type === 'transfer' ? (
          <>
            <FormField
              control={form.control}
              name="from_location"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>源位置 *</FormLabel>
                  <FormControl>
                    <Input placeholder="例如: 仓库A-01货架" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="to_location"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>目标位置 *</FormLabel>
                  <FormControl>
                    <Input placeholder="例如: 仓库B-05货架" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </>
        ) : (
          <FormField
            control={form.control}
            name="location"
            render={({ field }) => (
              <FormItem>
                <FormLabel>仓库位置 *</FormLabel>
                <FormControl>
                  <Input placeholder="例如: 仓库A-01货架" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        {/* 领料特有字段 */}
        {type === 'issue' && (
          <>
            <FormField
              control={form.control}
              name="work_order_no"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>工单号</FormLabel>
                  <FormControl>
                    <Input placeholder="输入工单号" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="cost_method"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>成本核算方法</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择核算方法" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value={CostMethod.FIFO}>先进先出(FIFO)</SelectItem>
                      <SelectItem value={CostMethod.LIFO}>后进先出(LIFO)</SelectItem>
                      <SelectItem value={CostMethod.WEIGHTED_AVG}>
                        加权平均
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>推荐使用先进先出方法</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </>
        )}

        {/* 批次号 */}
        {(type === 'return' || type === 'transfer') && (
          <FormField
            control={form.control}
            name="batch_number"
            render={({ field }) => (
              <FormItem>
                <FormLabel>批次号</FormLabel>
                <FormControl>
                  <Input placeholder="输入批次号（可选）" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        {/* 备注 */}
        <FormField
          control={form.control}
          name="remark"
          render={({ field }) => (
            <FormItem>
              <FormLabel>备注</FormLabel>
              <FormControl>
                <Textarea placeholder="输入备注信息（可选）" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex gap-4">
          <Button type="submit" disabled={loading} className="flex-1">
            {loading ? '提交中...' : `确认${getTitle()}`}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => form.reset()}
            disabled={loading}
          >
            重置
          </Button>
        </div>
      </form>
    </Form>
  );
};

export default OperationForm;
