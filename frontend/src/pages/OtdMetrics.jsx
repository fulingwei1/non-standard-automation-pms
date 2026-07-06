import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Progress,
  LoadingSpinner,
  ApiIntegrationError,
  EmptyState,
} from "../components/ui";
import { otdApi } from "../services/api/otd";
import {
  Download,
  TrendingUp,
  AlertTriangle,
  Clock,
  Repeat,
  GitCommit,
  DollarSign,
  CheckSquare,
  MessageSquareWarning,
} from "lucide-react";
import { cn } from "../lib/utils";

const metricMeta = [
  {
    key: "on_time_delivery_rate",
    label: "准时交付率",
    icon: CheckSquare,
    valueKey: "rate_pct",
    suffix: "%",
    descKey: "note",
  },
  {
    key: "delay_days",
    label: "平均延期天数",
    icon: Clock,
    valueKey: "avg_delay_days",
    suffix: " 天",
  },
  {
    key: "rework_count",
    label: "返工次数",
    icon: Repeat,
    valueKey: "total_retry_count",
    suffix: "",
  },
  {
    key: "change_count",
    label: "变更次数",
    icon: GitCommit,
    valueKey: "grand_total",
    suffix: "",
  },
  {
    key: "margin_deviation",
    label: "平均毛利偏差",
    icon: DollarSign,
    valueKey: "avg_margin_gap_pct",
    suffix: "%",
  },
  {
    key: "acceptance_cycle_days",
    label: "平均验收周期",
    icon: TrendingUp,
    valueKey: "avg_cycle_days",
    suffix: " 天",
  },
  {
    key: "customer_complaint_rate",
    label: "客户投诉率",
    icon: MessageSquareWarning,
    valueKey: "complaint_rate_pct",
    suffix: "%",
  },
];

export default function OtdMetrics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [includeOffenders, setIncludeOffenders] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await otdApi.metrics({ include_offenders: includeOffenders });
      setData(resp.data?.data || resp.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [includeOffenders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExport = async () => {
    try {
      const resp = await otdApi.exportMetrics();
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `OTD核心指标_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // 静默
    }
  };

  if (loading) return <LoadingSpinner text="加载核心指标..." />;
  if (error) return <ApiIntegrationError message={error} onRetry={fetchData} />;

  const metrics = data?.metrics || {};
  const window = data?.window || {};

  return (
    <div className="space-y-6">
      <PageHeader
        title="OTD 7 核心指标"
        description={`${window.start || ""} ~ ${window.end || ""} · 下钻拖后腿的项目`}
        action={
          <div className="flex gap-2">
            <Button
              variant={includeOffenders ? "default" : "outline"}
              size="sm"
              onClick={() => setIncludeOffenders(!includeOffenders)}
            >
              {includeOffenders ? "含下钻" : "仅数字"}
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="w-4 h-4 mr-1" />
              导出
            </Button>
          </div>
        }
      />

      {/* 指标卡片网格 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metricMeta.map((m, idx) => {
          const metric = metrics[m.key] || {};
          const value = metric[m.valueKey];
          const offenders = metric.top_offenders || [];
          const Icon = m.icon;

          return (
            <motion.div
              key={m.key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="w-4 h-4 text-gray-400" />
                    <span className="text-xs text-gray-500">{m.label}</span>
                  </div>
                  <p className="text-2xl font-bold">
                    {value ?? "-"}
                    {m.suffix}
                  </p>
                  {metric.note && (
                    <p className="text-xs text-gray-400 mt-1 truncate">
                      {metric.note}
                    </p>
                  )}

                  {/* 下钻：拖后腿的项目 */}
                  {includeOffenders && offenders.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs text-gray-500 mb-1">
                        拖后腿 Top {offenders.length}
                      </p>
                      <div className="space-y-1">
                        {offenders.map((o, i) => (
                          <div
                            key={i}
                            className="flex items-center gap-2 text-xs"
                          >
                            <span className="text-gray-600 truncate flex-1">
                              {o.project_code || o.project_name}
                            </span>
                            <span className="font-medium">
                              {o.delay_days ??
                                o.margin_gap ??
                                o.change_count ??
                                o.rework_count ??
                                o.cycle_days ??
                                o.complaint_count ??
                                "-"}
                              {m.suffix}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {includeOffenders && offenders.length === 0 && (
                    <p className="text-xs text-gray-300 mt-2">无下钻数据</p>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
