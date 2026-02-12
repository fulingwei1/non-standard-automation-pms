/**
 * Receivable Management Page - Accounts receivable tracking and collection
 * Features: Receivable list, payment recording, aging analysis, overdue tracking
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  DollarSign,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Building2,
  FileText,
  CreditCard,
  BarChart3,
  Download,
  Plus,
  Eye,
  Edit } from
"lucide-react";
import { PageHeader } from "../components/layout";
import { PaymentDialog } from "../components/invoice-management/dialogs";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Label,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Progress } from
"../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { receivableApi, paymentApi, invoiceApi as _invoiceApi } from "../services/api";

// 收款状态配置
const paymentStatusConfig = {
  PENDING: {
    label: "待收款",
    color: "bg-blue-500",
    textColor: "text-blue-400"
  },
  PARTIAL: {
    label: "部分收款",
    color: "bg-amber-500",
    textColor: "text-amber-400"
  },
  PAID: {
    label: "已收款",
    color: "bg-emerald-500",
    textColor: "text-emerald-400"
  },
  OVERDUE: { label: "已逾期", color: "bg-red-500", textColor: "text-red-400" }
};

export default function ReceivableManagement() {
  const [receivables, setReceivables] = useState([]);
  const [agingData, setAgingData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [selectedReceivable, setSelectedReceivable] = useState(null);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [paymentData, setPaymentData] = useState({
    paid_amount: "",
    paid_date: new Date().toISOString().split("T")[0],
    payment_method: "",
    bank_account: "",
    remark: ""
  });

  const loadReceivables = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        payment_status: statusFilter !== "all" ? statusFilter : undefined
      };
      // 如果只显示逾期，使用逾期接口
      if (overdueOnly) {
        const response = await receivableApi.list(params);
        if (response.data && response.data.items) {
          setReceivables(response.data.items);
          setTotal(response.data.total || 0);
        }
      } else {
        // 否则使用回款记录列表接口
        const response = await paymentApi.list(params);
        if (response.data && response.data.items) {
          setReceivables(response.data.items);
          setTotal(response.data.total || 0);
        }
      }
    } catch (error) {
      console.error("加载应收账款列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadAging = async () => {
    try {
      const response = await receivableApi.getAging();
      if (response.data && response.data.data) {
        setAgingData(response.data.data);
      } else if (response.data) {
        // 兼容直接返回数据的情况
        setAgingData(response.data);
      }
    } catch (error) {
      console.error("加载账龄分析失败:", error);
    }
  };

  useEffect(() => {
    loadReceivables();
  }, [page, searchTerm, statusFilter, overdueOnly]);

  useEffect(() => {
    loadAging();
  }, []);

  const handleReceivePayment = async () => {
    if (!selectedReceivable) {return;}
    try {
      // 使用新的回款登记API
      await paymentApi.create({
        invoice_id: selectedReceivable.id,
        paid_amount: paymentData.paid_amount,
        paid_date: paymentData.paid_date,
        payment_method: paymentData.payment_method || undefined,
        bank_account: paymentData.bank_account || undefined,
        remark: paymentData.remark || undefined
      });
      setShowPaymentDialog(false);
      setSelectedReceivable(null);
      setPaymentData({
        paid_amount: "",
        paid_date: new Date().toISOString().split("T")[0],
        payment_method: "",
        bank_account: "",
        remark: ""
      });
      loadReceivables();
      loadAging();
    } catch (error) {
      console.error("记录收款失败:", error);
      alert("记录收款失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const formatCurrency = (value) => {
    if (!value) {return "0";}
    const num = parseFloat(value);
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + "万";
    }
    return num.toLocaleString();
  };

  const [summary, setSummary] = useState(null);

  const loadSummary = async () => {
    try {
      const response = await receivableApi.getSummary();
      if (response.data && response.data.data) {
        setSummary(response.data.data);
      } else if (response.data) {
        setSummary(response.data);
      }
    } catch (error) {
      console.error("加载应收账款统计失败:", error);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  // 导出数据
  const handleExport = () => {
    try {
      // 准备导出数据
      const exportData = receivables.map((r) => ({
        发票编码: r.invoice_code,
        客户名称: r.customer_name,
        合同编码: r.contract_code,
        发票金额: r.invoice_amount || r.total_amount || 0,
        已收金额: r.paid_amount || 0,
        待收金额: r.unpaid_amount || r.invoice_amount - r.paid_amount || 0,
        到期日期: r.due_date || "",
        逾期天数: r.overdue_days || 0,
        收款状态:
        paymentStatusConfig[r.payment_status]?.label || r.payment_status
      }));

      // 转换为CSV格式
      const headers = Object.keys(exportData[0] || {});
      const csvContent = [
      headers.join(","),
      ...exportData.map((row) =>
      headers.map((header) => `"${row[header] || ""}"`).join(",")
      )].
      join("\n");

      // 添加BOM以支持中文
      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], {
        type: "text/csv;charset=utf-8;"
      });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute(
        "download",
        `应收账款列表_${new Date().toISOString().split("T")[0]}.csv`
      );
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("导出失败:", error);
      alert("导出失败: " + error.message);
    }
  };

  const stats = useMemo(() => {
    if (summary) {
      return {
        total: summary.invoice_count || total,
        totalUnpaid: summary.unpaid_amount || 0,
        totalOverdue: summary.overdue_amount || 0,
        overdueCount: summary.overdue_count || 0
      };
    }
    return {
      total: total,
      totalUnpaid: receivables.reduce(
        (sum, r) =>
        sum + (
        parseFloat(r.unpaid_amount || r.invoice_amount - r.paid_amount) ||
        0),
        0
      ),
      totalOverdue: receivables.
      filter((r) => r.overdue_days > 0).
      reduce(
        (sum, r) =>
        sum + (
        parseFloat(r.unpaid_amount || r.invoice_amount - r.paid_amount) ||
        0),
        0
      ),
      overdueCount: receivables.filter((r) => r.overdue_days > 0).length
    };
  }, [receivables, total, summary]);

  const receivableBaseAmount = selectedReceivable
    ? (selectedReceivable.invoice_amount ??
      selectedReceivable.total_amount ??
      0)
    : 0;
  const receivablePendingAmount = selectedReceivable
    ? (selectedReceivable.unpaid_amount ??
      (receivableBaseAmount - (selectedReceivable.paid_amount ?? 0)))
    : 0;
  const receivableMaxAmount = selectedReceivable
    ? (selectedReceivable.unpaid_amount ?? receivableBaseAmount)
    : undefined;
  const paymentDateMax = new Date().toISOString().split("T")[0];
  const paymentAmountPlaceholder = selectedReceivable
    ? `最大可收: ${formatCurrency(receivableMaxAmount)}`
    : "请输入收款金额";

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6">

      <PageHeader
        title="应收账款管理"
        description="跟踪和管理应收账款，记录收款，分析账龄"
        action={
        <div className="flex gap-2">
            <Button variant="outline" onClick={() => loadAging()}>
              <BarChart3 className="mr-2 h-4 w-4" />
              刷新账龄
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="mr-2 h-4 w-4" />
              导出数据
            </Button>
        </div>
        } />


      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">应收账款总数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">待收金额</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(stats.totalUnpaid)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">逾期金额</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(stats.totalOverdue)}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">逾期笔数</p>
                <p className="text-2xl font-bold text-white">
                  {stats.overdueCount}
                </p>
              </div>
              <Clock className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 账龄分析 */}
      {agingData &&
      <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>应收账款账龄分析</CardTitle>
              <div className="text-sm text-slate-400">
                总计待收: {formatCurrency(agingData.total_unpaid || 0)}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* 账龄卡片 */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {Object.entries(agingData.aging_buckets || {}).
              sort(([a], [b]) => {
                // 排序：0-30, 31-60, 61-90, 90+
                const order = {
                  "0-30": 1,
                  "31-60": 2,
                  "61-90": 3,
                  "90+": 4
                };
                return (order[a] || 99) - (order[b] || 99);
              }).
              map(([key, bucket]) => {
                const labelMap = {
                  "0-30": "0-30天",
                  "31-60": "31-60天",
                  "61-90": "61-90天",
                  "90+": "90+天"
                };
                const colorMap = {
                  "0-30": "bg-emerald-500",
                  "31-60": "bg-blue-500",
                  "61-90": "bg-amber-500",
                  "90+": "bg-red-500"
                };
                const percentage =
                agingData.total_unpaid > 0 ?
                (bucket.amount || 0) / agingData.total_unpaid * 100 :
                0;
                return (
                  <Card key={key} className="border-slate-700">
                        <CardContent className="p-4">
                          <div className="space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium text-slate-300">
                                {labelMap[key] || key}
                              </span>
                              <Badge className={colorMap[key] || "bg-blue-500"}>
                                {bucket.count || 0} 笔
                              </Badge>
                            </div>
                            <div className="text-2xl font-bold text-white">
                              {formatCurrency(bucket.amount || 0)}
                            </div>
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-400">占比</span>
                                <span className="text-slate-300">
                                  {percentage.toFixed(1)}%
                                </span>
                              </div>
                              <Progress value={percentage} className="h-2" />
                            </div>
                          </div>
                        </CardContent>
                  </Card>);

              })}
              </div>

              {/* 账龄分布图表（简化版） */}
              {agingData.total_unpaid > 0 &&
            <div className="mt-6 pt-6 border-t border-slate-700">
                  <h4 className="text-sm font-semibold text-slate-300 mb-4">
                    账龄分布
                  </h4>
                  <div className="flex items-end gap-2 h-32">
                    {Object.entries(agingData.aging_buckets || {}).
                sort(([a], [b]) => {
                  const order = {
                    "0-30": 1,
                    "31-60": 2,
                    "61-90": 3,
                    "90+": 4
                  };
                  return (order[a] || 99) - (order[b] || 99);
                }).
                map(([key, bucket]) => {
                  const height =
                  agingData.total_unpaid > 0 ?
                  (bucket.amount || 0) / agingData.total_unpaid *
                  100 :
                  0;
                  const colorMap = {
                    "0-30": "bg-emerald-500",
                    "31-60": "bg-blue-500",
                    "61-90": "bg-amber-500",
                    "90+": "bg-red-500"
                  };
                  const labelMap = {
                    "0-30": "0-30天",
                    "31-60": "31-60天",
                    "61-90": "61-90天",
                    "90+": "90+天"
                  };
                  return (
                    <div
                      key={key}
                      className="flex-1 flex flex-col items-center gap-2">

                            <div className="w-full flex flex-col items-center justify-end h-full">
                              <div
                          className={`w-full ${colorMap[key] || "bg-blue-500"} rounded-t transition-all hover:opacity-80 cursor-pointer`}
                          style={{ height: `${height}%` }}
                          title={`${labelMap[key]}: ${formatCurrency(bucket.amount || 0)}`} />

                            </div>
                            <span className="text-xs text-slate-400 text-center">
                              {labelMap[key] || key}
                            </span>
                            <span className="text-xs text-slate-500">
                              {formatCurrency(bucket.amount || 0)}
                            </span>
                    </div>);

                })}
                  </div>
            </div>
            }
            </div>
          </CardContent>
      </Card>
      }

      {/* 筛选栏 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索发票编码..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10" />

            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  状态:{" "}
                  {statusFilter === "all" ?
                  "全部" :
                  paymentStatusConfig[statusFilter]?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setStatusFilter("all")}>
                  全部
                </DropdownMenuItem>
                {Object.entries(paymentStatusConfig).map(([key, config]) =>
                <DropdownMenuItem
                  key={key}
                  onClick={() => setStatusFilter(key)}>

                    {config.label}
                </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={overdueOnly}
                onChange={(e) => setOverdueOnly(e.target.checked)}
                className="w-4 h-4" />

              <Label>仅显示逾期</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 应收账款列表 */}
      {loading ?
      <div className="text-center py-12 text-slate-400">加载中...</div> :
      receivables.length === 0 ?
      <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无应收账款数据</p>
          </CardContent>
      </Card> :

      <Card>
          <CardHeader>
            <CardTitle>应收账款列表</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {receivables.map((receivable) => {
              const invoiceAmount =
              receivable.invoice_amount || receivable.total_amount || 0;
              const paidAmount = receivable.paid_amount || 0;
              const unpaidAmount =
              receivable.unpaid_amount || invoiceAmount - paidAmount;
              const paymentProgress =
              invoiceAmount > 0 ? paidAmount / invoiceAmount * 100 : 0;

              return (
                <motion.div
                  key={receivable.id}
                  variants={fadeIn}
                  className="group flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 transition-all hover:border-slate-600 hover:bg-slate-800/60">

                    <div className="flex flex-1 items-center gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="font-semibold text-slate-100">
                            {receivable.invoice_code}
                          </span>
                          <Badge
                          className={cn(
                            paymentStatusConfig[receivable.payment_status]?.
                            color
                          )}>

                            {paymentStatusConfig[receivable.payment_status]?.
                          label || receivable.payment_status}
                          </Badge>
                          {receivable.overdue_days > 0 &&
                        <Badge className="bg-red-500">
                              逾期 {receivable.overdue_days} 天
                        </Badge>
                        }
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-sm">
                          <span className="text-slate-500">
                            {receivable.customer_name}
                          </span>
                          <span className="text-slate-600">|</span>
                          <span className="text-slate-500">
                            {receivable.contract_code}
                          </span>
                          {receivable.due_date &&
                        <>
                              <span className="text-slate-600">|</span>
                              <span className="text-slate-500">
                                到期: {receivable.due_date}
                              </span>
                        </>
                        }
                        </div>
                        <div className="mt-2">
                          <Progress value={paymentProgress} className="h-2" />
                          <div className="flex items-center justify-between mt-1 text-xs text-slate-400">
                            <span>
                              已收: {formatCurrency(paidAmount)} /{" "}
                              {formatCurrency(invoiceAmount)}
                            </span>
                            <span>待收: {formatCurrency(unpaidAmount)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <p className="font-semibold text-amber-400">
                          {formatCurrency(unpaidAmount)}
                        </p>
                        <p className="text-xs text-slate-500">待收金额</p>
                      </div>
                      <div className="ml-4 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                        {receivable.payment_status !== "PAID" &&
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedReceivable(receivable);
                          setShowPaymentDialog(true);
                        }}>

                            <CreditCard className="h-4 w-4 mr-2" />
                            记录收款
                      </Button>
                      }
                        <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          // 查看详情
                          window.open(
                            `/sales/invoices/${receivable.id}`,
                            "_blank"
                          );
                        }}>

                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                </motion.div>);

            })}
            </div>
          </CardContent>
      </Card>
      }

      {/* 分页 */}
      {total > pageSize &&
      <div className="flex justify-center gap-2">
          <Button
          variant="outline"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}>

            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
          variant="outline"
          disabled={page >= Math.ceil(total / pageSize)}
          onClick={() => setPage(page + 1)}>

            下一页
          </Button>
      </div>
      }

      {/* 记录收款对话框 */}
      <PaymentDialog
        open={showPaymentDialog}
        onOpenChange={setShowPaymentDialog}
        paymentData={paymentData}
        setPaymentData={setPaymentData}
        invoiceLabel={selectedReceivable?.invoice_code}
        pendingAmount={receivablePendingAmount}
        amountStep="0.01"
        amountMin={0}
        amountMax={receivableMaxAmount}
        amountPlaceholder={paymentAmountPlaceholder}
        dateMax={paymentDateMax}
        showPaymentMethod
        showBankAccount
        formatAmount={formatCurrency}
        onConfirm={handleReceivePayment}
      />
    </motion.div>);

}
