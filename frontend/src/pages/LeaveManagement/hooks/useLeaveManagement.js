import { useState, useEffect, useMemo } from 'react';
import { adminApi } from '../../../services/api';

export function useLeaveManagement() {
    const [searchText, setSearchText] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [typeFilter, setTypeFilter] = useState("all");
    const [loading, setLoading] = useState(false);
    const [leaveApplications, setLeaveApplications] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const res = await adminApi.leave.list();
                if (res.data?.items) {
                    setLeaveApplications(res.data.items);
                } else if (Array.isArray(res.data)) {
                    setLeaveApplications(res.data);
                }
            } catch (err) {
                console.log("Leave API unavailable", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredApplications = useMemo(() => {
        return leaveApplications.filter((app) => {
            const matchSearch =
                (app.employee || '').toLowerCase().includes(searchText.toLowerCase()) ||
                (app.department || '').toLowerCase().includes(searchText.toLowerCase());
            const matchStatus = statusFilter === "all" || app.status === statusFilter;
            const matchType = typeFilter === "all" || app.type === typeFilter;
            return matchSearch && matchStatus && matchType;
        });
    }, [leaveApplications, searchText, statusFilter, typeFilter]);

    const stats = useMemo(() => {
        const pending = leaveApplications.filter((a) => a.status === "pending").length;
        const approved = leaveApplications.filter((a) => a.status === "approved").length;
        const rejected = leaveApplications.filter((a) => a.status === "rejected").length;
        const totalDays = leaveApplications
            .filter((a) => a.status === "approved")
            .reduce((sum, a) => sum + Number(a.days || 0), 0);
        return { pending, approved, rejected, totalDays };
    }, [leaveApplications]);

    const leaveBalanceRows = useMemo(() => {
        const byEmployee = new Map();
        leaveApplications
            .filter((a) => a.status === "approved")
            .forEach((a) => {
                const key = a.employee || "未知员工";
                const existing = byEmployee.get(key) || {
                    employee: key,
                    department: a.department || "-",
                    usedDays: 0,
                    approvedCount: 0,
                };
                existing.usedDays += Number(a.days || 0);
                existing.approvedCount += 1;
                byEmployee.set(key, existing);
            });
        return Array.from(byEmployee.values()).sort((a, b) => b.usedDays - a.usedDays);
    }, [leaveApplications]);

    const leaveTypeChart = useMemo(() => {
        const byType = new Map();
        leaveApplications.forEach((a) => {
            const type = a.type || "未分类";
            byType.set(type, (byType.get(type) || 0) + 1);
        });
        return Array.from(byType.entries()).map(([label, value]) => ({ label, value }));
    }, [leaveApplications]);

    const leaveStatusChart = useMemo(() => {
        const counts = { pending: 0, approved: 0, rejected: 0 };
        leaveApplications.forEach((a) => {
            if (counts[a.status] !== undefined) counts[a.status] += 1;
        });
        return [
            { label: "待审批", value: counts.pending, color: "#f59e0b" },
            { label: "已批准", value: counts.approved, color: "#10b981" },
            { label: "已拒绝", value: counts.rejected, color: "#ef4444" },
        ];
    }, [leaveApplications]);

    const monthlyLeaveTrend = useMemo(() => {
        const byMonth = new Map();
        leaveApplications
            .filter((a) => a.status === "approved")
            .forEach((a) => {
                const date = a.startDate ? new Date(a.startDate) : null;
                const key = date && !Number.isNaN(date.getTime())
                    ? `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`
                    : "unknown";
                if (key !== "unknown") {
                    byMonth.set(key, (byMonth.get(key) || 0) + Number(a.days || 0));
                }
            });
        return Array.from(byMonth.entries())
            .sort(([a], [b]) => a.localeCompare(b))
            .slice(-12)
            .map(([month, value]) => ({ month, value }));
    }, [leaveApplications]);

    return {
        searchText, setSearchText,
        statusFilter, setStatusFilter,
        typeFilter, setTypeFilter,
        loading,
        leaveApplications,
        filteredApplications,
        stats,
        leaveBalanceRows,
        leaveTypeChart,
        leaveStatusChart,
        monthlyLeaveTrend
    };
}
