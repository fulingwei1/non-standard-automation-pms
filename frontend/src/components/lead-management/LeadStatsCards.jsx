import React from "react";
import { Card, CardContent } from "../../components/ui";
import {
  Target,
  TrendingUp,
  Star,
  Trophy,
  Clock,
  CheckCircle2,
  Flame,
  Thermometer,
  Snowflake,
} from "lucide-react";
import { cn } from "../../lib/utils";

// 评分颜色配置
const getScoreColor = (score) => {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-blue-400";
  if (score >= 40) return "text-amber-400";
  return "text-red-400";
};

// 资格分级配置
const qualificationConfig = {
  hot: { label: "热线索", color: "bg-red-500", textColor: "text-red-400", icon: Flame, minScore: 80 },
  warm: { label: "温线索", color: "bg-amber-500", textColor: "text-amber-400", icon: Thermometer, minScore: 60 },
  cold: { label: "冷线索", color: "bg-blue-500", textColor: "text-blue-400", icon: Snowflake, minScore: 40 },
  unqualified: { label: "待培养", color: "bg-slate-500", textColor: "text-slate-400", icon: Clock, minScore: 0 },
};

// 根据评分获取资格分级
const getQualification = (score) => {
  if (score >= 80) return "hot";
  if (score >= 60) return "warm";
  if (score >= 40) return "cold";
  return "unqualified";
};

export default function LeadStatsCards({ stats, leads = [] }) {
  // 计算扩展统计数据
  const extendedStats = React.useMemo(() => {
    const total = leads.length || stats.total || 0;
    const converted = (leads || []).filter((l) => l.status === "CONVERTED").length || stats.converted || 0;
    const qualified = (leads || []).filter((l) =>
      ["QUALIFIED", "QUALIFYING", "CONVERTED"].includes(l.status)
    ).length;

    // 计算平均评分
    const scores = (leads || []).filter((l) => l.priority_score != null).map((l) => l.priority_score);
    const avgScore = scores.length > 0 ? (scores || []).reduce((a, b) => a + b, 0) / scores.length : 0;

    // 资格分级分布
    const qualificationDist = { hot: 0, warm: 0, cold: 0, unqualified: 0 };
    (leads || []).forEach((lead) => {
      const score = lead.priority_score || 0;
      const qual = getQualification(score);
      qualificationDist[qual]++;
    });

    return {
      total,
      converted,
      qualified,
      conversionRate: total > 0 ? ((converted / total) * 100).toFixed(1) : 0,
      qualificationRate: total > 0 ? ((qualified / total) * 100).toFixed(1) : 0,
      avgScore: avgScore.toFixed(1),
      qualificationDist,
    };
  }, [leads, stats]);

  return (
    <div className="space-y-4">
      {/* 主要指标卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">线索总数</p>
                <p className="text-2xl font-bold text-white">{extendedStats.total}</p>
                <p className="text-xs text-slate-500 mt-1">
                  合格 {extendedStats.qualified} 条
                </p>
              </div>
              <Target className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">转化率</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {extendedStats.conversionRate}%
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  已转化 {extendedStats.converted} 条
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">合格率</p>
                <p className="text-2xl font-bold text-purple-400">
                  {extendedStats.qualificationRate}%
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  进入评估/转化
                </p>
              </div>
              <Star className="h-8 w-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">平均评分</p>
                <p className={cn("text-2xl font-bold", getScoreColor(parseFloat(extendedStats.avgScore)))}>
                  {extendedStats.avgScore}
                </p>
                <p className="text-xs text-slate-500 mt-1">满分 100</p>
              </div>
              <Trophy className={cn("h-8 w-8", getScoreColor(parseFloat(extendedStats.avgScore)))} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 资格分级分布 */}
      <div className="grid grid-cols-4 gap-3">
        {Object.entries(qualificationConfig).map(([key, config]) => {
          const count = extendedStats.qualificationDist[key] || 0;
          const percentage = extendedStats.total > 0
            ? ((count / extendedStats.total) * 100).toFixed(0)
            : 0;
          const Icon = config.icon;

          return (
            <Card key={key} className="bg-slate-900/50">
              <CardContent className="p-3">
                <div className="flex items-center gap-2">
                  <div className={cn("p-1.5 rounded", config.color.replace("bg-", "bg-opacity-20 bg-"))}>
                    <Icon className={cn("h-4 w-4", config.textColor)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs text-slate-400">{config.label}</span>
                      <span className={cn("text-lg font-bold", config.textColor)}>{count}</span>
                    </div>
                    <div className="mt-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all", config.color)}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
