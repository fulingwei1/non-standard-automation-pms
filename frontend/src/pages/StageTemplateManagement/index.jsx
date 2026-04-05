import { Plus, Upload, Layers } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import useStageTemplates from "./useStageTemplates";
import StatsCards from "./StatsCards";
import SearchFilterBar from "./SearchFilterBar";
import TemplateTable from "./TemplateTable";
import {
  CreateDialog,
  EditDialog,
  CopyDialog,
  TemplateDeleteDialog,
} from "./TemplateDialogs";

export default function StageTemplateManagement() {
  const {
    loading,
    showCreateDialog,
    setShowCreateDialog,
    showEditDialog,
    setShowEditDialog,
    showCopyDialog,
    setShowCopyDialog,
    showDeleteDialog,
    setShowDeleteDialog,
    selectedTemplate,
    searchKeyword,
    setSearchKeyword,
    filterType,
    setFilterType,
    filterActive,
    setFilterActive,
    formData,
    filteredTemplates,
    stats,
    handleCreateClick,
    handleEditClick,
    handleCopyClick,
    handleDeleteClick,
    handleViewClick,
    handleFormChange,
    handleCreate,
    handleUpdate,
    handleCopy,
    handleDelete,
    handleToggleActive,
  } = useStageTemplates();

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="阶段模板管理"
        subtitle="配置项目的阶段流程模板，定义阶段和节点的工作流程"
        icon={Layers}
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Upload className="h-4 w-4 mr-2" />
              导入模板
            </Button>
            <Button onClick={handleCreateClick}>
              <Plus className="h-4 w-4 mr-2" />
              新建模板
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        <StatsCards stats={stats} />

        <SearchFilterBar
          searchKeyword={searchKeyword}
          setSearchKeyword={setSearchKeyword}
          filterType={filterType}
          setFilterType={setFilterType}
          filterActive={filterActive}
          setFilterActive={setFilterActive}
        />

        <TemplateTable
          loading={loading}
          filteredTemplates={filteredTemplates}
          onView={handleViewClick}
          onEdit={handleEditClick}
          onCopy={handleCopyClick}
          onDelete={handleDeleteClick}
          onToggleActive={handleToggleActive}
        />
      </div>

      <CreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        formData={formData}
        onFormChange={handleFormChange}
        onCreate={handleCreate}
      />

      <EditDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        formData={formData}
        onFormChange={handleFormChange}
        onUpdate={handleUpdate}
      />

      <CopyDialog
        open={showCopyDialog}
        onOpenChange={setShowCopyDialog}
        formData={formData}
        onFormChange={handleFormChange}
        onCopy={handleCopy}
        selectedTemplate={selectedTemplate}
      />

      <TemplateDeleteDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        selectedTemplate={selectedTemplate}
        onConfirm={handleDelete}
      />
    </div>
  );
}
