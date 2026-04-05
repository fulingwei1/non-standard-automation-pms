/**
 * BOM Assembly Attributes - Custom hook for state and data management
 */
import { useState, useEffect } from "react";
import { bomApi, projectApi } from "../../services/api";
import { assemblyKitApi } from "../../services/api/production";
import { confirmAction } from "@/lib/confirmAction";

export function useBomAssemblyAttrs() {
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [boms, setBoms] = useState([]);
  const [_stages, setStages] = useState([]);
  const [templates, setTemplates] = useState([]);

  const [selectedProject, setSelectedProject] = useState("");
  const [selectedBom, setSelectedBom] = useState("");
  const [filterStage, setFilterStage] = useState("all");
  const [filterBlocking, setFilterBlocking] = useState("all");
  const [searchText, setSearchText] = useState("");

  const [_bomItems, _setBomItems] = useState([]);
  const [assemblyAttrs, setAssemblyAttrs] = useState([]);
  const [editedAttrs, setEditedAttrs] = useState([]);
  const [hasChanges, setHasChanges] = useState(false);

  const [autoAssignDialogOpen, setAutoAssignDialogOpen] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [overwrite, setOverwrite] = useState(false);

  useEffect(() => {
    fetchProjects();
    fetchStages();
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchBoms();
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedBom) {
      fetchBomAssemblyAttrs();
    }
  }, [selectedBom]);

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  const fetchBoms = async () => {
    try {
      const res = await bomApi.list({
        project_id: selectedProject,
        page_size: 100,
      });
      setBoms(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch BOMs:", error);
      setBoms([]);
    }
  };

  const fetchStages = async () => {
    try {
      const res = await assemblyKitApi.getStages();
      setStages(res.data || res || []);
    } catch (error) {
      console.error("Failed to fetch stages:", error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const res = await assemblyKitApi.getTemplates();
      setTemplates(res.data || res || []);
    } catch (error) {
      console.error("Failed to fetch templates:", error);
    }
  };

  const fetchBomAssemblyAttrs = async () => {
    try {
      setLoading(true);
      const res = await assemblyKitApi.getBomAssemblyAttrs(selectedBom);
      const attrs = res.data || res || [];
      setAssemblyAttrs(attrs);

      // 初始化编辑状态
      const initialEdits = {};
      (attrs || []).forEach((attr) => {
        initialEdits[attr.bom_item_id] = { ...attr };
      });
      setEditedAttrs(initialEdits);
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to fetch assembly attrs:", error);
      setAssemblyAttrs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAttrChange = (bomItemId, field, value) => {
    setEditedAttrs((prev) => ({
      ...prev,
      [bomItemId]: {
        ...prev[bomItemId],
        bom_item_id: bomItemId,
        bom_id: parseInt(selectedBom),
        [field]: value,
      },
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const items = Object.values(editedAttrs).filter(
        (attr) => attr.assembly_stage
      );

      if (items?.length === 0) {
        console.error("没有需要保存的配置");
        return;
      }

      await assemblyKitApi.batchSetAssemblyAttrs(selectedBom, { items });
      console.log("保存成功");
      setHasChanges(false);
      fetchBomAssemblyAttrs();
    } catch (error) {
      console.error("保存失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoAssign = async () => {
    try {
      setLoading(true);
      const res = await assemblyKitApi.autoAssignAttrs(selectedBom, {
        bom_id: parseInt(selectedBom),
        overwrite,
      });
      console.log(res.message || "自动分配完成");
      setAutoAssignDialogOpen(false);
      fetchBomAssemblyAttrs();
    } catch (error) {
      console.error("自动分配失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSmartRecommend = async () => {
    try {
      setLoading(true);
      // 先获取推荐结果预览
      const previewRes = await assemblyKitApi.getRecommendations(selectedBom);
      console.log("推荐结果预览:", previewRes.data);

      // 询问用户是否应用推荐
      if (
        await confirmAction(
          `智能推荐完成，共推荐 ${previewRes.data?.total || 0} 项。是否应用推荐结果？`
        )
      ) {
        const res = await assemblyKitApi.smartRecommend(selectedBom, {
          bom_id: parseInt(selectedBom),
          overwrite,
        });
        console.log(res.message || "智能推荐完成");
        if (res.data?.recommendation_stats) {
          const stats = res.data.recommendation_stats;
          const statsText = Object.entries(stats)
            .filter(([_, count]) => count > 0)
            .map(([source, count]) => {
              const sourceNames = {
                HISTORY: "历史数据",
                CATEGORY: "分类匹配",
                KEYWORD: "关键词",
                SUPPLIER: "供应商类型",
                DEFAULT: "默认",
              };
              return `${sourceNames[source] || source}: ${count}项`;
            })
            .join(", ");
          alert(`推荐完成！\n${statsText}`);
        }
        setAutoAssignDialogOpen(false);
        fetchBomAssemblyAttrs();
      }
    } catch (error) {
      console.error("智能推荐失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplate) {
      console.error("请选择模板");
      return;
    }
    try {
      setLoading(true);
      const res = await assemblyKitApi.applyTemplate(selectedBom, {
        bom_id: parseInt(selectedBom),
        template_id: parseInt(selectedTemplate),
        overwrite,
      });
      console.log(res.message || "模板套用完成");
      setTemplateDialogOpen(false);
      fetchBomAssemblyAttrs();
    } catch (error) {
      console.error("模板套用失败:", error);
    } finally {
      setLoading(false);
    }
  };

  return {
    // State
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
    // Actions
    handleAttrChange,
    handleSave,
    handleAutoAssign,
    handleSmartRecommend,
    handleApplyTemplate,
  };
}
