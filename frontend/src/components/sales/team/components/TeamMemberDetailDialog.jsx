/**
 * TeamMemberDetailDialog - 团队成员详情对话框组件
 * 显示成员的完整详细信息
 */

import { Users, TrendingUp } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Button,
  Progress,
  Badge,
} from "../../../ui";
import { formatCurrency, formatFollowUpType, formatDateTime } from "@/lib/constants/salesTeam";

export default function TeamMemberDetailDialog({
  open,
  onOpenChange,
  member,
  onNavigatePerformance,
  onNavigateCRM,
}) {
  if (!member) {return null;}

  const personalMonthly = member.personalTargets?.monthly;
  const recentFollowUp = member.recentFollowUp;
  const distribution = member.customerDistribution || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{member.name} - 详细信息</DialogTitle>
          <DialogDescription>
            查看团队成员的详细业绩和活动信息
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-400">角色</p>
              <p className="text-white font-medium">{member.role}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">部门</p>
              <p className="text-white font-medium">{member.department}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">所属区域</p>
              <p className="text-white font-medium">
                {member.region || "未分配"}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-400">邮箱</p>
              <p className="text-white font-medium">{member.email}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">电话</p>
              <p className="text-white font-medium">{member.phone}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">入职日期</p>
              <p className="text-white font-medium">{member.joinDate}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">最后活动</p>
              <p className="text-white font-medium">{member.lastActivity}</p>
            </div>
          </div>

          {/* 业绩概览 */}
          <div className="pt-4 border-t border-slate-700">
            <h4 className="text-sm font-medium text-white mb-3">业绩概览</h4>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-slate-400">本月完成</span>
                  <span className="text-white font-medium">
                    {formatCurrency(member.monthlyAchieved)} /{" "}
                    {formatCurrency(member.monthlyTarget)}
                  </span>
                </div>
                <Progress
                  value={member.achievementRate}
                  className="h-2"
                />
              </div>
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-slate-400">年度完成</span>
                  <span className="text-white font-medium">
                    {formatCurrency(member.yearAchieved)} /{" "}
                    {formatCurrency(member.yearTarget)}
                  </span>
                </div>
                <Progress
                  value={member.yearProgress}
                  className="h-2"
                />
              </div>
            </div>
          </div>

          {/* 客户洞察与跟进 */}
          <div className="pt-4 border-t border-slate-700">
            <h4 className="text-sm font-medium text-white mb-3">
              客户洞察与跟进
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {/* 个人目标完成率 */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">
                  个人目标完成率
                </p>
                {personalMonthly ? (
                  <>
                    <p className="text-white font-semibold">
                      {personalMonthly.completion_rate ?? member.achievementRate}
                      %
                    </p>
                    <p className="text-slate-500 text-xs mt-1">
                      {formatCurrency(
                        personalMonthly.actual_value || member.monthlyAchieved,
                      )}{" "}
                      /{" "}
                      {formatCurrency(
                        personalMonthly.target_value || member.monthlyTarget,
                      )}
                    </p>
                    <p className="text-slate-500 text-[11px] mt-1">
                      周期：
                      {personalMonthly.period_value || "本月"}
                    </p>
                  </>
                ) : (
                  <p className="text-slate-500 text-xs">暂无个人目标数据</p>
                )}
              </div>

              {/* 最近跟进 */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">最近跟进</p>
                {recentFollowUp ? (
                  <>
                    <p className="text-white font-semibold">
                      {recentFollowUp.leadName || "线索"} ·{" "}
                      {formatFollowUpType(recentFollowUp.followUpType)}
                    </p>
                    <p className="text-slate-500 text-xs mt-1">
                      {formatDateTime(recentFollowUp.createdAt)}
                    </p>
                    {recentFollowUp.content && (
                      <p className="text-slate-500 text-[11px] mt-1">
                        {recentFollowUp.content}
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-slate-500 text-xs">暂无跟进记录</p>
                )}
              </div>

              {/* 客户分布 */}
              <div className="md:col-span-2 bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-2">客户分布</p>
                {distribution.length ? (
                  <div className="flex flex-wrap gap-2">
                    {distribution.map((item) => (
                      <Badge
                        key={`${member.id}-${item.label}`}
                        variant="outline"
                        className="text-[11px] bg-slate-900 border-slate-700/70 text-slate-200"
                      >
                        {item.label} · {item.value} ({item.percentage}%)
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-xs">暂无客户分布数据</p>
                )}
                <p className="text-slate-500 text-[11px] mt-2">
                  客户总数：{member.customerTotal || 0}，本月新增{" "}
                  {member.newCustomers || 0}
                </p>
              </div>
            </div>
          </div>

          {/* 跟进行为与线索质量 */}
          <div className="pt-4 border-t border-slate-700">
            <h4 className="text-sm font-medium text-white mb-3">
              跟进行为与线索质量
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {/* 跟进行为统计 */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-2">跟进行为统计</p>
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                  <div>
                    电话沟通：
                    <span className="text-white font-semibold ml-1">
                      {member.followUpStats?.call || 0}
                    </span>
                  </div>
                  <div>
                    拜访次数：
                    <span className="text-white font-semibold ml-1">
                      {member.followUpStats?.visit || 0}
                    </span>
                  </div>
                  <div>
                    会议/邮件：
                    <span className="text-white font-semibold ml-1">
                      {(member.followUpStats?.meeting || 0) +
                        (member.followUpStats?.email || 0)}
                    </span>
                  </div>
                  <div>
                    总跟进：
                    <span className="text-white font-semibold ml-1">
                      {member.followUpStats?.total || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* 线索质量与商机建模 */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-2">
                  线索质量与商机建模
                </p>
                <div className="space-y-1 text-xs text-slate-400">
                  <div>
                    线索成功率：
                    <span className="text-white font-semibold ml-1">
                      {member.leadQuality?.conversionRate || 0}%
                    </span>
                  </div>
                  <div>
                    建模覆盖率：
                    <span className="text-white font-semibold ml-1">
                      {member.leadQuality?.modelingRate || 0}%
                    </span>
                  </div>
                  <div>
                    商务信息完整度：
                    <span className="text-white font-semibold ml-1">
                      {member.leadQuality?.avgCompleteness || 0} 分
                    </span>
                  </div>
                  <div>
                    在谈金额：
                    <span className="text-white font-semibold ml-1">
                      {formatCurrency(member.pipelineAmount || 0)}
                    </span>
                  </div>
                  <div>
                    平均预估毛利：
                    <span className="text-white font-semibold ml-1">
                      {member.avgEstMargin || 0}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 底部操作按钮 */}
        <DialogFooter className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              className="text-xs"
              onClick={() => onNavigatePerformance(member)}
            >
              <TrendingUp className="w-3 h-3" />
              绩效详情
            </Button>
            <Button
              variant="secondary"
              size="sm"
              className="text-xs"
              onClick={() => onNavigateCRM(member)}
            >
              <Users className="w-3 h-3" />
              CRM详情
            </Button>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              关闭
            </Button>
            <Button>编辑目标</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
