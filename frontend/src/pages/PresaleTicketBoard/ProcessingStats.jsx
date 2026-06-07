import { Timer, UserRound } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui";
import { formatDateTime } from "./utils";

export default function ProcessingStats({
  stats,
  selectedTicket,
  flowUpdatingId,
  handleAdvanceFlow,
  renderFlowActionLabel,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Timer className="h-4 w-4 text-emerald-400" />
          处理统计
        </CardTitle>
        <CardDescription>关注响应、处理、按期交付三项核心指标。</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-[1.1fr,1fr]">
        <div className="space-y-3 rounded-xl border border-slate-800/70 p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">平均响应时长</span>
            <span className="font-medium text-cyan-300">{stats.avgResponseHours.toFixed(1)}h</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">平均处理时长</span>
            <span className="font-medium text-amber-300">{stats.avgHandleHours.toFixed(1)}h</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">按期完结率</span>
            <span className="font-medium text-emerald-300">{stats.onTimeRate.toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">已接单待处理</span>
            <span className="font-medium text-blue-300">{stats.accepted + stats.inProgress} 单</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800/70 p-4">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
            <UserRound className="h-4 w-4 text-violet-400" />
            当前选中工单
          </h3>

          {selectedTicket ? (
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-medium text-white">{selectedTicket.title}</p>
                <p className="mt-1 text-xs text-slate-400">
                  {selectedTicket.ticketNo} · {selectedTicket.customerName}
                </p>
              </div>

              <p className="rounded-lg bg-slate-900/70 p-3 text-slate-300">
                {selectedTicket.description}
              </p>

              <div className="space-y-2 text-xs text-slate-400">
                <p>创建时间：{formatDateTime(selectedTicket.applyTime)}</p>
                <p>接单时间：{formatDateTime(selectedTicket.acceptTime)}</p>
                <p>完成时间：{formatDateTime(selectedTicket.completeTime)}</p>
                <p>截止时间：{formatDateTime(selectedTicket.deadline || selectedTicket.expectedDate)}</p>
              </div>

              <Button
                size="sm"
                variant={selectedTicket.status === "COMPLETED" ? "secondary" : "default"}
                disabled={
                  selectedTicket.status === "COMPLETED" ||
                  selectedTicket.status === "REVIEWING" ||
                  flowUpdatingId === selectedTicket.id
                }
                onClick={() => handleAdvanceFlow(selectedTicket)}
              >
                {renderFlowActionLabel(selectedTicket.status)}
              </Button>
            </div>
          ) : (
            <p className="text-sm text-slate-500">请选择一条工单查看详情</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
