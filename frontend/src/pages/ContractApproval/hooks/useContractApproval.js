import { useState, useMemo, useCallback, useEffect } from "react";
import { contractApi } from "../../../services/api";

export function useContractApproval() {
  // ── List / tab state ──────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState("pending");
  const [searchTerm, setSearchTerm] = useState("");
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ── Detail dialog state ───────────────────────────────────────────────────
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [approvalComments, setApprovalComments] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);

  // ── Data fetching ─────────────────────────────────────────────────────────
  const fetchApprovals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pendingRes = await contractApi.list({ approval_status: "pending" });
      const pendingData =
        pendingRes.data?.items || pendingRes.data || [];
      setPendingApprovals(Array.isArray(pendingData) ? pendingData : []);

      const historyRes = await contractApi.list({ approval_status: "completed" });
      const historyData =
        historyRes.data?.items || historyRes.data || [];
      setApprovalHistory(Array.isArray(historyData) ? historyData : []);
    } catch (err) {
      console.error("Failed to load contract approvals:", err);
      setError("加载合同审批数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchApprovals();
  }, [fetchApprovals]);

  // ── Filtered list ─────────────────────────────────────────────────────────
  const filteredApprovals = useMemo(() => {
    const approvals =
      activeTab === "pending" ? pendingApprovals : approvalHistory;
    if (!searchTerm) return approvals;
    const searchLower = searchTerm.toLowerCase();
    return approvals.filter(
      (item) =>
        (item.title || "").toLowerCase().includes(searchLower) ||
        (item.customerName || "").toLowerCase().includes(searchLower) ||
        (item.submitter || "").toLowerCase().includes(searchLower)
    );
  }, [searchTerm, activeTab, pendingApprovals, approvalHistory]);

  // ── Dialog helpers ────────────────────────────────────────────────────────
  const handleViewDetail = useCallback((approval) => {
    setSelectedApproval(approval);
    setActionError(null);
    setApprovalComments("");
    setShowDetailDialog(true);
  }, []);

  const handleCloseDialog = useCallback(() => {
    setShowDetailDialog(false);
    setApprovalComments("");
    setActionError(null);
  }, []);

  // Moves the selected approval out of pending and into history
  const moveSelectedToHistory = useCallback(
    (status) => {
      if (!selectedApproval) return;
      const now = new Date();
      const historyItem = {
        ...selectedApproval,
        status,
        approveTime: now.toLocaleString("zh-CN"),
        comments: approvalComments || selectedApproval.comments,
        approver: selectedApproval.approver || "当前用户",
        amount:
          selectedApproval.amount ??
          selectedApproval.totalAmount ??
          selectedApproval.contract_amount ??
          selectedApproval.contractAmount ??
          0,
        customerName:
          selectedApproval.customerName ||
          selectedApproval.customer_name ||
          selectedApproval.customerShort ||
          "",
        title:
          selectedApproval.title ||
          selectedApproval.contract_code ||
          selectedApproval.contractCode ||
          "合同审批",
      };
      setPendingApprovals((prev) =>
        prev.filter((a) => a.id !== selectedApproval.id)
      );
      setApprovalHistory((prev) => [historyItem, ...prev]);
    },
    [selectedApproval, approvalComments]
  );

  // ── Approval actions ──────────────────────────────────────────────────────
  const handleApprove = useCallback(async () => {
    if (!selectedApproval?.id || actionLoading) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await contractApi.approvalAction(selectedApproval.id, {
        action: "APPROVE",
        comment: approvalComments || undefined,
      });
      moveSelectedToHistory("approved");
      handleCloseDialog();
    } catch (err) {
      console.error("Failed to approve contract:", err);
      setActionError("审批通过失败，请稍后重试");
    } finally {
      setActionLoading(false);
    }
  }, [selectedApproval, actionLoading, approvalComments, moveSelectedToHistory, handleCloseDialog]);

  const handleReject = useCallback(async () => {
    if (!selectedApproval?.id || actionLoading) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await contractApi.approvalAction(selectedApproval.id, {
        action: "REJECT",
        comment: approvalComments || "审批驳回",
      });
      moveSelectedToHistory("rejected");
      handleCloseDialog();
    } catch (err) {
      console.error("Failed to reject contract:", err);
      setActionError("审批驳回失败，请稍后重试");
    } finally {
      setActionLoading(false);
    }
  }, [selectedApproval, actionLoading, approvalComments, moveSelectedToHistory, handleCloseDialog]);

  return {
    // list state
    activeTab,
    setActiveTab,
    searchTerm,
    setSearchTerm,
    pendingApprovals,
    approvalHistory,
    filteredApprovals,
    loading,
    error,
    fetchApprovals,
    // dialog state
    selectedApproval,
    showDetailDialog,
    approvalComments,
    setApprovalComments,
    actionLoading,
    actionError,
    // handlers
    handleViewDetail,
    handleCloseDialog,
    handleApprove,
    handleReject,
  };
}
