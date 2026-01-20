import { motion } from "framer-motion";
import { Users, ChevronRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress
} from "../../components/ui";
import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function TeamPerformanceCard({ teamMembers }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-5 w-5 text-purple-400" />
              团队成员业绩
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-xs text-primary">
              查看详情 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {teamMembers && teamMembers.length > 0 ? (
            <div className="space-y-4">
              {teamMembers.map((member, index) => (
                <div
                  key={member.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm",
                          index === 0 &&
                            "bg-gradient-to-br from-amber-500 to-orange-500",
                          index === 1 &&
                            "bg-gradient-to-br from-blue-500 to-cyan-500",
                          index === 2 &&
                            "bg-gradient-to-br from-slate-500 to-gray-600",
                          index === 3 &&
                            "bg-gradient-to-br from-purple-500 to-pink-500"
                        )}
                      >
                        {index + 1}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">
                            {member.name || "N/A"}
                          </span>
                          <Badge
                            variant="outline"
                            className="text-xs bg-slate-700/40"
                          >
                            {member.role || "N/A"}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          {member.activeProjects || 0} 个项目 ·{" "}
                          {member.newCustomers || 0} 个新客户
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-white">
                        {formatCurrency(member.monthlyAchieved || 0)}
                      </div>
                      <div className="text-xs text-slate-400">
                        目标: {formatCurrency(member.monthlyTarget || 0)}
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">完成率</span>
                      <span
                        className={cn(
                          "font-medium",
                          (member.achievementRate || 0) >= 90
                            ? "text-emerald-400"
                            : (member.achievementRate || 0) >= 70
                            ? "text-amber-400"
                            : "text-red-400"
                        )}
                      >
                        {member.achievementRate || 0}%
                      </span>
                    </div>
                    <Progress
                      value={member.achievementRate || 0}
                      className="h-1.5 bg-slate-700/50"
                    />

                    <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                      <div>电话：{member.followUpStats?.call || 0}</div>
                      <div>拜访：{member.followUpStats?.visit || 0}</div>
                      <div>
                        会议/邮件：
                        {(member.followUpStats?.meeting || 0) +
                          (member.followUpStats?.email || 0)}
                      </div>
                      <div>
                        线索成功率：
                        {member.leadQuality?.conversionRate || 0}%
                      </div>
                      <div>
                        建模覆盖率：
                        {member.leadQuality?.modelingRate || 0}%
                      </div>
                      <div>
                        信息完整度：
                        {member.leadQuality?.avgCompleteness || 0} 分
                      </div>
                      <div>
                        在谈金额：
                        {formatCurrency(member.pipelineAmount || 0)}
                      </div>
                      <div>平均毛利率：{member.avgEstMargin || 0}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>团队成员数据需要从API获取</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
