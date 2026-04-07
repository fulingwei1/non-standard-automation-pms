import { useParams, useNavigate } from "react-router-dom";
import { Settings } from "lucide-react";
import { fadeIn } from "../../lib/animations";
import { useStageTemplate } from "./useStageTemplate";

export default function StageTemplateEditor() {
  const { templateId } = useParams();
  const navigate = useNavigate();

  const {
    template,
    stages,
    loading,
    expandedStages,
    toggleStageExpanded,

    showStageDialog,
    setShowStageDialog,
    stageDialogMode,
    stageFormData,
    setStageFormData,
    handleAddStage,
    handleEditStage,
    handleDeleteStage,
    handleSaveStage,

    showNodeDialog,
    setShowNodeDialog,
    nodeDialogMode,
    nodeFormData,
    setNodeFormData,
    selectedStageForNode,
    handleAddNode,
    handleEditNode,
    handleDeleteNode,
    handleSaveNode,
  } = useStageTemplate(templateId);

  if (loading && !template) {
    return (
      <div className="min-h-screen bg-surface-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-violet-500" />
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title={
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => navigate("/system/stage-templates")}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <span>{template?.template_name}</span>
                <Badge variant="outline" className="text-xs">
                  {template?.template_code}
                </Badge>
              </div>
              <p className="text-sm text-slate-400 font-normal mt-0.5">
                {template?.description}
              </p>
            </div>
          </div>
        }
        subtitle="配置项目的阶段流程和节点定义"
        icon={Settings}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate("/system/stage-templates")}>
              取消
            </Button>
            <Button onClick={() => navigate("/system/stage-templates")}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-4">
        {/* 阶段列表 */}
        <AnimatePresence>
          {(stages || []).map((stage, stageIndex) => (
            <motion.div
              key={stage.id}
              variants={fadeIn}
              initial="hidden"
              animate="show"
              exit="hidden"
              transition={{ delay: stageIndex * 0.05 }}
            >
              <StageCard
                stage={stage}
                stageIndex={stageIndex}
                isExpanded={expandedStages.has(stage.id)}
                onToggleExpanded={toggleStageExpanded}
                onAddNode={handleAddNode}
                onEditStage={handleEditStage}
                onDeleteStage={handleDeleteStage}
                onEditNode={handleEditNode}
                onDeleteNode={handleDeleteNode}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {/* 添加阶段按钮 */}
        <motion.div variants={fadeIn} initial="hidden" animate="show">
          <Button
            variant="outline"
            className="w-full border-dashed border-white/20 hover:border-violet-500/50 hover:bg-violet-500/5"
            onClick={handleAddStage}
          >
            <Plus className="h-4 w-4 mr-2" />
            添加阶段
          </Button>
        </motion.div>

        {stages.length === 0 && !loading && (
          <Card className="bg-surface-100 border-white/5">
            <CardContent className="p-12 text-center">
              <Settings className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">暂无阶段定义</p>
              <p className="text-sm text-slate-500 mt-2">点击上方按钮添加第一个阶段</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 阶段对话框 */}
      <StageDialog
        open={showStageDialog}
        onOpenChange={setShowStageDialog}
        mode={stageDialogMode}
        formData={stageFormData}
        setFormData={setStageFormData}
        onSave={handleSaveStage}
      />

      {/* 节点对话框 */}
      <NodeDialog
        open={showNodeDialog}
        onOpenChange={setShowNodeDialog}
        mode={nodeDialogMode}
        formData={nodeFormData}
        setFormData={setNodeFormData}
        selectedStageForNode={selectedStageForNode}
        onSave={handleSaveNode}
      />
    </div>
  );
}
