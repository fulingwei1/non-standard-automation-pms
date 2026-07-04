import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { projectContributionApi } from "../services/api";
import { PageHeader } from "../components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, Skeleton } from "../components/ui";
import ContributionChart from "../components/project/ContributionChart";
import { formatCurrency } from "../lib/utils";
import { Award, Calculator, RotateCcw } from "lucide-react";

const getCurrentPeriod = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

export default function ProjectContributionReport() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [report, setReport] = useState(null);
  const [period, setPeriod] = useState("");

  useEffect(() => {
    fetchReport();
  }, [id, period]);

  const fetchReport = async (targetPeriod = period) => {
    try {
      setLoading(true);
      const params = targetPeriod ? { period: targetPeriod } : {};
      const response = await projectContributionApi.getReport(id, params);
      setReport(response.data);
    } catch (error) {
      console.error("Failed to load contribution report:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async () => {
    const targetPeriod = period || getCurrentPeriod();
    try {
      setCalculating(true);
      await projectContributionApi.calculate(id, targetPeriod);
      if (targetPeriod !== period) {
        setPeriod(targetPeriod);
      }
      await fetchReport(targetPeriod);
    } catch (error) {
      console.error("Failed to calculate contributions:", error);
    } finally {
      setCalculating(false);
    }
  };

  const handleRateMember = async (contribution, value) => {
    const pmRating = Number(value);
    const rowPeriod = contribution.period || period || report?.period;
    if (!pmRating || !rowPeriod) {
      return;
    }

    try {
      await projectContributionApi.rateMember(id, contribution.user_id, {
        period: rowPeriod,
        pm_rating: pmRating,
      });
      await fetchReport(period);
    } catch (error) {
      console.error("Failed to rate contribution:", error);
    }
  };

  if (loading && !report) {
    return (
      <div className="p-6">
        <Skeleton className="h-12 w-64 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) =>
          <Skeleton key={i} className="h-24" />
          )}
        </div>
      </div>);

  }

  if (!report) {
    return (
      <div className="p-6">
        <PageHeader title="项目贡献度报告" />
        <Card>
          <CardContent className="p-6 text-center text-gray-500">
            无法加载报告数据
          </CardContent>
        </Card>
      </div>);

  }

  const periodLabel = period || "全部周期";

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="项目贡献度报告" description={`统计周期: ${periodLabel}`} />

      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-1">
          <label htmlFor="contribution-period" className="text-sm text-gray-500">
            统计周期
          </label>
          <input
            id="contribution-period"
            type="month"
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
            className="h-10 rounded-md border border-white/10 bg-transparent px-3 text-sm"
          />
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPeriod("")}
            className="inline-flex h-10 items-center gap-2 rounded-md border border-white/10 px-3 text-sm">
            <RotateCcw className="h-4 w-4" />
            全部周期
          </button>
          <button
            type="button"
            onClick={handleCalculate}
            disabled={calculating}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60">
            <Calculator className="h-4 w-4" />
            计算贡献
          </button>
        </div>
      </div>

      {/* 统计概览 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">团队成员</p>
            <p className="text-2xl font-bold">{report.total_members}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">总任务数</p>
            <p className="text-2xl font-bold">{report.total_task_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">总工时</p>
            <p className="text-2xl font-bold">
              {report.total_hours.toFixed(1)}h
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">总奖金</p>
            <p className="text-2xl font-bold">
              {formatCurrency(report.total_bonus)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 贡献度图表 */}
      <ContributionChart contributions={report.contributions || []} />

      {/* TOP贡献者 */}
      {report.top_contributors && report.top_contributors?.length > 0 &&
      <Card>
          <CardHeader>
            <CardTitle>TOP 贡献者</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(report.top_contributors || []).map((contributor, index) =>
            <div
              key={contributor.user_id}
              className="flex items-center justify-between p-3 border rounded-lg">

                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{contributor.user_name}</p>
                      <p className="text-sm text-gray-500">
                        贡献度: {contributor.contribution_score.toFixed(1)}
                      </p>
                    </div>
                  </div>
                  <Award className="h-5 w-5 text-yellow-500" />
            </div>
            )}
            </div>
          </CardContent>
      </Card>
      }

      {/* 详细贡献列表 */}
      <Card>
        <CardHeader>
          <CardTitle>成员贡献详情</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">成员</th>
                  <th className="text-left p-3">周期</th>
                  <th className="text-left p-3">任务数</th>
                  <th className="text-left p-3">工时</th>
                  <th className="text-left p-3">交付物</th>
                  <th className="text-left p-3">解决问题</th>
                  <th className="text-left p-3">奖金</th>
                  <th className="text-left p-3">贡献度</th>
                  <th className="text-left p-3">PM评分</th>
                </tr>
              </thead>
              <tbody>
	                {report.contributions?.map((contrib) =>
	                  <tr
	                    key={contrib.user_id}
	                    className="border-b hover:bg-gray-50">
	                    <td className="p-3 font-medium">{contrib.user_name}</td>
	                    <td className="p-3">{contrib.period || report.period || "-"}</td>
	                    <td className="p-3">{contrib.task_count}</td>
	                    <td className="p-3">{contrib.actual_hours.toFixed(1)}h</td>
	                    <td className="p-3">{contrib.deliverable_count}</td>
                    <td className="p-3">{contrib.issue_resolved}</td>
                    <td className="p-3">
                      {formatCurrency(contrib.bonus_amount)}
                    </td>
                    <td className="p-3 font-semibold">
	                      {contrib.contribution_score.toFixed(1)}
	                    </td>
	                    <td className="p-3">
                      <select
                        aria-label={`PM评分-${contrib.user_name}`}
                        value={contrib.pm_rating || ""}
                        onChange={(event) => handleRateMember(contrib, event.target.value)}
                        className="h-9 rounded-md border border-white/10 bg-transparent px-2 text-sm">
                        <option value="">未评分</option>
                        {[1, 2, 3, 4, 5].map((score) =>
                          <option key={score} value={score}>
                            {score}/5
                          </option>
                        )}
                      </select>
	                    </td>
	                </tr>
	                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>);

}
