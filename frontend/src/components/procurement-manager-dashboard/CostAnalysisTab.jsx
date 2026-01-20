import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Progress,
} from "../../components/ui";
import { BarChart3, PieChart, Target } from "lucide-react";
import { formatCurrency } from "../../lib/utils";
import { mockCostAnalysis } from "./constants";

export default function CostAnalysisTab() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-surface-50 border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              月度采购趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockCostAnalysis.monthlyTrend.map((item, index) => (
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
                    value={
                      (item.amount /
                        mockCostAnalysis.monthlyTrend[
                          mockCostAnalysis.monthlyTrend.length - 1
                        ].amount) *
                      100
                    }
                    className="h-2"
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-50 border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-primary" />
              类别分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockCostAnalysis.categoryDistribution.map(
                (item, index) => (
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
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <Progress value={item.percentage} className="h-2" />
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-surface-50 border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            项目采购TOP3
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockCostAnalysis.topProjects.map((project, index) => (
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
                      {project.percentage}%
                    </p>
                  </div>
                </div>
                <span className="text-lg font-semibold text-amber-400">
                  {formatCurrency(project.amount)}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
