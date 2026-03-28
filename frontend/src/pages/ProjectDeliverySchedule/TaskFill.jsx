/**
 * 项目交付排产计划 - 任务填写页面
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Badge, Alert } from '@/components/ui';
import { projectDeliveryApi } from '@/services/api/projectDelivery';

export default function ProjectDeliveryScheduleTaskFill() {
  const { scheduleId, department } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [conflicts, setConflicts] = useState([]);
  const [formData, setFormData] = useState({ task_type: department || 'MECHANICAL', task_name: '', machine_name: '', module_name: '', assigned_engineer_id: '', assigned_engineer_name: '', planned_start: '', planned_end: '', estimated_hours: '' });

  useEffect(() => { if (formData.assigned_engineer_id && formData.planned_start && formData.planned_end) checkConflicts(); }, [formData.assigned_engineer_id, formData.planned_start, formData.planned_end]);

  const checkConflicts = async () => {
    try { const data = await projectDeliveryApi.getConflicts(scheduleId); setConflicts(data.engineer_conflicts || []); }
    catch (error) { console.error('检测冲突失败:', error); }
  };

  const handleSubmit = async () => {
    try { setLoading(true); await projectDeliveryApi.createTask(scheduleId, formData); alert('任务创建成功！'); navigate(`/project-delivery-schedule/${scheduleId}`); }
    catch (error) { alert('创建失败：' + error.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-6">
      <div className="mb-6"><h1 className="text-2xl font-bold mb-2">填写任务 - {department}</h1><p className="text-gray-500">细化到具体工程师和时间</p></div>
      {conflicts.length > 0 && (
        <Alert variant="destructive" className="mb-6">
          <div className="font-bold">发现时间冲突</div>
          <ul className="list-disc list-inside mt-2">{conflicts.map((c, i) => <li key={i}>{c.engineer_name} - {c.task1_name} 与 {c.task2_name} 冲突（{c.overlap_days}天）</li>)}</ul>
          <div className="mt-2 text-sm">提示：允许带冲突提交，由项目经理协调</div>
        </Alert>
      )}
      <Card>
        <CardHeader><CardTitle>任务信息</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div><Label>任务类型</Label><Select value={formData.task_type} onValueChange={(v) => setFormData({...formData, task_type: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="MECHANICAL">机械设计</SelectItem><SelectItem value="ELECTRICAL">电气设计</SelectItem><SelectItem value="SOFTWARE">软件设计</SelectItem><SelectItem value="PURCHASE">采购</SelectItem><SelectItem value="PRODUCTION">生产</SelectItem></SelectContent></Select></div>
          <div><Label>任务名称 *</Label><Input value={formData.task_name} onChange={(e) => setFormData({...formData, task_name: e.target.value})} placeholder="如：3D 设计 - 机架模块" /></div>
          <div className="grid grid-cols-2 gap-4"><div><Label>机台名称</Label><Input value={formData.machine_name} onChange={(e) => setFormData({...formData, machine_name: e.target.value})} /></div><div><Label>模块名称</Label><Input value={formData.module_name} onChange={(e) => setFormData({...formData, module_name: e.target.value})} /></div></div>
          <div><Label>分配工程师 *</Label><Input value={formData.assigned_engineer_name} onChange={(e) => setFormData({...formData, assigned_engineer_name: e.target.value})} placeholder="输入工程师姓名" /></div>
          <div className="grid grid-cols-2 gap-4"><div><Label>计划开始日期 *</Label><Input type="date" value={formData.planned_start} onChange={(e) => setFormData({...formData, planned_start: e.target.value})} /></div><div><Label>计划结束日期 *</Label><Input type="date" value={formData.planned_end} onChange={(e) => setFormData({...formData, planned_end: e.target.value})} /></div></div>
          <div><Label>预估工时（小时）</Label><Input type="number" value={formData.estimated_hours} onChange={(e) => setFormData({...formData, estimated_hours: e.target.value})} placeholder="如：120" /></div>
          <div className="pt-4 flex gap-4"><Button onClick={handleSubmit} disabled={loading}>{loading ? '提交中...' : '提交任务'}</Button><Button variant="outline" onClick={() => navigate(-1)}>取消</Button></div>
        </CardContent>
      </Card>
    </div>
  );
}
