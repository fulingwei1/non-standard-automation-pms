import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Badge,
  LoadingSpinner,
  EmptyState,
  ApiIntegrationError,
} from "../components/ui";
import { otdApi } from "../services/api/otd";
import {
  CheckCircle,
  XCircle,
  HelpCircle,
  ClipboardList,
} from "lucide-react";
import { cn } from "../lib/utils";

const healthConfig = {
  healthy: "text-green-600 bg-green-50",
  warning: "text-yellow-600 bg-yellow-50",
  critical: "text-red-600 bg-red-50",
};

const actionIcon = {
  auto_passed: { Icon: CheckCircle, color: "text-green-500" },
  auto_failed: { Icon: XCircle, color: "text-red-500" },
  manual: { Icon: HelpCircle, color: "text-gray-400" },
};

export default function PmMonthlyCheck() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await otdApi.pmMonthlyCheck();
      setData(resp.data?.data || resp.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) return <LoadingSpinner text="正在生成月度自检..." />;
  if (error) return <ApiIntegrationError message={error} onRetry={fetchData} />;

  const summary = data?.summary || {};
  const healthTable = data?.health_table || [];
  const actions = data?.actions || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={`PM 月度自检 · ${data?.period?.year}年${data?.period?.month}月`}
        description="在管项目利润健康度 · 8 项关键动作自动判定"
      />

      {/* 汇总 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard label="在管项目" value={summary.total_projects} />
        <SummaryCard
          label="健康"
          value={summary.healthy}
          className="text-green-600"
        />
        <SummaryCard
          label="预警"
          value={summary.warning}
          className="text-yellow-600"
        />
        <SummaryCard
          label="需关注动作"
          value={summary.auto_failed_actions}
          className="text-red-600"
        />
      </div>

      {/* 8 项动作自检 */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-1">
            <ClipboardList className="w-4 h-4" />
            8 项关键动作自检
          </h3>
          <div className="space-y-2">
            {actions.map((a, idx) => {
              const cfg = actionIcon[a.status] || actionIcon.manual;
              const ActionIcon = cfg.Icon;
              return (
                <motion.div
                  key={a.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-start gap-3 p-3 rounded-lg border"
                >
                  <ActionIcon className={cn("w-5 h-5 mt-0.5 shrink-0", cfg.color)} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{a.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{a.detail}</p>
                  </div>
                  <Badge
                    variant={
                      a.status === "auto_passed"
                        ? "secondary"
                        : a.status === "auto_failed"
                        ? "destructive"
                        : "outline"
                    }
                    className="text-xs"
                  >
                    {a.status === "auto_passed"
                      ? "通过"
                      : a.status === "auto_failed"
                      ? "需关注"
                      : "待自填"}
                  </Badge>
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 在管项目健康度表 */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-semibold mb-3">
            在管项目利润健康度（按严重程度排序）
          </h3>
          {healthTable.length === 0 ? (
            <EmptyState title="无在管项目" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 pr-4">项目</th>
                    <th className="pb-2 pr-4">合同额</th>
                    <th className="pb-2 pr-4">当前毛利率</th>
                    <th className="pb-2 pr-4">目标</th>
                    <th className="pb-2 pr-4">偏差</th>
                    <th className="pb-2 pr-4">健康度</th>
                    <th className="pb-2">风险点</th>
                  </tr>
                </thead>
                <tbody>
                  {healthTable.map((p) => (
                    <tr key={p.project_id} className="border-b hover:bg-gray-50">
                      <td className="py-2 pr-4">
                        <div className="font-medium">{p.project_name}</div>
                        <div className="text-xs text-gray-400">{p.project_code}</div>
                      </td>
                      <td className="py-2 pr-4">
                        {p.contract_amount
                          ? `${(p.contract_amount / 10000).toFixed(1)} 万`
                          : "-"}
                      </td>
                      <td className="py-2 pr-4 font-medium">
                        {p.current_margin_rate ?? "-"}%
                      </td>
                      <td className="py-2 pr-4 text-gray-500">
                        {p.target_margin_rate ?? "-"}%
                      </td>
                      <td className="py-2 pr-4">
                        {p.margin_gap != null && (
                          <span
                            className={
                              p.margin_gap < 0
                                ? "text-red-600"
                                : "text-green-600"
                            }
                          >
                            {p.margin_gap}%
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-4">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-xs",
                            healthConfig[p.health] || ""
                          )}
                        >
                          {p.health || "-"}
                        </span>
                      </td>
                      <td className="py-2 text-xs text-gray-500 max-w-xs truncate">
                        {p.risk_point}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryCard({ label, value, className }) {
  return (
    <Card>
      <CardContent className="p-4 text-center">
        <p className={cn("text-2xl font-bold", className)}>{value}</p>
        <p className="text-xs text-gray-500 mt-1">{label}</p>
      </CardContent>
    </Card>
  );
}
