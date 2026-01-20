import { motion } from "framer-motion";
import { Settings, Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { staggerContainer } from "../../lib/animations";
import { LoadingCard, ErrorMessage, EmptyState } from "../../components/common";
import { useAlertRules } from "./useAlertRules";
import { RuleFilters } from "./RuleFilters";
import { RuleCard } from "./RuleCard";
import { RuleFormDialog } from "./RuleFormDialog";

export default function AlertRuleConfig() {
  const {
    rules,
    loading,
    error,
    page,
    setPage,
    total,
    pageSize,
    searchQuery,
    setSearchQuery,
    selectedType,
    setSelectedType,
    selectedTarget,
    setSelectedTarget,
    showEnabled,
    setShowEnabled,
    showDialog,
    setShowDialog,
    editingRule,
    templates,
    selectedTemplate,
    formData,
    setFormData,
    loadRules,
    handleCreate,
    handleEdit,
    handleDelete,
    handleToggle,
    handleSave,
    handleTemplateSelect,
    handleChannelToggle,
  } = useAlertRules();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="预警规则配置"
        description="管理预警规则，配置触发条件和通知方式"
        actions={
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="w-4 h-4" />
            新建规则
          </Button>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        <RuleFilters
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedType={selectedType}
          setSelectedType={setSelectedType}
          selectedTarget={selectedTarget}
          setSelectedTarget={setSelectedTarget}
          showEnabled={showEnabled}
          setShowEnabled={setShowEnabled}
          onRefresh={loadRules}
        />

        {loading ? (
          <LoadingCard />
        ) : error ? (
          <ErrorMessage message={error} />
        ) : rules.length === 0 ? (
          <EmptyState
            icon={Settings}
            title="暂无预警规则"
            description="点击「新建规则」按钮创建第一个预警规则"
          />
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-4"
          >
            {rules.map((rule) => (
              <RuleCard
                key={rule.id}
                rule={rule}
                onToggle={handleToggle}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </motion.div>
        )}

        {total > pageSize && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              上一页
            </Button>
            <span className="text-sm text-slate-400">
              第 {page} 页，共 {Math.ceil(total / pageSize)} 页
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
              }
              disabled={page >= Math.ceil(total / pageSize)}
            >
              下一页
            </Button>
          </div>
        )}
      </div>

      <RuleFormDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        editingRule={editingRule}
        formData={formData}
        setFormData={setFormData}
        templates={templates}
        selectedTemplate={selectedTemplate}
        onTemplateSelect={handleTemplateSelect}
        onChannelToggle={handleChannelToggle}
        onSave={handleSave}
      />
    </div>
  );
}
