import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Badge,
  Input,
  Button,
  LoadingSpinner,
  EmptyState,
  ApiIntegrationError,
} from "../components/ui";
import { otdApi } from "../services/api/otd";
import {
  ChevronLeft,
  Search,
  CheckCircle,
  XCircle,
  HelpCircle,
  Package,
} from "lucide-react";
import { cn } from "../lib/utils";

const checkIcon = {
  auto_passed: { Icon: CheckCircle, color: "text-green-500" },
  auto_failed: { Icon: XCircle, color: "text-red-500" },
  manual: { Icon: HelpCircle, color: "text-gray-400" },
};

export default function BomCostCheck() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [inputId, setInputId] = useState(projectId || "");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (id) => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const resp = await otdApi.bomCostCheck(Number(id));
      setData(resp.data?.data || resp.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (projectId) fetchData(projectId);
  }, [projectId, fetchData]);

  const handleSearch = () => {
    if (inputId) {
      navigate(`/otd/bom-check/${inputId}`);
      fetchData(inputId);
    }
  };

  const items = data?.items || [];
  const summary = data?.summary || {};

  return (
    <div className="space-y-6">
      <PageHeader
        title="BOM 成本检查"
        description="12 项检查清单 · 2 项自动判定（历史比价 + 同类对比）"
        action={
          <Button variant="ghost" size="sm" onClick={() => navigate("/otd/dashboard")}>
            <ChevronLeft className="w-4 h-4 mr-1" />
            返回
          </Button>
        }
      />

      {/* 项目搜索 */}
      <div className="flex gap-2">
        <Input
          placeholder="输入项目 ID"
          value={inputId}
          onChange={(e) => setInputId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="w-48"
        />
        <Button size="sm" onClick={handleSearch}>
          <Search className="w-4 h-4 mr-1" />
          检查
        </Button>
      </div>

      {loading && <LoadingSpinner text="正在检查 BOM 成本..." />}
      {error && <ApiIntegrationError message={error} />}

      {!loading && data && !data.has_bom && (
        <Card>
          <CardContent className="p-4">
            <EmptyState
              icon={<Package className="w-8 h-8 text-gray-400" />}
              title={data.message || "项目无 BOM"}
              description="请先创建 BOM 后再检查"
            />
          </CardContent>
        </Card>
      )}

      {!loading && data?.has_bom && (
        <>
          {/* BOM 概况 */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="border-l-4 border-blue-200">
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold">{data.bom_item_count}</p>
                <p className="text-xs text-gray-500">物料数</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-green-200">
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-green-600">
                  {summary.auto_passed || 0}
                </p>
                <p className="text-xs text-gray-500">自动通过</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-red-200">
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-red-600">
                  {summary.auto_failed || 0}
                </p>
                <p className="text-xs text-gray-500">需关注</p>
              </CardContent>
            </Card>
          </div>

          {/* 12 项检查清单 */}
          <Card>
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold mb-3">12 项检查清单</h3>
              <div className="space-y-2">
                {items.map((item, idx) => {
                  const cfg = checkIcon[item.status] || checkIcon.manual;
                  const CheckIcon = cfg.Icon;
                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.03 }}
                      className="flex items-start gap-3 p-3 rounded-lg border"
                    >
                      <span className="text-xs text-gray-400 font-mono w-6 mt-0.5">
                        {item.id}.
                      </span>
                      <CheckIcon className={cn("w-5 h-5 mt-0.5 shrink-0", cfg.color)} />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{item.name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{item.desc}</p>
                        <p className="text-xs text-gray-600 mt-1">{item.detail}</p>
                        {item.evidence?.deviations?.length > 0 && (
                          <details className="mt-1">
                            <summary className="text-xs text-blue-500 cursor-pointer">
                              查看 {item.evidence.deviations.length} 项偏差明细
                            </summary>
                            <div className="mt-1 p-2 bg-gray-100 rounded text-xs space-y-1">
                              {item.evidence.deviations.map((d, i) => (
                                <div key={i}>
                                  {d.material_code}: 当前 {d.current_price} / 历史{" "}
                                  {d.historical_avg}（偏差{" "}
                                  <span
                                    className={
                                      Math.abs(d.deviation_pct) > 15
                                        ? "text-red-600 font-medium"
                                        : ""
                                    }
                                  >
                                    {d.deviation_pct}%
                                  </span>
                                  ）
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                      <Badge
                        variant={
                          item.status === "auto_passed"
                            ? "secondary"
                            : item.status === "auto_failed"
                            ? "destructive"
                            : "outline"
                        }
                        className="text-xs"
                      >
                        {item.status === "auto_passed"
                          ? "通过"
                          : item.status === "auto_failed"
                          ? "需关注"
                          : "待检查"}
                      </Badge>
                    </motion.div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
