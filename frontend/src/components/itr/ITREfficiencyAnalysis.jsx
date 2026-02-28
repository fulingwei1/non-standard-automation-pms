import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Calendar,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import { itrApi } from "../../services/api";
import {
  SimpleBarChart,
  SimpleLineChart,
  SimplePieChart,
} from "../administrative/StatisticsCharts";

export default function ITREfficiencyAnalysis() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [efficiencyData, setEfficiencyData] = useState(null);
  const [satisfactionData, setSatisfactionData] = useState(null);
  const [bottlenecksData, setBottlenecksData] = useState(null);
  const [slaData, setSlaData] = useState(null);

  // 筛选条件
  const [projectId, setProjectId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {};
      if (projectId) {params.project_id = parseInt(projectId);}
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}

      // 并行加载所有数据
      const [efficiencyRes, satisfactionRes, bottlenecksRes, slaRes] =
        await Promise.all([
          itrApi.getEfficiencyAnalysis(params),
          itrApi.getSatisfactionTrend(params),
          itrApi.getBottlenecksAnalysis(params),
          itrApi.getSlaAnalysis(params),
        ]);

      setEfficiencyData(efficiencyRes.data?.data || efficiencyRes.data);
      setSatisfactionData(satisfactionRes.data?.data || satisfactionRes.data);
      setBottlenecksData(bottlenecksRes.data?.data || bottlenecksRes.data);
      setSlaData(slaRes.data?.data || slaRes.data);
    } catch (err) {
      console.error("Failed to load ITR efficiency data:", err);
      setError(err.response?.data?.detail || err.message || "加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 处理筛选
  const handleFilter = () => {
    loadData();
  };

  // 重置筛选
  const handleReset = () => {
    setProjectId("");
    setStartDate("");
    setEndDate("");
    setTimeout(() => {
      loadData();
    }, 100);
  };

  // 准备图表数据
  const prepareResolutionTimeChart = () => {
    if (!efficiencyData?.resolution_time) {return null;}

    const data = efficiencyData.resolution_time;
    return {
      labels: data.time_distribution?.map((item) => item.range) || [],
      datasets: [
        {
          label: "问题数量",
          data: data.time_distribution?.map((item) => item.count) || [],
        },
      ],
    };
  };

  const prepareSatisfactionChart = () => {
    if (!satisfactionData?.trend) {return null;}

    const trend = satisfactionData.trend || [];
    return {
      labels: (trend || []).map((item) => item.period) || [],
      datasets: [
        {
          label: "满意度",
          data: (trend || []).map((item) => item.avg_satisfaction) || [],
        },
      ],
    };
  };

  const prepareBottlenecksChart = () => {
    if (!bottlenecksData?.bottlenecks) {return null;}

    const bottlenecks = bottlenecksData.bottlenecks || [];
    return {
      labels: (bottlenecks || []).map((item) => item.stage) || [],
      datasets: [
        {
          label: "平均耗时(小时)",
          data: (bottlenecks || []).map((item) => item.avg_duration) || [],
        },
      ],
    };
  };

  return (
    <div className="space-y-6">
      {/* 筛选条件 */}
      <Card className="bg-surface-50 border-white/5">
        <CardHeader>
          <CardTitle className="text-white">筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">
                项目ID
              </label>
              <Input
                type="number"
                placeholder="项目ID（可选）"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">
                开始日期
              </label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">
                结束日期
              </label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div className="flex items-end gap-2">
              <Button
                onClick={handleFilter}
                className="bg-primary hover:bg-primary/90"
              >
                查询
              </Button>
              <Button
                onClick={handleReset}
                variant="outline"
                className="border-white/10"
              >
                重置
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 加载状态 */}
      {loading && (
        <Card className="bg-surface-50 border-white/5">
          <CardContent className="p-8 text-center">
            <div className="text-slate-400">加载中...</div>
          </CardContent>
        </Card>
      )}

      {/* 错误状态 */}
      {error && !loading && (
        <Card className="bg-red-500/10 border-red-500/30">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="font-semibold text-red-400 mb-1">加载失败</div>
                <div className="text-sm text-red-300 mb-3">{error}</div>
                <Button
                  onClick={loadData}
                  variant="outline"
                  size="sm"
                  className="border-red-500/30 text-red-400 hover:bg-red-500/20"
                >
                  重试
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 数据展示 */}
      {!loading && !error && (
        <div className="space-y-6">
          {/* 关键指标卡片 */}
          {efficiencyData && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="bg-surface-50 border-white/5">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        平均解决时间
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {efficiencyData.resolution_time?.avg_hours
                          ? `${Math.round(
                              efficiencyData.resolution_time.avg_hours
                            )} 小时`
                          : "-"}
                      </div>
                    </div>
                    <Clock className="w-8 h-8 text-blue-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-surface-50 border-white/5">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        最快解决时间
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {efficiencyData.resolution_time?.min_hours
                          ? `${Math.round(
                              efficiencyData.resolution_time.min_hours
                            )} 小时`
                          : "-"}
                      </div>
                    </div>
                    <TrendingUp className="w-8 h-8 text-green-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-surface-50 border-white/5">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        最慢解决时间
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {efficiencyData.resolution_time?.max_hours
                          ? `${Math.round(
                              efficiencyData.resolution_time.max_hours
                            )} 小时`
                          : "-"}
                      </div>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-orange-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-surface-50 border-white/5">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        总问题数
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {efficiencyData.resolution_time?.total_count || 0}
                      </div>
                    </div>
                    <BarChart3 className="w-8 h-8 text-purple-400" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 解决时间分布 */}
          {efficiencyData?.resolution_time && (
            <Card className="bg-surface-50 border-white/5">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  问题解决时间分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                {prepareResolutionTimeChart() ? (
                  <SimpleBarChart
                    data={prepareResolutionTimeChart()}
                    height={300}
                  />
                ) : (
                  <div className="text-slate-400 text-center py-8">
                    暂无数据
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 满意度趋势 */}
          {satisfactionData && (
            <Card className="bg-surface-50 border-white/5">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  客户满意度趋势
                </CardTitle>
              </CardHeader>
              <CardContent>
                {prepareSatisfactionChart() ? (
                  <SimpleLineChart
                    data={prepareSatisfactionChart()}
                    height={300}
                  />
                ) : (
                  <div className="text-slate-400 text-center py-8">
                    暂无数据
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 流程瓶颈 */}
          {bottlenecksData?.bottlenecks && (
            <Card className="bg-surface-50 border-white/5">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  流程瓶颈识别
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {bottlenecksData.bottlenecks?.length > 0 ? (
                    <>
                      {prepareBottlenecksChart() && (
                        <SimpleBarChart
                          data={prepareBottlenecksChart()}
                          height={300}
                        />
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        {(bottlenecksData.bottlenecks || []).map((bottleneck, idx) => (
                          <div
                            key={idx}
                            className="p-4 bg-surface-100 rounded-lg border border-white/10"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-semibold text-white">
                                {bottleneck.stage}
                              </span>
                              <Badge
                                className={
                                  bottleneck.avg_duration > 48
                                    ? "bg-red-500/20 text-red-400"
                                    : bottleneck.avg_duration > 24
                                    ? "bg-orange-500/20 text-orange-400"
                                    : "bg-yellow-500/20 text-yellow-400"
                                }
                              >
                                {Math.round(bottleneck.avg_duration)} 小时
                              </Badge>
                            </div>
                            <div className="text-sm text-slate-400">
                              平均耗时: {Math.round(bottleneck.avg_duration)}{" "}
                              小时
                            </div>
                            <div className="text-sm text-slate-400">
                              问题数量: {bottleneck.issue_count || 0}
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="text-slate-400 text-center py-8">
                      暂无瓶颈数据
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* SLA性能 */}
          {slaData && (
            <Card className="bg-surface-50 border-white/5">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" />
                  SLA性能分析
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-surface-100 rounded-lg border border-white/10">
                    <div className="text-sm text-slate-400 mb-1">SLA达成率</div>
                    <div className="text-2xl font-bold text-white">
                      {slaData.achievement_rate
                        ? `${(slaData.achievement_rate * 100).toFixed(1)}%`
                        : "-"}
                    </div>
                  </div>
                  <div className="p-4 bg-surface-100 rounded-lg border border-white/10">
                    <div className="text-sm text-slate-400 mb-1">
                      符合SLA数量
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {slaData.compliant_count || 0}
                    </div>
                  </div>
                  <div className="p-4 bg-surface-100 rounded-lg border border-white/10">
                    <div className="text-sm text-slate-400 mb-1">
                      违反SLA数量
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {slaData.violation_count || 0}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
