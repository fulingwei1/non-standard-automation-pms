/**
 * Production Exception List Page - 生产异常管理页面
 * Features: 生产异常列表、上报、处理、关闭
 *
 * This file is the orchestrator. State and API logic live in
 * hooks/useProductionExceptionList.js; UI is split into:
 *   - ExceptionFilters
 *   - ExceptionTable
 *   - CreateExceptionDialog
 *   - ExceptionDetailDialog
 *   - HandleExceptionDialog
 */
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { useProductionExceptionList } from "./hooks";
import { ExceptionFilters } from "./ExceptionFilters";
import { ExceptionTable } from "./ExceptionTable";
import { CreateExceptionDialog } from "./CreateExceptionDialog";
import { ExceptionDetailDialog } from "./ExceptionDetailDialog";
import { HandleExceptionDialog } from "./HandleExceptionDialog";

export default function ProductionExceptionList({ embedded = false }) {
  const {
    // Data
    loading,
    projects,
    filteredExceptions,
    // Filters
    searchKeyword, setSearchKeyword,
    filterProject, setFilterProject,
    filterType, setFilterType,
    filterLevel, setFilterLevel,
    filterStatus, setFilterStatus,
    // Dialogs
    showCreateDialog, setShowCreateDialog,
    showDetailDialog, setShowDetailDialog,
    showHandleDialog, setShowHandleDialog,
    // Selection & forms
    selectedException, setSelectedException,
    newException, setNewException,
    handleData, setHandleData,
    // Actions
    handleCreateException,
    handleViewDetail,
    handleException,
    handleClose,
  } = useProductionExceptionList();

  /** Open the handle dialog from either the table row or the detail dialog. */
  const openHandleDialog = (exc) => {
    setSelectedException(exc);
    setShowHandleDialog(true);
  };

  return (
    <div className="space-y-6 p-6">
      {!embedded && (
        <PageHeader
          title="生产异常管理"
          description="生产异常列表、上报、处理、关闭"
        />
      )}

      <ExceptionFilters
        projects={projects}
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterProject={filterProject}
        setFilterProject={setFilterProject}
        filterType={filterType}
        setFilterType={setFilterType}
        filterLevel={filterLevel}
        setFilterLevel={setFilterLevel}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
      />

      {/* Action bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          上报异常
        </Button>
      </div>

      <ExceptionTable
        loading={loading}
        filteredExceptions={filteredExceptions}
        onViewDetail={handleViewDetail}
        onOpenHandleDialog={openHandleDialog}
        onClose={handleClose}
      />

      <CreateExceptionDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        projects={projects}
        newException={newException}
        setNewException={setNewException}
        onSubmit={handleCreateException}
      />

      <ExceptionDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedException={selectedException}
        onOpenHandleDialog={openHandleDialog}
        onClose={handleClose}
      />

      <HandleExceptionDialog
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
