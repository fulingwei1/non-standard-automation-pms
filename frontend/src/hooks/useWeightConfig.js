import { useState, useEffect } from "react";
import { performanceApi } from "../services/api";
import { defaultWeights } from "../utils/weightConfigUtils";

/**
 * 权重配置自定义 Hook
 */
import { confirmAction } from "@/lib/confirmAction";
export const useWeightConfig = () => {
  const [weights, setWeights] = useState(defaultWeights);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // 配置历史记录
  const [configHistory, setConfigHistory] = useState([
    {
      id: 1,
      date: "2024-12-01",
      operator: "李HR",
      deptWeight: 50,
      projectWeight: 50,
      reason: "初始配置",
    },
    {
      id: 2,
      date: "2024-06-15",
      operator: "张HR",
      deptWeight: 40,
      projectWeight: 60,
      reason: "根据公司战略调整，加大项目评价权重",
    },
    {
      id: 3,
      date: "2024-01-10",
      operator: "王HR",
      deptWeight: 60,
      projectWeight: 40,
      reason: "年初配置，强化部门管理",
    },
  ]);

  // 影响统计
  const [impactStatistics, setImpactStatistics] = useState({
    totalEmployees: 156,
    affectedEmployees: 89, // 参与项目的员工
    departments: 8,
    activeProjects: 12,
  });

  // 加载当前权重配置
  const loadWeightConfig = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await performanceApi.getWeightConfig();

      // 设置权重值
      setWeights({
        deptManager:
          response.data.dept_manager_weight ||
          response.data.deptManagerWeight ||
          50,
        projectManager:
          response.data.project_manager_weight ||
          response.data.projectManagerWeight ||
          50,
      });

      // 设置配置历史
      if (response.data.history) {
        setConfigHistory(
          response.data.history.map((record) => ({
            id: record.id,
            date: record.updated_at || record.updatedAt || record.date,
            operator:
              record.updated_by_name ||
              record.updatedByName ||
              record.operator ||
              "系统",
            deptWeight:
              record.dept_manager_weight || record.deptManagerWeight || 50,
            projectWeight:
              record.project_manager_weight ||
              record.projectManagerWeight ||
              50,
            reason: record.reason || record.description || "配置更新",
          })),
        );
      }

      // 设置影响统计(如果API返回)
      if (response.data.statistics) {
        setImpactStatistics({
          totalEmployees:
            response.data.statistics.total_employees ||
            response.data.statistics.totalEmployees ||
            156,
          affectedEmployees:
            response.data.statistics.affected_employees ||
            response.data.statistics.affectedEmployees ||
            89,
          departments: response.data.statistics.departments || 8,
          activeProjects:
            response.data.statistics.active_projects ||
            response.data.statistics.activeProjects ||
            12,
        });
      }
    } catch (err) {
      console.error("加载权重配置失败:", err);
      setError(err.response?.data?.detail || "加载失败");
      // Fallback to default values (already set)
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWeightConfig();
  }, []);

  // 处理权重变化
  const handleWeightChange = (type, value) => {
    const numValue = Number(value);
    if (numValue < 0 || numValue > 100) {return;}

    if (type === "dept") {
      setWeights({
        deptManager: numValue,
        projectManager: 100 - numValue,
      });
    } else {
      setWeights({
        deptManager: 100 - numValue,
        projectManager: numValue,
      });
    }
    setIsDirty(true);
  };

  // 重置为默认值
  const handleReset = async () => {
    if (!await confirmAction("确认重置为默认权重配置吗？（部门50%、项目50%）")) {
      return;
    }
    setWeights(defaultWeights);
    setIsDirty(true);
  };

  // 保存配置
  const handleSave = async () => {
    if (weights.deptManager + weights.projectManager !== 100) {
      alert("权重总和必须为100%");
      return;
    }

    if (
      !await confirmAction(
        `确认保存权重配置吗？\n\n部门经理权重：${weights.deptManager}%\n项目经理权重：${weights.projectManager}%\n\n此配置将影响所有员工的绩效计算`,
      )
    ) {
      return;
    }

    setIsSaving(true);
    try {
      await performanceApi.updateWeightConfig({
        dept_manager_weight: weights.deptManager,
        project_manager_weight: weights.projectManager,
      });
      setIsDirty(false);
      alert("权重配置保存成功！");
      // 重新加载配置以更新历史记录
      await loadWeightConfig();
    } catch (err) {
      console.error("保存权重配置失败:", err);
      alert("保存失败: " + (err.response?.data?.detail || "请稍后重试"));
    } finally {
      setIsSaving(false);
    }
  };

  return {
    weights,
    isDirty,
    isSaving,
    isLoading,
    error,
    configHistory,
    impactStatistics,
    handleWeightChange,
    handleReset,
    handleSave,
    loadWeightConfig,
  };
};
