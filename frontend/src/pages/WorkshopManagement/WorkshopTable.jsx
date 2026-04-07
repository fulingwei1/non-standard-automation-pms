import { useNavigate } from "react-router-dom";




import { typeConfigs } from "./constants";

export function WorkshopTable({
  loading,
  filteredWorkshops,
  onViewDetail,
  onEditClick,
}) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <CardTitle>车间列表</CardTitle>
        <CardDescription>共 {filteredWorkshops.length} 个车间</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredWorkshops.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无车间</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>车间编码</TableHead>
                <TableHead>车间名称</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>主管</TableHead>
                <TableHead>位置</TableHead>
                <TableHead>产能（小时）</TableHead>
                <TableHead>状态</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredWorkshops.map((workshop) => (
                <TableRow key={workshop.id}>
                  <TableCell className="font-mono text-sm">
                    {workshop.workshop_code}
                  </TableCell>
                  <TableCell className="font-medium">
                    {workshop.workshop_name}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        typeConfigs[workshop.workshop_type]?.color ||
                        "bg-slate-500"
                      }
                    >
                      {typeConfigs[workshop.workshop_type]?.label ||
                        workshop.workshop_type}
                    </Badge>
                  </TableCell>
                  <TableCell>{workshop.manager_name || "-"}</TableCell>
                  <TableCell>{workshop.location || "-"}</TableCell>
                  <TableCell>{workshop.capacity_hours || 0}</TableCell>
                  <TableCell>
                    {workshop.is_active !== false ? (
                      <Badge className="bg-emerald-500">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        启用
                      </Badge>
                    ) : (
                      <Badge className="bg-gray-500">
                        <XCircle className="w-3 h-3 mr-1" />
                        停用
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(workshop.id)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditClick(workshop)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          navigate(`/workshops/${workshop.id}/task-board`)
                        }
                      >
                        <Wrench className="w-4 h-4" />
                      </Button>
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
