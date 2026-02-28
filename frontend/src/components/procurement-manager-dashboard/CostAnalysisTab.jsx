import { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Progress,
} from "../../components/ui";
import { BarChart3, PieChart, Target, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { formatCurrency } from "../../lib/utils";
import { procurementAnalysisApi } from "../../services/api";

export default function CostAnalysisTab() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [costData, setCostData] = useState({
    monthlyTrend: [],
    categoryDistribution: [],
    topProjects: [],
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await procurementAnalysisApi.getCostTrend({
        group_by: "month",
      });

      const data = response.data?.data || response.data || {};

      // 转换后端数据格式为前端展示格式
      const monthlyTrend = (data.trend || []).map((item) => ({
        month: item.period || item.month,
        amount: item.total_amount || item.amount || 0,
      }));

      const categoryDistribution = (data.by_category || []).map((item) => ({
        category: item.category_name || item.category,
        amount: item.total_amount || item.amount || 0,
        percentage: item.percentage || 0,
      }));

      const topProjects = (data.top_projects || []).slice(0, 3).map((item) => ({
        project: item.project_name || item.project,
        amount: item.total_amount || item.amount || 0,
        percentage: item.percentage || 0,
      }));

      setCostData({
        monthlyTrend,
        categoryDistribution,
        topProjects,
      });
    } catch (err) {
      console.error("加载采购成本数据失败:", err);
      setError(err.response?.data?.detail || err.message || "加载数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 加载状态
  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 text-primary animate-spin" />
        <span className="ml-2 text-slate-400">加载采购成本数据...</span>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-slate-400">
        <AlertCircle className="w-10 h-10 mb-3 text-red-400" />
        <p className="text-sm mb-3">{error}</p>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 text-sm text-primary hover:text-primary/80 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          重新加载
        </button>
      </div>
    );
  }

  // 计算最大值用于进度条
  const maxMonthlyAmount = Math.max(...(costData.monthlyTrend || []).map(t => t.amount), 1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 月度采购趋势 */}
        <Card className="bg-surface-50 border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              月度采购趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            {costData.monthlyTrend?.length > 0 ? (
              <div className="space-y-4">
                {(costData.monthlyTrend || []).map((item, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-400">
                        {item.month}
                      </span>
                      <span className="text-sm font-semibold text-white">
                        {formatCurrency(item.amount)}
                      </span>
                    </div>
                    <Progress
                      value={(item.amount / maxMonthlyAmount) * 100}
                      className="h-2"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                暂无趋势数据
              </div>
            )}
          </CardContent>
        </Card>

        {/* 类别分布 */}
        <Card className="bg-surface-50 border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-primary" />
              类别分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            {costData.categoryDistribution?.length > 0 ? (
              <div className="space-y-4">
                {(costData.categoryDistribution || []).map((item, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-400">
                        {item.category}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">
                          {formatCurrency(item.amount)}
                        </span>
                        <span className="text-xs text-slate-500">
                          {item.percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <Progress value={item.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                暂无分类数据
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 项目采购 TOP3 */}
      <Card className="bg-surface-50 border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            项目采购TOP3
          </CardTitle>
        </CardHeader>
        <CardContent>
          {costData.topProjects?.length > 0 ? (
            <div className="space-y-4">
              {(costData.topProjects || []).map((project, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 rounded-lg bg-surface-100 border border-white/5"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                      <span className="text-sm font-bold text-white">
                        {index + 1}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">
                        {project.project}
                      </p>
                      <p className="text-xs text-slate-400">
                        {project.percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <span className="text-lg font-semibold text-amber-400">
                    {formatCurrency(project.amount)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              暂无项目数据
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
