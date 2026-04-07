



import { cn } from "../../lib/utils";
import { BOARD_STATUS_ORDER, PRIORITY_CONFIG, STATUS_CONFIG } from "./constants";
import { formatDate } from "./utils";

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
              <TableHead>处理人</TableHead>
              <TableHead>截止时间</TableHead>
              <TableHead className="text-right">流转</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTickets.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="py-10 text-center text-slate-400">
                  当前筛选下暂无工单
                </TableCell>
              </TableRow>
            )}

            {filteredTickets.map((ticket) => {
              const statusConfig = STATUS_CONFIG[ticket.status];
              const priorityConfig = PRIORITY_CONFIG[ticket.priority];
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
                      disabled={ticket.status === "COMPLETED" || flowUpdatingId === ticket.id}
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
