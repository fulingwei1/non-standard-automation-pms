import { useState, useEffect, useMemo } from "react";
import { issueApi } from "../../../services/api";

/**
 * 问题统计快照页面核心数据 Hook
 * 管理快照列表、过滤器、分页、详情加载及派生的趋势/对比数据
 */
export function useIssueStatisticsSnapshot() {
  const [loading, setLoading] = useState(true);
  const [snapshots, setSnapshots] = useState([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // Filters
  const [startDate, setStartDate] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
  );
  const [endDate, setEndDate] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadSnapshots();
     
  }, [startDate, endDate, page]);

  const loadSnapshots = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pageSize,
        start_date: startDate,
        end_date: endDate,
      };
      const res = await issueApi.getSnapshots(params);
      const data = res.data?.data || res.data || res;
      if (data && typeof data === "object" && "items" in data) {
        setSnapshots(data.items || []);
        setTotal(data.total || 0);
      } else if (Array.isArray(data)) {
        setSnapshots(data);
        setTotal(data?.length);
      } else {
        setSnapshots([]);
        setTotal(0);
      }
    } catch (error) {
      console.error("Failed to load snapshots:", error);
      setSnapshots([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (snapshotId) => {
    try {
      const res = await issueApi.getSnapshot(snapshotId);
      setSelectedSnapshot(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to load snapshot detail:", error);
    }
  };

  // 计算趋势数据
  const trendData = useMemo(() => {
    if (snapshots.length < 2) { return null; }

    const sorted = [...snapshots].sort(
      (a, b) => new Date(a.snapshot_date) - new Date(b.snapshot_date),
    );

    return {
      total: (sorted || []).map((s) => ({ date: s.snapshot_date, value: s.total_issues })),
      open: (sorted || []).map((s) => ({ date: s.snapshot_date, value: s.open_issues })),
      resolved: (sorted || []).map((s) => ({ date: s.snapshot_date, value: s.resolved_issues })),
      blocking: (sorted || []).map((s) => ({ date: s.snapshot_date, value: s.blocking_issues })),
    };
  }, [snapshots]);

  // 计算对比数据（最新 vs 最早）
  const comparison = useMemo(() => {
    if (snapshots.length < 2) { return null; }

    const sorted = [...snapshots].sort(
      (a, b) => new Date(a.snapshot_date) - new Date(b.snapshot_date),
    );
    const latest = sorted[sorted.length - 1];
    const earliest = sorted[0];

    return {
      total: { current: latest.total_issues, previous: earliest.total_issues },
      open: { current: latest.open_issues, previous: earliest.open_issues },
      resolved: { current: latest.resolved_issues, previous: earliest.resolved_issues },
      blocking: { current: latest.blocking_issues, previous: earliest.blocking_issues },
    };
  }, [snapshots]);

  return {
    // state
    loading,
    snapshots,
    selectedSnapshot,
    showDetailDialog,
    setShowDetailDialog,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    page,
    setPage,
    pageSize,
    total,
    // derived
    trendData,
    comparison,
    // actions
    loadSnapshots,
    handleViewDetail,
  };
}
