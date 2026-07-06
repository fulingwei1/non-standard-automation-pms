import { useEffect, useState, useCallback } from "react";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Input,
  Badge,
  LoadingSpinner,
  ApiIntegrationError,
  toast,
} from "../components/ui";
import { otdApi } from "../services/api/otd";
import { Save, RotateCcw, Settings2 } from "lucide-react";

const thresholdGroups = [
  {
    title: "扫描范围",
    items: [
      { key: "scan_limit", label: "扫描项目上限", unit: "个" },
    ],
  },
  {
    title: "维度1 采购延期（天）",
    items: [
      { key: "procurement_overdue_medium_days", label: "MEDIUM", unit: "天" },
      { key: "procurement_overdue_high_days", label: "HIGH", unit: "天" },
      { key: "procurement_overdue_critical_days", label: "CRITICAL", unit: "天" },
    ],
  },
  {
    title: "维度3 客户变更",
    items: [
      { key: "change_window_short_days", label: "短时间窗", unit: "天" },
      { key: "change_high_count", label: "HIGH 次数", unit: "次" },
      { key: "change_critical_count", label: "CRITICAL 次数", unit: "次" },
    ],
  },
  {
    title: "维度5 调试反复",
    items: [
      { key: "debug_window_days", label: "时间窗", unit: "天" },
      { key: "debug_medium_count", label: "MEDIUM 次数", unit: "次" },
      { key: "debug_high_count", label: "HIGH 次数", unit: "次" },
    ],
  },
  {
    title: "维度9-10 偏差阈值（%）",
    items: [
      { key: "progress_medium_threshold", label: "进度 MEDIUM", unit: "%" },
      { key: "progress_high_threshold", label: "进度 HIGH", unit: "%" },
      { key: "margin_medium_threshold", label: "毛利 MEDIUM", unit: "%" },
      { key: "margin_high_threshold", label: "毛利 HIGH", unit: "%" },
      { key: "margin_critical_threshold", label: "毛利 CRITICAL", unit: "%" },
    ],
  },
  {
    title: "维度11 未关闭事项",
    items: [
      { key: "open_items_medium_count", label: "MEDIUM", unit: "项" },
      { key: "open_items_high_count", label: "HIGH", unit: "项" },
    ],
  },
];

export default function OTDThresholdConfig() {
  const [config, setConfig] = useState(null);
  const [original, setOriginal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await otdApi.getThresholds();
      const data = resp.data?.data || resp.data;
      setConfig({ ...data });
      setOriginal({ ...data });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleChange = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      // 只传变更的字段
      const changes = {};
      for (const group of thresholdGroups) {
        for (const item of group.items) {
          if (config[item.key] != original[item.key]) {
            changes[item.key] = Number(config[item.key]);
          }
        }
      }
      if (Object.keys(changes).length === 0) {
        toast.info("没有变更");
        return;
      }
      await otdApi.updateThresholds(changes);
      toast.success(`已更新 ${Object.keys(changes).length} 个阈值，下次扫描立即生效`);
      setOriginal({ ...config });
    } catch (err) {
      toast.error("保存失败: " + (err.message || ""));
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig({ ...original });
  };

  const hasChanges = JSON.stringify(config) !== JSON.stringify(original);

  if (loading) return <LoadingSpinner text="加载阈值配置..." />;
  if (error) return <ApiIntegrationError message={error} onRetry={fetchData} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="OTD 阈值配置"
        description="11 维风险检测阈值 · 改完立即生效 · 无需重启"
        action={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={!hasChanges}
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              撤销
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={!hasChanges || saving}
            >
              <Save className="w-4 h-4 mr-1" />
              {saving ? "保存中..." : "保存"}
            </Button>
          </div>
        }
      />

      {hasChanges && (
        <div className="px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
          有未保存的修改，保存后下次扫描立即生效
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {thresholdGroups.map((group) => (
          <Card key={group.title}>
            <CardContent className="p-4">
              <div className="flex items-center gap-1 mb-3">
                <Settings2 className="w-4 h-4 text-gray-400" />
                <h3 className="text-sm font-semibold">{group.title}</h3>
              </div>
              <div className="space-y-2">
                {group.items.map((item) => (
                  <div key={item.key} className="flex items-center gap-3">
                    <label className="text-sm text-gray-600 w-32">
                      {item.label}
                    </label>
                    <Input
                      type="number"
                      value={config[item.key] ?? ""}
                      onChange={(e) => handleChange(item.key, e.target.value)}
                      className="w-24"
                    />
                    <span className="text-xs text-gray-400">{item.unit}</span>
                    {original[item.key] != config[item.key] && (
                      <Badge variant="secondary" className="text-xs">
                        原: {original[item.key]}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
