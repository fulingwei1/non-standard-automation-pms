/**
 * 健康度评分卡组件
 * 展示战略整体健康度评分和等级
 */
import { motion } from "framer-motion";
import { Activity, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Progress } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import { getStrategyHealthConfig, HEALTH_LEVELS } from "../../../lib/constants/strategy";

export function HealthScoreCard({ healthStats }) {
  if (!healthStats) {
    return (
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50 h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="w-5 h-5 text-primary" />
            战略健康度
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-500">
            暂无健康度数据
          </div>
        </CardContent>
      </Card>
    );
  }

  const { overall, dimensions, trend } = healthStats;
  const healthConfig = getStrategyHealthConfig(overall?.level);
  const Icon = healthConfig?.icon || Activity;

  // 计算趋势
  const getTrendIcon = () => {
    if (!trend || trend.length < 2) return <Minus className="w-4 h-4 text-slate-400" />;
    const latest = trend[trend.length - 1]?.score || 0;
    const previous = trend[trend.length - 2]?.score || 0;
    const diff = latest - previous;
    if (diff > 0) return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    if (diff < 0) return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  return (
    <motion.div variants={fadeIn} className="h-full">
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50 h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="w-5 h-5 text-primary" />
            战略健康度
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 整体评分 */}
          <div className="text-center">
            <div className="relative inline-flex items-center justify-center w-32 h-32">
              {/* 背景圆环 */}
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  className="text-slate-700"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke={healthConfig?.color || "#1890ff"}
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={`${(overall?.score || 0) * 3.52} 352`}
                  strokeLinecap="round"
                  className="transition-all duration-1000"
                />
              </svg>
              {/* 中心分数 */}
              <div className="absolute flex flex-col items-center">
                <span
                  className="text-3xl font-bold"
                  style={{ color: healthConfig?.color || "#1890ff" }}
                >
                  {(overall?.score || 0).toFixed(0)}
                </span>
                <span className="text-xs text-slate-400">分</span>
              </div>
            </div>

            {/* 等级标签 */}
            <div className="mt-4 flex items-center justify-center gap-2">
              <div
                className={cn(
                  "px-3 py-1 rounded-full flex items-center gap-1",
                  healthConfig?.bgColor || "bg-blue-100"
                )}
              >
                <Icon className="w-4 h-4" style={{ color: healthConfig?.color }} />
                <span
                  className="text-sm font-medium"
                  style={{ color: healthConfig?.color }}
                >
                  {healthConfig?.label || "未知"}
                </span>
              </div>
              {getTrendIcon()}
            </div>
          </div>

          {/* 等级说明 */}
          <div className="space-y-2 pt-4 border-t border-slate-700/50">
            <p className="text-xs text-slate-400 text-center">健康度等级说明</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {Object.entries(HEALTH_LEVELS).map(([key, config]) => (
                <div
                  key={key}
                  className={cn(
                    "flex items-center gap-1 px-2 py-1 rounded",
                    overall?.level === key ? config.bgColor : "bg-slate-800/50"
                  )}
                >
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: config.color }}
                  />
                  <span className={overall?.level === key ? config.textColor : "text-slate-500"}>
                    {config.label} {config.range}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 维度简要 */}
          {dimensions && dimensions.length > 0 && (
            <div className="space-y-2 pt-4 border-t border-slate-700/50">
              <p className="text-xs text-slate-400">各维度健康度</p>
              <div className="space-y-2">
                {dimensions.map((d) => (
                  <div key={d.dimension} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{d.name}</span>
                      <span className="text-white font-medium">
                        {(d.score || 0).toFixed(1)}%
                      </span>
                    </div>
                    <Progress
                      value={d.score || 0}
                      className="h-1.5"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
