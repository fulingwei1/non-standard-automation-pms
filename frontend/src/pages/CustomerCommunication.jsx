/**
 * Customer Communication Management
 * 客户沟通历史管理 - 客服工程师高级功能
 *
 * 功能：
 * 1. 客户沟通记录创建、查看、编辑
 * 2. 沟通方式管理（电话、邮件、现场、微信、会议等）
 * 3. 沟通主题分类
 * 4. 沟通内容详细记录
 * 5. 后续跟进任务
 * 6. 沟通记录搜索和筛选
 * 7. 沟通统计分析
 */

import { useState, useMemo as _useMemo, useEffect, useCallback as _useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  Phone,
  Mail,
  MessageSquare,
  Calendar,
  User,
  Users,
  Clock,
  FileText,
  CheckCircle2,
  XCircle,
  RefreshCw,
  MapPin,
  Video,
  TrendingUp,
  Download,
  Star,
  AlertCircle,
  ChevronRight,
  Send,
  Tag } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { cn, formatDate } from "../lib/utils";
import { customerCommunicationApi, customerApi, userApi } from "../services/api";
import { toast } from "../components/ui/toast";
import {
  CustomerCommunicationOverview,
  COMMUNICATION_TYPE,
  COMMUNICATION_TYPE_LABELS,
  COMMUNICATION_PRIORITY,
  COMMUNICATION_PRIORITY_LABELS,
  COMMUNICATION_STATUS,
  COMMUNICATION_STATUS_LABELS,
  COMMUNICATION_TOPIC,
  COMMUNICATION_TOPIC_LABELS,
  CUSTOMER_SATISFACTION,
  CUSTOMER_SATISFACTION_LABELS,
  COMMUNICATION_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS,
  TOPIC_FILTER_OPTIONS,
  getCommunicationTypeIcon,
  getCommunicationStatusColor as _getCommunicationStatusColor,
  getPriorityColor as _getPriorityColor,
  getTopicColor as _getTopicColor,
  getSatisfactionColor as _getSatisfactionColor,
  validateCommunicationData } from
"../components/customer-communication";

// 配置常量 - 使用新的配置系统
import { confirmAction } from "@/lib/confirmAction";
const communicationTypeConfig = {
  [COMMUNICATION_TYPE.PHONE]: { label: COMMUNICATION_TYPE_LABELS[COMMUNICATION_TYPE.PHONE], icon: Phone },
  [COMMUNICATION_TYPE.EMAIL]: { label: COMMUNICATION_TYPE_LABELS[COMMUNICATION_TYPE.EMAIL], icon: Mail },
  [COMMUNICATION_TYPE.ON_SITE]: { label: COMMUNICATION_TYPE_LABELS[COMMUNICATION_TYPE.ON_SITE], icon: MapPin },
  [COMMUNICATION_TYPE.WECHAT]: { label: COMMUNICATION_TYPE_LABELS[COMMUNICATION_TYPE.WECHAT], icon: MessageSquare },
  [COMMUNICATION_TYPE.MEETING]: { label: COMMUNICATION_TYPE_LABELS[COMMUNICATION_TYPE.MEETING], icon: Users },
  [COMMUNICATION_TYPE.VIDEO_CALL]: { label: COMMUNICATION_TYPE_LABELS[COMMUNICATION_TYPE.VIDEO_CALL], icon: Video }
};

const priorityConfig = {
  [COMMUNICATION_PRIORITY.HIGH]: { label: COMMUNICATION_PRIORITY_LABELS[COMMUNICATION_PRIORITY.HIGH], color: "text-red-400", bg: "bg-red-500/20" },
  [COMMUNICATION_PRIORITY.MEDIUM]: { label: COMMUNICATION_PRIORITY_LABELS[COMMUNICATION_PRIORITY.MEDIUM], color: "text-yellow-400", bg: "bg-yellow-500/20" },
  [COMMUNICATION_PRIORITY.LOW]: { label: COMMUNICATION_PRIORITY_LABELS[COMMUNICATION_PRIORITY.LOW], color: "text-green-400", bg: "bg-green-500/20" }
};

const statusConfig = {
  [COMMUNICATION_STATUS.PENDING]: { label: COMMUNICATION_STATUS_LABELS[COMMUNICATION_STATUS.PENDING], color: "text-purple-400", bg: "bg-purple-500/20" },
  [COMMUNICATION_STATUS.IN_PROGRESS]: { label: COMMUNICATION_STATUS_LABELS[COMMUNICATION_STATUS.IN_PROGRESS], color: "text-blue-400", bg: "bg-blue-500/20" },
  [COMMUNICATION_STATUS.COMPLETED]: { label: COMMUNICATION_STATUS_LABELS[COMMUNICATION_STATUS.COMPLETED], color: "text-green-400", bg: "bg-green-500/20" },
  [COMMUNICATION_STATUS.FOLLOW_UP]: { label: COMMUNICATION_STATUS_LABELS[COMMUNICATION_STATUS.FOLLOW_UP], color: "text-orange-400", bg: "bg-orange-500/20" }
};

const satisfactionConfig = {
  [CUSTOMER_SATISFACTION.VERY_SATISFIED]: { label: CUSTOMER_SATISFACTION_LABELS[CUSTOMER_SATISFACTION.VERY_SATISFIED], color: "text-green-500", stars: 5 },
  [CUSTOMER_SATISFACTION.SATISFIED]: { label: CUSTOMER_SATISFACTION_LABELS[CUSTOMER_SATISFACTION.SATISFIED], color: "text-green-400", stars: 4 },
  [CUSTOMER_SATISFACTION.NEUTRAL]: { label: CUSTOMER_SATISFACTION_LABELS[CUSTOMER_SATISFACTION.NEUTRAL], color: "text-yellow-400", stars: 3 },
  [CUSTOMER_SATISFACTION.DISSATISFIED]: { label: CUSTOMER_SATISFACTION_LABELS[CUSTOMER_SATISFACTION.DISSATISFIED], color: "text-orange-400", stars: 2 },
  [CUSTOMER_SATISFACTION.VERY_DISSATISFIED]: { label: CUSTOMER_SATISFACTION_LABELS[CUSTOMER_SATISFACTION.VERY_DISSATISFIED], color: "text-red-400", stars: 1 }
};

export default function CustomerCommunication() {
  const [loading, setLoading] = useState(true);
  const [communications, setCommunications] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterTopic, setFilterTopic] = useState("");
  const [filterCustomer, setFilterCustomer] = useState("");
  const [dateFilter, setDateFilter] = useState({ start: "", end: "" });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedCommunication, setSelectedCommunication] = useState(null);
  const [formData, setFormData] = useState({
    customer_id: "",
    communication_type: COMMUNICATION_TYPE.PHONE,
    topic: COMMUNICATION_TOPIC.SUPPORT,
    priority: COMMUNICATION_PRIORITY.MEDIUM,
    subject: "",
    content: "",
    communication_date: new Date().toISOString().split('T')[0],
    duration_minutes: "",
    customer_feedback: "",
    satisfaction_rating: null,
    next_action: "",
    next_action_date: "",
    assigned_to: "",
    notes: ""
  });

  const [_stats, setStats] = useState({
    total: 0,
    pending: 0,
    in_progress: 0,
    completed: 0,
    follow_up: 0,
    high_priority: 0,
    today_count: 0,
    avg_satisfaction: 0
  });

  useEffect(() => {
    fetchData();
    fetchStats();
  }, [searchQuery, filterStatus, filterPriority, filterType, filterTopic, filterCustomer, dateFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        search: searchQuery,
        status: filterStatus || undefined,
        priority: filterPriority || undefined,
        communication_type: filterType || undefined,
        topic: filterTopic || undefined,
        customer_id: filterCustomer || undefined,
        start_date: dateFilter.start || undefined,
        end_date: dateFilter.end || undefined
      };

      const [commRes, customerRes, userRes] = await Promise.all([
      customerCommunicationApi.list(params),
      customerApi.list({ page_size: 1000 }),
      userApi.list({ page_size: 1000 })]
      );

      const commData = commRes.data?.items || commRes.data || [];
      const customerData = customerRes.data?.items || customerRes.data || [];
      const userData = userRes.data?.items || userRes.data || [];

      const transformedCommunications = commData.map((comm) => ({
        ...comm,
        customer: customerData.find((c) => c.id === comm.customer_id),
        assigned_user: userData.find((u) => u.id === comm.assigned_to)
      }));

      setCommunications(transformedCommunications);
      setCustomers(customerData);
      setUsers(userData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await customerCommunicationApi.statistics();
      setStats(res.data || {});
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const handleCreate = async () => {
    const validation = validateCommunicationData(formData);
    if (!validation.isValid) {
      toast.error(validation.errors.join(", "));
      return;
    }

    try {
      await customerCommunicationApi.create(formData);
      toast.success("沟通记录创建成功");
      setShowCreateDialog(false);
      resetForm();
      fetchData();
      fetchStats();
    } catch (error) {
      console.error("Failed to create communication:", error);
      toast.error("创建沟通记录失败");
    }
  };

  const handleUpdate = async () => {
    try {
      await customerCommunicationApi.update(selectedCommunication.id, formData);
      toast.success("沟通记录更新成功");
      setShowEditDialog(false);
      resetForm();
      fetchData();
      fetchStats();
    } catch (error) {
      console.error("Failed to update communication:", error);
      toast.error("更新沟通记录失败");
    }
  };

  const handleDelete = async (id) => {
    if (!await confirmAction("确定要删除这个沟通记录吗？")) {return;}

    try {
      await customerCommunicationApi.delete(id);
      toast.success("沟通记录删除成功");
      fetchData();
      fetchStats();
    } catch (error) {
      console.error("Failed to delete communication:", error);
      toast.error("删除沟通记录失败");
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: "",
      communication_type: COMMUNICATION_TYPE.PHONE,
      topic: COMMUNICATION_TOPIC.SUPPORT,
      priority: COMMUNICATION_PRIORITY.MEDIUM,
      subject: "",
      content: "",
      communication_date: new Date().toISOString().split('T')[0],
      duration_minutes: "",
      customer_feedback: "",
      satisfaction_rating: null,
      next_action: "",
      next_action_date: "",
      assigned_to: "",
      notes: ""
    });
    setSelectedCommunication(null);
  };

  const openEditDialog = (communication) => {
    setSelectedCommunication(communication);
    setFormData({
      customer_id: communication.customer_id,
      communication_type: communication.communication_type,
      topic: communication.topic,
      priority: communication.priority,
      subject: communication.subject,
      content: communication.content,
      communication_date: communication.communication_date,
      duration_minutes: communication.duration_minutes,
      customer_feedback: communication.customer_feedback,
      satisfaction_rating: communication.satisfaction_rating,
      next_action: communication.next_action,
      next_action_date: communication.next_action_date,
      assigned_to: communication.assigned_to,
      notes: communication.notes
    });
    setShowEditDialog(true);
  };

  // Helper functions for display
  const getStatusBadge = (status) => {
    const config = statusConfig[status];
    if (!config) {return <Badge variant="secondary">{status}</Badge>;}

    return (
      <Badge variant="secondary" className={cn("border-0", config.bg, config.color)}>
        {config.label}
      </Badge>);

  };

  const getPriorityBadge = (priority) => {
    const config = priorityConfig[priority];
    if (!config) {return <Badge variant="secondary">{priority}</Badge>;}

    return (
      <Badge variant="secondary" className={cn("border-0", config.bg, config.color)}>
        {config.label}
      </Badge>);

  };

  const getTypeDisplay = (type) => {
    const config = communicationTypeConfig[type];
    if (!config) {return type;}
    const Icon = config.icon;
    return (
      <div className="flex items-center space-x-1">
        <Icon className="h-4 w-4" />
        <span>{config.label}</span>
      </div>);

  };

  const getSatisfactionDisplay = (rating) => {
    if (!rating) {return <span className="text-gray-400">未评分</span>;}
    const config = satisfactionConfig[rating];
    if (!config) {return <span>{rating}</span>;}

    return (
      <div className="flex items-center space-x-1">
        <div className="flex">
          {Array.from({ length: 5 }, (_, i) =>
          <Star
            key={i}
            className={cn(
              "h-4 w-4",
              i < config.stars ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
            )} />

          )}
        </div>
        <span className={cn("text-sm", config.color)}>{config.label}</span>
      </div>);

  };

  // Quick action handlers for overview component
  const handleQuickAction = (action) => {
    switch (action) {
      case 'createCommunication':
        setShowCreateDialog(true);
        break;
      case 'viewPending':
        setFilterStatus(COMMUNICATION_STATUS.PENDING);
        break;
      case 'viewOverdue':
        // Filter for overdue communications
        {
          const today = new Date();
          const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
          setDateFilter({ start: '', end: weekAgo.toISOString().split('T')[0] });
        }
        break;
      case 'viewAnalytics':
        // Navigate to analytics view or show analytics dialog
        toast.info('统计分析功能开发中...');
        break;
      default:
        break;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="客户沟通管理"
        description="管理客户沟通记录、跟进和分析"
        actions={
        <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建沟通记录
        </Button>
        } />


      {/* Overview Section */}
      <CustomerCommunicationOverview
        communications={communications}
        customers={customers}
        onQuickAction={handleQuickAction} />


      {/* Filters Section */}
      <Card>
        <CardHeader>
          <CardTitle>沟通记录列表</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索沟通记录..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10" />

            </div>
            
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                {COMMUNICATION_FILTER_OPTIONS.map((option) =>
                <SelectItem key={option.value} value={option.value}>
                    {option.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger>
                <SelectValue placeholder="优先级" />
              </SelectTrigger>
              <SelectContent>
                {PRIORITY_FILTER_OPTIONS.map((option) =>
                <SelectItem key={option.value} value={option.value}>
                    {option.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="沟通方式" />
              </SelectTrigger>
              <SelectContent>
                {TYPE_FILTER_OPTIONS.map((option) =>
                <SelectItem key={option.value} value={option.value}>
                    {option.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={filterTopic} onValueChange={setFilterTopic}>
              <SelectTrigger>
                <SelectValue placeholder="主题" />
              </SelectTrigger>
              <SelectContent>
                {TOPIC_FILTER_OPTIONS.map((option) =>
                <SelectItem key={option.value} value={option.value}>
                    {option.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={filterCustomer} onValueChange={setFilterCustomer}>
              <SelectTrigger>
                <SelectValue placeholder="客户" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部客户</SelectItem>
                {customers.map((customer) =>
                <SelectItem key={customer.id} value={customer.id}>
                    {customer.name}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <Input
              type="date"
              placeholder="开始日期"
              value={dateFilter.start}
              onChange={(e) => setDateFilter({ ...dateFilter, start: e.target.value })} />

            <Input
              type="date"
              placeholder="结束日期"
              value={dateFilter.end}
              onChange={(e) => setDateFilter({ ...dateFilter, end: e.target.value })} />

          </div>

          {/* Communications Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>客户</TableHead>
                  <TableHead>主题</TableHead>
                  <TableHead>沟通方式</TableHead>
                  <TableHead>优先级</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>满意度</TableHead>
                  <TableHead>沟通日期</TableHead>
                  <TableHead>负责人</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ?
                <TableRow>
                    <TableCell colSpan={9} className="text-center py-8">
                      加载中...
                    </TableCell>
                </TableRow> :
                communications.length === 0 ?
                <TableRow>
                    <TableCell colSpan={9} className="text-center py-8">
                      暂无沟通记录
                    </TableCell>
                </TableRow> :

                communications.map((comm) =>
                <TableRow key={comm.id}>
                      <TableCell className="font-medium">
                        {comm.customer?.name || "未知客户"}
                      </TableCell>
                      <TableCell>
                        <div className="max-w-xs truncate">{comm.subject}</div>
                      </TableCell>
                      <TableCell>{getTypeDisplay(comm.communication_type)}</TableCell>
                      <TableCell>{getPriorityBadge(comm.priority)}</TableCell>
                      <TableCell>{getStatusBadge(comm.status)}</TableCell>
                      <TableCell>{getSatisfactionDisplay(comm.satisfaction_rating)}</TableCell>
                      <TableCell>{formatDate(comm.communication_date)}</TableCell>
                      <TableCell>{comm.assigned_user?.name || "未分配"}</TableCell>
                      <TableCell>
                        <div className="flex space-x-1">
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedCommunication(comm);
                          setShowDetailDialog(true);
                        }}>

                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(comm)}>

                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(comm.id)}>

                            <XCircle className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                </TableRow>
                )
                }
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">新建沟通记录</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-200">客户</label>
              <Select
                value={formData.customer_id}
                onValueChange={(value) =>
                setFormData({ ...formData, customer_id: value })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择客户" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {customers.map((customer) =>
                  <SelectItem key={customer.id} value={customer.id} className="text-white">
                      {customer.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-200">沟通方式</label>
              <Select
                value={formData.communication_type}
                onValueChange={(value) =>
                setFormData({ ...formData, communication_type: value })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择沟通方式" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {Object.entries(COMMUNICATION_TYPE).map(([_key, value]) =>
                  <SelectItem key={value} value={value} className="text-white">
                      {getCommunicationTypeIcon(value)} {COMMUNICATION_TYPE_LABELS[value]}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">主题</label>
              <Select
                value={formData.topic}
                onValueChange={(value) =>
                setFormData({ ...formData, topic: value })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择主题" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {Object.entries(COMMUNICATION_TOPIC).map(([_key, value]) =>
                  <SelectItem key={value} value={value} className="text-white">
                      {COMMUNICATION_TOPIC_LABELS[value]}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">优先级</label>
              <Select
                value={formData.priority}
                onValueChange={(value) =>
                setFormData({ ...formData, priority: value })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择优先级" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {Object.entries(COMMUNICATION_PRIORITY).map(([_key, value]) =>
                  <SelectItem key={value} value={value} className="text-white">
                      {COMMUNICATION_PRIORITY_LABELS[value]}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium text-gray-200">主题标题</label>
              <Input
                value={formData.subject}
                onChange={(e) =>
                setFormData({ ...formData, subject: e.target.value })
                }
                placeholder="输入沟通主题"
                className="bg-slate-800 border-slate-600 text-white" />

            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium text-gray-200">沟通内容</label>
              <Textarea
                value={formData.content}
                onChange={(e) =>
                setFormData({ ...formData, content: e.target.value })
                }
                placeholder="详细描述沟通内容"
                rows={4}
                className="bg-slate-800 border-slate-600 text-white" />

            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">沟通日期</label>
              <Input
                type="date"
                value={formData.communication_date}
                onChange={(e) =>
                setFormData({ ...formData, communication_date: e.target.value })
                }
                className="bg-slate-800 border-slate-600 text-white" />

            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">持续时间(分钟)</label>
              <Input
                type="number"
                value={formData.duration_minutes}
                onChange={(e) =>
                setFormData({ ...formData, duration_minutes: e.target.value })
                }
                placeholder="分钟"
                className="bg-slate-800 border-slate-600 text-white" />

            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">负责人</label>
              <Select
                value={formData.assigned_to}
                onValueChange={(value) =>
                setFormData({ ...formData, assigned_to: value })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择负责人" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {users.map((user) =>
                  <SelectItem key={user.id} value={user.id} className="text-white">
                      {user.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">满意度评分</label>
              <Select
                value={formData.satisfaction_rating?.toString() || ""}
                onValueChange={(value) =>
                setFormData({
                  ...formData,
                  satisfaction_rating: value ? parseInt(value) : null
                })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择满意度" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  <SelectItem value="__none__" className="text-white">未评分</SelectItem>
                  {Object.entries(CUSTOMER_SATISFACTION).map(([_key, value]) =>
                  <SelectItem key={value} value={value.toString()} className="text-white">
                      {CUSTOMER_SATISFACTION_LABELS[value]}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium text-gray-200">客户反馈</label>
              <Textarea
                value={formData.customer_feedback}
                onChange={(e) =>
                setFormData({ ...formData, customer_feedback: e.target.value })
                }
                placeholder="客户反馈内容"
                rows={3}
                className="bg-slate-800 border-slate-600 text-white" />

            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">后续行动</label>
              <Input
                value={formData.next_action}
                onChange={(e) =>
                setFormData({ ...formData, next_action: e.target.value })
                }
                placeholder="后续行动计划"
                className="bg-slate-800 border-slate-600 text-white" />

            </div>

            <div>
              <label className="text-sm font-medium text-gray-200">行动日期</label>
              <Input
                type="date"
                value={formData.next_action_date}
                onChange={(e) =>
                setFormData({ ...formData, next_action_date: e.target.value })
                }
                className="bg-slate-800 border-slate-600 text-white" />

            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium text-gray-200">备注</label>
              <Textarea
                value={formData.notes}
                onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="备注信息"
                rows={2}
                className="bg-slate-800 border-slate-600 text-white" />

            </div>
          </div>
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">沟通记录详情</DialogTitle>
          </DialogHeader>
          {selectedCommunication &&
          <div className="space-y-4 text-white">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-400">客户</label>
                  <p className="mt-1 text-sm">{selectedCommunication.customer?.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">沟通方式</label>
                  <p className="mt-1 text-sm">{getTypeDisplay(selectedCommunication.communication_type)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">主题</label>
                  <p className="mt-1 text-sm">{COMMUNICATION_TOPIC_LABELS[selectedCommunication.topic]}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">优先级</label>
                  <div className="mt-1">{getPriorityBadge(selectedCommunication.priority)}</div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">状态</label>
                  <div className="mt-1">{getStatusBadge(selectedCommunication.status)}</div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">满意度</label>
                  <div className="mt-1">{getSatisfactionDisplay(selectedCommunication.satisfaction_rating)}</div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">沟通日期</label>
                  <p className="mt-1 text-sm">{formatDate(selectedCommunication.communication_date)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">持续时间</label>
                  <p className="mt-1 text-sm">{selectedCommunication.duration_minutes} 分钟</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-400">负责人</label>
                  <p className="mt-1 text-sm">{selectedCommunication.assigned_user?.name || "未分配"}</p>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-400">主题标题</label>
                <p className="mt-1 text-sm font-medium">{selectedCommunication.subject}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-400">沟通内容</label>
                <p className="mt-1 text-sm whitespace-pre-wrap bg-slate-800 p-3 rounded">
                  {selectedCommunication.content}
                </p>
              </div>

              {selectedCommunication.customer_feedback &&
            <div>
                  <label className="text-sm font-medium text-gray-400">客户反馈</label>
                  <p className="mt-1 text-sm whitespace-pre-wrap bg-slate-800 p-3 rounded">
                    {selectedCommunication.customer_feedback}
                  </p>
            </div>
            }

              {selectedCommunication.next_action &&
            <div>
                  <label className="text-sm font-medium text-gray-400">后续行动</label>
                  <p className="mt-1 text-sm">{selectedCommunication.next_action}</p>
            </div>
            }

              {selectedCommunication.next_action_date &&
            <div>
                  <label className="text-sm font-medium text-gray-400">行动日期</label>
                  <p className="mt-1 text-sm">{formatDate(selectedCommunication.next_action_date)}</p>
            </div>
            }

              {selectedCommunication.notes &&
            <div>
                  <label className="text-sm font-medium text-gray-400">备注</label>
                  <p className="mt-1 text-sm whitespace-pre-wrap bg-slate-800 p-3 rounded">
                    {selectedCommunication.notes}
                  </p>
            </div>
            }
          </div>
          }
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">编辑沟通记录</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            {/* Form fields similar to create dialog */}
            <div>
              <label className="text-sm font-medium text-gray-200">客户</label>
              <Select
                value={formData.customer_id}
                onValueChange={(value) =>
                setFormData({ ...formData, customer_id: value })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择客户" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {customers.map((customer) =>
                  <SelectItem key={customer.id} value={customer.id} className="text-white">
                      {customer.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-200">沟通方式</label>
              <Select
                value={formData.communication_type}
                onValueChange={(value) =>
                setFormData({ ...formData, communication_type: value })
                }>

                <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                  <SelectValue placeholder="选择沟通方式" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {Object.entries(COMMUNICATION_TYPE).map(([_key, value]) =>
                  <SelectItem key={value} value={value} className="text-white">
                      {getCommunicationTypeIcon(value)} {COMMUNICATION_TYPE_LABELS[value]}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Additional form fields... */}
          </div>
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdate}>更新</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}
