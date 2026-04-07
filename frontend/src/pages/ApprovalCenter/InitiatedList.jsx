import { FileText } from "lucide-react";

import { cn } from "../../lib/utils";
import { formatDateTime } from "@/lib/formatters";
import { STATUS_CONFIG, ENTITY_TYPE_CONFIG } from "./configMaps";

const InitiatedList = ({ items, loading, goToDetail }) => (
  <Card className="bg-slate-800/50 border-slate-700">
    <CardContent className="p-0">
      <Table>
        <TableHeader>
          <TableRow className="border-slate-700 hover:bg-slate-800/50">
            <TableHead className="text-slate-300">审批信息</TableHead>
            <TableHead className="text-slate-300">类型</TableHead>
            <TableHead className="text-slate-300">状态</TableHead>
            <TableHead className="text-slate-300">当前节点</TableHead>
            <TableHead className="text-slate-300">发起时间</TableHead>
            <TableHead className="text-slate-300">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(items || []).map((item) => {
            const statusConfig = STATUS_CONFIG[item.status] || STATUS_CONFIG.PENDING;
            const entityConfig = ENTITY_TYPE_CONFIG[item.entity_type] || {};

            return (
              <TableRow key={item.id} className="border-slate-700 hover:bg-slate-800/50">
                <TableCell>
                  <div className="space-y-1">
                    <span className="text-white font-medium block">{item.title}</span>
                    <span className="text-xs text-slate-500">{item.instance_no}</span>
                  </div>
                </TableCell>
                <TableCell>
                  {entityConfig.label && (
                    <Badge className={cn(entityConfig.color, "text-white text-xs")}>
                      {entityConfig.label}
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  <Badge className={cn(statusConfig.color, "text-white text-xs")}>
                    {statusConfig.label}
                  </Badge>
                </TableCell>
                <TableCell className="text-slate-300">
                  {item.current_node_name || "-"}
                </TableCell>
                <TableCell className="text-slate-400 text-sm">
                  {formatDateTime(item.created_at)}
                </TableCell>
                <TableCell>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 p-0"
                    onClick={() => goToDetail(item.id)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      <EmptyState
        items={items}
        loading={loading}
        icon={FileText}
        message="暂无发起的审批"
      />
    </CardContent>
  </Card>
);

export default InitiatedList;
