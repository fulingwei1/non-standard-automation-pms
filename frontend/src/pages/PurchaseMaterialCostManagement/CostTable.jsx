/**
 * Cost List Table Component
 */



import { formatCurrency, formatDate } from "../../lib/utils";

export default function CostTable({
  filteredCosts,
  loading,
  onEdit,
  onDelete,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>成本清单</CardTitle>
        <CardDescription>共 {filteredCosts.length} 条记录</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>物料名称</TableHead>
              <TableHead>规格型号</TableHead>
              <TableHead>物料类型</TableHead>
              <TableHead>单位成本</TableHead>
              <TableHead>供应商</TableHead>
              <TableHead>采购日期</TableHead>
              <TableHead>优先级</TableHead>
              <TableHead>使用次数</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(filteredCosts || []).map((cost) => (
              <TableRow key={cost.id}>
                <TableCell>
                  <div>
                    <div className="font-medium">{cost.material_name}</div>
                    {cost.material_code && (
                      <div className="text-xs text-slate-400">
                        {cost.material_code}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>{cost.specification || "-"}</TableCell>
                <TableCell>
                  <Badge variant="outline">{cost.material_type || "-"}</Badge>
                </TableCell>
                <TableCell className="font-medium">
                  {formatCurrency(cost.unit_cost || 0)}
                </TableCell>
                <TableCell>{cost.supplier_name || "-"}</TableCell>
                <TableCell>
                  {cost.purchase_date ? formatDate(cost.purchase_date) : "-"}
                </TableCell>
                <TableCell>
                  <Badge
                    className={
                      cost.match_priority > 0 ? "bg-blue-500" : "bg-slate-500"
                    }
                  >
                    {cost.match_priority}
                  </Badge>
                </TableCell>
                <TableCell>{cost.usage_count || 0}</TableCell>
                <TableCell>
                  <Badge
                    className={
                      cost.is_active ? "bg-green-500" : "bg-slate-500"
                    }
                  >
                    {cost.is_active ? "启用" : "禁用"}
                  </Badge>
                  {cost.is_standard_part && (
                    <Badge className="ml-2 bg-purple-500">标准件</Badge>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onEdit(cost)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onDelete(cost)}
                      className="text-red-400"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {filteredCosts.length === 0 && !loading && (
          <div className="text-center py-12 text-slate-400">
            暂无成本记录，点击"新增成本"添加第一条记录
          </div>
        )}
      </CardContent>
    </Card>
  );
}
