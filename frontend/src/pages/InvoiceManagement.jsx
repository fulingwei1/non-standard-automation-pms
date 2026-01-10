/**
 * Invoice Management Page - Accounts receivable and invoicing management
 * Handles invoice creation, tracking, and reconciliation
 */

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Receipt,
  Search,
  Filter,
  Plus,
  Download,
  Send,
  Check,
  X,
  AlertTriangle,
  Clock,
  FileText,
  DollarSign,
  Building2,
  Calendar,
  ChevronRight,
  TrendingUp,
  BarChart3,
} from "lucide-react";
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
  DialogFooter,
  Label,
  Textarea,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui";
import { cn, formatCurrency, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { invoiceApi, contractApi } from "../services/api";
import { CreditCard } from "lucide-react";

// Invoice status mapping
const statusMap = {
  DRAFT: "draft",
  APPLIED: "applied",
  APPROVED: "approved",
  ISSUED: "issued",
  VOID: "void",
};

const paymentStatusMap = {
  PENDING: "pending",
  PARTIAL: "partial",
  PAID: "paid",
  OVERDUE: "overdue",
};

// Mock invoice data (fallback)
// Mock data - 已移除，使用真实API
const statusConfig = {
  draft: {
    label: "草稿",
    color: "bg-slate-500/20 text-slate-400",
    icon: FileText,
  },
  applied: {
    label: "申请中",
    color: "bg-blue-500/20 text-blue-400",
    icon: Clock,
  },
  approved: {
    label: "已批准",
    color: "bg-purple-500/20 text-purple-400",
    icon: Check,
  },
  issued: {
    label: "已开票",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check,
  },
  void: { label: "作废", color: "bg-red-500/20 text-red-400", icon: X },
};

const paymentStatusConfig = {
  pending: {
    label: "未收款",
    color: "bg-slate-500/20 text-slate-400",
    icon: Clock,
  },
  partial: {
    label: "部分收款",
    color: "bg-amber-500/20 text-amber-400",
    icon: TrendingUp,
  },
  paid: {
    label: "已收款",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check,
  },
  overdue: {
    label: "已逾期",
    color: "bg-red-500/20 text-red-400",
    icon: AlertTriangle,
  },
};

const InvoiceRow = ({
  invoice,
  onView,
  onEdit,
  onDelete,
  onIssue,
  onReceivePayment,
}) => {
  const invoiceConfig = statusConfig[invoice.status];
  const paymentConfig = paymentStatusConfig[invoice.paymentStatus];
  const InvoiceIcon = invoiceConfig.icon;
  const PaymentIcon = paymentConfig.icon;

  return (
    <motion.div
      variants={fadeIn}
      className="group flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 transition-all hover:border-slate-600 hover:bg-slate-800/60"
    >
      <div className="flex flex-1 items-center gap-4">
        {/* Checkbox */}
        <input type="checkbox" className="h-4 w-4 rounded cursor-pointer" />

        {/* Invoice Info */}
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-100">{invoice.id}</span>
            <span className="text-sm text-slate-400">
              {invoice.projectName}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-3 text-sm">
            <span className="text-slate-500">{invoice.customerName}</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-500">{invoice.invoiceType}</span>
            {invoice.issueDate && (
              <>
                <span className="text-slate-600">|</span>
                <span className="text-slate-500">{invoice.issueDate}</span>
              </>
            )}
          </div>
        </div>

        {/* Amount */}
        <div className="flex flex-col items-end gap-1">
          <p className="font-semibold text-amber-400">
            {formatCurrency(invoice.totalAmount)}
          </p>
          <p className="text-xs text-slate-500">含税</p>
        </div>

        {/* Status Badges */}
        <div className="ml-4 flex flex-col gap-2">
          <Badge className={cn("text-xs", invoiceConfig.color)}>
            <InvoiceIcon className="mr-1 h-3 w-3" />
            {invoiceConfig.label}
          </Badge>
          <Badge className={cn("text-xs", paymentConfig.color)}>
            <PaymentIcon className="mr-1 h-3 w-3" />
            {paymentConfig.label}
          </Badge>
        </div>

        {/* Actions */}
        <div className="ml-4 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0"
            onClick={() => onView(invoice)}
          >
            <FileText className="h-4 w-4 text-blue-400" />
          </Button>
          {invoice.status === "draft" && (
            <>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0"
                onClick={() => onEdit(invoice)}
                title="编辑"
              >
                <Edit className="h-4 w-4 text-amber-400" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0"
                onClick={() => onDelete(invoice)}
                title="删除"
              >
                <X className="h-4 w-4 text-red-400" />
              </Button>
            </>
          )}
          {invoice.status === "approved" && onIssue && (
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => onIssue(invoice)}
            >
              <Send className="h-4 w-4 text-purple-400" />
            </Button>
          )}
          {invoice.status === "issued" &&
            invoice.paymentStatus !== "paid" &&
            onReceivePayment && (
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0"
                onClick={() => onReceivePayment(invoice)}
                title="记录收款"
              >
                <DollarSign className="h-4 w-4 text-emerald-400" />
              </Button>
            )}
          <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
            <Download className="h-4 w-4 text-slate-400" />
          </Button>
        </div>
      </div>
    </motion.div>
  );
};

export default function InvoiceManagement() {
  const [invoices, setInvoices] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchText, setSearchText] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterPayment, setFilterPayment] = useState("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showIssueDialog, setShowIssueDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [formData, setFormData] = useState({
    contract_id: "",
    invoice_type: "SPECIAL",
    amount: "",
    tax_rate: "13",
    issue_date: "",
    due_date: "",
    remark: "",
  });

  const [issueData, setIssueData] = useState({
    invoice_no: "",
    issue_date: new Date().toISOString().split("T")[0],
    remark: "",
  });

  const [paymentData, setPaymentData] = useState({
    paid_amount: "",
    paid_date: new Date().toISOString().split("T")[0],
    remark: "",
  });

  const loadInvoices = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchText || undefined,
        status:
          filterStatus !== "all"
            ? Object.keys(statusMap).find((k) => statusMap[k] === filterStatus)
            : undefined,
        payment_status:
          filterPayment !== "all"
            ? Object.keys(paymentStatusMap).find(
                (k) => paymentStatusMap[k] === filterPayment,
              )
            : undefined,
      };
      const response = await invoiceApi.list(params);
      if (response.data && response.data.items) {
        // Transform API data to match UI format
        const transformed = response.data.items.map((inv) => ({
          id: inv.invoice_code || inv.id,
          contractId: inv.contract_code,
          projectName: inv.project_name || "",
          customerName: inv.customer_name || "",
          amount: parseFloat(inv.amount || 0),
          taxRate: parseFloat(inv.tax_rate || 0),
          taxAmount: parseFloat(inv.tax_amount || 0),
          totalAmount: parseFloat(inv.total_amount || 0),
          invoiceType: inv.invoice_type === "SPECIAL" ? "专票" : "普票",
          status: statusMap[inv.status] || "draft",
          issueDate: inv.issue_date || null,
          dueDate: inv.due_date || null,
          paymentStatus: paymentStatusMap[inv.payment_status] || "pending",
          paidAmount: parseFloat(inv.paid_amount || 0),
          paidDate: inv.paid_date || null,
          notes: inv.remark || "",
          raw: inv, // Keep original data
        }));
        setInvoices(transformed);
        setTotal(response.data.total || 0);
      }
    } catch (error) {
      console.error("加载发票列表失败:", error);
      setError(
        error.response?.data?.detail || error.message || "加载发票列表失败",
      );
      setInvoices([]); // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false);
    }
  };

  const loadContracts = async () => {
    try {
      const response = await contractApi.list({ page: 1, page_size: 100 });
      if (response.data && response.data.items) {
        setContracts(response.data.items);
      }
    } catch (error) {
      console.error("加载合同列表失败:", error);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, [page, searchText, filterStatus, filterPayment]);

  useEffect(() => {
    loadContracts();
  }, []);

  const handleCreate = async () => {
    try {
      await invoiceApi.create(formData);
      setShowCreateDialog(false);
      resetForm();
      loadInvoices();
    } catch (error) {
      console.error("创建发票失败:", error);
      alert("创建发票失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleIssue = async () => {
    if (!selectedInvoice) return;
    try {
      await invoiceApi.issue(selectedInvoice.raw.id, issueData);
      setShowIssueDialog(false);
      setSelectedInvoice(null);
      loadInvoices();
    } catch (error) {
      console.error("开票失败:", error);
      alert("开票失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleReceivePayment = async () => {
    if (!selectedInvoice) return;
    try {
      await invoiceApi.receivePayment(selectedInvoice.raw.id, paymentData);
      setShowPaymentDialog(false);
      setSelectedInvoice(null);
      setPaymentData({
        paid_amount: "",
        paid_date: new Date().toISOString().split("T")[0],
        remark: "",
      });
      loadInvoices();
    } catch (error) {
      console.error("记录收款失败:", error);
      alert("记录收款失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = async (invoice) => {
    try {
      const response = await invoiceApi.get(invoice.raw.id);
      if (response.data) {
        const inv = response.data;
        setSelectedInvoice(invoice);
        setFormData({
          contract_id: inv.contract_id || "",
          invoice_type: inv.invoice_type || "SPECIAL",
          amount: inv.amount || "",
          tax_rate: inv.tax_rate ? String(inv.tax_rate) : "13",
          issue_date: inv.issue_date || "",
          due_date: inv.due_date || "",
          remark: inv.remark || "",
        });
        setShowEditDialog(true);
      }
    } catch (error) {
      console.error("加载发票详情失败:", error);
      alert("加载发票详情失败");
    }
  };

  const handleUpdate = async () => {
    if (!selectedInvoice) return;
    try {
      await invoiceApi.update(selectedInvoice.raw.id, formData);
      setShowEditDialog(false);
      setSelectedInvoice(null);
      resetForm();
      loadInvoices();
    } catch (error) {
      console.error("更新发票失败:", error);
      alert("更新发票失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async () => {
    if (!selectedInvoice) return;
    try {
      // 只有草稿状态的发票可以删除
      if (selectedInvoice.status !== "draft") {
        alert("只能删除草稿状态的发票");
        return;
      }
      // 注意：后端API可能没有delete方法，需要检查
      // 如果有delete方法，使用：await invoiceApi.delete(selectedInvoice.raw.id)
      // 否则可能需要使用update方法将状态改为VOID
      await invoiceApi.update(selectedInvoice.raw.id, { status: "VOID" });
      setShowDeleteDialog(false);
      setSelectedInvoice(null);
      loadInvoices();
      alert("发票已删除");
    } catch (error) {
      console.error("删除发票失败:", error);
      alert("删除发票失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setFormData({
      contract_id: "",
      invoice_type: "SPECIAL",
      amount: "",
      tax_rate: "13",
      issue_date: "",
      due_date: "",
      remark: "",
    });
  };

  const filteredInvoices = useMemo(() => {
    return invoices.filter((invoice) => {
      const matchSearch =
        invoice.id.toLowerCase().includes(searchText.toLowerCase()) ||
        invoice.projectName.toLowerCase().includes(searchText.toLowerCase()) ||
        invoice.customerName.toLowerCase().includes(searchText.toLowerCase());

      const matchStatus =
        filterStatus === "all" || invoice.status === filterStatus;
      const matchPayment =
        filterPayment === "all" || invoice.paymentStatus === filterPayment;

      return matchSearch && matchStatus && matchPayment;
    });
  }, [invoices, searchText, filterStatus, filterPayment]);

  const stats = {
    totalInvoices: invoices.length,
    totalAmount: invoices.reduce((sum, inv) => sum + inv.totalAmount, 0),
    paidAmount: invoices.reduce(
      (sum, inv) => sum + (inv.paymentStatus === "paid" ? inv.totalAmount : 0),
      0,
    ),
    pendingAmount: invoices.reduce(
      (sum, inv) =>
        sum +
        (inv.paymentStatus === "pending" || inv.paymentStatus === "overdue"
          ? inv.totalAmount
          : 0),
      0,
    ),
  };

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="对账开票管理"
        description="发票申请、开票、收款跟踪"
        action={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建发票
          </Button>
        }
      />

      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
      >
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">发票总数</p>
              <p className="text-3xl font-bold text-blue-400">
                {stats.totalInvoices}
              </p>
              <p className="text-xs text-slate-500">份</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">发票总金额</p>
              <p className="text-2xl font-bold text-amber-400">
                {formatCurrency(stats.totalAmount)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">已收款</p>
              <p className="text-2xl font-bold text-emerald-400">
                {formatCurrency(stats.paidAmount)}
              </p>
              <p className="text-xs text-slate-500">
                {((stats.paidAmount / stats.totalAmount) * 100).toFixed(1)}%
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">待收款</p>
              <p className="text-2xl font-bold text-red-400">
                {formatCurrency(stats.pendingAmount)}
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder="搜索发票号、项目名、客户名..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterStatus === "all" ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterStatus("all")}
              >
                全部状态
              </Button>
              {Object.entries(statusConfig).map(([key, config]) => (
                <Button
                  key={key}
                  variant={filterStatus === key ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setFilterStatus(key)}
                  className={cn(filterStatus === key && config.color)}
                >
                  {config.label}
                </Button>
              ))}
              <div className="w-full border-t border-slate-700/30" />
              <Button
                variant={filterPayment === "all" ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterPayment("all")}
              >
                全部收款状态
              </Button>
              {Object.entries(paymentStatusConfig).map(([key, config]) => (
                <Button
                  key={key}
                  variant={filterPayment === key ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setFilterPayment(key)}
                  className={cn(filterPayment === key && config.color)}
                >
                  {config.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Invoice List */}
      <Card>
        <CardHeader>
          <CardTitle>发票列表</CardTitle>
          <p className="mt-2 text-sm text-slate-400">
            共 {filteredInvoices.length} 份发票
          </p>
        </CardHeader>
        <CardContent>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-2"
          >
            <AnimatePresence>
              {filteredInvoices.length > 0 ? (
                filteredInvoices.map((invoice) => (
                  <InvoiceRow
                    key={invoice.id}
                    invoice={invoice}
                    onView={(inv) => {
                      setSelectedInvoice(inv);
                      // Show detail dialog or navigate
                    }}
                    onEdit={handleEdit}
                    onDelete={(inv) => {
                      setSelectedInvoice(inv);
                      setShowDeleteDialog(true);
                    }}
                    onIssue={(inv) => {
                      setSelectedInvoice(inv);
                      setShowIssueDialog(true);
                    }}
                    onReceivePayment={(inv) => {
                      setSelectedInvoice(inv);
                      setPaymentData({
                        paid_amount: (inv.totalAmount - inv.paidAmount).toFixed(
                          2,
                        ),
                        paid_date: new Date().toISOString().split("T")[0],
                        remark: "",
                      });
                      setShowPaymentDialog(true);
                    }}
                  />
                ))
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="py-12 text-center"
                >
                  <p className="text-slate-400">没有符合条件的发票</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {filteredInvoices.length > 0 && (
        <Card className="bg-blue-500/10 border-blue-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-300">
                已选择 0 / {filteredInvoices.length} 份发票
              </p>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" className="gap-2">
                  <Send className="h-4 w-4" />
                  批量发送
                </Button>
                <Button variant="ghost" size="sm" className="gap-2">
                  <Download className="h-4 w-4" />
                  批量下载
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-2 text-red-400 hover:text-red-300"
                >
                  <X className="h-4 w-4" />
                  取消选择
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 创建发票对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建发票</DialogTitle>
            <DialogDescription>创建新的发票申请</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>合同 *</Label>
                <select
                  value={formData.contract_id}
                  onChange={(e) =>
                    setFormData({ ...formData, contract_id: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="">请选择合同</option>
                  {contracts.map((contract) => (
                    <option key={contract.id} value={contract.id}>
                      {contract.contract_code} - {contract.customer_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>发票类型 *</Label>
                <select
                  value={formData.invoice_type}
                  onChange={(e) =>
                    setFormData({ ...formData, invoice_type: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="SPECIAL">专票</option>
                  <option value="NORMAL">普票</option>
                </select>
              </div>
              <div>
                <Label>金额 *</Label>
                <Input
                  type="number"
                  value={formData.amount}
                  onChange={(e) =>
                    setFormData({ ...formData, amount: e.target.value })
                  }
                  placeholder="请输入金额"
                />
              </div>
              <div>
                <Label>税率 (%)</Label>
                <Input
                  type="number"
                  value={formData.tax_rate}
                  onChange={(e) =>
                    setFormData({ ...formData, tax_rate: e.target.value })
                  }
                  placeholder="13"
                />
              </div>
              <div>
                <Label>开票日期</Label>
                <Input
                  type="date"
                  value={formData.issue_date}
                  onChange={(e) =>
                    setFormData({ ...formData, issue_date: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>到期日期</Label>
                <Input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) =>
                    setFormData({ ...formData, due_date: e.target.value })
                  }
                />
              </div>
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={formData.remark}
                onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="请输入备注"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 开票对话框 */}
      <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>开票</DialogTitle>
            <DialogDescription>确认开票信息</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>发票号码 *</Label>
              <Input
                value={issueData.invoice_no}
                onChange={(e) =>
                  setIssueData({ ...issueData, invoice_no: e.target.value })
                }
                placeholder="请输入发票号码"
              />
            </div>
            <div>
              <Label>开票日期 *</Label>
              <Input
                type="date"
                value={issueData.issue_date}
                onChange={(e) =>
                  setIssueData({ ...issueData, issue_date: e.target.value })
                }
              />
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={issueData.remark}
                onChange={(e) =>
                  setIssueData({ ...issueData, remark: e.target.value })
                }
                placeholder="请输入备注"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowIssueDialog(false)}>
              取消
            </Button>
            <Button onClick={handleIssue}>确认开票</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 记录收款对话框 */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>记录收款</DialogTitle>
            <DialogDescription>
              发票: {selectedInvoice?.id}
              <br />
              待收金额:{" "}
              {formatCurrency(
                (selectedInvoice?.totalAmount || 0) -
                  (selectedInvoice?.paidAmount || 0),
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>收款金额 *</Label>
              <Input
                type="number"
                value={paymentData.paid_amount}
                onChange={(e) =>
                  setPaymentData({
                    ...paymentData,
                    paid_amount: e.target.value,
                  })
                }
                placeholder="请输入收款金额"
              />
            </div>
            <div>
              <Label>收款日期 *</Label>
              <Input
                type="date"
                value={paymentData.paid_date}
                onChange={(e) =>
                  setPaymentData({ ...paymentData, paid_date: e.target.value })
                }
              />
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={paymentData.remark}
                onChange={(e) =>
                  setPaymentData({ ...paymentData, remark: e.target.value })
                }
                placeholder="请输入备注"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowPaymentDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleReceivePayment}>确认收款</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑发票对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑发票</DialogTitle>
            <DialogDescription>更新发票信息</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>合同 *</Label>
                <select
                  value={formData.contract_id}
                  onChange={(e) =>
                    setFormData({ ...formData, contract_id: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="">请选择合同</option>
                  {contracts.map((contract) => (
                    <option key={contract.id} value={contract.id}>
                      {contract.contract_code} - {contract.customer_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>发票类型 *</Label>
                <select
                  value={formData.invoice_type}
                  onChange={(e) =>
                    setFormData({ ...formData, invoice_type: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="SPECIAL">专票</option>
                  <option value="NORMAL">普票</option>
                </select>
              </div>
              <div>
                <Label>金额 *</Label>
                <Input
                  type="number"
                  value={formData.amount}
                  onChange={(e) =>
                    setFormData({ ...formData, amount: e.target.value })
                  }
                  placeholder="请输入金额"
                />
              </div>
              <div>
                <Label>税率 (%)</Label>
                <Input
                  type="number"
                  value={formData.tax_rate}
                  onChange={(e) =>
                    setFormData({ ...formData, tax_rate: e.target.value })
                  }
                  placeholder="13"
                />
              </div>
              <div>
                <Label>开票日期</Label>
                <Input
                  type="date"
                  value={formData.issue_date}
                  onChange={(e) =>
                    setFormData({ ...formData, issue_date: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>到期日期</Label>
                <Input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) =>
                    setFormData({ ...formData, due_date: e.target.value })
                  }
                />
              </div>
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={formData.remark}
                onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="请输入备注"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除发票 {selectedInvoice?.id} 吗？
              <br />
              此操作不可撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(total / pageSize)}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  );
}
