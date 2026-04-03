/**
 * Issue Statistics Snapshot Page - 问题统计快照查看页面
 * Features: 快照列表、历史趋势对比、快照详情、数据导出
 */
import { PageHeader } from "../../components/layout";
import { useIssueStatisticsSnapshot } from "./hooks";
import { FilterBar } from "./FilterBar";
import { ComparisonCards } from "./ComparisonCards";
import { TrendCharts } from "./TrendCharts";
import { SnapshotTable } from "./SnapshotTable";
import { SnapshotDetailDialog } from "./SnapshotDetailDialog";

export default function IssueStatisticsSnapshot() {
  const {
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
    trendData,
    comparison,
    loadSnapshots,
    handleViewDetail,
  } = useIssueStatisticsSnapshot();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <PageHeader
        title="问题统计快照"
        description="查看历史问题统计数据，分析趋势变化"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 过滤器 */}
        <FilterBar
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
          onQuery={loadSnapshots}
          snapshots={snapshots}
        />

        {/* 趋势对比卡片 */}
        <ComparisonCards comparison={comparison} />

        {/* 趋势图表 */}
        <TrendCharts trendData={trendData} />

        {/* 快照列表 */}
        <SnapshotTable
          loading={loading}
          snapshots={snapshots}
          total={total}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onViewDetail={handleViewDetail}
        />
      </div>

      {/* 快照详情对话框 */}
      <SnapshotDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        snapshot={selectedSnapshot}
      />
    </div>
  );
}
