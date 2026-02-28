/**
 * TeamMemberCard - 团队成员卡片组件
 * 显示单个成员的完整信息，包括基本信息、跟进统计、业绩进度等
 */

import { Users, TrendingUp, BarChart3, MoreHorizontal, Mail, Phone, Edit } from "lucide-react";
import { Badge, Progress, Button, DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "../../../ui";
import { cn } from "../../../../lib/utils";
import { statusConfig, formatCurrency, formatFollowUpType, formatTimeAgo } from "@/lib/constants/salesTeam";

export default function TeamMemberCard({
  member,
  index,
  onViewDetail,
  onNavigatePerformance,
  onNavigateCRM,
}) {
  const status = statusConfig[member.status] || statusConfig.good;
  const avatarInitial = member.name?.[0] || member.role?.[0] || "员";
  const personalMonthly = member.personalTargets?.monthly;
  const recentFollowUp = member.recentFollowUp;
  const distribution = member.customerDistribution || [];

  return (
    <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">
      {/* 头部：头像、姓名、状态、操作菜单 */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1">
          {/* 头像 */}
          <div
            className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold",
              index === 0 && "bg-gradient-to-br from-amber-500 to-orange-500",
              index === 1 && "bg-gradient-to-br from-blue-500 to-cyan-500",
              index === 2 && "bg-gradient-to-br from-purple-500 to-pink-500",
              index >= 3 && "bg-slate-600",
            )}
          >
            {avatarInitial}
          </div>

          {/* 基本信息 */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-white">{member.name}</span>
              <Badge variant="outline" className="text-xs bg-slate-700/40">
                {member.role}
              </Badge>
              <Badge variant="outline" className={cn("text-xs", status.textColor)}>
                {status.label}
              </Badge>
              <Badge variant="outline" className="text-xs text-slate-300 bg-slate-800/60">
                {member.region || "未分配"}
              </Badge>
            </div>

            {/* 业务数据 */}
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span>{member.leadCount || 0} 个线索</span>
              <span>{member.opportunityCount || 0} 个商机</span>
              <span>{member.contractCount || 0} 个合同</span>
              {member.activeProjects > 0 && (
                <span>{member.activeProjects} 个项目</span>
              )}
            </div>
          </div>
        </div>

        {/* 右侧业绩显示 */}
        <div className="text-right mr-4">
          <div className="text-lg font-bold text-white">
            {formatCurrency(member.monthlyAchieved)}
          </div>
          <div className="text-xs text-slate-400">
            目标: {formatCurrency(member.monthlyTarget)}
          </div>
        </div>

        {/* 操作菜单 */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onViewDetail(member)}>
              <BarChart3 className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onNavigatePerformance(member)}>
              <TrendingUp className="w-4 h-4 mr-2" />
              跳转绩效
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onNavigateCRM(member)}>
              <Users className="w-4 h-4 mr-2" />
              打开CRM
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑目标
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Mail className="w-4 h-4 mr-2" />
              发送邮件
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Phone className="w-4 h-4 mr-2" />
              拨打电话
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* 跟进统计网格 */}
      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] text-slate-400">
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>电话沟通</p>
          <p className="text-white text-sm font-semibold">
            {member.followUpStats.call || 0}
          </p>
        </div>
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>拜访记录</p>
          <p className="text-white text-sm font-semibold">
            {member.followUpStats.visit || 0}
          </p>
        </div>
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>会议/邮件</p>
          <p className="text-white text-sm font-semibold">
            {(member.followUpStats.meeting || 0) + (member.followUpStats.email || 0)}
          </p>
        </div>
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>线索成功率</p>
          <p className="text-white text-sm font-semibold">
            {member.leadQuality.conversionRate || 0}%
          </p>
        </div>
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>建模覆盖率</p>
          <p className="text-white text-sm font-semibold">
            {member.leadQuality.modelingRate || 0}%
          </p>
        </div>
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>信息完整度</p>
          <p className="text-white text-sm font-semibold">
            {member.leadQuality.avgCompleteness || 0} 分
          </p>
        </div>
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>在谈金额</p>
          <p className="text-white text-sm font-semibold">
            {formatCurrency(member.pipelineAmount || 0)}
          </p>
        </div>
        <div className="bg-slate-900/30 rounded-md p-2 border border-slate-800/60">
          <p>平均毛利率</p>
          <p className="text-white text-sm font-semibold">
            {member.avgEstMargin || 0}%
          </p>
        </div>
      </div>

      {/* 业绩进度条 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">本月完成率</span>
          <span
            className={cn(
              "font-medium",
              member.achievementRate >= 90
                ? "text-emerald-400"
                : member.achievementRate >= 70
                  ? "text-amber-400"
                  : "text-red-400",
            )}
          >
            {member.achievementRate}%
          </span>
        </div>
        <Progress
          value={member.achievementRate}
          className="h-1.5 bg-slate-700/50"
        />
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">年度进度</span>
          <span className="text-slate-400">
            {formatCurrency(member.yearAchieved)} /{" "}
            {formatCurrency(member.yearTarget)}
          </span>
        </div>
        <Progress
          value={member.yearProgress}
          className="h-1.5 bg-slate-700/50"
        />
      </div>

      {/* 快捷操作按钮 */}
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          className="text-xs"
          onClick={() => onNavigatePerformance(member)}
        >
          <TrendingUp className="w-3 h-3" />
          绩效分析
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="text-xs"
          onClick={() => onNavigateCRM(member)}
        >
          <Users className="w-3 h-3" />
          CRM客户
        </Button>
      </div>

      {/* 详细信息网格 */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-400">
        {/* 个人目标完成率 */}
        <div className="bg-slate-900/30 rounded-md p-3 border border-slate-800/60">
          <p className="mb-1">个人目标完成率</p>
          {personalMonthly ? (
            <>
              <p className="text-sm font-semibold text-white">
                {personalMonthly.completion_rate ?? member.achievementRate}
                %
              </p>
              <p className="text-slate-500 mt-1">
                {formatCurrency(
                  personalMonthly.actual_value || member.monthlyAchieved,
                )}{" "}
                /{" "}
                {formatCurrency(
                  personalMonthly.target_value || member.monthlyTarget,
                )}
              </p>
              <p className="text-slate-500 text-[11px]">
                周期：{personalMonthly.period_value || "本月"}
              </p>
            </>
          ) : (
            <p className="text-slate-500">暂无个人目标数据</p>
          )}
        </div>

        {/* 最近跟进 */}
        <div className="bg-slate-900/30 rounded-md p-3 border border-slate-800/60">
          <p className="mb-1">最近跟进</p>
          {recentFollowUp ? (
            <>
              <p className="text-sm font-semibold text-white">
                {recentFollowUp.leadName || "线索"} ·{" "}
                {formatFollowUpType(recentFollowUp.followUpType)}
              </p>
              <p className="text-slate-500 mt-1">
                {formatTimeAgo(recentFollowUp.createdAt)}
              </p>
              {recentFollowUp.content && (
                <p className="text-slate-500 text-[11px] mt-1 truncate">
                  {recentFollowUp.content}
                </p>
              )}
            </>
          ) : (
            <p className="text-slate-500">暂无跟进记录</p>
          )}
        </div>

        {/* 客户分布 */}
        <div className="bg-slate-900/30 rounded-md p-3 border border-slate-800/60">
          <p className="mb-1">客户分布</p>
          {distribution.length ? (
            <div className="flex flex-wrap gap-1">
              {distribution.slice(0, 3).map((item) => (
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
            <p className="text-slate-500">暂无客户分布数据</p>
          )}
          <p className="text-slate-500 text-[11px] mt-1">
            客户数：{member.customerTotal || 0}，本月新增{" "}
            {member.newCustomers || 0}
          </p>
        </div>
      </div>
    </div>
  );
}
