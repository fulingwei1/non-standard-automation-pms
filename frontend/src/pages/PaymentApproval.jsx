/**
 * Payment Approval Page - Payment approval workflow for finance manager
 * Features: Payment approval, Payment query, Approval history, Batch approval
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ClipboardCheck,
  Search,
  CheckCircle2,
  AlertTriangle,
  DollarSign,
  FileText,
  Eye,
  Check,
  X,
  Download,
  CreditCard,
  Receipt,
  ShoppingCart,
  Users } from
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter } from
"../components/ui";
import { cn, formatCurrency } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { invoiceApi, purchaseApi } from "../services/api";
import { toast } from "../components/ui/toast";

// Mock payment approvals (reuse from FinanceManagerDashboard)
// Mock data - 已移除，使用真实API
const typeConfig = {
  purchase: {
    label: "采购付款",
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: ShoppingCart
  },
  outsourcing: {
    label: "外协付款",
    color: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    icon: Receipt
  },
  expense: {
    label: "费用报销",
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    icon: FileText
  },
  salary: {
    label: "工资发放",
    color: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    icon: Users
  }
};

export default function PaymentApproval() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedPriority, setSelectedPriority] = useState("all");
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [approvalAction, setApprovalAction] = useState(null); // 'approve' or 'reject'
  const [approvalComment, setApprovalComment] = useState("");
  const [_loading, setLoading] = useState(false);
  const [pendingPayments, setPendingPayments] = useState([]);

  // Filter payments
  const filteredPayments = useMemo(() => {
    return pendingPayments.filter((payment) => {
      const searchLower = searchTerm?.toLowerCase() || "";
    const matchesSearch =
      !searchTerm ||
      (payment.orderNo || "").toLowerCase().includes(searchLower) ||
      (payment.projectName || "").toLowerCase().includes(searchLower) ||
      (payment.supplier || "").toLowerCase().includes(searchLower) ||
      (payment.submitter || "").toLowerCase().includes(searchLower);

      const matchesType =
      selectedType === "all" || payment.type === selectedType;
      const matchesPriority =
      selectedPriority === "all" || payment.priority === selectedPriority;

      return matchesSearch && matchesType && matchesPriority;
    });
  }, [searchTerm, selectedType, selectedPriority]);

  // Statistics
  const stats = useMemo(() => {
    return {
      total: filteredPayments.length,
      totalAmount: filteredPayments.reduce((sum, p) => sum + p.amount, 0),
      urgent: filteredPayments.filter(
        (p) => p.priority === "high" || p.priority === "urgent"
      ).length,
      urgentAmount: filteredPayments.
      filter((p) => p.priority === "high" || p.priority === "urgent").
      reduce((sum, p) => sum + p.amount, 0)
    };
  }, [filteredPayments]);

  const handleApprove = (payment) => {
    setSelectedPayment(payment);
    setApprovalAction("approve");
    setShowApprovalDialog(true);
  };

  const handleReject = (payment) => {
    setSelectedPayment(payment);
    setApprovalAction("reject");
    setShowApprovalDialog(true);
  };

  // Load pending approvals
  const loadPendingPayments = useCallback(async () => {
    try {
      setLoading(true);
      // Load pending invoices (status = PENDING or IN_APPROVAL)
      const invoiceResponse = await invoiceApi.
      list({
        status: "PENDING,IN_APPROVAL",
        page: 1,
        page_size: 100
      }).
      catch(() => ({ data: { items: [] } }));

      const invoices =
      invoiceResponse.data?.items || invoiceResponse.data || [];

      // Transform invoices to payment format
      const invoicePayments = invoices.map((inv) => ({
        id: inv.id,
        type: "invoice",
        typeLabel: "发票审批",
        orderNo: inv.invoice_code || `INV-${inv.id}`,
        projectName: inv.project_name || "",
        projectId: inv.project_id,
        amount: inv.total_amount || inv.amount || 0,
        submitter: inv.created_by_name || "系统",
        submitTime: inv.created_at || "",
        priority: inv.amount > 100000 ? "high" : "medium",
        daysPending: inv.created_at ?
        Math.floor(
          (new Date() - new Date(inv.created_at)) / (1000 * 60 * 60 * 24)
        ) :
        0,
        dueDate: inv.due_date || "",
        description: inv.remark || "",
        status: inv.status,
        raw: inv // Keep original data
      }));

      // Load pending purchase orders
      const poResponse = await purchaseApi.orders.
      list({
        status: "SUBMITTED",
        page: 1,
        page_size: 100
      }).
      catch(() => ({ data: { items: [] } }));

      const purchaseOrders = poResponse.data?.items || poResponse.data || [];
      const poPayments = purchaseOrders.map((po) => ({
        id: po.id,
        type: "purchase",
        typeLabel: "采购付款",
        orderNo: po.order_no || `PO-${po.id}`,
        supplier: po.supplier_name || "",
        projectName: po.project_name || "",
        projectId: po.project_id,
        amount: po.amount_with_tax || po.total_amount || 0,
        submitter: po.created_by_name || "系统",
        submitTime: po.created_at || "",
        priority:
        (po.amount_with_tax || po.total_amount || 0) > 100000 ?
        "high" :
        "medium",
        daysPending: po.created_at ?
        Math.floor(
          (new Date() - new Date(po.created_at)) / (1000 * 60 * 60 * 24)
        ) :
        0,
        dueDate: po.required_date || "",
        description: po.order_title || "",
        status: po.status,
        raw: po
      }));

      // Combine all payments
      const allPayments = [...invoicePayments, ...poPayments];

      // If no real data, use mock data as fallback
      if (allPayments.length === 0) {
        setPendingPayments([]);
      } else {
        setPendingPayments(allPayments);
      }
    } catch (error) {
      console.error("Failed to load pending payments:", error);
      // Use mock data as fallback
      setPendingPayments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPendingPayments();
  }, [loadPendingPayments]);

  const handleConfirmApproval = async () => {
    if (!selectedPayment) {return;}

    // Validate rejection reason
    if (approvalAction === "reject" && !approvalComment.trim()) {
      toast.error("请输入拒绝原因");
      return;
    }

    try {
      setLoading(true);
      const isApprove = approvalAction === "approve";

      // Call appropriate API based on payment type
      if (selectedPayment.type === "invoice" && selectedPayment.raw) {
        // For invoices, use invoice approval API
        await invoiceApi.approve(selectedPayment.raw.id, {
          approved: isApprove,
          remark: approvalComment
        });
        toast.success(isApprove ? "发票审批通过" : "发票已驳回");
      } else if (selectedPayment.type === "purchase" && selectedPayment.raw) {
        // For purchase orders, use purchase order approval API
        await purchaseApi.orders.approve(selectedPayment.raw.id, {
          approved: isApprove,
          approval_note: approvalComment
        });
        toast.success(isApprove ? "采购订单审批通过" : "采购订单已驳回");
      } else {
        // For other types, show message
        toast.info("该类型付款审批功能待完善");
      }

      setShowApprovalDialog(false);
      setSelectedPayment(null);
      setApprovalAction(null);
      setApprovalComment("");

      // Reload pending payments
      await loadPendingPayments();
    } catch (error) {
      console.error("Failed to approve/reject payment:", error);
      toast.error(
        "审批失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="付款审批"
        description="审批付款申请、查询审批历史"
        icon={ClipboardCheck}
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              批量审批
            </Button>
        </motion.div>
        } />


      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">待审批</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
                <p className="text-xs text-slate-500 mt-1">笔</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <ClipboardCheck className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">待审批金额</p>
                <p className="text-2xl font-bold text-amber-400">
                  {formatCurrency(stats.totalAmount)}
                </p>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">紧急事项</p>
                <p className="text-2xl font-bold text-red-400">
                  {stats.urgent}
                </p>
                <p className="text-xs text-slate-500 mt-1">笔</p>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">紧急金额</p>
                <p className="text-2xl font-bold text-red-400">
                  {formatCurrency(stats.urgentAmount)}
                </p>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <CreditCard className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="搜索单号、项目、供应商、申请人..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10" />

              </div>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">

                <option value="all">全部类型</option>
                {Object.entries(typeConfig).map(([key, val]) =>
                <option key={key} value={key}>
                    {val.label}
                </option>
                )}
              </select>
              <select
                value={selectedPriority}
                onChange={(e) => setSelectedPriority(e.target.value)}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">

                <option value="all">全部优先级</option>
                <option value="urgent">紧急</option>
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Payment List */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <ClipboardCheck className="h-5 w-5 text-amber-400" />
                待审批付款
              </CardTitle>
              <Badge
                variant="outline"
                className="bg-amber-500/20 text-amber-400 border-amber-500/30">

                {filteredPayments.length}笔
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredPayments.map((payment) => {
                const typeConf = typeConfig[payment.type];
                const TypeIcon = typeConf?.icon || FileText;
                return (
                  <div
                    key={payment.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">

                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge
                            variant="outline"
                            className={cn("text-xs", typeConf?.color)}>

                            <TypeIcon className="w-3 h-3 mr-1" />
                            {payment.typeLabel}
                          </Badge>
                          {payment.priority === "high" ||
                          payment.priority === "urgent" ?
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              {payment.priority === "urgent" ?
                            "紧急" :
                            "高优先级"}
                          </Badge> :
                          null}
                          <span className="text-sm text-slate-400">
                            {payment.daysPending > 0 ?
                            `待审批${payment.daysPending}天` :
                            "今日提交"}
                          </span>
                        </div>
                        <div className="font-medium text-white text-sm mb-1">
                          {payment.orderNo}
                        </div>
                        <div className="text-xs text-slate-400 space-y-1">
                          {payment.projectName &&
                          <div>项目: {payment.projectName}</div>
                          }
                          {payment.supplier &&
                          <div>供应商: {payment.supplier}</div>
                          }
                          {payment.department &&
                          <div>部门: {payment.department}</div>
                          }
                          <div>
                            申请人: {payment.submitter} ·{" "}
                            {payment.submitTime.split(" ")[1]}
                          </div>
                          {payment.description &&
                          <div className="text-slate-500 mt-1">
                              {payment.description}
                          </div>
                          }
                        </div>
                        {payment.attachments &&
                        payment.attachments.length > 0 &&
                        <div className="flex items-center gap-2 mt-2">
                              <FileText className="w-3 h-3 text-slate-500" />
                              <span className="text-xs text-slate-500">
                                {payment.attachments.length}个附件
                              </span>
                        </div>
                        }
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-lg font-bold text-amber-400 mb-2">
                          {formatCurrency(payment.amount)}
                        </div>
                        {payment.dueDate &&
                        <div className="text-xs text-slate-400 mb-3">
                            到期: {payment.dueDate}
                        </div>
                        }
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs"
                            onClick={() => setSelectedPayment(payment)}>

                            <Eye className="w-3 h-3 mr-1" />
                            查看
                          </Button>
                          <Button
                            size="sm"
                            className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30"
                            onClick={() => handleApprove(payment)}>

                            <Check className="w-3 h-3 mr-1" />
                            通过
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs text-red-400 border-red-500/30 hover:bg-red-500/20"
                            onClick={() => handleReject(payment)}>

                            <X className="w-3 h-3 mr-1" />
                            拒绝
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>);

              })}
              {filteredPayments.length === 0 &&
              <div className="text-center py-12 text-slate-500">
                  暂无待审批付款
              </div>
              }
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Approval Dialog */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {approvalAction === "approve" ? "审批通过" : "审批拒绝"}
            </DialogTitle>
            <DialogDescription>
              {selectedPayment &&
              <div className="mt-2">
                  <p className="text-sm text-slate-400">
                    单号: {selectedPayment.orderNo}
                  </p>
                  <p className="text-sm text-slate-400">
                    金额: {formatCurrency(selectedPayment.amount)}
                  </p>
              </div>
              }
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-400">
                {approvalAction === "approve" ? "审批意见" : "拒绝原因"}
                {approvalAction === "reject" &&
                <span className="text-red-400"> *</span>
                }
              </label>
              <textarea
                value={approvalComment}
                onChange={(e) => setApprovalComment(e.target.value)}
                placeholder={
                approvalAction === "approve" ?
                "请输入审批意见（可选）" :
                "请输入拒绝原因（必填）"
                }
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-24"
                required={approvalAction === "reject"} />

            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApprovalDialog(false)}>

              取消
            </Button>
            <Button
              className={
              approvalAction === "approve" ?
              "bg-emerald-500 hover:bg-emerald-600" :
              "bg-red-500 hover:bg-red-600"
              }
              onClick={handleConfirmApproval}>

              {approvalAction === "approve" ? "确认通过" : "确认拒绝"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payment Detail Dialog */}
      <Dialog
        open={!!selectedPayment && !showApprovalDialog}
        onOpenChange={() => setSelectedPayment(null)}>

        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>付款详情</DialogTitle>
          </DialogHeader>
          {selectedPayment &&
          <div className="py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">单号</label>
                  <p className="text-white font-medium">
                    {selectedPayment.orderNo}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">类型</label>
                  <p className="text-white font-medium">
                    {selectedPayment.typeLabel}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">金额</label>
                  <p className="text-amber-400 font-bold text-lg">
                    {formatCurrency(selectedPayment.amount)}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">申请人</label>
                  <p className="text-white">{selectedPayment.submitter}</p>
                </div>
                {selectedPayment.projectName &&
              <div>
                    <label className="text-sm text-slate-400">项目</label>
                    <p className="text-white">{selectedPayment.projectName}</p>
              </div>
              }
                {selectedPayment.supplier &&
              <div>
                    <label className="text-sm text-slate-400">供应商</label>
                    <p className="text-white">{selectedPayment.supplier}</p>
              </div>
              }
                {selectedPayment.department &&
              <div>
                    <label className="text-sm text-slate-400">部门</label>
                    <p className="text-white">{selectedPayment.department}</p>
              </div>
              }
                <div>
                  <label className="text-sm text-slate-400">提交时间</label>
                  <p className="text-white">{selectedPayment.submitTime}</p>
                </div>
              </div>
              {selectedPayment.description &&
            <div>
                  <label className="text-sm text-slate-400">描述</label>
                  <p className="text-white">{selectedPayment.description}</p>
            </div>
            }
              {selectedPayment.attachments &&
            selectedPayment.attachments.length > 0 &&
            <div>
                    <label className="text-sm text-slate-400">附件</label>
                    <div className="space-y-2 mt-2">
                      {selectedPayment.attachments.map((file, index) =>
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 bg-slate-800/40 rounded">

                          <FileText className="w-4 h-4 text-slate-400" />
                          <span className="text-sm text-white">{file}</span>
                          <Button variant="ghost" size="sm" className="ml-auto">
                            下载
                          </Button>
                </div>
                )}
                    </div>
            </div>
            }
          </div>
          }
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedPayment(null)}>
              关闭
            </Button>
            <Button
              className="bg-emerald-500 hover:bg-emerald-600"
              onClick={() => handleApprove(selectedPayment)}>

              审批通过
            </Button>
            <Button
              variant="outline"
              className="text-red-400 border-red-500/30 hover:bg-red-500/20"
              onClick={() => handleReject(selectedPayment)}>

              拒绝
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}
