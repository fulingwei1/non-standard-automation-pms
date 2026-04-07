import { useNavigate } from "react-router-dom";




import { formatDate } from "../../lib/utils";
import { statusConfigs, priorityConfigs } from "./statusConstants";

export default function WorkOrderTable({
  loading,
  filteredOrders,
  setSelectedOrder,
  setShowAssignDialog,
}) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <CardTitle>工单列表</CardTitle>
        <CardDescription>共 {filteredOrders.length} 个工单</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredOrders.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无工单</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>工单号</TableHead>
                <TableHead>任务名称</TableHead>
                <TableHead>项目</TableHead>
                <TableHead>物料</TableHead>
                <TableHead>计划数量</TableHead>
                <TableHead>完成数量</TableHead>
                <TableHead>进度</TableHead>
                <TableHead>优先级</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>计划日期</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(filteredOrders || []).map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-mono text-sm">
                    {order.work_order_no}
                  </TableCell>
                  <TableCell className="font-medium">
                    {order.task_name}
                  </TableCell>
                  <TableCell>{order.project_name || "-"}</TableCell>
                  <TableCell>
                    {order.material_name || "-"}
                    {order.specification && (
                      <div className="text-xs text-slate-500">
                        {order.specification}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>{order.plan_qty || 0}</TableCell>
                  <TableCell className="font-medium">
                    {order.completed_qty || 0}
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span>{order.progress || 0}%</span>
                      </div>
                      <Progress value={order.progress || 0} className="h-1.5" />
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        priorityConfigs[order.priority]?.color || "bg-slate-500"
                      }
                    >
                      {priorityConfigs[order.priority]?.label || order.priority}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        statusConfigs[order.status]?.color || "bg-slate-500"
                      }
                    >
                      {statusConfigs[order.status]?.label || order.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-500 text-sm">
                    {order.plan_start_date
                      ? formatDate(order.plan_start_date)
                      : "-"}
                    {order.plan_end_date && (
                      <>
                        <span className="mx-1">-</span>
                        {formatDate(order.plan_end_date)}
                      </>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/work-orders/${order.id}`)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      {order.status === "PENDING" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedOrder(order);
                            setShowAssignDialog(true);
                          }}
                        >
                          <User className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
