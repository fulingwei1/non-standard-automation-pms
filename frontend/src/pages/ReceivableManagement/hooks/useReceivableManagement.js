import { useState, useCallback, useEffect, useMemo } from "react";
import { receivableApi, paymentApi } from "../../../services/api";
import { paymentStatusConfig } from "../constants";

/**
 * 应收账款管理数据 Hook
 * Covers: list, aging, summary, payment recording, export, pagination, filters.
 */
export function useReceivableManagement() {
  // ── List state ──────────────────────────────────────────────────────────────
  const [receivables, setReceivables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  // ── Filters ─────────────────────────────────────────────────────────────────
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [overdueOnly, setOverdueOnly] = useState(false);

  // ── Aging & Summary ──────────────────────────────────────────────────────────
  const [agingData, setAgingData] = useState(null);
  const [summary, setSummary] = useState(null);

  // ── Payment dialog state ─────────────────────────────────────────────────────
  const [selectedReceivable, setSelectedReceivable] = useState(null);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [paymentData, setPaymentData] = useState({
    paid_amount: "",
    paid_date: new Date().toISOString().split("T")[0],
    payment_method: "",
    bank_account: "",
    remark: "",
  });

  // ── Data loaders ─────────────────────────────────────────────────────────────
  const loadReceivables = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        payment_status: statusFilter !== "all" ? statusFilter : undefined,
      };
      const response = await receivableApi.list(params);
      if (response.data && response.data.items) {
        setReceivables(response.data.items);
        setTotal(response.data.total || 0);
      }
    } catch (err) {
      console.error("加载应收账款列表失败:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter]);

  const loadAging = useCallback(async () => {
    try {
      const response = await receivableApi.getAging();
      if (response.data && response.data.data) {
        setAgingData(response.data.data);
      } else if (response.data) {
        setAgingData(response.data);
      }
    } catch (err) {
      console.error("加载账龄分析失败:", err);
    }
  }, []);

  const loadSummary = useCallback(async () => {
    try {
      const response = await receivableApi.getSummary();
      if (response.data && response.data.data) {
        setSummary(response.data.data);
      } else if (response.data) {
        setSummary(response.data);
      }
    } catch (err) {
      console.error("加载应收账款统计失败:", err);
    }
  }, []);

  useEffect(() => {
    loadReceivables();
  }, [loadReceivables]);

  useEffect(() => {
    loadAging();
    loadSummary();
  }, [loadAging, loadSummary]);

  // ── Payment handler ──────────────────────────────────────────────────────────
  const handleReceivePayment = useCallback(async () => {
    if (!selectedReceivable) return;
    try {
      await paymentApi.create({
        invoice_id: selectedReceivable.id,
        paid_amount: paymentData.paid_amount,
        paid_date: paymentData.paid_date,
        payment_method: paymentData.payment_method || undefined,
        bank_account: paymentData.bank_account || undefined,
        remark: paymentData.remark || undefined,
      });
      setShowPaymentDialog(false);
      setSelectedReceivable(null);
      setPaymentData({
        paid_amount: "",
        paid_date: new Date().toISOString().split("T")[0],
        payment_method: "",
        bank_account: "",
        remark: "",
      });
      loadReceivables();
      loadAging();
      loadSummary();
    } catch (err) {
      console.error("记录收款失败:", err);
      alert("记录收款失败: " + (err.response?.data?.detail || err.message));
    }
  }, [selectedReceivable, paymentData, loadReceivables, loadAging, loadSummary]);

  // ── Export handler ───────────────────────────────────────────────────────────
  const handleExport = useCallback(() => {
    try {
      const exportData = (receivables || []).map((r) => ({
        发票编码: r.invoice_code,
        客户名称: r.customer_name,
        合同编码: r.contract_code,
        发票金额: r.invoice_amount || r.total_amount || 0,
        已收金额: r.paid_amount || 0,
        待收金额:
          r.unpaid_amount || (r.invoice_amount - r.paid_amount) || 0,
        到期日期: r.due_date || "",
        逾期天数: r.overdue_days || 0,
        收款状态:
          paymentStatusConfig[r.payment_status]?.label || r.payment_status,
      }));

      const headers = Object.keys(exportData[0] || {});
      const csvContent = [
        headers.join(","),
        ...(exportData || []).map((row) =>
          headers.map((header) => `"${row[header] || ""}"`).join(",")
        ),
      ].join("\n");

      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], {
        type: "text/csv;charset=utf-8;",
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
    } catch (err) {
      console.error("导出失败:", err);
      alert("导出失败: " + err.message);
    }
  }, [receivables]);

  // ── Derived stats ────────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    if (summary) {
      return {
        total: summary.invoice_count || total,
        totalUnpaid: summary.unpaid_amount || 0,
        totalOverdue: summary.overdue_amount || 0,
        overdueCount: summary.overdue_count || 0,
      };
    }
    return {
      total,
      totalUnpaid: (receivables || []).reduce(
        (sum, r) =>
          sum +
          (parseFloat(
            r.unpaid_amount || r.invoice_amount - r.paid_amount
          ) || 0),
        0
      ),
      totalOverdue: (receivables || [])
        .filter((r) => r.overdue_days > 0)
        .reduce(
          (sum, r) =>
            sum +
            (parseFloat(
              r.unpaid_amount || r.invoice_amount - r.paid_amount
            ) || 0),
          0
        ),
      overdueCount: (receivables || []).filter((r) => r.overdue_days > 0)
        .length,
    };
  }, [receivables, total, summary]);

  // ── Currency formatter (shared utility) ─────────────────────────────────────
  const formatCurrency = useCallback((value) => {
    if (!value) return "0";
    const num = parseFloat(value);
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + "万";
    }
    return num.toLocaleString();
  }, []);

  // ── Pagination helpers ───────────────────────────────────────────────────────
  // Kept for backwards-compat with existing hook consumers
  const filters = { status: statusFilter, overdue: overdueOnly ? "true" : "" };
  const setFilters = ({ status, overdue } = {}) => {
    if (status !== undefined) setStatusFilter(status);
    if (overdue !== undefined) setOverdueOnly(overdue === "true");
  };
  const pagination = { page, pageSize, total };
  const setPagination = ({ page: p } = {}) => {
    if (p !== undefined) setPage(p);
  };

  return {
    // list
    receivables,
    loading,
    error,
    // pagination
    page,
    setPage,
    total,
    pageSize,
    pagination,
    setPagination,
    // filters
    searchTerm,
    setSearchTerm,
    statusFilter,
    setStatusFilter,
    overdueOnly,
    setOverdueOnly,
    filters,
    setFilters,
    // aging & summary
    agingData,
    summary,
    // stats
    stats,
    // dialog
    selectedReceivable,
    setSelectedReceivable,
    showPaymentDialog,
    setShowPaymentDialog,
    paymentData,
    setPaymentData,
    // actions
    loadReceivables,
    loadAging,
    loadSummary,
    handleReceivePayment,
    handleExport,
    formatCurrency,
  };
}
