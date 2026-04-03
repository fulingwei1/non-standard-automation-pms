/**
 * 项目交付排产计划 - 创建页面
 * 
 * 使用角色：销售、售前、项目经理
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card, CardContent, CardHeader, CardTitle,
  Button, Input, Label, Select, SelectContent,
  SelectItem, SelectTrigger, SelectValue, Alert,
} from '@/components/ui';
import { projectDeliveryApi } from '@/services/api/projectDelivery';

export default function ProjectDeliveryScheduleCreate() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    schedule_name: '',
    lead_id: '',
    project_id: '',
    usage_type: 'BOTH',
    departments: ['MECHANICAL', 'ELECTRICAL', 'SOFTWARE', 'PURCHASE', 'PRODUCTION'],
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const data = {
        ...formData,
        lead_id: formData.lead_id ? parseInt(formData.lead_id) : null,
        project_id: formData.project_id ? parseInt(formData.project_id) : null,
      };
      
      const response = await projectDeliveryApi.createSchedule(data);
      alert('排产计划创建成功！');
      navigate(`/project-delivery-schedule/${response.id}`);
    } catch (error) {
      alert('创建失败：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">创建项目交付排产计划</h1>
        <p className="text-gray-500">销售/售前/项目经理均可创建</p>
      </div>

      <Alert className="mb-6">
        <div className="font-bold">使用说明</div>
        <ul className="list-disc list-inside mt-2 text-sm">
          <li>合同签订前创建：用于向客户展示交付能力和时间承诺</li>
          <li>合同签订后创建：作为项目执行的基准计划</li>
          <li>支持细化到工程师级别的任务分配</li>
          <li>支持长周期采购管理（&gt;60 天）</li>
        </ul>
      </Alert>

      <Card>
        <CardHeader><CardTitle>基本信息</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>计划名称 *</Label>
            <Input
              value={formData.schedule_name}
              onChange={(e) => handleInputChange('schedule_name', e.target.value)}
              placeholder="如：ICT 测试机台项目交付排产计划"
            />
          </div>

          <div>
            <Label>关联商机 ID（合同签订前）</Label>
            <Input
              type="number"
              value={formData.lead_id}
              onChange={(e) => handleInputChange('lead_id', e.target.value)}
              placeholder="输入商机 ID"
            />
          </div>

          <div>
            <Label>关联项目 ID（合同签订后）</Label>
            <Input
              type="number"
              value={formData.project_id}
              onChange={(e) => handleInputChange('project_id', e.target.value)}
              placeholder="输入项目 ID"
            />
          </div>

          <div>
            <Label>使用类型</Label>
            <Select value={formData.usage_type} onValueChange={(v) => handleInputChange('usage_type', v)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="INTERNAL">内部使用</SelectItem>
                <SelectItem value="CUSTOMER">客户使用</SelectItem>
                <SelectItem value="BOTH">内外共用</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="pt-4 flex gap-4">
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? '创建中...' : '创建排产计划'}
            </Button>
            <Button variant="outline" onClick={() => navigate(-1)}>取消</Button>
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader><CardTitle>参与部门</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {['MECHANICAL', 'ELECTRICAL', 'SOFTWARE', 'PURCHASE', 'PRODUCTION'].map(dept => (
              <div key={dept} className="flex items-center">
                <input
                  type="checkbox"
                  id={dept}
                  checked={formData.departments.includes(dept)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData(prev => ({ ...prev, departments: [...prev.departments, dept] }));
                    } else {
                      setFormData(prev => ({ ...prev, departments: prev.departments.filter(d => d !== dept) }));
                    }
                  }}
                  className="mr-2"
                />
                <Label htmlFor={dept}>
                  {dept === 'MECHANICAL' && '机械部'}
                  {dept === 'ELECTRICAL' && '电气部'}
                  {dept === 'SOFTWARE' && '软件部'}
                  {dept === 'PURCHASE' && '采购部'}
                  {dept === 'PRODUCTION' && '生产部'}
                </Label>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-4">
            选中的部门将收到填写通知，需细化到具体工程师和时间
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
