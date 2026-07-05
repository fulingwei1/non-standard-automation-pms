import { Eye, FileText, Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";
import { cn } from "../../lib/utils";
import { formatDateTime } from "@/lib/formatters";
import { STATUS_CONFIG, ENTITY_TYPE_CONFIG } from "./configMaps";
import EmptyState from "./EmptyState";

const InitiatedList = ({ items, loading, goToDetail }) => {
  const navigate = useNavigate();
  return (
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
                  <div className="flex items-center gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      title="查看详情"
                      onClick={() => goToDetail(item.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0 text-slate-400 hover:text-white"
                      title="查看对应通知"
                      onClick={() =>
                        navigate(`/notifications?sourceType=approval&sourceId=${item.id}`)
                      }
                    >
                      <Bell className="h-4 w-4" />
                    </Button>
                  </div>
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
};

export default InitiatedList;
