/**
 * Delay Reasons Report Page - 延期原因统计报表页面
 * Features: 显示任务延期原因统计（Top N）
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  BarChart3,
  FileText,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { cn } from "../lib/utils";
import { progressApi, projectApi } from "../services/api";

export default function DelayReasonsReport() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const projectIdFromQuery = searchParams.get("project_id");

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState(
    id
      ? parseInt(id)
      : projectIdFromQuery
        ? parseInt(projectIdFromQuery)
        : null,
  );
  const [topN, setTopN] = useState(10);

  useEffect(() => {
    if (selectedProjectId) {
      fetchProject();
    }
    fetchReportData();
  }, [selectedProjectId, topN]);

  const fetchProject = async () => {
    if (!selectedProjectId) return;
    try {
      const res = await projectApi.get(selectedProjectId);
      setProject(res.data || res);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const res = await progressApi.reports.getDelayReasons(
        selectedProjectId,
        topN,
      );
      const data = res.data || res || {};
      setReportData(data);
    } catch (error) {
      console.error("Failed to fetch delay reasons data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {selectedProjectId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/projects/${selectedProjectId}`)}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目
            </Button>
          )}
          <PageHeader
            title={
              selectedProjectId
                ? `${project?.project_name || "项目"} - 延期原因统计`
                : "延期原因统计"
            }
            description="分析任务延期的主要原因"
          />
        </div>
        <Button variant="outline" onClick={fetchReportData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="project-select">项目筛选</Label>
              <Select
                value={selectedProjectId?.toString() || "all"}
                onValueChange={(value) =>
                  setSelectedProjectId(value === "all" ? null : parseInt(value))
                }
              >
                <SelectTrigger id="project-select" className="mt-2">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部项目</SelectItem>
                  {/* TODO: 添加项目列表选择 */}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="top-n">显示Top N</Label>
              <Input
                id="top-n"
                type="number"
                min="1"
                max="50"
                value={topN}
                onChange={(e) =>
                  setTopN(
                    Math.max(1, Math.min(50, parseInt(e.target.value) || 10)),
                  )
                }
                className="mt-2"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Card */}
      {reportData && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">延期任务总数</div>
                <div className="text-3xl font-bold text-red-600">
                  {reportData.total_delayed_tasks || 0}
                </div>
              </div>
              <AlertTriangle className="w-12 h-12 text-red-500" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Delay Reasons List */}
      {reportData?.reasons && reportData.reasons.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              延期原因统计（Top {topN}）
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {reportData.reasons.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <Badge
                        variant="outline"
                        className="w-8 h-8 flex items-center justify-center"
                      >
                        {index + 1}
                      </Badge>
                      <div className="flex-1">
                        <div className="font-medium">
                          {item.reason || "未填写原因"}
                        </div>
                        <div className="text-sm text-slate-500 mt-1">
                          {item.count} 个任务 ({item.percentage.toFixed(1)}%)
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold">{item.count}</div>
                      <div className="text-xs text-slate-500">任务数</div>
                    </div>
                  </div>
                  <Progress value={item.percentage} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {reportData?.reasons && reportData.reasons.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">
              {reportData.total_delayed_tasks === 0
                ? "暂无延期任务"
                : "暂无延期原因数据"}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Insights */}
      {reportData?.reasons && reportData.reasons.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              分析洞察
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              {reportData.reasons[0] && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="font-medium text-blue-900 mb-1">主要原因</div>
                  <div className="text-blue-700">
                    "{reportData.reasons[0].reason || "未填写原因"}"
                    是导致任务延期的主要原因， 涉及{" "}
                    {reportData.reasons[0].count} 个任务，占比{" "}
                    {reportData.reasons[0].percentage.toFixed(1)}%。
                  </div>
                </div>
              )}
              {reportData.reasons.length > 1 && (
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="font-medium text-slate-900 mb-1">
                    前3大原因占比
                  </div>
                  <div className="text-slate-700">
                    前3大延期原因共涉及{" "}
                    {reportData.reasons
                      .slice(0, 3)
                      .reduce((sum, item) => sum + item.count, 0)}{" "}
                    个任务， 占总延期任务的{" "}
                    {reportData.reasons
                      .slice(0, 3)
                      .reduce((sum, item) => sum + item.percentage, 0)
                      .toFixed(1)}
                    %。
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
