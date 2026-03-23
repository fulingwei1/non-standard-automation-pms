/**
 * 客服工作台 - 范围摘要统计卡片
 */

import {
  AlertTriangle,
  Briefcase,
  ClipboardList,
  Wrench,
} from "lucide-react";


export function ScopeSummary({ title, description, stats }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <DashboardStatCard
        icon={Briefcase}
        label={`${title}负责项目`}
        value={stats.projectCount}
        description={description}
        iconColor="text-cyan-300"
        iconBg="bg-cyan-500/10"
      />
      <DashboardStatCard
        icon={ClipboardList}
        label="待跟进工单"
        value={stats.openTickets}
        description="待处理 / 处理中 / 待验证"
        iconColor="text-amber-300"
        iconBg="bg-amber-500/10"
      />
      <DashboardStatCard
        icon={AlertTriangle}
        label="未解决问题"
        value={stats.unresolvedIssues}
        description={`已解决 ${stats.resolvedIssues} 项`}
        iconColor="text-rose-300"
        iconBg="bg-rose-500/10"
      />
      <DashboardStatCard
        icon={Wrench}
        label="现场任务"
        value={stats.activeFieldTasks}
        description="服务记录 + 安装调试派工"
        iconColor="text-emerald-300"
        iconBg="bg-emerald-500/10"
      />
    </div>
  );
}
