/**
 * InvoiceManagement - 发票管理页面（页面级组件）
 *
 * ARCHITECTURE NOTE:
 * This is the PAGE-LEVEL component that composes reusable UI components from
 * components/invoice-management/ with page-specific business logic (API calls,
 * state management, routing context).
 *
 * Component hierarchy:
 * pages/invoice/InvoiceManagement.jsx (THIS FILE - page composition + business logic)
 * -> components/invoice-management/InvoiceRow.jsx  (reusable row UI)
 * -> components/invoice-management/InvoiceStats.jsx (reusable stats UI)
 * -> components/invoice-management/InvoiceFilters.jsx (reusable filters UI)
 * -> components/invoice-management/InvoiceList.jsx (reusable list wrapper)
 * -> components/invoice-management/dialogs/   (reusable dialog components)
 *
 * Constants are centralized in lib/constants/finance.js (single source of truth).
 */

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Send, Download, X } from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
 Card,
  CardContent,
  CardHeader,
 CardTitle,
 Button
} from "../../components/ui";
import { staggerContainer } from "../../lib/animations";
import { invoiceApi, contractApi } from "../../services/api";

// 从 components/invoice-management/ 导入可复用 UI 组件
import InvoiceRow from "../../components/invoice-management/InvoiceRow";
import InvoiceStats from "../../components/invoice-management/InvoiceStats";
import InvoiceFilters from "../../components/invoice-management/InvoiceFilters";
// 从共享常量导入（单一数据源：lib/constants/finance.js）
import {
 statusMap,
 paymentStatusMap,
 defaultFormData,
  defaultIssueData,
 defaultPaymentData
} from "../../lib/constants/finance";
// 对话框组件（统一从 components/invoice-management/dialogs/ 导入）
import {
 CreateInvoiceDialog,
  EditInvoiceDialog,
  IssueInvoiceDialog,
 PaymentDialog,
 DeleteConfirmDialog
} from "../../components/invoice-management/dialogs";

export default function InvoiceManagement() {
  const [invoices, setInvoices] = useState([]);
 const [contracts, setContracts] = useState([]);
  const [_loading, setLoading] = useState(false);
 const [_error, setError] = useState(null);
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

 const [formData, setFormData] = useState(defaultFormData);
 const [issueData, setIssueData] = useState(defaultIssueData);
 const [paymentData, setPaymentData] = useState(defaultPaymentData);

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
     (k) => paymentStatusMap[k] === filterPayment
   )
  : undefined
 };
  const response = await invoiceApi.list(params);
 if (response.data && response.data.items) {
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
 raw: inv
 }));
  setInvoices(transformed);
  setTotal(response.data.total || 0);
  }
 } catch (error) {
  console.error("加载发票列表失败:", error);
 setError(
 error.response?.data?.detail || error.message || "加载发票列表失败"
 );
 setInvoices([]);
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
 setPaymentData(defaultPaymentData);
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
   remark: inv.remark || ""
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
 if (selectedInvoice.status !== "draft") {
  alert("只能删除草稿状态的发票");
 return;
  }
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
 setFormData(defaultFormData);
 };

 const filteredInvoices = useMemo(() => {
 return invoices.filter((invoice) => {
   const searchLower = (searchText || "").toLowerCase();
 const matchSearch =
  (invoice.id || "").toLowerCase().includes(searchLower) ||
  (invoice.projectName || "").toLowerCase().includes(searchLower) ||
   (invoice.customerName || "").toLowerCase().includes(searchLower);

 const matchStatus =
 filterStatus === "all" || invoice.status === filterStatus;
  const matchPayment =
 filterPayment === "all" || invoice.paymentStatus === filterPayment;

  return matchSearch && matchStatus && matchPayment;
 });
  }, [invoices, searchText, filterStatus, filterPayment]);

 const stats = useMemo(
 () => ({
 totalInvoices: invoices.length,
  totalAmount: invoices.reduce((sum, inv) => sum + inv.totalAmount, 0),
  paidAmount: invoices.reduce(
  (sum, inv) =>
   sum + (inv.paymentStatus === "paid" ? inv.totalAmount : 0),
  0
  ),
  pendingAmount: invoices.reduce(
 (sum, inv) =>
  sum +
  (inv.paymentStatus === "pending" || inv.paymentStatus === "overdue"
   ? inv.totalAmount
   : 0),
  0
  )
 }),
  [invoices]
 );

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

  <InvoiceStats stats={stats} />

   <InvoiceFilters
   searchText={searchText}
  onSearchChange={setSearchText}
  filterStatus={filterStatus}
  onStatusChange={setFilterStatus}
  filterPayment={filterPayment}
   onPaymentChange={setFilterPayment}
  />

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
    2
     ),
     paid_date: new Date().toISOString().split("T")[0],
     remark: ""
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

 <CreateInvoiceDialog
  open={showCreateDialog}
  onOpenChange={setShowCreateDialog}
 formData={formData}
  onFormChange={setFormData}
 contracts={contracts}
  onSubmit={handleCreate}
   />

   <IssueInvoiceDialog
  open={showIssueDialog}
  onOpenChange={setShowIssueDialog}
  issueData={issueData}
   onIssueDataChange={setIssueData}
  onSubmit={handleIssue}
   />

 <PaymentDialog
 open={showPaymentDialog}
  onOpenChange={setShowPaymentDialog}
   selectedInvoice={selectedInvoice}
   paymentData={paymentData}
 onPaymentDataChange={setPaymentData}
 onSubmit={handleReceivePayment}
  />

 <EditInvoiceDialog
 open={showEditDialog}
  onOpenChange={setShowEditDialog}
  formData={formData}
 onFormChange={setFormData}
 contracts={contracts}
  onSubmit={handleUpdate}
  />

 <DeleteConfirmDialog
  open={showDeleteDialog}
  onOpenChange={setShowDeleteDialog}
  selectedInvoice={selectedInvoice}
  onConfirm={handleDelete}
  />

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
