import { useState, useEffect, useCallback } from "react";
import { stageTemplateApi } from "../../services/api";
import { confirmAction } from "@/lib/confirmAction";
import { INITIAL_STAGE_FORM_DATA, INITIAL_NODE_FORM_DATA } from "./constants";

export function useStageTemplate(templateId) {
  const [template, setTemplate] = useState(null);
  const [stages, setStages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedStages, setExpandedStages] = useState(new Set());

  // Stage Dialog states
  const [showStageDialog, setShowStageDialog] = useState(false);
  const [stageDialogMode, setStageDialogMode] = useState("create");
  const [selectedStage, setSelectedStage] = useState(null);
  const [stageFormData, setStageFormData] = useState(INITIAL_STAGE_FORM_DATA);

  // Node Dialog states
  const [showNodeDialog, setShowNodeDialog] = useState(false);
  const [nodeDialogMode, setNodeDialogMode] = useState("create");
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedStageForNode, setSelectedStageForNode] = useState(null);
  const [nodeFormData, setNodeFormData] = useState(INITIAL_NODE_FORM_DATA);

  // 加载模板详情
  const loadTemplate = useCallback(async () => {
    setLoading(true);
    try {
      const response = await stageTemplateApi.get(templateId);
      setTemplate(response.data);
      setStages(response.data.stage_definitions || []);
      // 默认展开所有阶段
      setExpandedStages(new Set((response.data.stage_definitions || []).map((s) => s.id)));
    } catch (error) {
      console.error("加载模板详情失败:", error);
      // Mock data
      setTemplate({
        id: parseInt(templateId),
        template_code: "STD_9_STAGE",
        template_name: "标准九阶段流程",
        description: "适用于大多数非标自动化项目的标准九阶段流程模板",
        project_type: "STANDARD",
        is_default: true,
        is_active: true,
      });
      setStages([
        {
          id: 1,
          stage_code: "S1",
          stage_name: "需求进入",
          sequence: 1,
          estimated_days: 3,
          description: "项目需求收集和初步评估",
          is_required: true,
          node_definitions: [
            {
              id: 1,
              node_code: "S1_N1",
              node_name: "需求调研",
              node_type: "TASK",
              sequence: 1,
              estimated_days: 2,
              completion_method: "MANUAL",
              is_required: true,
            },
            {
              id: 2,
              node_code: "S1_N2",
              node_name: "需求评审",
              node_type: "APPROVAL",
              sequence: 2,
              estimated_days: 1,
              completion_method: "APPROVAL",
              is_required: true,
            },
          ],
        },
        {
          id: 2,
          stage_code: "S2",
          stage_name: "方案设计",
          sequence: 2,
          estimated_days: 7,
          description: "技术方案设计和评审",
          is_required: true,
          node_definitions: [
            {
              id: 3,
              node_code: "S2_N1",
              node_name: "方案设计",
              node_type: "TASK",
              sequence: 1,
              estimated_days: 5,
              completion_method: "MANUAL",
              is_required: true,
            },
            {
              id: 4,
              node_code: "S2_N2",
              node_name: "方案评审",
              node_type: "APPROVAL",
              sequence: 2,
              estimated_days: 2,
              completion_method: "APPROVAL",
              is_required: true,
            },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [templateId]);

  useEffect(() => {
    loadTemplate();
  }, [loadTemplate]);

  const toggleStageExpanded = (stageId) => {
    setExpandedStages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(stageId)) {
        newSet.delete(stageId);
      } else {
        newSet.add(stageId);
      }
      return newSet;
    });
  };

  // Stage handlers
  const handleAddStage = () => {
    setStageDialogMode("create");
    setStageFormData({
      ...INITIAL_STAGE_FORM_DATA,
      sequence: stages.length + 1,
    });
    setShowStageDialog(true);
  };

  const handleEditStage = (stage) => {
    setStageDialogMode("edit");
    setSelectedStage(stage);
    setStageFormData({
      stage_code: stage.stage_code,
      stage_name: stage.stage_name,
      sequence: stage.sequence,
      estimated_days: stage.estimated_days,
      description: stage.description || "",
      is_required: stage.is_required,
    });
    setShowStageDialog(true);
  };

  const handleDeleteStage = async (stage) => {
    if (!await confirmAction(`确定要删除阶段 "${stage.stage_name}" 吗？`)) return;
    try {
      await stageTemplateApi.stages.delete(stage.id);
      loadTemplate();
    } catch (error) {
      console.error("删除阶段失败:", error);
      setStages((prev) => (prev || []).filter((s) => s.id !== stage.id));
    }
  };

  const handleSaveStage = async () => {
    try {
      if (stageDialogMode === "create") {
        await stageTemplateApi.stages.add(template.id, {
          ...stageFormData,
          template_id: parseInt(templateId),
        });
      } else {
        await stageTemplateApi.stages.update(selectedStage.id, stageFormData);
      }
      setShowStageDialog(false);
      loadTemplate();
    } catch (error) {
      console.error("保存阶段失败:", error);
      alert("保存失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // Node handlers
  const handleAddNode = (stage) => {
    setNodeDialogMode("create");
    setSelectedStageForNode(stage);
    const existingNodes = stage.node_definitions || [];
    setNodeFormData({
      ...INITIAL_NODE_FORM_DATA,
      sequence: existingNodes.length + 1,
    });
    setShowNodeDialog(true);
  };

  const handleEditNode = (stage, node) => {
    setNodeDialogMode("edit");
    setSelectedStageForNode(stage);
    setSelectedNode(node);
    setNodeFormData({
      node_code: node.node_code,
      node_name: node.node_name,
      node_type: node.node_type,
      sequence: node.sequence,
      estimated_days: node.estimated_days,
      completion_method: node.completion_method,
      is_required: node.is_required,
      required_attachments: node.required_attachments || false,
      description: node.description || "",
      approval_role_ids: node.approval_role_ids || [],
      auto_condition: node.auto_condition || "",
      dependency_node_ids: node.dependency_node_ids || [],
    });
    setShowNodeDialog(true);
  };

  const handleDeleteNode = async (stage, node) => {
    if (!await confirmAction(`确定要删除节点 "${node.node_name}" 吗？`)) return;
    try {
      await stageTemplateApi.nodes.delete(node.id);
      loadTemplate();
    } catch (error) {
      console.error("删除节点失败:", error);
      setStages((prev) =>
        (prev || []).map((s) => {
          if (s.id === stage.id) {
            return {
              ...s,
              node_definitions: (s.node_definitions || []).filter((n) => n.id !== node.id),
            };
          }
          return s;
        })
      );
    }
  };

  const handleSaveNode = async () => {
    try {
      const stageId = selectedStageForNode.id;
      if (nodeDialogMode === "create") {
        await stageTemplateApi.nodes.add(stageId, {
          ...nodeFormData,
          stage_definition_id: stageId,
        });
      } else {
        await stageTemplateApi.nodes.update(selectedNode.id, nodeFormData);
      }
      setShowNodeDialog(false);
      loadTemplate();
    } catch (error) {
      console.error("保存节点失败:", error);
      alert("保存失败: " + (error.response?.data?.detail || error.message));
    }
  };

  return {
    template,
    stages,
    loading,
    expandedStages,
    toggleStageExpanded,

    // Stage dialog
    showStageDialog,
    setShowStageDialog,
    stageDialogMode,
    stageFormData,
    setStageFormData,
    handleAddStage,
    handleEditStage,
    handleDeleteStage,
    handleSaveStage,

    // Node dialog
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
  };
}
