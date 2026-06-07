import {
  AlertTriangle,
  Filter,
  ListFilter,
  Search,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { BOARD_STATUS_ORDER, PRIORITY_CONFIG, STATUS_CONFIG } from "./constants";
import { formatDate } from "./utils";

function getPmRiskBadgeClass(riskLevel) {
  if (riskLevel === "高" || String(riskLevel || "").toUpperCase() === "HIGH") {
    return "bg-red-500/20 text-red-300 border border-red-500/40";
  }
  return "bg-amber-500/20 text-amber-300 border border-amber-500/40";
}

function formatRiskLevel(riskLevel) {
  if (!riskLevel) {
    return "风险待判";
  }
  if (String(riskLevel).includes("风险")) {
    return riskLevel;
  }
  return `${riskLevel}风险`;
}

export default function TicketTable({
  filteredTickets,
  searchKeyword,
  setSearchKeyword,
  statusFilter,
  setStatusFilter,
  priorityFilter,
  setPriorityFilter,
  selectedTicketId,
  setSelectedTicketId,
  priorityUpdatingId,
  flowUpdatingId,
  handlePriorityChange,
  handleAdvanceFlow,
  renderFlowActionLabel,
}) {
  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-base text-white">
          <ListFilter className="h-4 w-4 text-violet-400" />
          工单列表
        </CardTitle>
        <CardDescription>支持关键词、状态和优先级组合筛选，并可直接调整优先级。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <Input
              value={searchKeyword}
              onChange={(event) => setSearchKeyword(event.target.value)}
              placeholder="搜索工单号 / 标题 / 客户"
              className="pl-9"
            />
          </div>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger>
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-slate-500" />
                <SelectValue placeholder="全部状态" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              {BOARD_STATUS_ORDER.map((status) => (
                <SelectItem key={status} value={status}>
                  {STATUS_CONFIG[status].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={priorityFilter} onValueChange={setPriorityFilter}>
            <SelectTrigger>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-slate-500" />
                <SelectValue placeholder="全部优先级" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部优先级</SelectItem>
              {Object.entries(PRIORITY_CONFIG).map(([priority, config]) => (
                <SelectItem key={priority} value={priority}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>工单</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>优先级管理</TableHead>
              <TableHead>PM介入</TableHead>
              <TableHead>处理人</TableHead>
              <TableHead>截止时间</TableHead>
              <TableHead className="text-right">流转</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTickets.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="py-10 text-center text-slate-400">
                  当前筛选下暂无工单
                </TableCell>
              </TableRow>
            )}

            {filteredTickets.map((ticket) => {
              const statusConfig = STATUS_CONFIG[ticket.status];
              const priorityConfig = PRIORITY_CONFIG[ticket.priority];
              const riskFactors = ticket.pmInvolvementRiskFactors || [];
              return (
                <TableRow
                  key={ticket.id}
                  className={cn(
                    "cursor-pointer",
                    selectedTicketId === ticket.id && "bg-slate-800/60",
                  )}
                  onClick={() => setSelectedTicketId(ticket.id)}
                >
                  <TableCell>
                    <div className="space-y-1">
                      <p className="font-medium text-white">{ticket.title}</p>
                      <p className="text-xs text-slate-400">
                        {ticket.ticketNo} · {ticket.customerName} · {ticket.ticketTypeLabel}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={statusConfig.badgeClass}>{statusConfig.label}</Badge>
                  </TableCell>
                  <TableCell>
                    <Select
                      value={ticket.priority}
                      onValueChange={(value) => handlePriorityChange(ticket, value)}
                      disabled={priorityUpdatingId === ticket.id}
                    >
                      <SelectTrigger className="h-8 w-[120px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(PRIORITY_CONFIG).map(([priority, config]) => (
                          <SelectItem key={priority} value={priority}>
                            {config.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Badge className={cn("mt-2", priorityConfig.badgeClass)}>
                      当前：{priorityConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-2 text-xs">
                      {ticket.pmInvolvementRequired ? (
                        <>
                          <div className="flex flex-wrap gap-2">
                            <Badge className="bg-violet-500/20 text-violet-300 border border-violet-500/40">
                              需PM介入
                            </Badge>
                            <Badge className={getPmRiskBadgeClass(ticket.pmInvolvementRiskLevel)}>
                              {formatRiskLevel(ticket.pmInvolvementRiskLevel)}
                            </Badge>
                          </div>
                          {riskFactors.length > 0 && (
                            <p className="max-w-[180px] text-slate-400">
                              {riskFactors.join("、")}
                            </p>
                          )}
                          <p className={ticket.pmAssigned ? "text-emerald-300" : "text-amber-300"}>
                            {ticket.pmAssigned ? "PM已分配" : "PM未分配"}
                          </p>
                        </>
                      ) : (
                        <Badge className="bg-slate-500/20 text-slate-300 border border-slate-500/30">
                          常规跟进
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1 text-sm">
                      <p className="text-slate-200">{ticket.assigneeName}</p>
                      <p className="text-xs text-slate-500">申请：{ticket.applicantName}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1 text-sm">
                      <p className="text-slate-200">{formatDate(ticket.deadline || ticket.expectedDate)}</p>
                      <p className="text-xs text-slate-500">创建：{formatDate(ticket.applyTime)}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant={ticket.status === "COMPLETED" ? "secondary" : "outline"}
                      size="sm"
                      disabled={
                        ticket.status === "COMPLETED" ||
                        ticket.status === "REVIEWING" ||
                        flowUpdatingId === ticket.id
                      }
                      onClick={(event) => {
                        event.stopPropagation();
                        handleAdvanceFlow(ticket);
                      }}
                    >
                      {renderFlowActionLabel(ticket.status)}
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
