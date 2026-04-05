import { useState, useMemo, useEffect, useCallback } from "react";
import { invoiceApi, purchaseApi } from "../../../services/api";
import { toast } from "../../../components/ui/toast";

/**
 * Page-level hook for PaymentApproval.
 * Loads pending invoices and purchase orders, normalises them into a
 * unified payment shape, and provides approve/reject handlers.
 *
 * The lower-level usePaymentApproval hook (hooks/usePaymentApproval.js)
 * targets the unified approval API and is kept separately for other
 * consumers that use that endpoint.
 */
export function usePaymentApprovalPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedPriority, setSelectedPriority] = useState("all");
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [approvalAction, setApprovalAction] = useState(null); // 'approve' | 'reject'
  const [approvalComment, setApprovalComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingPayments, setPendingPayments] = useState([]);

  // ─── Derived state ────────────────────────────────────────────────────────

  const filteredPayments = useMemo(() => {
    return (pendingPayments || []).filter((payment) => {
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
  }, [searchTerm, selectedType, selectedPriority, pendingPayments]);

  const stats = useMemo(() => {
    const isUrgent = (p) => p.priority === "high" || p.priority === "urgent";
    return {
      total: filteredPayments.length,
      totalAmount: filteredPayments.reduce((sum, p) => sum + p.amount, 0),
      urgent: filteredPayments.filter(isUrgent).length,
      urgentAmount: filteredPayments
        .filter(isUrgent)
        .reduce((sum, p) => sum + p.amount, 0),
    };
  }, [filteredPayments]);

  // ─── Data loading ─────────────────────────────────────────────────────────

  const loadPendingPayments = useCallback(async () => {
    try {
      setLoading(true);

      // Pending invoices
      const invoiceResponse = await invoiceApi
        .list({ status: "PENDING,IN_APPROVAL", page: 1, page_size: 100 })
        .catch(() => ({ data: { items: [] } }));

      const invoices =
        invoiceResponse.data?.items || invoiceResponse.data || [];

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
        priority: (inv.total_amount || inv.amount || 0) > 100000 ? "high" : "medium",
        daysPending: inv.created_at
          ? Math.floor((new Date() - new Date(inv.created_at)) / (1000 * 60 * 60 * 24))
          : 0,
        dueDate: inv.due_date || "",
        description: inv.remark || "",
        status: inv.status,
        raw: inv,
      }));

      // Pending purchase orders
      const poResponse = await purchaseApi.orders
        .list({ status: "SUBMITTED", page: 1, page_size: 100 })
        .catch(() => ({ data: { items: [] } }));

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
          (po.amount_with_tax || po.total_amount || 0) > 100000 ? "high" : "medium",
        daysPending: po.created_at
          ? Math.floor((new Date() - new Date(po.created_at)) / (1000 * 60 * 60 * 24))
          : 0,
        dueDate: po.required_date || "",
        description: po.order_title || "",
        status: po.status,
        raw: po,
      }));

      setPendingPayments([...invoicePayments, ...poPayments]);
    } catch (error) {
      console.error("Failed to load pending payments:", error);
      setPendingPayments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPendingPayments();
  }, [loadPendingPayments]);

  // ─── Action handlers ──────────────────────────────────────────────────────

  const handleApprove = useCallback((payment) => {
    setSelectedPayment(payment);
    setApprovalAction("approve");
    setShowApprovalDialog(true);
  }, []);

  const handleReject = useCallback((payment) => {
    setSelectedPayment(payment);
    setApprovalAction("reject");
    setShowApprovalDialog(true);
  }, []);

  const handleCloseApprovalDialog = useCallback(() => {
    setShowApprovalDialog(false);
  }, []);

  const handleConfirmApproval = useCallback(async () => {
    if (!selectedPayment) return;

    if (approvalAction === "reject" && !approvalComment.trim()) {
      toast.error("请输入拒绝原因");
      return;
    }

    try {
      setLoading(true);
      const isApprove = approvalAction === "approve";

      if (selectedPayment.type === "invoice" && selectedPayment.raw) {
        await invoiceApi.approve(selectedPayment.raw.id, {
          approved: isApprove,
          remark: approvalComment,
        });
        toast.success(isApprove ? "发票审批通过" : "发票已驳回");
      } else if (selectedPayment.type === "purchase" && selectedPayment.raw) {
        await purchaseApi.orders.approve(selectedPayment.raw.id, {
          approved: isApprove,
          approval_note: approvalComment,
        });
        toast.success(isApprove ? "采购订单审批通过" : "采购订单已驳回");
      } else {
        toast.info("该类型付款审批功能待完善");
      }

      setShowApprovalDialog(false);
      setSelectedPayment(null);
      setApprovalAction(null);
      setApprovalComment("");

      await loadPendingPayments();
    } catch (error) {
      console.error("Failed to approve/reject payment:", error);
      toast.error("审批失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  }, [selectedPayment, approvalAction, approvalComment, loadPendingPayments]);

  return {
    // Filter state
    searchTerm,
    setSearchTerm,
    selectedType,
    setSelectedType,
    selectedPriority,
    setSelectedPriority,
    // Derived
    filteredPayments,
    stats,
    // Loading
    loading,
    // Dialog state
    selectedPayment,
    setSelectedPayment,
    showApprovalDialog,
    approvalAction,
    approvalComment,
    setApprovalComment,
    // Handlers
    handleApprove,
    handleReject,
    handleCloseApprovalDialog,
    handleConfirmApproval,
  };
}
