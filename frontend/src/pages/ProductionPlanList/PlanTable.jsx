



import { formatDate } from "../../lib/utils";
import { statusConfigs, typeConfigs } from "./constants";

export default function PlanTable({ loading, filteredPlans, onViewDetail, onPublish }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>生产计划列表</CardTitle>
        <CardDescription>共 {filteredPlans.length} 个生产计划</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredPlans.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无生产计划</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>计划编号</TableHead>
                <TableHead>计划名称</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>项目</TableHead>
                <TableHead>车间</TableHead>
                <TableHead>计划日期</TableHead>
                <TableHead>进度</TableHead>
                <TableHead>状态</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(filteredPlans || []).map((plan) => (
                <TableRow key={plan.id}>
                  <TableCell className="font-mono text-sm">{plan.plan_no}</TableCell>
                  <TableCell className="font-medium">{plan.plan_name}</TableCell>
                  <TableCell>
                    <Badge className={typeConfigs[plan.plan_type]?.color || "bg-slate-500"}>
                      {typeConfigs[plan.plan_type]?.label || plan.plan_type}
                    </Badge>
                  </TableCell>
                  <TableCell>{plan.project_name || "-"}</TableCell>
                  <TableCell>{plan.workshop_name || "-"}</TableCell>
                  <TableCell className="text-slate-500 text-sm">
                    {plan.plan_start_date ? formatDate(plan.plan_start_date) : "-"}
                    {plan.plan_end_date && (
                      <>
                        <span className="mx-1">-</span>
                        {formatDate(plan.plan_end_date)}
                      </>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span>{plan.progress || 0}%</span>
                      </div>
                      <Progress value={plan.progress || 0} className="h-1.5" />
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={statusConfigs[plan.status]?.color || "bg-slate-500"}>
                      {statusConfigs[plan.status]?.label || plan.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(plan.id)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      {plan.status === "APPROVED" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onPublish(plan.id)}
                        >
                          <CheckCircle2 className="w-4 h-4" />
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
