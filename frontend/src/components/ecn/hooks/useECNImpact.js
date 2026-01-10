/**
 * useECNImpact Hook
 * 管理 ECN 影响分析相关的状态和逻辑
 */
import { useState, useCallback } from "react";
import { ecnApi } from "../../../services/api";

const initialMaterialForm = {
  material_id: null,
  bom_item_id: null,
  material_code: "",
  material_name: "",
  specification: "",
  change_type: "UPDATE",
  old_quantity: "",
  old_specification: "",
  old_supplier_id: null,
  new_quantity: "",
  new_specification: "",
  new_supplier_id: null,
  cost_impact: 0,
  remark: "",
};

const initialOrderForm = {
  order_type: "PURCHASE",
  order_id: null,
  order_no: "",
  impact_description: "",
  action_type: "",
  action_description: "",
};

const initialResponsibilityForm = [
  {
    dept: "",
    responsibility_ratio: 0,
    responsibility_type: "PRIMARY",
    impact_description: "",
    responsibility_scope: "",
  },
];

const initialRcaForm = {
  root_cause: "",
  root_cause_analysis: "",
  root_cause_category: "",
};

export function useECNImpact(ecnId, refetchECN) {
  // BOM 分析状态
  const [analyzingBom, setAnalyzingBom] = useState(false);
  const [bomImpactSummary, setBomImpactSummary] = useState(null);
  const [obsoleteAlerts, setObsoleteAlerts] = useState([]);

  // 责任分摊状态
  const [responsibilitySummary, setResponsibilitySummary] = useState(null);
  const [showResponsibilityDialog, setShowResponsibilityDialog] =
    useState(false);
  const [responsibilityForm, setResponsibilityForm] = useState(
    initialResponsibilityForm,
  );

  // RCA 分析状态
  const [rcaAnalysis, setRcaAnalysis] = useState(null);
  const [showRcaDialog, setShowRcaDialog] = useState(false);
  const [rcaForm, setRcaForm] = useState(initialRcaForm);

  // 物料对话框状态
  const [showMaterialDialog, setShowMaterialDialog] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [materialForm, setMaterialForm] = useState(initialMaterialForm);

  // 订单对话框状态
  const [showOrderDialog, setShowOrderDialog] = useState(false);
  const [editingOrder, setEditingOrder] = useState(null);
  const [orderForm, setOrderForm] = useState(initialOrderForm);

  // BOM 影响分析
  const handleAnalyzeBomImpact = useCallback(async () => {
    setAnalyzingBom(true);
    try {
      const result = await ecnApi.analyzeBomImpact(ecnId, {
        include_cascade: true,
      });
      const data = result.data || result;
      setBomImpactSummary(data);
      await refetchECN(); // 刷新数据以获取最新的受影响物料
      return {
        success: true,
        message: data?.has_impact
          ? `BOM影响分析完成：影响${data.total_affected_items}项物料，成本影响¥${data.total_cost_impact?.toLocaleString()}`
          : "BOM影响分析完成：未发现影响",
      };
    } catch (error) {
      return {
        success: false,
        message: "分析失败: " + (error.response?.data?.detail || error.message),
      };
    } finally {
      setAnalyzingBom(false);
    }
  }, [ecnId, refetchECN]);

  // 检查呆滞料风险
  const handleCheckObsoleteRisk = useCallback(async () => {
    setAnalyzingBom(true);
    try {
      const result = await ecnApi.checkObsoleteRisk(ecnId);
      const data = result.data || result;
      const alerts = data?.obsolete_risks || data || [];
      setObsoleteAlerts(alerts);
      return {
        success: true,
        message: data?.has_obsolete_risk
          ? `呆滞料风险检查完成：发现${alerts.length}个风险，总成本¥${data.total_obsolete_cost?.toLocaleString()}`
          : "呆滞料风险检查完成：未发现呆滞料风险",
      };
    } catch (error) {
      return {
        success: false,
        message: "检查失败: " + (error.response?.data?.detail || error.message),
      };
    } finally {
      setAnalyzingBom(false);
    }
  }, [ecnId]);

  // 保存物料
  const handleSaveMaterial = useCallback(async () => {
    try {
      if (editingMaterial) {
        await ecnApi.updateAffectedMaterial(
          ecnId,
          editingMaterial.id,
          materialForm,
        );
      } else {
        await ecnApi.createAffectedMaterial(ecnId, materialForm);
      }
      setShowMaterialDialog(false);
      setMaterialForm(initialMaterialForm);
      setEditingMaterial(null);
      await refetchECN();
      return {
        success: true,
        message: editingMaterial ? "物料已更新" : "物料已添加",
      };
    } catch (error) {
      return {
        success: false,
        message: "保存失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, editingMaterial, materialForm, refetchECN]);

  // 删除物料
  const handleDeleteMaterial = useCallback(
    async (materialId) => {
      try {
        await ecnApi.deleteAffectedMaterial(ecnId, materialId);
        await refetchECN();
        return {
          success: true,
          message: "物料已删除",
        };
      } catch (error) {
        return {
          success: false,
          message:
            "删除失败: " + (error.response?.data?.detail || error.message),
        };
      }
    },
    [ecnId, refetchECN],
  );

  // 保存订单
  const handleSaveOrder = useCallback(async () => {
    try {
      if (editingOrder) {
        await ecnApi.updateAffectedOrder(ecnId, editingOrder.id, orderForm);
      } else {
        await ecnApi.createAffectedOrder(ecnId, orderForm);
      }
      setShowOrderDialog(false);
      setOrderForm(initialOrderForm);
      setEditingOrder(null);
      await refetchECN();
      return {
        success: true,
        message: editingOrder ? "订单已更新" : "订单已添加",
      };
    } catch (error) {
      return {
        success: false,
        message: "保存失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, editingOrder, orderForm, refetchECN]);

  // 删除订单
  const handleDeleteOrder = useCallback(
    async (orderId) => {
      try {
        await ecnApi.deleteAffectedOrder(ecnId, orderId);
        await refetchECN();
        return {
          success: true,
          message: "订单已删除",
        };
      } catch (error) {
        return {
          success: false,
          message:
            "删除失败: " + (error.response?.data?.detail || error.message),
        };
      }
    },
    [ecnId, refetchECN],
  );

  // 添加物料
  const handleAddMaterial = useCallback(() => {
    setEditingMaterial(null);
    setMaterialForm(initialMaterialForm);
    setShowMaterialDialog(true);
  }, []);

  // 编辑物料
  const handleEditMaterial = useCallback((material) => {
    setEditingMaterial(material);
    setMaterialForm({
      material_id: material.material_id,
      bom_item_id: material.bom_item_id,
      material_code: material.material_code || "",
      material_name: material.material_name || "",
      specification: material.specification || "",
      change_type: material.change_type || "UPDATE",
      old_quantity: material.old_quantity || "",
      old_specification: material.old_specification || "",
      old_supplier_id: material.old_supplier_id,
      new_quantity: material.new_quantity || "",
      new_specification: material.new_specification || "",
      new_supplier_id: material.new_supplier_id,
      cost_impact: material.cost_impact || 0,
      remark: material.remark || "",
    });
    setShowMaterialDialog(true);
  }, []);

  // 添加订单
  const handleAddOrder = useCallback(() => {
    setEditingOrder(null);
    setOrderForm(initialOrderForm);
    setShowOrderDialog(true);
  }, []);

  // 编辑订单
  const handleEditOrder = useCallback((order) => {
    setEditingOrder(order);
    setOrderForm({
      order_type: order.order_type || "PURCHASE",
      order_id: order.order_id,
      order_no: order.order_no || "",
      impact_description: order.impact_description || "",
      action_type: order.action_type || "",
      action_description: order.action_description || "",
    });
    setShowOrderDialog(true);
  }, []);

  // 创建责任分摊
  const handleCreateResponsibility = useCallback(async () => {
    const totalRatio = responsibilityForm.reduce(
      (sum, r) => sum + parseFloat(r.responsibility_ratio || 0),
      0,
    );
    if (Math.abs(totalRatio - 100) > 0.01) {
      return {
        success: false,
        message: `责任比例总和必须为100%，当前为${totalRatio.toFixed(2)}%`,
      };
    }

    try {
      await ecnApi.createResponsibilityAnalysis(ecnId, responsibilityForm);
      setShowResponsibilityDialog(false);
      await refetchECN();
      return {
        success: true,
        message: "责任分摊创建成功",
      };
    } catch (error) {
      return {
        success: false,
        message: "创建失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, responsibilityForm, refetchECN]);

  // 保存 RCA 分析
  const handleSaveRcaAnalysis = useCallback(async () => {
    try {
      await ecnApi.updateRcaAnalysis(ecnId, rcaForm);
      setShowRcaDialog(false);
      await refetchECN();
      return {
        success: true,
        message: "RCA分析保存成功",
      };
    } catch (error) {
      return {
        success: false,
        message: "保存失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, rcaForm, refetchECN]);

  return {
    // BOM 分析
    analyzingBom,
    bomImpactSummary,
    obsoleteAlerts,
    handleAnalyzeBomImpact,
    handleCheckObsoleteRisk,
    // 责任分摊
    responsibilitySummary,
    setResponsibilitySummary,
    showResponsibilityDialog,
    setShowResponsibilityDialog,
    responsibilityForm,
    setResponsibilityForm,
    handleCreateResponsibility,
    // RCA 分析
    rcaAnalysis,
    setRcaAnalysis,
    showRcaDialog,
    setShowRcaDialog,
    rcaForm,
    setRcaForm,
    handleSaveRcaAnalysis,
    // 物料管理
    showMaterialDialog,
    setShowMaterialDialog,
    editingMaterial,
    materialForm,
    setMaterialForm,
    handleAddMaterial,
    handleEditMaterial,
    handleSaveMaterial,
    handleDeleteMaterial,
    // 订单管理
    showOrderDialog,
    setShowOrderDialog,
    editingOrder,
    orderForm,
    setOrderForm,
    handleAddOrder,
    handleEditOrder,
    handleSaveOrder,
    handleDeleteOrder,
  };
}
