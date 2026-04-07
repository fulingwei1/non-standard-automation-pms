

import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { stages } from "./constants";

export default function Overview({ funnelData, maxCount, handleStageClick }) {
  return (
    <div className="space-y-6">
      {/* 漏斗可视化 */}
      <Card>
        <CardHeader>
          <CardTitle>销售漏斗分析</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(funnelData || []).map((data, index) => {
              const stageConfig = (stages || []).find((s) => s.key === data.stage) || stages[0];
              const width = (data.count / maxCount) * 100;
              const prevData = index > 0 ? funnelData[index - 1] : null;
              const dropRate =
                prevData && prevData.count > 0 ? (((prevData.count - data.count) / prevData.count) * 100).toFixed(1) : 0;
              const conversionRate = parseFloat(data.conversion) || 0;

              return (
                <motion.div
                  key={data.stage}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handleStageClick(data.stage)}
                  className="space-y-2 cursor-pointer hover:bg-surface-50/50 p-3 rounded-lg transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge
                        variant="outline"
                        className={cn(
                          `bg-${stageConfig.color}-500/10`,
                          `border-${stageConfig.color}-500/30`,
                          `text-${stageConfig.color}-400`
                        )}
                      >
                        {data.label || stageConfig.label}
                      </Badge>
                      <span className="text-white font-medium">{data.count}个</span>
                      {data.value > 0 && <span className="text-slate-400 text-sm">¥{(data.value / 10000).toFixed(0)}万</span>}
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-slate-400">
                        转化率: <span className="text-white">{conversionRate}%</span>
                      </span>
                      {prevData && dropRate > 0 && (
                        <span className={cn("flex items-center gap-1", dropRate > 50 ? "text-red-400" : "text-slate-400")}>
                          {dropRate > 50 ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
                          流失 {dropRate}%
                        </span>
                      )}
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                    </div>
                  </div>
                  <div className="relative">
                    <Progress value={width || 0} className={cn(`bg-${stageConfig.color}-500/20`)} />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 统计指标 */}
      <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">总线索数</p>
                  <p className="text-2xl font-bold text-white">{funnelData[0]?.count || 0}</p>
                </div>
                <Target className="w-8 h-8 text-blue-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">签约数</p>
                  <p className="text-2xl font-bold text-emerald-400">{funnelData[funnelData.length - 1]?.count || 0}</p>
                </div>
                <Users className="w-8 h-8 text-emerald-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">总签约额</p>
                  <p className="text-2xl font-bold text-purple-400">
                    ¥{((funnelData || []).reduce((sum, d) => sum + (d.value || 0), 0) / 10000).toFixed(0)}万
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-purple-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">整体转化率</p>
                  <p className="text-2xl font-bold text-amber-400">
                    {funnelData.length > 0 && funnelData[0].count > 0
                      ? ((funnelData[funnelData.length - 1].count / funnelData[0].count) * 100).toFixed(1)
                      : 0}
                    %
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-amber-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
}
