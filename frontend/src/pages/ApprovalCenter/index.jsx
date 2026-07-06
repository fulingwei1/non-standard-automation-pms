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
  Clock,
  CheckCircle2,
  Send,
  Mail,
  RefreshCw,
} from "lucide-react";

import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import { cn } from "../../lib/utils";

import { useApprovalCenter, APPROVAL_TABS } from "./hooks/useApprovalCenter";
import StatCards from "./StatCards";
import FilterBar from "./FilterBar";
import PendingList from "./PendingList";
import InitiatedList from "./InitiatedList";
import CcList from "./CcList";
import ProcessedList from "./ProcessedList";
import QuickApprovalDialog from "./QuickApprovalDialog";

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
      <StatCards counts={counts} />

      {/* 筛选栏 */}
      <FilterBar
        searchText={searchText}
        setSearchText={setSearchText}
        filters={filters}
        updateFilters={updateFilters}
        refresh={refresh}
        loading={loading}
      />

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
          <PendingList
            items={items}
            loading={loading}
            goToDetail={goToDetail}
            openQuickApproval={openQuickApproval}
          />
        </TabsContent>

        <TabsContent value={APPROVAL_TABS.INITIATED} className="mt-6">
          <InitiatedList
            items={items}
            loading={loading}
            goToDetail={goToDetail}
          />
        </TabsContent>

        <TabsContent value={APPROVAL_TABS.CC} className="mt-6">
          <CcList
            items={items}
            loading={loading}
            goToDetail={goToDetail}
            handleMarkRead={handleMarkRead}
          />
        </TabsContent>

        <TabsContent value={APPROVAL_TABS.PROCESSED} className="mt-6">
          <ProcessedList
            items={items}
            loading={loading}
            goToDetail={goToDetail}
          />
        </TabsContent>
      </Tabs>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* 快速审批弹窗 */}
      <QuickApprovalDialog
        dialogState={quickApprovalDialog}
        setDialogState={setQuickApprovalDialog}
        onClose={closeQuickApproval}
        onSubmit={handleQuickApproval}
      />
    </motion.div>
  );
};

export default ApprovalCenter;
