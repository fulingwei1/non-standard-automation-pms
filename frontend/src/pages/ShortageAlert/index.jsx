/**
 * Shortage Alert Page - 缺料预警页面
 * Features: 缺料预警列表、详情、确认、处理、统计分析
 */
import { PageHeader } from "../../components/layout";
import { useShortageAlert } from "./hooks/useShortageAlert";
import SummaryCards from "./SummaryCards";
import AlertFilters from "./AlertFilters";
import AlertTable from "./AlertTable";
import AlertDetailDialog from "./AlertDetailDialog";
import HandleAlertDialog from "./HandleAlertDialog";

export default function ShortageAlert() {
  const {
    loading,
    filteredAlerts,
    projects,
    summary,
    searchKeyword,
    setSearchKeyword,
    filterProject,
    setFilterProject,
    filterStatus,
    setFilterStatus,
    filterLevel,
    setFilterLevel,
    showDetailDialog,
    setShowDetailDialog,
    showHandleDialog,
    setShowHandleDialog,
    selectedAlert,
    handleData,
    setHandleData,
    handleViewDetail,
    handleAcknowledge,
    handleResolve,
    openHandleDialog,
    isUrgent,
  } = useShortageAlert();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="缺料预警"
          description="缺料预警管理，支持确认、处理、统计分析"
        />

        <SummaryCards summary={summary} />

        <AlertFilters
          searchKeyword={searchKeyword}
          setSearchKeyword={setSearchKeyword}
          filterProject={filterProject}
          setFilterProject={setFilterProject}
          filterStatus={filterStatus}
          setFilterStatus={setFilterStatus}
          filterLevel={filterLevel}
          setFilterLevel={setFilterLevel}
          projects={projects}
        />

        <AlertTable
          loading={loading}
          filteredAlerts={filteredAlerts}
          isUrgent={isUrgent}
          onViewDetail={handleViewDetail}
          onAcknowledge={handleAcknowledge}
          onOpenHandle={openHandleDialog}
        />

        <AlertDetailDialog
          open={showDetailDialog}
          onOpenChange={setShowDetailDialog}
          selectedAlert={selectedAlert}
          onAcknowledge={handleAcknowledge}
          onOpenHandle={openHandleDialog}
        />

        <HandleAlertDialog
          open={showHandleDialog}
          onOpenChange={setShowHandleDialog}
          selectedAlert={selectedAlert}
          handleData={handleData}
          setHandleData={setHandleData}
          onResolve={handleResolve}
        />
      </div>
    </div>
  );
}
