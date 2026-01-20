import { useState, useEffect, useMemo, useCallback } from "react";
import { paymentApi, receivableApi } from "../../../services/api";

export function usePaymentManagement() {
    const [viewMode, setViewMode] = useState("list");
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

    const [reminders, setReminders] = useState([]);
    const [statistics, setStatistics] = useState(null);
    const [showReminders, setShowReminders] = useState(false);
    const [agingData, setAgingData] = useState({
        current: { count: 0, amount: 0 },
        days_1_30: { count: 0, amount: 0 },
        days_31_60: { count: 0, amount: 0 },
        days_61_90: { count: 0, amount: 0 },
        days_over_90: { count: 0, amount: 0 }
    });

    const loadPayments = useCallback(async () => {
        setLoading(true);
        try {
            const params = {
                page,
                page_size: pageSize,
                payment_status: selectedStatus !== "all" ? selectedStatus.toUpperCase() : undefined
            };

            if (searchTerm) {
                params.keyword = searchTerm;
            }

            const response = await paymentApi.list(params);
            const data = response.data || {};

            const transformedPayments = (data.items || []).map((item) => {
                const statusMap = { PAID: "paid", PENDING: "pending", PARTIAL: "pending", OVERDUE: "overdue" };
                return {
                    id: item.id || item.invoice_id,
                    type: "progress",
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
    }, [page, selectedStatus, searchTerm, pageSize]);

    const loadAgingData = useCallback(async () => {
        try {
            const response = await receivableApi.getAging({});
            setAgingData(response.data || {
                current: { count: 0, amount: 0 },
                days_1_30: { count: 0, amount: 0 },
                days_31_60: { count: 0, amount: 0 },
                days_61_90: { count: 0, amount: 0 },
                days_over_90: { count: 0, amount: 0 }
            });
        } catch (error) {
            console.error("加载账龄数据失败:", error);
        }
    }, []);

    const loadReminders = useCallback(async () => {
        try {
            const response = await paymentApi.getReminders({ page: 1, page_size: 50 });
            setReminders(response.data?.items || []);
        } catch (error) {
            console.error("加载回款提醒失败:", error);
            setReminders([]);
        }
    }, []);

    const loadStatistics = useCallback(async () => {
        try {
            const response = await paymentApi.getStatistics({});
            setStatistics(response.data || { total_receivables: 0, overdue_amount: 0, collection_rate: 0, dso: 0 });
        } catch (error) {
            console.error("加载统计数据失败:", error);
            setStatistics({ total_receivables: 0, overdue_amount: 0, collection_rate: 0, dso: 0 });
        }
    }, []);

    useEffect(() => {
        loadPayments();
        loadAgingData();
        loadReminders();
        loadStatistics();
    }, [page, selectedStatus]);

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

    const refresh = useCallback(() => {
        loadPayments();
        loadStatistics();
        loadReminders();
    }, [loadPayments, loadStatistics, loadReminders]);

    return {
        viewMode, setViewMode,
        searchTerm, setSearchTerm,
        selectedType, setSelectedType,
        selectedStatus, setSelectedStatus,
        selectedPayment, setSelectedPayment,
        showInvoiceDialog, setShowInvoiceDialog,
        showCollectionDialog, setShowCollectionDialog,
        showDetailDialog, setShowDetailDialog,
        showReminders, setShowReminders,
        payments, filteredPayments,
        loading, page, setPage, total, pageSize,
        reminders, statistics, agingData,
        refresh
    };
}
