/**
 * KPI 数据管理 Hook
 */
import { useState, useEffect } from "react";
import { strategyApi, kpiApi } from "../../services/api/strategy";

export default function useKPIData() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeStrategy, setActiveStrategy] = useState(null);
  const [kpis, setKpis] = useState([]);
  const [_collecting, setCollecting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // 获取当前战略
      const strategyRes = await strategyApi.getActive();
      const strategy = strategyRes.data;
      setActiveStrategy(strategy);

      if (strategy?.id) {
        // 获取 KPI 列表
        const kpiRes = await kpiApi.list({ strategy_id: strategy.id });
        setKpis(kpiRes.data || []);
      } else {
        setKpis([]);
      }
    } catch (error) {
      // 404 = 当前没有生效的战略，属于正常业务状态，显示空状态
      if (error?.response?.status === 404) {
        setActiveStrategy(null);
        setKpis([]);
        return;
      }
      console.error("加载数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCollect = async (kpi) => {
    if (!confirm(`确定要采集 KPI "${kpi.name}" 的数据吗？`)) return;

    try {
      setCollecting(true);
      await kpiApi.collect(kpi.id);
      loadData();
      alert("数据采集成功");
    } catch (error) {
      console.error("数据采集失败:", error);
      alert("采集失败，请重试");
    } finally {
      setCollecting(false);
    }
  };

  const handleSubmit = async (data, editingKpi) => {
    try {
      setSaving(true);
      if (editingKpi?.id) {
        await kpiApi.update(editingKpi.id, data);
      } else {
        await kpiApi.create({
          ...data,
          strategy_id: activeStrategy.id,
        });
      }
      loadData();
      return true;
    } catch (error) {
      console.error("保存 KPI 失败:", error);
      alert("保存失败，请重试");
      return false;
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateValue = async (updatingKpi, data) => {
    if (!updatingKpi?.id) return false;

    try {
      setSaving(true);
      await kpiApi.updateValue(updatingKpi.id, data);
      loadData();
      return true;
    } catch (error) {
      console.error("更新 KPI 值失败:", error);
      alert("更新失败，请重试");
      return false;
    } finally {
      setSaving(false);
    }
  };

  return {
    loading,
    saving,
    activeStrategy,
    kpis,
    loadData,
    handleCollect,
    handleSubmit,
    handleUpdateValue,
  };
}
