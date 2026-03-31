import { useState, useEffect } from "react";
import { AlertCircle } from "lucide-react";
import {
  Card, CardContent, CardHeader, CardTitle,
  Badge, Progress,
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
  Alert,
} from "../../components/ui";
import { funnelOptimizationApi } from "../../services/api";
import { STAGE_NAME_MAP } from "./constants";

export default function PredictionAccuracy() {
  const [accuracyData, setAccuracyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await funnelOptimizationApi.getPredictionAccuracy();
        setAccuracyData(res.formatted || res.data?.data || res.data);
      } catch (err) {
        console.error("加载预测准确性数据失败:", err);
        setError("加载预测准确性数据失败，请稍后重试");
        setAccuracyData(null);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <div className="text-slate-400 p-4">加载中...</div>;
  if (!accuracyData) return <div className="text-slate-400 p-4">暂无数据</div>;

  return (
    <div className="space-y-6">
      {error && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <div className="text-sm">{error}</div>
        </Alert>
      )}

      {/* 整体准确性 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">预测赢单率</div>
            <div className="text-2xl font-bold">{accuracyData.overall_accuracy?.predicted_win_rate?.toFixed(1) || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">实际赢单率</div>
            <div className="text-2xl font-bold">{accuracyData.overall_accuracy?.actual_win_rate?.toFixed(1) || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">准确性评分</div>
            <div className="text-2xl font-bold text-green-500">{accuracyData.overall_accuracy?.accuracy_score?.toFixed(1) || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">偏差</div>
            <div className="text-2xl font-bold text-orange-500">{accuracyData.overall_accuracy?.bias || "未知"}</div>
          </CardContent>
        </Card>
      </div>

      {/* 各阶段对比 */}
      <Card>
        <CardHeader>
          <CardTitle>各阶段预测准确性</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>阶段</TableHead>
                <TableHead>预测赢单率</TableHead>
                <TableHead>实际赢单率</TableHead>
                <TableHead>差距</TableHead>
                <TableHead>准确性</TableHead>
                <TableHead>评估</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(accuracyData.by_stage || []).map((stage) => (
                <TableRow key={stage.stage}>
                  <TableCell className="font-medium">{stage.stage_name || STAGE_NAME_MAP[stage.stage] || stage.stage}</TableCell>
                  <TableCell>{stage.predicted?.toFixed(1) || 0}%</TableCell>
                  <TableCell>{stage.actual?.toFixed(1) || 0}%</TableCell>
                  <TableCell className={(stage.predicted || 0) > (stage.actual || 0) ? "text-red-500" : "text-green-500"}>
                    {(stage.predicted || 0) > (stage.actual || 0) ? "+" : ""}
                    {((stage.predicted || 0) - (stage.actual || 0)).toFixed(1)}%
                  </TableCell>
                  <TableCell>
                    <Progress value={stage.accuracy || 0} className="w-20 h-2" />
                  </TableCell>
                  <TableCell>
                    <Badge variant={stage.bias === "准确" ? "default" : "secondary"}>{stage.bias || "未知"}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
