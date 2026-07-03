/**
 * Alert Center Management (重构版)
 * 预警中心 - 统一预警管理平台
 *
 * 功能：
 * 1. 预警创建、编辑、查看
 * 2. 预警级别和状态管理
 * 3. 预警规则配置和触发条件
 * 4. 多渠道通知设置
 * 5. SLA监控和分析
 * 6. 预警批量处理和导出
 */

import { Settings } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { LoadingCard, ErrorMessage } from "../../components/common";
import { AlertCenterOverview } from "../../components/alert-center";

import useAlertData from "./useAlertData";
import AlertFilterBar from "./AlertFilterBar";
import AlertList from "./AlertList";
import ResolveDialog from "./ResolveDialog";
import DetailDialog from "./DetailDialog";

export default function AlertCenter() {
  const {
    alerts,
    stats,
    loading,
    error,
    page,
    total,
    pageSize,
    searchQuery,
    selectedLevel,
    selectedStatus,
    selectedProject,
    dateRange,
    showDetail,
    selectedAlert,
    showResolveDialog,
    resolveResult,
    selectedAlerts,
    sortBy,
    projects,
    filteredAlerts,
    navigate,

    setPage,
    setSearchQuery,
    setSelectedLevel,
    setSelectedStatus,
    setSelectedProject,
    setDateRange,
    setShowDetail,
    setSelectedAlert,
    setShowResolveDialog,
    setResolveResult,
    setSelectedAlerts,
    setSortBy,

    loadAlerts,
    handleBatchAcknowledge,
    handleBatchResolve,
    handleExportExcel,
    handleExportPdf,
    handleViewDetail,
    handleAcknowledge,
    handleResolve,
    handleSelectOne,
    handleQuickAction
  } = useAlertData();

  if (loading && alerts?.length === 0) {
    return (
      <LoadingCard message="加载预警数据中..." />);

  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={loadAlerts} />);

  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="container mx-auto px-4 pt-6">
        <PageHeader
          title="预警中心"
          subtitle="统一预警管理平台 - 实时监控、智能分析、快速响应"
          breadcrumbs={[
        { label: "系统管理", href: "/system" },
        { label: "预警中心" }]
        }
          actions={[
        {
          label: "新建规则",
          icon: Settings,
          onClick: () => navigate('/alert-rules'),
          variant: "default"
        }]
        } />
      </div>

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 预警概览 */}
        <AlertCenterOverview
          alerts={alerts}
          stats={stats}
          onQuickAction={handleQuickAction} />

        {/* 筛选和搜索 */}
        <AlertFilterBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedLevel={selectedLevel}
          setSelectedLevel={setSelectedLevel}
          selectedStatus={selectedStatus}
          setSelectedStatus={setSelectedStatus}
          selectedProject={selectedProject}
          setSelectedProject={setSelectedProject}
          dateRange={dateRange}
          setDateRange={setDateRange}
          sortBy={sortBy}
          setSortBy={setSortBy}
          projects={projects} />

        {/* 预警列表 */}
        <AlertList
          filteredAlerts={filteredAlerts}
          selectedAlerts={selectedAlerts}
          setSelectedAlerts={setSelectedAlerts}
          searchQuery={searchQuery}
          selectedLevel={selectedLevel}
          selectedStatus={selectedStatus}
          page={page}
          setPage={setPage}
          total={total}
          pageSize={pageSize}
          navigate={navigate}
          handleBatchAcknowledge={handleBatchAcknowledge}
          handleBatchResolve={handleBatchResolve}
          handleExportExcel={handleExportExcel}
          handleExportPdf={handleExportPdf}
          handleAcknowledge={handleAcknowledge}
          handleViewDetail={handleViewDetail}
          handleSelectOne={handleSelectOne}
          setSelectedAlert={setSelectedAlert}
          setShowResolveDialog={setShowResolveDialog} />

        {/* 解决预警对话框 */}
        <ResolveDialog
          open={showResolveDialog}
          onOpenChange={setShowResolveDialog}
          selectedAlert={selectedAlert}
          resolveResult={resolveResult}
          setResolveResult={setResolveResult}
          onResolve={handleResolve} />

        {/* 预警详情对话框 */}
        <DetailDialog
          open={showDetail}
          onOpenChange={setShowDetail}
          selectedAlert={selectedAlert} />
      </div>
    </div>);

}
