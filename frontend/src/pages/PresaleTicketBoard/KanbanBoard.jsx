import { KanbanSquare } from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { BOARD_STATUS_ORDER, STATUS_CONFIG } from "./constants";

export default function KanbanBoard({
  groupedByStatus,
  selectedTicketId,
  setSelectedTicketId,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <KanbanSquare className="h-4 w-4 text-cyan-400" />
          工单流转
        </CardTitle>
        <CardDescription>按状态查看当前排队，点击卡片可联动左侧工单列表。</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {BOARD_STATUS_ORDER.map((status) => {
            const statusConfig = STATUS_CONFIG[status];
            const columnTickets = groupedByStatus[status] || [];
            return (
              <div
                key={status}
                className="rounded-xl border border-slate-800/70 bg-slate-900/40 p-3"
              >
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                    <span className={cn("h-2 w-2 rounded-full", statusConfig.dotClass)} />
                    {statusConfig.label}
                  </div>
                  <Badge className="bg-slate-800 text-slate-200">{columnTickets.length}</Badge>
                </div>

                <div className="space-y-2">
                  {columnTickets.slice(0, 4).map((ticket) => (
                    <button
                      key={ticket.id}
                      type="button"
                      onClick={() => setSelectedTicketId(ticket.id)}
                      className={cn(
                        "w-full rounded-lg border border-slate-800 bg-slate-950/70 p-2 text-left transition hover:border-cyan-500/40",
                        selectedTicketId === ticket.id && "border-cyan-400/60",
                      )}
                    >
                      <p className="truncate text-xs font-medium text-slate-100">{ticket.title}</p>
                      <p className="mt-1 text-[11px] text-slate-400">
                        {ticket.ticketNo} · {ticket.customerName}
                      </p>
                    </button>
                  ))}

                  {columnTickets.length > 4 && (
                    <p className="pt-1 text-[11px] text-slate-500">还有 {columnTickets.length - 4} 条...</p>
                  )}

                  {columnTickets.length === 0 && (
                    <p className="py-2 text-[11px] text-slate-500">暂无工单</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
