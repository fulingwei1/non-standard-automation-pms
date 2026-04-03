/**
 * BOM Assembly Attributes Management Page - BOM装配属性维护页面
 * Features: 物料装配阶段配置、阻塞性设置、批量分配、模板套用
 */
import { Save, Wand2, FileDown } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";

import { useBomAssemblyAttrs } from "./useBomAssemblyAttrs";
import { FilterCard } from "./FilterCard";
import { StageStatsGrid } from "./StageStatsGrid";
import { AssemblyAttrsTable } from "./AssemblyAttrsTable";
import { AutoAssignDialog } from "./AutoAssignDialog";
import { TemplateDialog } from "./TemplateDialog";

export default function BomAssemblyAttrs() {
  const {
    loading,
    projects,
    boms,
    templates,
    selectedProject,
    setSelectedProject,
    selectedBom,
    setSelectedBom,
    filterStage,
    setFilterStage,
    filterBlocking,
    setFilterBlocking,
    searchText,
    setSearchText,
    assemblyAttrs,
    editedAttrs,
    hasChanges,
    autoAssignDialogOpen,
    setAutoAssignDialogOpen,
    templateDialogOpen,
    setTemplateDialogOpen,
    selectedTemplate,
    setSelectedTemplate,
    overwrite,
    setOverwrite,
    handleAttrChange,
    handleSave,
    handleAutoAssign,
    handleSmartRecommend,
    handleApplyTemplate,
  } = useBomAssemblyAttrs();

  // 过滤显示的数据
  const filteredAttrs = (assemblyAttrs || []).filter((attr) => {
    if (filterStage !== "all" && attr.assembly_stage !== filterStage) {
      return false;
    }
    if (filterBlocking === "blocking" && !attr.is_blocking) {
      return false;
    }
    if (filterBlocking === "postpone" && attr.is_blocking) {
      return false;
    }
    if (searchText) {
      const search = searchText.toLowerCase();
      if (
        !attr.material_code?.toLowerCase().includes(search) &&
        !attr.material_name?.toLowerCase().includes(search)
      ) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <PageHeader
          title="BOM装配属性配置"
          description="配置物料的装配阶段、阻塞性和重要程度，用于齐套分析"
        />

        <div className="flex items-center gap-2">
          {hasChanges && (
            <Badge
              variant="outline"
              className="bg-yellow-50 text-yellow-700 border-yellow-300"
            >
              有未保存的更改
            </Badge>
          )}
          <Button
            variant="outline"
            disabled={!selectedBom || loading}
            onClick={() => setAutoAssignDialogOpen(true)}
          >
            <Wand2 className="w-4 h-4 mr-2" />
            自动分配
          </Button>
          <Button
            variant="outline"
            disabled={!selectedBom || loading}
            onClick={handleSmartRecommend}
            className="bg-blue-50 hover:bg-blue-100 border-blue-300"
          >
            <Wand2 className="w-4 h-4 mr-2" />
            智能推荐
          </Button>
          <Button
            variant="outline"
            disabled={!selectedBom || loading}
            onClick={() => setTemplateDialogOpen(true)}
          >
            <FileDown className="w-4 h-4 mr-2" />
            套用模板
          </Button>
          <Button disabled={!hasChanges || loading} onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            保存配置
          </Button>
        </div>
      </div>

      {/* Selectors */}
      <FilterCard
        projects={projects}
        boms={boms}
        selectedProject={selectedProject}
        setSelectedProject={setSelectedProject}
        selectedBom={selectedBom}
        setSelectedBom={setSelectedBom}
        filterStage={filterStage}
        setFilterStage={setFilterStage}
        filterBlocking={filterBlocking}
        setFilterBlocking={setFilterBlocking}
        searchText={searchText}
        setSearchText={setSearchText}
      />

      {/* Stage Statistics */}
      {selectedBom && assemblyAttrs.length > 0 && (
        <StageStatsGrid
          assemblyAttrs={assemblyAttrs}
          filterStage={filterStage}
          setFilterStage={setFilterStage}
        />
      )}

      {/* Main Table */}
      <AssemblyAttrsTable
        selectedBom={selectedBom}
        loading={loading}
        assemblyAttrs={assemblyAttrs}
        filteredAttrs={filteredAttrs}
        editedAttrs={editedAttrs}
        searchText={searchText}
        handleAttrChange={handleAttrChange}
      />

      {/* Auto Assign Dialog */}
      <AutoAssignDialog
        open={autoAssignDialogOpen}
        onOpenChange={setAutoAssignDialogOpen}
        overwrite={overwrite}
        setOverwrite={setOverwrite}
        loading={loading}
        onAutoAssign={handleAutoAssign}
      />

      {/* Template Dialog */}
      <TemplateDialog
        open={templateDialogOpen}
        onOpenChange={setTemplateDialogOpen}
        templates={templates}
        selectedTemplate={selectedTemplate}
        setSelectedTemplate={setSelectedTemplate}
        overwrite={overwrite}
        setOverwrite={setOverwrite}
        loading={loading}
        onApplyTemplate={handleApplyTemplate}
      />
    </div>
  );
}
