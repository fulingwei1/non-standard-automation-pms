/**
 * AI工作台主页面
 * Team 10: 售前AI系统集成与前端UI
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Plus,
  Brain,
  Workflow,
  TrendingUp,
  FileText,
  Filter,
} from 'lucide-react';
import { presaleAIService } from '@/services/presaleAIService';
import { presaleApi } from '@/services/api';
import { toast } from 'sonner';

const AIWorkbench = () => {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    try {
      setLoading(true);
      const response = await presaleApi.tickets.list({ page_size: 50 });
      const items = response.data?.items || response.data?.items || response.data || [];
      // Map backend ticket fields to component's expected shape
      const mapped = (items || []).map((t) => ({
        id: t.id,
        title: t.title || t.name || '',
        customer: t.customer_name || t.customer || '',
        status: t.status === 'COMPLETED' || t.status === 'completed'
          ? 'completed'
          : t.status === 'IN_PROGRESS' || t.status === 'in_progress' || t.status === 'ACCEPTED'
            ? 'in_progress'
            : 'pending',
        aiProgress: t.ai_progress ?? (t.status === 'COMPLETED' ? 100 : t.progress || 0),
        createdAt: t.created_at ? t.created_at.split('T')[0] : '',
        lastUpdated: t.updated_at ? t.updated_at.split('T')[0] : '',
      }));
      setTickets(mapped);
    } catch (error) {
      console.error('Failed to load tickets:', error);
      toast.error('加载工单失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStartWorkflow = async (ticketId) => {
    try {
      await presaleAIService.startWorkflow(ticketId, {}, true);
      toast.success('AI工作流已启动');
      loadTickets();
    } catch (error) {
      console.error('Failed to start workflow:', error);
      toast.error('启动工作流失败');
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: { label: '待处理', variant: 'secondary' },
      in_progress: { label: '进行中', variant: 'default' },
      completed: { label: '已完成', variant: 'success' },
    };
    const { label, variant } = variants[status] || variants.pending;
    return <Badge variant={variant}>{label}</Badge>;
  };

  const filteredTickets = (tickets || []).filter((ticket) => {
    const matchesSearch =
      ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.customer.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter =
      filterStatus === 'all' || ticket.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8" />
            AI工作台
          </h1>
          <p className="text-muted-foreground mt-1">
            智能化售前工作流管理
          </p>
        </div>
        <Button onClick={() => navigate('/presales-ai/workbench/new')}>
          <Plus className="h-4 w-4 mr-2" />
          新建工单
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">总工单</p>
                <p className="text-2xl font-bold">{tickets.length}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">进行中</p>
                <p className="text-2xl font-bold">
                  {(tickets || []).filter((t) => t.status === 'in_progress').length}
                </p>
              </div>
              <Workflow className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已完成</p>
                <p className="text-2xl font-bold">
                  {(tickets || []).filter((t) => t.status === 'completed').length}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">AI完成率</p>
                <p className="text-2xl font-bold">
                  {tickets.length > 0
                    ? Math.round(
                        (tickets || []).reduce((sum, t) => sum + t.aiProgress, 0) /
                          tickets.length
                      )
                    : 0}
                  %
                </p>
              </div>
              <Brain className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>售前工单列表</CardTitle>
            <div className="flex gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索工单..."
                  value={searchTerm || "unknown"}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <select
                value={filterStatus || "unknown"}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border rounded-md"
              >
                <option value="all">全部状态</option>
                <option value="pending">待处理</option>
                <option value="in_progress">进行中</option>
                <option value="completed">已完成</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>工单标题</TableHead>
                  <TableHead>客户</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>AI进度</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>最后更新</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(filteredTickets || []).map((ticket) => (
                  <TableRow
                    key={ticket.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() =>
                      navigate(`/presales-ai/workbench/ticket/${ticket.id}`)
                    }
                  >
                    <TableCell className="font-medium">{ticket.title}</TableCell>
                    <TableCell>{ticket.customer}</TableCell>
                    <TableCell>{getStatusBadge(ticket.status)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-secondary rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full"
                            style={{ width: `${ticket.aiProgress}%` }}
                          />
                        </div>
                        <span className="text-sm">{ticket.aiProgress}%</span>
                      </div>
                    </TableCell>
                    <TableCell>{ticket.createdAt}</TableCell>
                    <TableCell>{ticket.lastUpdated}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartWorkflow(ticket.id);
                        }}
                        disabled={ticket.aiProgress === 100}
                      >
                        <Workflow className="h-4 w-4 mr-1" />
                        启动AI
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AIWorkbench;
