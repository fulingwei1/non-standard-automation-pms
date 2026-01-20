import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui";
import { formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function TeamInsightsCard({ teamInsights }) {
  if (!teamInsights) return null;

  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <Activity className="h-5 w-5 text-cyan-400" />
            团队行为洞察
          </CardTitle>
          <p className="text-sm text-slate-400">
            跟进动作 · 线索质量 · 管道健康
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-300">
            <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-400 mb-2">跟进行为</p>
              <p className="text-2xl font-semibold text-white">
                {teamInsights.followUps.total} 次
              </p>
              <div className="mt-2 space-y-1 text-xs">
                <p>电话沟通：{teamInsights.followUps.call}</p>
                <p>拜访次数：{teamInsights.followUps.visit}</p>
                <p>
                  会议/邮件：
                  {teamInsights.followUps.meeting + teamInsights.followUps.email}
                </p>
              </div>
            </div>
            <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-400 mb-2">线索质量</p>
              <p className="text-2xl font-semibold text-white">
                {teamInsights.leadQuality.totalLeads} 个线索
              </p>
              <div className="mt-2 space-y-1 text-xs">
                <p>线索成功率：{teamInsights.leadQuality.conversionRate}%</p>
                <p>建模覆盖率：{teamInsights.leadQuality.modelingRate}%</p>
                <p>
                  信息完整度：{teamInsights.leadQuality.avgCompleteness} 分
                </p>
              </div>
            </div>
            <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-400 mb-2">销售管道</p>
              <p className="text-2xl font-semibold text-white">
                {formatCurrency(teamInsights.pipeline.pipelineAmount || 0)}
              </p>
              <div className="mt-2 space-y-1 text-xs">
                <p>平均毛利率：{teamInsights.pipeline.avgMargin || 0}%</p>
                <p>
                  在谈商机：
                  {teamInsights.pipeline.opportunityCount} 个
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
