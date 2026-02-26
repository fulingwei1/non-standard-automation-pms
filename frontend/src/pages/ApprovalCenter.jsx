/**
 * ApprovalCenter - 审批中心页面
 *
 * 统一审批管理平台，支持四个标签页：
 * - 待我审批：需要当前用户处理的审批任务
 * - 我发起的：当前用户提交的审批申请
 * - 抄送我的：抄送给当前用户的审批记录
 * - 已处理：当前用户已处理的审批历史
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ClipboardCheck,
  Clock,
  CheckCircle2,
  XCircle,
  Search,
  FileText,
  Eye,
  Check,
  X,
  RefreshCw,
  Send,
  Mail,
  MailOpen,
  Loader2,
  AlertTriangle,
} from "lucide-react";

import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import StatCard from "../components/common/StatCard";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { cn } from "../lib/utils";

import { useApprovalCenter, APPROVAL_TABS } from "./ApprovalCenter/hooks/useApprovalCenter";
import { formatDateTime } from "@/lib/formatters";

/**
 * 紧急程度配置
 */
const URGENCY_CONFIG = {
  NORMAL: { label: "普通", color: "bg-slate-500" },
  URGENT: { label: "紧急", color: "bg-orange-500" },
  CRITICAL: { label: "特急", color: "bg-red-500" },
};

/**
 * 状态配置
 */
const STATUS_CONFIG = {
  PENDING: { label: "待审批", color: "bg-amber-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  APPROVED: { label: "已通过", color: "bg-emerald-500" },
  REJECTED: { label: "已驳回", color: "bg-red-500" },
};

/**
 * 实体类型配置
 */
const ENTITY_TYPE_CONFIG = {
  ECN: { label: "工程变更", color: "bg-purple-500" },
  QUOTE: { label: "报价", color: "bg-blue-500" },
  CONTRACT: { label: "合同", color: "bg-cyan-500" },
  INVOICE: { label: "发票", color: "bg-green-500" },
};

/**
 * 格式化日期时间
 */

const ApprovalCenter = () => {
  const navigate = useNavigate();

  // 使用 hook 获取数据和操作
  const {
    items,
    loading,
    error,
    pagination: _pagination,
    counts,
    tabBadges,
    activeTab,
    filters,
    switchTab,
    updateFilters,
    refresh,
    approve,
    reject,
    markCcAsRead,
  } = useApprovalCenter();

  // 搜索关键词（本地状态，延迟更新到 filters）
  const [searchText, setSearchText] = useState("");

  // 快速审批弹窗
  const [quickApprovalDialog, setQuickApprovalDialog] = useState({
    open: false,
    item: null,
    action: null, // 'approve' | 'reject'
    comment: "",
    submitting: false,
  });

  /**
   * 跳转到详情页
   */
  const goToDetail = (instanceId) => {
    navigate(`/approvals/${instanceId}`);
  };

  /**
   * 打开快速审批弹窗
   */
  const openQuickApproval = (item, action) => {
    setQuickApprovalDialog({
      open: true,
      item,
      action,
      comment: "",
      submitting: false,
    });
  };

  /**
   * 关闭快速审批弹窗
   */
  const closeQuickApproval = () => {
    setQuickApprovalDialog({
      open: false,
      item: null,
      action: null,
      comment: "",
      submitting: false,
    });
  };

  /**
   * 执行快速审批
   */
  const handleQuickApproval = async () => {
    const { item, action, comment } = quickApprovalDialog;
    if (!item) return;

    setQuickApprovalDialog((prev) => ({ ...prev, submitting: true }));

    const result = action === "approve"
      ? await approve(item.id, comment)
      : await reject(item.id, comment);

    if (result.success) {
      closeQuickApproval();
    } else {
      // TODO: 显示错误提示
      setQuickApprovalDialog((prev) => ({ ...prev, submitting: false }));
    }
  };

  /**
   * 标记抄送已读
   */
  const handleMarkRead = async (item) => {
    await markCcAsRead(item.id);
  };

  /**
   * 渲染统计卡片
   */
  const renderStatCards = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <StatCard
        title="待我审批"
        value={counts.pending}
        icon={Clock}
        color="text-amber-400"
        iconColor="text-amber-400/30"
        bg="bg-transparent"
        showDecoration={false}
        cardClassName="bg-slate-800/50 border-slate-700 hover:border-slate-600 bg-none hover:shadow-none p-4"
        iconWrapperClassName="p-0 bg-transparent rounded-none"
        iconClassName="h-8 w-8"
      />

      <StatCard
        title="我发起的"
        value={counts.initiated_pending}
        icon={Send}
        color="text-blue-400"
        iconColor="text-blue-400/30"
        bg="bg-transparent"
        showDecoration={false}
        cardClassName="bg-slate-800/50 border-slate-700 hover:border-slate-600 bg-none hover:shadow-none p-4"
        iconWrapperClassName="p-0 bg-transparent rounded-none"
        iconClassName="h-8 w-8"
      />

      <StatCard
        title="未读抄送"
        value={counts.unread_cc}
        icon={Mail}
        color="text-purple-400"
        iconColor="text-purple-400/30"
        bg="bg-transparent"
        showDecoration={false}
        cardClassName="bg-slate-800/50 border-slate-700 hover:border-slate-600 bg-none hover:shadow-none p-4"
        iconWrapperClassName="p-0 bg-transparent rounded-none"
        iconClassName="h-8 w-8"
      />

      <StatCard
        title="紧急待办"
        value={counts.urgent}
        icon={AlertTriangle}
        color="text-red-400"
        iconColor="text-red-400/30"
        bg="bg-transparent"
        showDecoration={false}
        cardClassName="bg-slate-800/50 border-slate-700 hover:border-slate-600 bg-none hover:shadow-none p-4"
        iconWrapperClassName="p-0 bg-transparent rounded-none"
        iconClassName="h-8 w-8"
      />
    </div>
  );

  /**
   * 渲染筛选栏
   */
  const renderFilters = () => (
    <Card className="bg-slate-800/50 border-slate-700 mb-6">
      <CardContent className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="搜索标题、编号..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  updateFilters({ keyword: searchText });
                }
              }}
              className="pl-10 bg-slate-900/50 border-slate-700"
            />
          </div>

          <Select
            value={filters.urgency}
            onValueChange={(value) => updateFilters({ urgency: value })}
          >
            <SelectTrigger className="w-[130px] bg-slate-900/50 border-slate-700">
              <SelectValue placeholder="紧急程度" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部紧急度</SelectItem>
              <SelectItem value="NORMAL">普通</SelectItem>
              <SelectItem value="URGENT">紧急</SelectItem>
              <SelectItem value="CRITICAL">特急</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            className="border-slate-600"
            onClick={refresh}
            disabled={loading}
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
            刷新
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  /**
   * 渲染待我审批列表
   */
  const renderPendingList = () => (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-slate-800/50">
              <TableHead className="text-slate-300">审批信息</TableHead>
              <TableHead className="text-slate-300">类型</TableHead>
              <TableHead className="text-slate-300">紧急度</TableHead>
              <TableHead className="text-slate-300">当前节点</TableHead>
              <TableHead className="text-slate-300">发起人</TableHead>
              <TableHead className="text-slate-300">发起时间</TableHead>
              <TableHead className="text-slate-300">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => {
              const urgencyConfig = URGENCY_CONFIG[item.instance_urgency] || URGENCY_CONFIG.NORMAL;
              const entityConfig = ENTITY_TYPE_CONFIG[item.instance?.entity_type] || {};
              const instanceId = item.instance_id || item.instance?.id;

              return (
                <TableRow key={item.id} className="border-slate-700 hover:bg-slate-800/50">
                  <TableCell>
                    <div className="space-y-1">
                      <span className="text-white font-medium block">
                        {item.instance_title || item.instance?.title}
                      </span>
                      <span className="text-xs text-slate-500">
                        {item.instance_no || item.instance?.instance_no}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {entityConfig.label && (
                      <Badge className={cn(entityConfig.color, "text-white text-xs")}>
                        {entityConfig.label}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={cn(urgencyConfig.color, "text-white text-xs")}>
                      {urgencyConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {item.node_name || "-"}
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {item.instance?.initiator_name || "-"}
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {formatDateTime(item.created_at)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => goToDetail(instanceId)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-emerald-500 hover:text-emerald-400"
                        onClick={() => openQuickApproval(item, "approve")}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-red-500 hover:text-red-400"
                        onClick={() => openQuickApproval(item, "reject")}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        {items.length === 0 && !loading && (
          <div className="text-center py-12 text-slate-400">
            <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-emerald-500" />
            <p>暂无待审批任务</p>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
          </div>
        )}
      </CardContent>
    </Card>
  );

  /**
   * 渲染我发起的列表
   */
  const renderInitiatedList = () => (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-slate-800/50">
              <TableHead className="text-slate-300">审批信息</TableHead>
              <TableHead className="text-slate-300">类型</TableHead>
              <TableHead className="text-slate-300">状态</TableHead>
              <TableHead className="text-slate-300">当前节点</TableHead>
              <TableHead className="text-slate-300">发起时间</TableHead>
              <TableHead className="text-slate-300">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => {
              const statusConfig = STATUS_CONFIG[item.status] || STATUS_CONFIG.PENDING;
              const entityConfig = ENTITY_TYPE_CONFIG[item.entity_type] || {};

              return (
                <TableRow key={item.id} className="border-slate-700 hover:bg-slate-800/50">
                  <TableCell>
                    <div className="space-y-1">
                      <span className="text-white font-medium block">{item.title}</span>
                      <span className="text-xs text-slate-500">{item.instance_no}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {entityConfig.label && (
                      <Badge className={cn(entityConfig.color, "text-white text-xs")}>
                        {entityConfig.label}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={cn(statusConfig.color, "text-white text-xs")}>
                      {statusConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {item.current_node_name || "-"}
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {formatDateTime(item.created_at)}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      onClick={() => goToDetail(item.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        {items.length === 0 && !loading && (
          <div className="text-center py-12 text-slate-400">
            <FileText className="h-12 w-12 mx-auto mb-2" />
            <p>暂无发起的审批</p>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
          </div>
        )}
      </CardContent>
    </Card>
  );

  /**
   * 渲染抄送我的列表
   */
  const renderCcList = () => (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-slate-800/50">
              <TableHead className="text-slate-300">审批信息</TableHead>
              <TableHead className="text-slate-300">发起人</TableHead>
              <TableHead className="text-slate-300">状态</TableHead>
              <TableHead className="text-slate-300">抄送时间</TableHead>
              <TableHead className="text-slate-300">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => {
              const isRead = item.is_read;

              return (
                <TableRow
                  key={item.id}
                  className={cn(
                    "border-slate-700 hover:bg-slate-800/50",
                    !isRead && "bg-slate-800/30"
                  )}
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {!isRead && (
                        <span className="w-2 h-2 rounded-full bg-blue-500" />
                      )}
                      <div className="space-y-1">
                        <span className="text-white font-medium block">
                          {item.instance_title}
                        </span>
                        <span className="text-xs text-slate-500">
                          {item.instance_no}
                        </span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {item.initiator_name || "-"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={isRead ? "secondary" : "info"}>
                      {isRead ? "已读" : "未读"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {formatDateTime(item.created_at)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => goToDetail(item.instance_id)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {!isRead && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0 text-blue-500 hover:text-blue-400"
                          onClick={() => handleMarkRead(item)}
                        >
                          <MailOpen className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        {items.length === 0 && !loading && (
          <div className="text-center py-12 text-slate-400">
            <Mail className="h-12 w-12 mx-auto mb-2" />
            <p>暂无抄送记录</p>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
          </div>
        )}
      </CardContent>
    </Card>
  );

  /**
   * 渲染已处理列表
   */
  const renderProcessedList = () => (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-slate-800/50">
              <TableHead className="text-slate-300">审批信息</TableHead>
              <TableHead className="text-slate-300">我的操作</TableHead>
              <TableHead className="text-slate-300">审批意见</TableHead>
              <TableHead className="text-slate-300">处理时间</TableHead>
              <TableHead className="text-slate-300">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => {
              const actionLabel = item.action === "APPROVE" ? "通过" : item.action === "REJECT" ? "驳回" : item.action;
              const actionColor = item.action === "APPROVE" ? "bg-emerald-500" : "bg-red-500";
              const instanceId = item.instance_id || item.instance?.id;

              return (
                <TableRow key={item.id} className="border-slate-700 hover:bg-slate-800/50">
                  <TableCell>
                    <div className="space-y-1">
                      <span className="text-white font-medium block">
                        {item.instance_title || item.instance?.title}
                      </span>
                      <span className="text-xs text-slate-500">
                        {item.instance_no || item.instance?.instance_no}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={cn(actionColor, "text-white text-xs")}>
                      {actionLabel}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-300 max-w-[200px] truncate">
                    {item.comment || "-"}
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {formatDateTime(item.completed_at)}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      onClick={() => goToDetail(instanceId)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        {items.length === 0 && !loading && (
          <div className="text-center py-12 text-slate-400">
            <FileText className="h-12 w-12 mx-auto mb-2" />
            <p>暂无已处理记录</p>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <PageHeader
        title="审批中心"
        description="统一审批管理平台"
        actions={
          <Button variant="outline" onClick={refresh} disabled={loading}>
            <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
            刷新
          </Button>
        }
      />

      {/* 统计卡片 */}
      {renderStatCards()}

      {/* 筛选栏 */}
      {renderFilters()}

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={switchTab}>
        <TabsList className="bg-slate-800/50 border border-slate-700">
          <TabsTrigger value={APPROVAL_TABS.PENDING} className="data-[state=active]:bg-slate-700">
            <Clock className="h-4 w-4 mr-2" />
            待我审批
            {tabBadges[APPROVAL_TABS.PENDING] > 0 && (
              <Badge className="ml-2 bg-amber-500 text-white">
                {tabBadges[APPROVAL_TABS.PENDING]}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value={APPROVAL_TABS.INITIATED} className="data-[state=active]:bg-slate-700">
            <Send className="h-4 w-4 mr-2" />
            我发起的
            {tabBadges[APPROVAL_TABS.INITIATED] > 0 && (
              <Badge className="ml-2 bg-blue-500 text-white">
                {tabBadges[APPROVAL_TABS.INITIATED]}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value={APPROVAL_TABS.CC} className="data-[state=active]:bg-slate-700">
            <Mail className="h-4 w-4 mr-2" />
            抄送我的
            {tabBadges[APPROVAL_TABS.CC] > 0 && (
              <Badge className="ml-2 bg-purple-500 text-white">
                {tabBadges[APPROVAL_TABS.CC]}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value={APPROVAL_TABS.PROCESSED} className="data-[state=active]:bg-slate-700">
            <CheckCircle2 className="h-4 w-4 mr-2" />
            已处理
          </TabsTrigger>
        </TabsList>

        <TabsContent value={APPROVAL_TABS.PENDING} className="mt-6">
          {renderPendingList()}
        </TabsContent>

        <TabsContent value={APPROVAL_TABS.INITIATED} className="mt-6">
          {renderInitiatedList()}
        </TabsContent>

        <TabsContent value={APPROVAL_TABS.CC} className="mt-6">
          {renderCcList()}
        </TabsContent>

        <TabsContent value={APPROVAL_TABS.PROCESSED} className="mt-6">
          {renderProcessedList()}
        </TabsContent>
      </Tabs>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* 快速审批弹窗 */}
      <Dialog
        open={quickApprovalDialog.open}
        onOpenChange={(open) => !open && closeQuickApproval()}
      >
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">
              {quickApprovalDialog.action === "approve" ? "审批通过" : "审批驳回"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-400 mb-2">审批标题</p>
              <p className="text-white">
                {quickApprovalDialog.item?.instance_title || quickApprovalDialog.item?.instance?.title}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-400 mb-2">审批意见</p>
              <Textarea
                placeholder={quickApprovalDialog.action === "approve" ? "同意" : "请输入驳回理由"}
                value={quickApprovalDialog.comment}
                onChange={(e) =>
                  setQuickApprovalDialog((prev) => ({
                    ...prev,
                    comment: e.target.value,
                  }))
                }
                className="bg-slate-900/50 border-slate-700"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              className="border-slate-600"
              onClick={closeQuickApproval}
              disabled={quickApprovalDialog.submitting}
            >
              取消
            </Button>
            <Button
              className={
                quickApprovalDialog.action === "approve"
                  ? "bg-emerald-600 hover:bg-emerald-700"
                  : "bg-red-600 hover:bg-red-700"
              }
              onClick={handleQuickApproval}
              disabled={quickApprovalDialog.submitting}
            >
              {quickApprovalDialog.submitting && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              确认{quickApprovalDialog.action === "approve" ? "通过" : "驳回"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
};

export default ApprovalCenter;
