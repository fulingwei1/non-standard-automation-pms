/**
 * Exception Management Page - 异常管理页面
 * Features: 异常事件列表、创建、处理、升级、统计分析
 *
 * This file is the orchestrator — it composes sub-components and wires them
 * together via the useExceptionManagement hook.
 */
import { useExceptionManagement } from "./hooks";

export default function ExceptionManagement() {
  const {
    // data
    loading,
    filteredExceptions,
    projects,
    // filters
    searchKeyword,
    setSearchKeyword,
    filterProject,
    setFilterProject,
    filterType,
    setFilterType,
    filterSeverity,
    setFilterSeverity,
    filterStatus,
    setFilterStatus,
    // dialogs
    showCreateDialog,
    setShowCreateDialog,
    showDetailDialog,
    setShowDetailDialog,
    showHandleDialog,
    setShowHandleDialog,
    selectedException,
    // form
    newException,
    setNewException,
    handleData,
    setHandleData,
    // actions
    handleCreateException,
    handleViewDetail,
    handleException,
    openHandleDialog,
  } = useExceptionManagement();

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="异常管理"
        description="异常事件管理，支持创建、处理、升级、统计分析"
      />

      {/* Filters */}
      <ExceptionFilterBar
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterProject={filterProject}
        setFilterProject={setFilterProject}
        filterType={filterType}
        setFilterType={setFilterType}
        filterSeverity={filterSeverity}
        setFilterSeverity={setFilterSeverity}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
        projects={projects}
      />

      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建异常
        </Button>
      </div>

      {/* Exception List */}
      <ExceptionTable
        loading={loading}
        filteredExceptions={filteredExceptions}
        onViewDetail={handleViewDetail}
        onOpenHandle={openHandleDialog}
      />

      {/* Create Exception Dialog */}
      <CreateExceptionDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        newException={newException}
        setNewException={setNewException}
        onSubmit={handleCreateException}
        projects={projects}
      />

      {/* Exception Detail Dialog */}
      <DetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedException={selectedException}
        onOpenHandle={openHandleDialog}
      />

      {/* Handle Exception Dialog */}
      <HandleDialog
        open={showHandleDialog}
        onOpenChange={setShowHandleDialog}
        selectedException={selectedException}
        handleData={handleData}
        setHandleData={setHandleData}
        onSubmit={handleException}
      />
    </div>
  );
}
