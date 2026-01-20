/**
 * Quote Management Page - Refactored Version
 * 报价管理页面 - 重构版本
 * Features: Quote list, creation, version management, approval
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { cn as _cn } from "../lib/utils";

// Import refactored components
import {
  QuoteStatsOverview,
  QuoteListManager,
  DEFAULT_QUOTE_STATS,
  QUOTE_VIEW_MODES } from
"../components/quote";

// Import services
import {
  quoteApi,
  opportunityApi,
  customerApi,
  salesTemplateApi as _salesTemplateApi } from
"../services/api";

// Import utilities
import { fadeIn, staggerContainer } from "../lib/animations";

export default function QuoteManagement() {
  // 状态管理
  const [quotes, setQuotes] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [selectedQuotes, setSelectedQuotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);

  // 统计数据
  const [stats, setStats] = useState(DEFAULT_QUOTE_STATS);

  // 视图和筛选
  const [viewMode, setViewMode] = useState("list");
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    status: "all",
    type: "all",
    priority: "all",
    customer_id: "all",
    opportunity_id: "all"
  });
  const [sortBy, setSortBy] = useState("created_desc");
  const [timeRange, setTimeRange] = useState("month");

  // 获取报价列表
  const fetchQuotes = useCallback(async () => {
    try {
      setLoading(true);
      const response = await quoteApi.getQuotes({
        ...filters,
        search: searchTerm,
        sort: sortBy,
        timeRange
      });
      const quotesData = response.data || [];
      setQuotes(quotesData);
    } catch (error) {
      console.error('Failed to fetch quotes:', error);
      // 使用模拟数据
      const mockQuotes = [
      {
        id: "QT-000001",
        title: "ERP系统年度维护服务",
        status: "SENT",
        type: "SERVICE",
        priority: "HIGH",
        customer_id: "CUST001",
        customer_name: "ABC科技有限公司",
        opportunity_id: "OPP001",
        opportunity_title: "ERP系统升级项目",
        created_by: "USER001",
        created_by_name: "张三",
        created_at: "2024-01-10T10:00:00Z",
        updated_at: "2024-01-12T15:30:00Z",
        valid_until: "2024-02-10T23:59:59Z",
        version: {
          version_no: "V1",
          total_price: 150000,
          cost_total: 120000,
          gross_margin: 20.0,
          lead_time_days: 30,
          delivery_date: "2024-02-20",
          items: [
          {
            id: 1,
            name: "系统维护服务",
            description: "全年系统维护和技术支持",
            quantity: 1,
            unit_price: 150000,
            discount: 0,
            total_price: 150000
          }]

        }
      },
      {
        id: "QT-000002",
        title: "生产设备自动化改造",
        status: "APPROVED",
        type: "PROJECT",
        priority: "URGENT",
        customer_id: "CUST002",
        customer_name: "XYZ制造公司",
        opportunity_id: "OPP002",
        opportunity_title: "生产线自动化项目",
        created_by: "USER002",
        created_by_name: "李四",
        created_at: "2024-01-08T14:00:00Z",
        updated_at: "2024-01-11T09:15:00Z",
        valid_until: "2024-02-08T23:59:59Z",
        version: {
          version_no: "V2",
          total_price: 850000,
          cost_total: 680000,
          gross_margin: 20.0,
          lead_time_days: 45,
          delivery_date: "2024-03-15",
          items: [
          {
            id: 1,
            name: "自动化设备",
            description: "生产线自动化改造设备",
            quantity: 5,
            unit_price: 170000,
            discount: 0,
            total_price: 850000
          }]

        }
      },
      {
        id: "QT-000003",
        title: "办公用品批量采购",
        status: "DRAFT",
        type: "STANDARD",
        priority: "MEDIUM",
        customer_id: "CUST003",
        customer_name: "DEF贸易公司",
        opportunity_id: "OPP003",
        opportunity_title: "办公用品供应",
        created_by: "USER003",
        created_by_name: "王五",
        created_at: "2024-01-12T16:00:00Z",
        updated_at: "2024-01-12T16:00:00Z",
        valid_until: "2024-02-12T23:59:59Z",
        version: {
          version_no: "V1",
          total_price: 25000,
          cost_total: 20000,
          gross_margin: 20.0,
          lead_time_days: 7,
          delivery_date: "2024-01-20",
          items: [
          {
            id: 1,
            name: "办公桌椅",
            description: "办公桌椅套装",
            quantity: 10,
            unit_price: 2500,
            discount: 0,
            total_price: 25000
          }]

        }
      }];

      setQuotes(mockQuotes);
    } finally {
      setLoading(false);
    }
  }, [filters, searchTerm, sortBy, timeRange]);

  // 获取统计数据
  const fetchStats = useCallback(async () => {
    try {
      const response = await quoteApi.getStats({ timeRange });
      setStats(response.data || DEFAULT_QUOTE_STATS);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // 使用模拟数据
      setStats({
        total: 25,
        draft: 3,
        inReview: 5,
        approved: 8,
        sent: 6,
        expired: 2,
        rejected: 1,
        accepted: 4,
        converted: 3,
        totalAmount: 3500000,
        avgAmount: 140000,
        avgMargin: 18.5,
        conversionRate: 75.0,
        thisMonth: 12,
        lastMonth: 10,
        growth: 20.0,
        expiringSoon: 2
      });
    }
  }, [timeRange]);

  // 获取商机列表
  const fetchOpportunities = useCallback(async () => {
    try {
      const response = await opportunityApi.getOpportunities();
      setOpportunities(response.data || []);
    } catch (error) {
      console.error('Failed to fetch opportunities:', error);
      // 使用模拟数据
      setOpportunities([
      { id: "OPP001", title: "ERP系统升级项目", customer_id: "CUST001" },
      { id: "OPP002", title: "生产线自动化项目", customer_id: "CUST002" },
      { id: "OPP003", title: "办公用品供应", customer_id: "CUST003" }]
      );
    }
  }, []);

  // 获取客户列表
  const fetchCustomers = useCallback(async () => {
    try {
      const response = await customerApi.getCustomers();
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch customers:', error);
      // 使用模拟数据
      setCustomers([
      { id: "CUST001", name: "ABC科技有限公司" },
      { id: "CUST002", name: "XYZ制造公司" },
      { id: "CUST003", name: "DEF贸易公司" }]
      );
    }
  }, []);

  // 处理刷新
  const handleRefresh = useCallback(() => {
    fetchQuotes();
    fetchStats();
  }, [fetchQuotes, fetchStats]);

  // 处理查看报价详情
  const handleQuoteView = useCallback((quote) => {
    setSelectedQuote(quote);
    setShowDetailDialog(true);
  }, []);

  // 处理编辑报价
  const handleQuoteEdit = useCallback((quote) => {
    setSelectedQuote(quote);
    setShowEditDialog(true);
  }, []);

  // 处理复制报价
  const handleQuoteCopy = useCallback((quote) => {
    // 复制报价逻辑
    console.log('Copying quote:', quote.id);
    // 可以创建新的报价并填充相同内容
  }, []);

  // 处理发送报价
  const handleQuoteSend = useCallback((quote) => {
    // 发送报价逻辑
    console.log('Sending quote:', quote.id);
  }, []);

  // 处理审批报价
  const handleQuoteApprove = useCallback((quote) => {
    // 审批报价逻辑
    console.log('Approving quote:', quote.id);
  }, []);

  // 处理拒绝报价
  const handleQuoteReject = useCallback((quote) => {
    // 拒绝报价逻辑
    console.log('Rejecting quote:', quote.id);
  }, []);

  // 处理创建报价
  const handleQuoteCreate = useCallback(() => {
    setSelectedQuote(null);
    setShowCreateDialog(true);
  }, []);

  // 处理筛选变化
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  // 处理选择变化
  const handleSelectionChange = useCallback((newSelection) => {
    setSelectedQuotes(newSelection);
  }, []);

  // 处理导出
  const handleExport = useCallback(() => {
    // 导出逻辑
    console.log('Exporting quotes:', selectedQuotes.length);
  }, [selectedQuotes]);

  // 处理导入
  const handleImport = useCallback(() => {
    // 导入逻辑
    console.log('Import dialog opened');
  }, []);

  // 初始化数据
  useEffect(() => {
    handleRefresh();
    fetchOpportunities();
    fetchCustomers();
  }, []);

  // 当筛选条件变化时重新获取数据
  useEffect(() => {
    fetchQuotes();
  }, [filters, searchTerm, sortBy]);

  // 当时间范围变化时重新获取统计数据
  useEffect(() => {
    fetchStats();
  }, [timeRange]);

  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={staggerContainer}
      className="space-y-6">

      <PageHeader
        title="报价管理"
        subtitle="管理销售报价，支持多版本管理和审批流程"
        breadcrumbs={[
        { label: "销售管理", href: "/sales" },
        { label: "报价管理", href: "/quotes" }]
        }
        actions={
        <div className="flex items-center gap-3">
            <Button
            variant="outline"
            onClick={() => window.location.href = "/quote-analytics"}>

              数据分析
            </Button>
            <Button
            onClick={handleQuoteCreate}
            className="bg-blue-600 hover:bg-blue-700 text-white">

              新建报价
            </Button>
        </div>
        } />


      <motion.div variants={fadeIn} className="space-y-6">
        {/* 统计概览 */}
        <QuoteStatsOverview
          stats={stats}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onRefresh={handleRefresh}
          loading={loading}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange} />


        {/* 报价列表管理 */}
        <QuoteListManager
          quotes={quotes}
          opportunities={opportunities}
          customers={customers}
          viewMode={viewMode}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          filters={filters}
          onFilterChange={handleFilterChange}
          sortBy={sortBy}
          onSortChange={setSortBy}
          selectedQuotes={selectedQuotes}
          onSelectionChange={handleSelectionChange}
          onQuoteView={handleQuoteView}
          onQuoteEdit={handleQuoteEdit}
          onQuoteCreate={handleQuoteCreate}
          onQuoteCopy={handleQuoteCopy}
          onQuoteSend={handleQuoteSend}
          onQuoteApprove={handleQuoteApprove}
          onQuoteReject={handleQuoteReject}
          onExport={handleExport}
          onImport={handleImport}
          loading={loading} />

      </motion.div>

      {/* 报价详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 text-white max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              报价详情
              <span className="text-sm text-slate-400">#{selectedQuote?.id}</span>
            </DialogTitle>
          </DialogHeader>
          {selectedQuote &&
          <div className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">标题</label>
                  <p className="text-white font-medium">{selectedQuote.title}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">状态</label>
                  <div className="mt-1">
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-sm">
                      {selectedQuote.status}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-slate-400">类型</label>
                  <p className="text-white">{selectedQuote.type}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">优先级</label>
                  <p className="text-white">{selectedQuote.priority}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">客户</label>
                  <p className="text-white">{selectedQuote.customer_name}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">有效期至</label>
                  <p className="text-white">
                    {selectedQuote.valid_until ? new Date(selectedQuote.valid_until).toLocaleDateString() : '未设置'}
                  </p>
                </div>
              </div>

              {/* 版本信息 */}
              {selectedQuote.version &&
            <div>
                  <label className="text-sm text-slate-400 block mb-2">版本信息</label>
                  <div className="bg-slate-800/60 rounded-lg p-4 space-y-2">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">版本号:</span>
                        <span className="text-white ml-2">{selectedQuote.version.version_no}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">总金额:</span>
                        <span className="text-emerald-400 ml-2">
                          ¥{selectedQuote.version.total_price?.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">成本:</span>
                        <span className="text-red-400 ml-2">
                          ¥{selectedQuote.version.cost_total?.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">毛利率:</span>
                        <span className="text-blue-400 ml-2">
                          {selectedQuote.version.gross_margin}%
                        </span>
                      </div>
                    </div>
                  </div>
            </div>
            }

              {/* 操作按钮 */}
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                <Button
                variant="outline"
                onClick={() => setShowDetailDialog(false)}>

                  关闭
                </Button>
                <Button
                onClick={() => {
                  handleQuoteEdit(selectedQuote);
                  setShowDetailDialog(false);
                }}>

                  编辑
                </Button>
                <Button
                onClick={() => {
                  handleQuoteSend(selectedQuote);
                  setShowDetailDialog(false);
                }}>

                  发送
                </Button>
              </div>
          </div>
          }
        </DialogContent>
      </Dialog>

      {/* 创建报价对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>新建报价</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-400">创建新报价的表单将在这里显示</p>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}>

                取消
              </Button>
              <Button>
                创建
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 编辑报价对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>编辑报价</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-400">编辑报价的表单将在这里显示</p>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowEditDialog(false)}>

                取消
              </Button>
              <Button>
                保存
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </motion.div>);

}