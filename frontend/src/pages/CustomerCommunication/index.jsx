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

import {
  Phone, Mail, MessageSquare, Users, MapPin, Video,
} from "lucide-react";
import { cn, formatDate } from "../../lib/utils";
import {
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
} from "../../components/customer-communication";
import { useCustomerCommunicationPage } from './hooks';
import CommunicationFormFields from './components/CommunicationFormFields';
import CommunicationDetailView from './components/CommunicationDetailView';

// 本地配置常量（映射lucide图标到沟通类型）
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

// 显示辅助函数
function getStatusBadge(status) {
  const config = statusConfig[status];
  if (!config) return <Badge variant="secondary">{status}</Badge>;
  return <Badge variant="secondary" className={cn("border-0", config.bg, config.color)}>{config.label}</Badge>;
}

function getPriorityBadge(priority) {
  const config = priorityConfig[priority];
  if (!config) return <Badge variant="secondary">{priority}</Badge>;
  return <Badge variant="secondary" className={cn("border-0", config.bg, config.color)}>{config.label}</Badge>;
}

function getTypeDisplay(type) {
  const config = communicationTypeConfig[type];
  if (!config) return type;
  const Icon = config.icon;
  return <div className="flex items-center space-x-1"><Icon className="h-4 w-4" /><span>{config.label}</span></div>;
}

function getSatisfactionDisplay(rating) {
  if (!rating) return <span className="text-gray-400">未评分</span>;
  const config = satisfactionConfig[rating];
  if (!config) return <span>{rating}</span>;
  return (
    <div className="flex items-center space-x-1">
      <div className="flex">
        {Array.from({ length: 5 }, (_, i) => <Star key={i} className={cn("h-4 w-4", i < config.stars ? "fill-yellow-400 text-yellow-400" : "text-gray-300")} />)}
      </div>
      <span className={cn("text-sm", config.color)}>{config.label}</span>
    </div>
  );
}

export default function CustomerCommunication() {
  const cc = useCustomerCommunicationPage();

  return (
    <div className="space-y-6">
      <PageHeader
        title="客户沟通管理"
        description="管理客户沟通记录、跟进和分析"
        actions={<Button onClick={() => cc.setShowCreateDialog(true)}><Plus className="mr-2 h-4 w-4" />新建沟通记录</Button>}
      />

      {/* 概览 */}
      <CustomerCommunicationOverview communications={cc.communications} customers={cc.customers} onQuickAction={cc.handleQuickAction} />

      {/* 过滤和列表 */}
      <Card>
        <CardHeader><CardTitle>沟通记录列表</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input placeholder="搜索沟通记录..." value={cc.searchQuery} onChange={(e) => cc.setSearchQuery(e.target.value)} className="pl-10" />
            </div>
            <Select value={cc.filterStatus || "all"} onValueChange={(v) => cc.setFilterStatus(v === "all" ? "" : v)}>
              <SelectTrigger><SelectValue placeholder="状态" /></SelectTrigger>
              <SelectContent>{COMMUNICATION_FILTER_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={cc.filterPriority || "all"} onValueChange={(v) => cc.setFilterPriority(v === "all" ? "" : v)}>
              <SelectTrigger><SelectValue placeholder="优先级" /></SelectTrigger>
              <SelectContent>{PRIORITY_FILTER_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={cc.filterType || "all"} onValueChange={(v) => cc.setFilterType(v === "all" ? "" : v)}>
              <SelectTrigger><SelectValue placeholder="沟通方式" /></SelectTrigger>
              <SelectContent>{TYPE_FILTER_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={cc.filterTopic || "all"} onValueChange={(v) => cc.setFilterTopic(v === "all" ? "" : v)}>
              <SelectTrigger><SelectValue placeholder="主题" /></SelectTrigger>
              <SelectContent>{TOPIC_FILTER_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={cc.filterCustomer ? String(cc.filterCustomer) : "__all__"} onValueChange={(v) => cc.setFilterCustomer(v === "__all__" ? "" : v)}>
              <SelectTrigger><SelectValue placeholder="客户" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部客户</SelectItem>
                {(cc.customers || []).map((c) => <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <Input type="date" placeholder="开始日期" value={cc.dateFilter.start} onChange={(e) => cc.setDateFilter({ ...cc.dateFilter, start: e.target.value })} />
            <Input type="date" placeholder="结束日期" value={cc.dateFilter.end} onChange={(e) => cc.setDateFilter({ ...cc.dateFilter, end: e.target.value })} />
          </div>

          {/* 表格 */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>客户</TableHead><TableHead>主题</TableHead><TableHead>沟通方式</TableHead>
                  <TableHead>优先级</TableHead><TableHead>状态</TableHead><TableHead>满意度</TableHead>
                  <TableHead>沟通日期</TableHead><TableHead>负责人</TableHead><TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cc.loading ? (
                  <TableRow><TableCell colSpan={9} className="text-center py-8">加载中...</TableCell></TableRow>
                ) : cc.communications.length === 0 ? (
                  <TableRow><TableCell colSpan={9} className="text-center py-8">暂无沟通记录</TableCell></TableRow>
                ) : (cc.communications || []).map((comm) => (
                  <TableRow key={comm.id}>
                    <TableCell className="font-medium">{comm.customer?.name || comm.customer_name || "未知客户"}</TableCell>
                    <TableCell><div className="max-w-xs truncate">{comm.subject}</div></TableCell>
                    <TableCell>{getTypeDisplay(comm.communication_type)}</TableCell>
                    <TableCell>{getPriorityBadge(comm.priority)}</TableCell>
                    <TableCell>{getStatusBadge(comm.status)}</TableCell>
                    <TableCell>{getSatisfactionDisplay(comm.satisfaction_rating)}</TableCell>
                    <TableCell>{formatDate(comm.communication_date)}</TableCell>
                    <TableCell>{comm.assigned_user?.name || "未分配"}</TableCell>
                    <TableCell>
                      <div className="flex space-x-1">
                        <Button variant="ghost" size="sm" onClick={() => { cc.setSelectedCommunication(comm); cc.setShowDetailDialog(true); }}><Eye className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => cc.openEditDialog(comm)}><Edit className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => cc.handleDelete(comm.id)}><XCircle className="h-4 w-4" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* 创建对话框 */}
      <Dialog open={cc.showCreateDialog} onOpenChange={cc.setShowCreateDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="text-white">新建沟通记录</DialogTitle></DialogHeader>
          <CommunicationFormFields formData={cc.formData} setFormData={cc.setFormData} customers={cc.customers} users={cc.users} />
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => cc.setShowCreateDialog(false)}>取消</Button>
            <Button onClick={cc.handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={cc.showDetailDialog} onOpenChange={cc.setShowDetailDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="text-white">沟通记录详情</DialogTitle></DialogHeader>
          {cc.selectedCommunication && (
            <CommunicationDetailView
              communication={cc.selectedCommunication}
              getTypeDisplay={getTypeDisplay}
              getPriorityBadge={getPriorityBadge}
              getStatusBadge={getStatusBadge}
              getSatisfactionDisplay={getSatisfactionDisplay}
            />
          )}
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => cc.setShowDetailDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑对话框 */}
      <Dialog open={cc.showEditDialog} onOpenChange={cc.setShowEditDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="text-white">编辑沟通记录</DialogTitle></DialogHeader>
          <CommunicationFormFields formData={cc.formData} setFormData={cc.setFormData} customers={cc.customers} users={cc.users} />
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => cc.setShowEditDialog(false)}>取消</Button>
            <Button onClick={cc.handleUpdate}>更新</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
