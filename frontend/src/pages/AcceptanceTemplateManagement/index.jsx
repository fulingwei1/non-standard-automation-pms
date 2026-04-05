/**
 * Acceptance Template Management Page - 验收模板管理页面
 * Features: 验收模板列表、创建、编辑、检查项管理
 */
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { useAcceptanceTemplateManagement } from "./hooks";
import TemplateFilters from "./TemplateFilters";
import TemplateTable from "./TemplateTable";
import CreateTemplateDialog from "./CreateTemplateDialog";
import TemplateDetailDialog from "./TemplateDetailDialog";
import TemplateItemsDialog from "./TemplateItemsDialog";

export default function AcceptanceTemplateManagement() {
  const {
    loading,
    filteredTemplates,
    selectedTemplate,
    templateItems,
    templateForm,
    newItem,
    searchKeyword,
    setSearchKeyword,
    filterType,
    setFilterType,
    showCreateDialog,
    setShowCreateDialog,
    showDetailDialog,
    setShowDetailDialog,
    showItemsDialog,
    setShowItemsDialog,
    setTemplateForm,
    setNewItem,
    handleCreate,
    handleViewDetail,
    handleViewItems,
    handleAddItem,
  } = useAcceptanceTemplateManagement();

  const handleManageItemsFromDetail = (templateId) => {
    setShowDetailDialog(false);
    handleViewItems(templateId);
  };

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="验收模板管理"
        description="验收模板列表、创建、编辑、检查项管理"
      />

      <TemplateFilters
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterType={filterType}
        setFilterType={setFilterType}
      />

      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建模板
        </Button>
      </div>

      <TemplateTable
        loading={loading}
        filteredTemplates={filteredTemplates}
        onViewDetail={handleViewDetail}
        onViewItems={handleViewItems}
      />

      <CreateTemplateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        templateForm={templateForm}
        setTemplateForm={setTemplateForm}
        onConfirm={handleCreate}
      />

      <TemplateDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedTemplate={selectedTemplate}
        templateItems={templateItems}
        onManageItems={handleManageItemsFromDetail}
      />

      <TemplateItemsDialog
        open={showItemsDialog}
        onOpenChange={setShowItemsDialog}
        selectedTemplate={selectedTemplate}
        templateItems={templateItems}
        newItem={newItem}
        setNewItem={setNewItem}
        onAddItem={handleAddItem}
      />
    </div>
  );
}
