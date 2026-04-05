/**
 * Cost Template Management Page - 成本模板管理页面
 * Features: Template list, create, edit, delete, preview
 */

import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import DeleteConfirmDialog from "../../components/common/DeleteConfirmDialog";
import { Card, CardContent, Button } from "../../components/ui";
import { staggerContainer } from "../../lib/animations";

import { useCostTemplates } from "./useCostTemplates";
import TemplateFilters from "./TemplateFilters";
import TemplateCard from "./TemplateCard";
import TemplateFormDialog from "./TemplateFormDialog";
import TemplatePreviewDialog from "./TemplatePreviewDialog";

export default function CostTemplateManagement() {
  const {
    loading,
    filteredTemplates,
    searchTerm,
    setSearchTerm,
    typeFilter,
    setTypeFilter,
    equipmentFilter,
    setEquipmentFilter,
    equipmentTypes,
    showCreateDialog,
    showEditDialog,
    showPreviewDialog,
    setShowPreviewDialog,
    showDeleteDialog,
    setShowDeleteDialog,
    selectedTemplate,
    formData,
    setFormData,
    handleCreate,
    handleEdit,
    handlePreview,
    handleDelete,
    handleSave,
    handleConfirmDelete,
    closeFormDialog,
    addCategory,
    addItem,
    updateCategory,
    updateItem,
    removeCategory,
    removeItem,
  } = useCostTemplates();

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="成本模板管理"
        description="管理报价成本模板，快速生成报价成本"
        actions={
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            新建模板
          </Button>
        }
      />

      {/* Filters */}
      <TemplateFilters
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
        equipmentFilter={equipmentFilter}
        setEquipmentFilter={setEquipmentFilter}
        equipmentTypes={equipmentTypes}
      />

      {/* Template List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(filteredTemplates || []).map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onPreview={handlePreview}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>

      {filteredTemplates.length === 0 && !loading && (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            暂无模板，点击"新建模板"创建第一个模板
          </CardContent>
        </Card>
      )}

      {/* Create/Edit Dialog */}
      <TemplateFormDialog
        open={showCreateDialog || showEditDialog}
        onOpenChange={(open) => {
          if (!open) closeFormDialog();
        }}
        selectedTemplate={selectedTemplate}
        formData={formData}
        setFormData={setFormData}
        onSave={handleSave}
        onClose={closeFormDialog}
        addCategory={addCategory}
        addItem={addItem}
        updateCategory={updateCategory}
        updateItem={updateItem}
        removeCategory={removeCategory}
        removeItem={removeItem}
      />

      {/* Preview Dialog */}
      <TemplatePreviewDialog
        open={showPreviewDialog}
        onOpenChange={setShowPreviewDialog}
        template={selectedTemplate}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="确认删除"
        description={`确定要删除模板 "${selectedTemplate?.template_name}" 吗？此操作不可恢复。`}
        confirmText="删除"
        onConfirm={handleConfirmDelete}
      />
    </motion.div>
  );
}
