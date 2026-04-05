import { useState, useCallback, useEffect, useMemo } from "react";
import { adminApi } from "../../../services/api";

export function useAdministrativeApprovals() {
  const [loading, setLoading] = useState(true);
  const [approvals, setApprovals] = useState([]);
  const [approvedList, setApprovedList] = useState([]);
  const [rejectedList, setRejectedList] = useState([]);

  // Filter state
  const [searchText, setSearchText] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");

  const fetchData = useCallback(async () => {
    setLoading(true);

    try {
      const res = await adminApi.approvals.list({ status: "pending" });
      if (res.data?.items) setApprovals(res.data.items);
    } catch (_err) {
      console.error("Failed to fetch pending approvals");
    }

    try {
      const approvedRes = await adminApi.approvals.list({ status: "approved" });
      if (approvedRes.data?.items) setApprovedList(approvedRes.data.items);
    } catch (_err) {
      console.error("Failed to fetch approved list");
    }

    try {
      const rejectedRes = await adminApi.approvals.list({ status: "rejected" });
      if (rejectedRes.data?.items) setRejectedList(rejectedRes.data.items);
    } catch (_err) {
      console.error("Failed to fetch rejected list");
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Derived: filtered pending list
  const filteredApprovals = useMemo(() => {
    return (approvals || []).filter((approval) => {
      const searchLower = (searchText || "").toLowerCase();
      const matchSearch =
        (approval.title || "").toLowerCase().includes(searchLower) ||
        (approval.applicant || "").toLowerCase().includes(searchLower);
      const matchType = typeFilter === "all" || approval.type === typeFilter;
      const matchPriority =
        priorityFilter === "all" || approval.priority === priorityFilter;
      return matchSearch && matchType && matchPriority;
    });
  }, [approvals, searchText, typeFilter, priorityFilter]);

  // Derived: summary stats
  const stats = useMemo(() => {
    const total = approvals.length;
    const urgent = (approvals || []).filter((a) => a.priority === "high").length;
    const officeSupplies = (approvals || []).filter(
      (a) => a.type === "office_supplies"
    ).length;
    const vehicle = (approvals || []).filter((a) => a.type === "vehicle").length;
    const asset = (approvals || []).filter((a) => a.type === "asset").length;
    const meeting = (approvals || []).filter((a) => a.type === "meeting").length;
    const leave = (approvals || []).filter((a) => a.type === "leave").length;
    return { total, urgent, officeSupplies, vehicle, asset, meeting, leave };
  }, [approvals]);

  const handleApprove = useCallback(async (id) => {
    try {
      await adminApi.approvals.approve(id, { comment: "同意" });
      setApprovals((prev) => (prev || []).filter((a) => a.id !== id));
    } catch (_err) {
      console.error("Failed to approve request");
    }
  }, []);

  const handleReject = useCallback(async (id) => {
    try {
      await adminApi.approvals.reject(id, { reason: "不符合要求" });
      setApprovals((prev) => (prev || []).filter((a) => a.id !== id));
    } catch (_err) {
      console.error("Failed to reject request");
    }
  }, []);

  return {
    loading,
    approvals,
    approvedList,
    rejectedList,
    filteredApprovals,
    stats,
    searchText,
    setSearchText,
    typeFilter,
    setTypeFilter,
    priorityFilter,
    setPriorityFilter,
    handleApprove,
    handleReject,
    refetch: fetchData,
  };
}
