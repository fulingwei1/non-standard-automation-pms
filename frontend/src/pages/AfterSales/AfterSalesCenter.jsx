/**
 * 售后服务中心
 * 功能：客户反馈/维修保养/技术支持工单
 */
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Table, Badge, Tabs, TabsContent, TabsList, TabsTrigger, Button } from '@/components/ui';
import { api } from '../../services/api';

const asList = (payload) => {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.formatted?.items)) return payload.formatted.items;
  if (Array.isArray(payload?.formatted)) return payload.formatted;
  return [];
};

const formatDateCell = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString();
};

const ticketSubject = (ticket) => ticket.subject || ticket.title || ticket.problem_desc || '-';
const ticketCategory = (ticket) => ticket.category || ticket.problem_type || '-';
const ticketPriority = (ticket) => ticket.priority || ticket.urgency || '-';
const ticketAssignee = (ticket) => ticket.assignee_name || ticket.assigned_to_name || '-';

export default function AfterSalesCenter() {
  const { projectId } = useParams();
  const [loading, setLoading] = useState(true);
  const [feedbacks, setFeedbacks] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [tickets, setTickets] = useState([]);

  useEffect(() => { loadData(); }, [projectId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [fbRes, mtRes, tkRes] = await Promise.all([
        api.get(`/after-sales/projects/${projectId}/feedback`),
        api.get(`/after-sales/projects/${projectId}/maintenance`),
        api.get('/service/tickets', { params: { project_id: projectId } }),
      ]);
      setFeedbacks(asList(fbRes));
      setMaintenance(asList(mtRes));
      setTickets(asList(tkRes));
    } catch (error) {
      console.error('加载失败:', error);
      setFeedbacks([]);
      setMaintenance([]);
      setTickets([]);
    } finally { setLoading(false); }
  };

  const getStatusBadge = (status) => {
    const map = { PENDING: 'warning', PROCESSING: 'warning', RESOLVED: 'success', CLOSED: 'default', OPEN: 'destructive', SCHEDULED: 'warning', COMPLETED: 'success', IN_PROGRESS: 'warning' };
    return <Badge variant={map[status] || 'default'}>{status}</Badge>;
  };

  const runAction = async (request) => {
    try {
      await request();
      await loadData();
    } catch (error) {
      console.error('操作失败:', error);
    }
  };

  const updateFeedbackStatus = (feedbackId, nextStatus, extra = {}) =>
    runAction(() => api.put(`/after-sales/projects/${projectId}/feedback/${feedbackId}`, null, {
      params: { status: nextStatus, ...extra },
    }));

  const updateMaintenanceStatus = (maintenanceId, nextStatus) =>
    runAction(() => api.put(`/after-sales/projects/${projectId}/maintenance/${maintenanceId}`, null, {
      params: { status: nextStatus },
    }));

  const updateTicketStatus = (ticketId, nextStatus) =>
    runAction(() => api.put(`/service/tickets/${ticketId}/status`, null, {
      params: { status: nextStatus },
    }));

  const closeTicket = (ticket) =>
    runAction(() => api.put(`/service/tickets/${ticket.id}/close`, {
      solution: ticket.solution || ticket.problem_desc || ticket.subject || '售后中心关闭',
    }));

  if (loading) return <div className="p-6">加载中...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">售后服务中心</h1>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card><CardHeader><CardTitle className="text-sm">客户反馈</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{feedbacks.length}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">维修保养</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{maintenance.length}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">支持工单</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{tickets.length}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">待处理</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{feedbacks.filter(f => f.status === 'PENDING').length + tickets.filter(t => ['PENDING', 'OPEN'].includes(t.status)).length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="feedback">
        <TabsList><TabsTrigger value="feedback">客户反馈</TabsTrigger><TabsTrigger value="maintenance">维修保养</TabsTrigger><TabsTrigger value="tickets">支持工单</TabsTrigger></TabsList>

        <TabsContent value="feedback">
          <Card><CardHeader><CardTitle>客户反馈列表</CardTitle></CardHeader><CardContent>
            {feedbacks.length === 0 ? <div className="text-center py-8 text-gray-500">暂无反馈</div> : (
              <Table><thead><tr><th>类型</th><th>内容</th><th>优先级</th><th>状态</th><th>处理人</th><th>创建时间</th><th>操作</th></tr></thead>
                <tbody>{feedbacks.map(f => (
                  <tr key={f.id}><td>{f.feedback_type}</td><td>{f.feedback_content?.substring(0, 50)}</td><td>{f.priority}</td><td>{getStatusBadge(f.status)}</td><td>{f.assignee_name || '-'}</td><td>{formatDateCell(f.created_at)}</td><td className="space-x-2">{f.status === 'PENDING' && <Button size="sm" variant="outline" onClick={() => updateFeedbackStatus(f.id, 'PROCESSING')}>开始处理</Button>}{f.status === 'PROCESSING' && <Button size="sm" variant="success" onClick={() => updateFeedbackStatus(f.id, 'RESOLVED', { resolution: '已处理' })}>标记解决</Button>}{f.status === 'RESOLVED' && <Button size="sm" variant="secondary" onClick={() => updateFeedbackStatus(f.id, 'CLOSED')}>关闭反馈</Button>}</td></tr>
                ))}</tbody></Table>
            )}
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="maintenance">
          <Card><CardHeader><CardTitle>维修保养记录</CardTitle></CardHeader><CardContent>
            {maintenance.length === 0 ? <div className="text-center py-8 text-gray-500">暂无记录</div> : (
              <Table><thead><tr><th>保养类型</th><th>保养内容</th><th>计划日期</th><th>状态</th><th>技术员</th><th>操作</th></tr></thead>
                <tbody>{maintenance.map(m => (
                  <tr key={m.id}><td>{m.maintenance_type}</td><td>{m.maintenance_content?.substring(0, 50)}</td><td>{m.scheduled_date}</td><td>{getStatusBadge(m.status)}</td><td>{m.technician_name || '-'}</td><td className="space-x-2">{m.status === 'SCHEDULED' && <Button size="sm" variant="outline" onClick={() => updateMaintenanceStatus(m.id, 'IN_PROGRESS')}>开始保养</Button>}{m.status === 'IN_PROGRESS' && <Button size="sm" variant="success" onClick={() => updateMaintenanceStatus(m.id, 'COMPLETED')}>完成保养</Button>}</td></tr>
                ))}</tbody></Table>
            )}
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="tickets">
          <Card><CardHeader><CardTitle>技术支持工单</CardTitle></CardHeader><CardContent>
            {tickets.length === 0 ? <div className="text-center py-8 text-gray-500">暂无工单</div> : (
              <Table><thead><tr><th>工单号</th><th>主题</th><th>分类</th><th>优先级</th><th>状态</th><th>处理人</th><th>创建时间</th><th>操作</th></tr></thead>
                <tbody>{tickets.map(t => (
                  <tr key={t.id}><td>{t.ticket_no}</td><td>{ticketSubject(t)}</td><td>{ticketCategory(t)}</td><td>{ticketPriority(t)}</td><td>{getStatusBadge(t.status)}</td><td>{ticketAssignee(t)}</td><td>{formatDateCell(t.created_at)}</td><td className="space-x-2">{t.status === 'PENDING' && <Button size="sm" variant="outline" onClick={() => updateTicketStatus(t.id, 'IN_PROGRESS')}>开始处理</Button>}{t.status === 'IN_PROGRESS' && <Button size="sm" variant="success" onClick={() => updateTicketStatus(t.id, 'RESOLVED')}>标记解决</Button>}{t.status === 'RESOLVED' && <Button size="sm" variant="secondary" onClick={() => closeTicket(t)}>关闭工单</Button>}</td></tr>
                ))}</tbody></Table>
            )}
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
