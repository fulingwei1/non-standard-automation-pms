/**
 * 售后服务中心
 * 功能：客户反馈/维修保养/技术支持工单
 */
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Table, Badge, Tabs, TabsContent, TabsList, TabsTrigger, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui';

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
        fetch(`/api/v1/after-sales/projects/${projectId}/feedback`).then(r => r.json()),
        fetch(`/api/v1/after-sales/projects/${projectId}/maintenance`).then(r => r.json()),
        fetch(`/api/v1/after-sales/projects/${projectId}/support-tickets`).then(r => r.json()),
      ]);
      setFeedbacks(fbRes || []);
      setMaintenance(mtRes || []);
      setTickets(tkRes || []);
    } catch (error) { console.error('加载失败:', error); }
    finally { setLoading(false); }
  };

  const getStatusBadge = (status) => {
    const map = { PENDING: 'warning', PROCESSING: 'warning', RESOLVED: 'success', CLOSED: 'default', OPEN: 'destructive', SCHEDULED: 'warning', COMPLETED: 'success', IN_PROGRESS: 'warning' };
    return <Badge variant={map[status] || 'default'}>{status}</Badge>;
  };

  if (loading) return <div className="p-6">加载中...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">售后服务中心</h1>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card><CardHeader><CardTitle className="text-sm">客户反馈</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{feedbacks.length}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">维修保养</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{maintenance.length}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">支持工单</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{tickets.length}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">待处理</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{feedbacks.filter(f => f.status === 'PENDING').length + tickets.filter(t => t.status === 'OPEN').length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="feedback">
        <TabsList><TabsTrigger value="feedback">客户反馈</TabsTrigger><TabsTrigger value="maintenance">维修保养</TabsTrigger><TabsTrigger value="tickets">支持工单</TabsTrigger></TabsList>

        <TabsContent value="feedback">
          <Card><CardHeader><CardTitle>客户反馈列表</CardTitle></CardHeader><CardContent>
            {feedbacks.length === 0 ? <div className="text-center py-8 text-gray-500">暂无反馈</div> : (
              <Table><thead><tr><th>类型</th><th>内容</th><th>优先级</th><th>状态</th><th>处理人</th><th>创建时间</th></tr></thead>
                <tbody>{feedbacks.map(f => (
                  <tr key={f.id}><td>{f.feedback_type}</td><td>{f.feedback_content?.substring(0, 50)}</td><td>{f.priority}</td><td>{getStatusBadge(f.status)}</td><td>{f.assignee_name || '-'}</td><td>{new Date(f.created_at).toLocaleDateString()}</td></tr>
                ))}</tbody></Table>
            )}
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="maintenance">
          <Card><CardHeader><CardTitle>维修保养记录</CardTitle></CardHeader><CardContent>
            {maintenance.length === 0 ? <div className="text-center py-8 text-gray-500">暂无记录</div> : (
              <Table><thead><tr><th>保养类型</th><th>保养内容</th><th>计划日期</th><th>状态</th><th>技术员</th></tr></thead>
                <tbody>{maintenance.map(m => (
                  <tr key={m.id}><td>{m.maintenance_type}</td><td>{m.maintenance_content?.substring(0, 50)}</td><td>{m.scheduled_date}</td><td>{getStatusBadge(m.status)}</td><td>{m.technician_name || '-'}</td></tr>
                ))}</tbody></Table>
            )}
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="tickets">
          <Card><CardHeader><CardTitle>技术支持工单</CardTitle></CardHeader><CardContent>
            {tickets.length === 0 ? <div className="text-center py-8 text-gray-500">暂无工单</div> : (
              <Table><thead><tr><th>工单号</th><th>主题</th><th>分类</th><th>优先级</th><th>状态</th><th>处理人</th><th>创建时间</th></tr></thead>
                <tbody>{tickets.map(t => (
                  <tr key={t.id}><td>{t.ticket_no}</td><td>{t.subject}</td><td>{t.category}</td><td>{t.priority}</td><td>{getStatusBadge(t.status)}</td><td>{t.assignee_name || '-'}</td><td>{new Date(t.created_at).toLocaleDateString()}</td></tr>
                ))}</tbody></Table>
            )}
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
