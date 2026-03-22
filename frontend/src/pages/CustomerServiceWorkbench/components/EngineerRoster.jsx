/**
 * 客服工作台 - 工程师画像列表（左侧面板）
 */

import { UserRound } from "lucide-react";

import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  EmptyState,
} from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { TEAM_OVERVIEW_KEY } from "../constants";

export function EngineerRoster({
  engineers,
  selectedKey,
  onSelect,
  canViewTeam,
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>工程师画像</CardTitle>
        <CardDescription>
          经理可以先看团队总览，再切换到单个售后工程师。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {canViewTeam ? (
          <button
            type="button"
            onClick={() => onSelect(TEAM_OVERVIEW_KEY)}
            className={cn(
              "w-full rounded-2xl border px-4 py-3 text-left transition-all",
              selectedKey === TEAM_OVERVIEW_KEY
                ? "border-cyan-400/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/10"
                : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]",
            )}
          >
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-white">团队总览</div>
                <div className="mt-1 text-xs text-slate-400">
                  查看全部工程师、全部工单和全部项目情况
                </div>
              </div>
              <Badge variant="info">总览</Badge>
            </div>
          </button>
        ) : null}

        {engineers.length === 0 ? (
          <EmptyState
            icon={UserRound}
            title="暂无工程师数据"
            message="当前还没有可展示的售后工程师数据。"
          />
        ) : (
          <div className="space-y-3">
            {engineers.map((engineer) => (
              <button
                key={engineer.key}
                type="button"
                onClick={() => onSelect(engineer.key)}
                className={cn(
                  "w-full rounded-2xl border px-4 py-3 text-left transition-all",
                  selectedKey === engineer.key
                    ? "border-violet-400/50 bg-violet-500/10 shadow-lg shadow-violet-500/10"
                    : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-sm font-semibold text-white">
                        {(engineer.name || "?").slice(0, 1)}
                      </div>
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-white">
                          {engineer.name}
                        </div>
                        <div className="truncate text-xs text-slate-400">
                          {engineer.position || engineer.department || "售后服务工程师"}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300">
                      <Badge variant="secondary">项目 {engineer.projectCount}</Badge>
                      <Badge variant="warning">待办 {engineer.activeLoad}</Badge>
                      <Badge variant="outline">工单 {engineer.ticketCount}</Badge>
                    </div>
                  </div>
                  {engineer.openTicketCount > 0 ? (
                    <Badge variant="danger">{engineer.openTicketCount} 待跟进</Badge>
                  ) : (
                    <Badge variant="success">可响应</Badge>
                  )}
                </div>
                {engineer.primaryProjectName ? (
                  <div className="mt-3 text-xs text-slate-400">
                    当前重点项目: {engineer.primaryProjectName}
                  </div>
                ) : (
                  <div className="mt-3 text-xs text-slate-500">当前暂无关联项目</div>
                )}
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
