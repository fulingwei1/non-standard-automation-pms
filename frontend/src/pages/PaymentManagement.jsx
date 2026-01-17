/**
 * Payment Management Page - Accounts receivable tracking for sales
 * Features: Payment schedule, aging analysis, invoice management, collection reminders
 * Refactored version with modular components
 */

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DollarSign,
  Search,
  Filter,
  Plus,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle2,
  FileText,
  TrendingUp,
  TrendingDown,
  Building2,
  ChevronRight,
  Download,
  Send,
  Bell,
  BarChart3,
  PieChart,
  List,
  LayoutGrid,
  Eye,
  Edit,
  Receipt,
  CreditCard,
  Banknote,
  X,
  Phone,
  Mail } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter } from
"../components/ui";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { PaymentTimeline, PaymentStats } from "../components/sales";
import {
  PaymentStatsOverview,
  PAYMENT_TYPES,
  PAYMENT_STATUS,
  getPaymentType,
  getPaymentStatus,
  calculateAging as _calculateAging,
  formatCurrency } from
"../components/payment-management";
import {
  paymentApi,
  invoiceApi as _invoiceApi,
  receivableApi,
  paymentPlanApi as _paymentPlanApi } from
"../services/api";

export default function PaymentManagement() {
  const [viewMode, setViewMode] = useState("list"); // 'list', 'timeline', 'aging'
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showInvoiceDialog, setShowInvoiceDialog] = useState(false);
  const [showCollectionDialog, setShowCollectionDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  // 新增状态：回款提醒、统计分析
  const [reminders, setReminders] = useState([]);
  const [_remindersLoading, setRemindersLoading] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [_statisticsLoading, setStatisticsLoading] = useState(false);
  const [showReminders, setShowReminders] = useState(false);

  // Load payments from API
  const loadPayments = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        payment_status:
        selectedStatus !== "all" ? selectedStatus.toUpperCase() : undefined
      };

      if (searchTerm) {
        params.keyword = searchTerm;
      }

      const response = await paymentApi.list(params);
      const data = response.data || {};

      // 转换数据格式
      const transformedPayments = (data.items || []).map((item) => {
        const statusMap = {
          PAID: "paid",
          PENDING: "pending",
          PARTIAL: "pending",
          OVERDUE: "overdue"
        };

        const type = "progress"; // 默认类型

        return {
          id: item.id || item.invoice_id,
          type: type,
          projectId: item.project_code || item.project_id,
          projectName: item.project_name || item.project_code || "",
          contractNo: item.contract_code || "",
          customerName: item.customer_name || "",
          customerShort: item.customer_name || "",
          amount: parseFloat(item.invoice_amount || item.amount || 0),
          dueDate: item.due_date || "",
          status: statusMap[item.payment_status] || "pending",
          invoiceNo: item.invoice_code || "",
          invoiceDate: item.issue_date || "",
          paidAmount: parseFloat(item.paid_amount || 0),
          paidDate: item.paid_date || "",
          notes: item.remark || "",
          overdueDay: item.overdue_days || null,
          createdAt: item.created_at || "",
          raw: item
        };
      });

      setPayments(transformedPayments);
      setTotal(data.total || 0);
    } catch (error) {
      console.error("加载回款列表失败:", error);
      setPayments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // Load aging data
  const loadAgingData = async () => {
    try {
      const response = await receivableApi.getAging({});
      setAgingData(response.data || {});
    } catch (error) {
      console.error("加载账龄数据失败:", error);
      setAgingData({
        current: { count: 0, amount: 0 },
        days_1_30: { count: 0, amount: 0 },
        days_31_60: { count: 0, amount: 0 },
        days_61_90: { count: 0, amount: 0 },
        days_over_90: { count: 0, amount: 0 }
      });
    }
  };

  // Load reminders
  const loadReminders = async () => {
    try {
      setRemindersLoading(true);
      const response = await paymentApi.getReminders({
        page: 1,
        page_size: 50
      });
      setReminders(response.data?.items || []);
    } catch (error) {
      console.error("加载回款提醒失败:", error);
      setReminders([]);
    } finally {
      setRemindersLoading(false);
    }
  };

  // Load statistics
  const loadStatistics = async () => {
    try {
      setStatisticsLoading(true);
      const response = await paymentApi.getStatistics({});
      setStatistics(response.data || {});
    } catch (error) {
      console.error("加载统计数据失败:", error);
      setStatistics({
        total_receivables: 0,
        overdue_amount: 0,
        collection_rate: 0,
        dso: 0
      });
    } finally {
      setStatisticsLoading(false);
    }
  };

  // 读取账龄数据状态
  const [agingData, setAgingData] = useState({
    current: { count: 0, amount: 0 },
    days_1_30: { count: 0, amount: 0 },
    days_31_60: { count: 0, amount: 0 },
    days_61_90: { count: 0, amount: 0 },
    days_over_90: { count: 0, amount: 0 }
  });

  // 过滤后的支付列表
  const filteredPayments = useMemo(() => {
    let filtered = payments;

    if (searchTerm) {
      filtered = filtered.filter(
        (payment) =>
        payment.projectName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        payment.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        payment.contractNo.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedType !== "all") {
      filtered = filtered.filter((payment) => payment.type === selectedType);
    }

    if (selectedStatus !== "all") {
      filtered = filtered.filter((payment) => payment.status === selectedStatus);
    }

    return filtered;
  }, [payments, searchTerm, selectedType, selectedStatus]);

  // 初始化
  useEffect(() => {
    loadPayments();
    loadAgingData();
    loadReminders();
    loadStatistics();
  }, [page, selectedStatus]);

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        loadPayments();
      } else {
        setPage(1);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm, selectedType]);

  // 支付卡片组件
  const PaymentCard = ({ payment }) => {
    const statusInfo = getPaymentStatus(payment.status);
    const typeInfo = getPaymentType(payment.type);
    const isOverdue = payment.status === "overdue";

    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "rounded-xl border overflow-hidden transition-all hover:shadow-lg",
          isOverdue ?
          "bg-red-500/5 border-red-500/30" :
          payment.status === "paid" ?
          "bg-emerald-500/5 border-emerald-500/30" :
          "bg-slate-800/50 border-slate-700/50"
        )}>

        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${typeInfo.color}`}>
                  <DollarSign className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-white">
                    {payment.customerName}
                  </h4>
                  <p className="text-sm text-slate-400">{payment.projectName}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={cn(
                    "border",
                    typeInfo.borderColor,
                    typeInfo.textColor
                  )}>

                  {typeInfo.label}
                </Badge>
                <Badge
                  variant="outline"
                  className={cn(
                    "border",
                    statusInfo.borderColor,
                    statusInfo.textColor
                  )}>

                  <statusInfo.icon className="w-3 h-3 mr-1" />
                  {statusInfo.label}
                </Badge>
                {isOverdue &&
                <Badge variant="destructive">
                    逾期{payment.overdueDay}天
                  </Badge>
                }
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-white">
                {formatCurrency(payment.amount)}
              </div>
              {payment.paidAmount > 0 &&
              <div className="text-sm text-slate-400">
                  已付: {formatCurrency(payment.paidAmount)}
                </div>
              }
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className="text-slate-400">
              <span>合同号: {payment.contractNo}</span>
              {payment.dueDate &&
              <span className="ml-4">
                  到期日: {new Date(payment.dueDate).toLocaleDateString()}
                </span>
              }
            </div>
            <div className="flex items-center gap-2">
              {payment.status !== "paid" &&
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedPayment(payment);
                  setShowInvoiceDialog(true);
                }}>

                  <FileText className="w-3 h-3 mr-1" />
                  开票
                </Button>
              }
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedPayment(payment);
                  setShowDetailDialog(true);
                }}>

                <Eye className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </div>
      </motion.div>);

  };

  // 账龄分析组件
  const AgingAnalysis = () => {
    const agingItems = [
    { key: "current", label: "当前", ...agingData.current },
    { key: "days_1_30", label: "1-30天", ...agingData.days_1_30 },
    { key: "days_31_60", label: "31-60天", ...agingData.days_31_60 },
    { key: "days_61_90", label: "61-90天", ...agingData.days_61_90 },
    { key: "days_over_90", label: "90天以上", ...agingData.days_over_90 }];


    return (
      <div className="space-y-4">
        {agingItems.map((item) =>
        <Card
          key={item.key}
          className={cn(
            "bg-slate-800/50 border",
            item.key === "days_over_90" ?
            "border-red-500/30" :
            item.key === "days_61_90" ?
            "border-orange-500/30" :
            "border-slate-700/50"
          )}>

            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-white font-medium">{item.label}</h4>
                  <p className="text-slate-400 text-sm">
                    {item.count} 笔付款
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-white">
                    {formatCurrency(item.amount)}
                  </div>
                  <Progress
                  value={item.amount / Object.values(agingData).reduce((sum, d) => sum + d.amount, 0) * 100}
                  className="w-24 h-2 mt-1" />

                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>);

  };

  if (loading && payments.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>);

  }

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <PageHeader
        title="支付管理"
        description="应收账款跟踪、账龄分析、发票管理和催收提醒"
        action={
        <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2">
              <span className="text-sm text-slate-400">应收总额:</span>
              <span className="text-lg font-bold text-white">
                {formatCurrency(statistics?.total_receivables || 0)}
              </span>
            </div>
            <Button variant="outline" onClick={() => setShowCollectionDialog(true)}>
              <Bell className="w-4 h-4 mr-2" />
              批量催收
            </Button>
          </div>
        } />


      <Tabs value={viewMode} onValueChange={setViewMode} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">统计概览</TabsTrigger>
          <TabsTrigger value="list">付款列表</TabsTrigger>
          <TabsTrigger value="timeline">时间轴</TabsTrigger>
          <TabsTrigger value="aging">账龄分析</TabsTrigger>
        </TabsList>

        {/* 统计概览 */}
        <TabsContent value="overview" className="space-y-6">
          <PaymentStatsOverview
            payments={payments}
            invoices={payments.filter((p) => p.invoiceNo)}
            reminders={reminders}
            loading={loading}
            onRefresh={() => {
              loadPayments();
              loadStatistics();
              loadReminders();
            }} />

        </TabsContent>

        {/* 付款列表 */}
        <TabsContent value="list" className="space-y-6">
          {/* 回款提醒卡片 */}
          {reminders.length > 0 &&
          <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Bell className="w-5 h-5 text-amber-400" />
                      回款提醒
                    </CardTitle>
                    <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowReminders(!showReminders)}>

                      {showReminders ? "收起" : "展开"}
                    </Button>
                  </div>
                </CardHeader>
                {showReminders &&
              <CardContent>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {reminders.map((reminder) =>
                  <div
                    key={reminder.id}
                    className={cn(
                      "p-3 rounded-lg border",
                      reminder.reminder_level === "urgent" ?
                      "bg-red-500/10 border-red-500/20" :
                      reminder.reminder_level === "warning" ?
                      "bg-amber-500/10 border-amber-500/20" :
                      "bg-blue-500/10 border-blue-500/20"
                    )}>

                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-white">
                                  {reminder.customer_name || "未知客户"}
                                </span>
                                <Badge
                            variant={
                            reminder.reminder_level === "urgent" ?
                            "destructive" :
                            reminder.reminder_level === "warning" ?
                            "default" :
                            "secondary"
                            }>

                                  {reminder.is_overdue ?
                            `逾期${reminder.overdue_days}天` :
                            `还有${reminder.days_until_due}天到期`}
                                </Badge>
                              </div>
                              <div className="mt-1 text-sm text-slate-400">
                                {reminder.contract_code &&
                          `合同：${reminder.contract_code} | `}
                                {reminder.project_code &&
                          `项目：${reminder.project_code} | `}
                                未收金额：¥
                                {(reminder.unpaid_amount / 10000).toFixed(2)}万
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-medium text-white">
                                {reminder.due_date}
                              </div>
                            </div>
                          </div>
                        </div>
                  )}
                    </div>
                  </CardContent>
              }
              </Card>
            </motion.div>
          }

          {/* 搜索和筛选 */}
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <Input
                      placeholder="搜索客户、项目或合同..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 bg-slate-900 border-slate-700 text-white" />

                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2">

                    <option value="all">全部类型</option>
                    {Object.values(PAYMENT_TYPES).map((type) =>
                    <option key={type.key} value={type.key}>
                        {type.label}
                      </option>
                    )}
                  </select>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2">

                    <option value="all">全部状态</option>
                    {Object.values(PAYMENT_STATUS).map((status) =>
                    <option key={status.key} value={status.key}>
                        {status.label}
                      </option>
                    )}
                  </select>
                  <div className="flex items-center gap-1">
                    <Button
                      variant={viewMode === "list" ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("list")}>

                      <List className="w-4 h-4" />
                    </Button>
                    <Button
                      variant={viewMode === "grid" ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("grid")}>

                      <LayoutGrid className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 付款列表 */}
          <div className="space-y-4">
            {filteredPayments.length === 0 ?
            <Card className="bg-slate-800/50 border-slate-700/50">
                <CardContent className="p-12 text-center">
                  <div className="text-slate-400">
                    {searchTerm || selectedType !== "all" || selectedStatus !== "all" ?
                  "没有找到匹配的付款记录" :
                  "暂无付款记录"}
                  </div>
                </CardContent>
              </Card> :

            <>
                {viewMode === "list" ?
              <Card className="bg-slate-800/50 border-slate-700/50">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-slate-700">
                            <th className="text-left p-4 text-slate-400">客户</th>
                            <th className="text-left p-4 text-slate-400">项目</th>
                            <th className="text-left p-4 text-slate-400">类型</th>
                            <th className="text-right p-4 text-slate-400">金额</th>
                            <th className="text-left p-4 text-slate-400">到期日</th>
                            <th className="text-left p-4 text-slate-400">状态</th>
                            <th className="text-right p-4 text-slate-400">操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          <AnimatePresence>
                            {filteredPayments.map((payment, _index) =>
                        <motion.tr
                          key={payment.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          className="border-b border-slate-700/50">

                                <td className="p-4">
                                  <div>
                                    <div className="text-white font-medium">
                                      {payment.customerName}
                                    </div>
                                    <div className="text-slate-400 text-sm">
                                      {payment.contractNo}
                                    </div>
                                  </div>
                                </td>
                                <td className="p-4 text-white">
                                  {payment.projectName}
                                </td>
                                <td className="p-4">
                                  <Badge
                              variant="outline"
                              className={cn(
                                "border",
                                getPaymentType(payment.type).borderColor,
                                getPaymentType(payment.type).textColor
                              )}>

                                    {getPaymentType(payment.type).label}
                                  </Badge>
                                </td>
                                <td className="p-4 text-right font-medium text-white">
                                  {formatCurrency(payment.amount)}
                                </td>
                                <td className="p-4 text-white">
                                  {payment.dueDate ?
                            new Date(payment.dueDate).toLocaleDateString() :
                            "-"}
                                </td>
                                <td className="p-4">
                                  <Badge
                              variant="outline"
                              className={cn(
                                "border",
                                getPaymentStatus(payment.status).borderColor,
                                getPaymentStatus(payment.status).textColor
                              )}>

                                    {getPaymentStatus(payment.status).label}
                                  </Badge>
                                </td>
                                <td className="p-4">
                                  <div className="flex items-center justify-end gap-2">
                                    {payment.status !== "paid" &&
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedPayment(payment);
                                  setShowInvoiceDialog(true);
                                }}>

                                        <FileText className="w-3 h-3 mr-1" />
                                        开票
                                      </Button>
                              }
                                    <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setSelectedPayment(payment);
                                  setShowDetailDialog(true);
                                }}>

                                      <Eye className="w-3 h-3" />
                                    </Button>
                                  </div>
                                </td>
                              </motion.tr>
                        )}
                          </AnimatePresence>
                        </tbody>
                      </table>
                    </div>
                  </Card> :

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredPayments.map((payment) =>
                <PaymentCard key={payment.id} payment={payment} />
                )}
                  </div>
              }

                {/* 分页 */}
                {total > pageSize &&
              <div className="flex items-center justify-center gap-2 mt-6">
                    <Button
                  variant="outline"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}>

                      上一页
                    </Button>
                    <span className="text-slate-400">
                      第 {page} 页，共 {Math.ceil(total / pageSize)} 页
                    </span>
                    <Button
                  variant="outline"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= Math.ceil(total / pageSize)}>

                      下一页
                    </Button>
                  </div>
              }
              </>
            }
          </div>
        </TabsContent>

        {/* 时间轴视图 */}
        <TabsContent value="timeline" className="space-y-6">
          <PaymentTimeline payments={payments} />
        </TabsContent>

        {/* 账龄分析 */}
        <TabsContent value="aging" className="space-y-6">
          <AgingAnalysis />
        </TabsContent>
      </Tabs>

      {/* 对话框 */}
      {/* 发票申请对话框 */}
      <Dialog
        open={showInvoiceDialog}
        onOpenChange={setShowInvoiceDialog}>

        <DialogContent>
          <DialogHeader>
            <DialogTitle>申请开票</DialogTitle>
            <DialogDescription>
              为选中的付款申请开具发票
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {selectedPayment &&
            <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    客户名称
                  </label>
                  <div className="text-slate-300">
                    {selectedPayment.customerName}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    开票金额
                  </label>
                  <div className="text-lg font-medium text-white">
                    {formatCurrency(selectedPayment.amount)}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    项目信息
                  </label>
                  <div className="text-slate-300">
                    {selectedPayment.projectName}
                  </div>
                </div>
              </div>
            }
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInvoiceDialog(false)}>
              取消
            </Button>
            <Button onClick={() => {
              // TODO: 实现开票逻辑
              console.log("申请开票:", selectedPayment);
              setShowInvoiceDialog(false);
            }}>
              确认申请
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}>

        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>付款详情</DialogTitle>
          </DialogHeader>
          {selectedPayment &&
          <div className="space-y-6 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    客户名称
                  </label>
                  <div className="text-slate-300">
                    {selectedPayment.customerName}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    合同编号
                  </label>
                  <div className="text-slate-300">
                    {selectedPayment.contractNo}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    项目名称
                  </label>
                  <div className="text-slate-300">
                    {selectedPayment.projectName}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    付款类型
                  </label>
                  <div className="text-slate-300">
                    {getPaymentType(selectedPayment.type).label}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    应付金额
                  </label>
                  <div className="text-lg font-medium text-white">
                    {formatCurrency(selectedPayment.amount)}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    已付金额
                  </label>
                  <div className="text-lg font-medium text-emerald-400">
                    {formatCurrency(selectedPayment.paidAmount)}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    到期日期
                  </label>
                  <div className="text-slate-300">
                    {selectedPayment.dueDate ?
                  new Date(selectedPayment.dueDate).toLocaleDateString() :
                  "-"}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    付款状态
                  </label>
                  <Badge
                  variant="outline"
                  className={cn(
                    "border",
                    getPaymentStatus(selectedPayment.status).borderColor,
                    getPaymentStatus(selectedPayment.status).textColor
                  )}>

                    {getPaymentStatus(selectedPayment.status).label}
                  </Badge>
                </div>
              </div>
              {selectedPayment.notes &&
            <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    备注
                  </label>
                  <div className="text-slate-300">
                    {selectedPayment.notes}
                  </div>
                </div>
            }
            </div>
          }
          <DialogFooter>
            <Button onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 批量催收对话框 */}
      <Dialog
        open={showCollectionDialog}
        onOpenChange={setShowCollectionDialog}>

        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量催收</DialogTitle>
            <DialogDescription>
              向逾期客户发送催收通知
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="text-slate-300">
              将向 {reminders.length} 个逾期客户发送催收通知。
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCollectionDialog(false)}>
              取消
            </Button>
            <Button onClick={() => {
              // TODO: 实现批量催收逻辑
              console.log("批量催收:", reminders);
              setShowCollectionDialog(false);
            }}>
              确认发送
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}