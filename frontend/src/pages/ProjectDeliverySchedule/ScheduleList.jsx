/**
 * 项目交付排产计划 - 列表页面
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Table, Badge, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui';
import { projectDeliveryApi } from '@/services/api/projectDelivery';

export default function ProjectDeliveryScheduleList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [schedules, setSchedules] = useState([]);
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => { loadSchedules(); }, [statusFilter]);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const params = statusFilter !== 'ALL' ? { status: statusFilter } : {};
      const response = await projectDeliveryApi.getSchedules(params);
      setSchedules(response);
    } catch (error) { console.error('加载失败:', error); }
    finally { setLoading(false); }
  };

  const getStatusBadge = (status) => {
    const map = { DRAFT: { label: '草稿', variant: 'default' }, FILLING: { label: '填写中', variant: 'warning' }, REVIEWING: { label: '审核中', variant: 'warning' }, CONFIRMED: { label: '已确认', variant: 'success' } };
    const cfg = map[status] || { label: status, variant: 'default' };
    return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">项目交付排产计划</h1>
        <Button onClick={() => navigate('/project-delivery-schedule/new')}>+ 创建排产计划</Button>
      </div>
      <Card className="mb-6">
        <CardContent className="pt-6">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger><SelectValue placeholder="状态筛选" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">全部状态</SelectItem>
              <SelectItem value="DRAFT">草稿</SelectItem>
              <SelectItem value="FILLING">填写中</SelectItem>
              <SelectItem value="REVIEWING">审核中</SelectItem>
              <SelectItem value="CONFIRMED">已确认</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>排产计划列表</CardTitle></CardHeader>
        <CardContent>
          {loading ? <div className="text-center py-8">加载中...</div> :
           schedules.length === 0 ? <div className="text-center py-8 text-gray-500">暂无数据</div> : (
            <Table>
              <thead><tr><th>计划编号</th><th>计划名称</th><th>版本</th><th>状态</th><th>创建人</th><th>创建时间</th><th>操作</th></tr></thead>
              <tbody>
                {schedules.map(s => (
                  <tr key={s.id}>
                    <td>{s.schedule_no}</td><td>{s.schedule_name}</td><td>{s.version}</td>
                    <td>{getStatusBadge(s.status)}</td><td>{s.initiator_name}</td>
                    <td>{new Date(s.created_at).toLocaleDateString()}</td>
                    <td><Button size="sm" variant="outline" onClick={() => navigate(`/project-delivery-schedule/${s.id}`)}>查看</Button></td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
