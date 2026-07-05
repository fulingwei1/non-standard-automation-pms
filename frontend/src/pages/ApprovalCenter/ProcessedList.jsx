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
import EmptyState from "./EmptyState";

const ProcessedList = ({ items, loading, goToDetail }) => {
  const navigate = useNavigate();
  return (
  <Card className="bg-slate-800/50 border-slate-700">
    <CardContent className="p-0">
      <Table>
        <TableHeader>
          <TableRow className="border-slate-700 hover:bg-slate-800/50">
            <TableHead className="text-slate-300">审批信息</TableHead>
            <TableHead className="text-slate-300">我的操作</TableHead>
            <TableHead className="text-slate-300">审批意见</TableHead>
            <TableHead className="text-slate-300">处理时间</TableHead>
            <TableHead className="text-slate-300">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(items || []).map((item) => {
            const actionLabel = item.action === "APPROVE" ? "通过" : item.action === "REJECT" ? "驳回" : item.action;
            const actionColor = item.action === "APPROVE" ? "bg-emerald-500" : "bg-red-500";
            const instanceId = item.instance_id || item.instance?.id;

            return (
              <TableRow key={item.id} className="border-slate-700 hover:bg-slate-800/50">
                <TableCell>
                  <div className="space-y-1">
                    <span className="text-white font-medium block">
                      {item.instance_title || item.instance?.title}
                    </span>
                    <span className="text-xs text-slate-500">
                      {item.instance_no || item.instance?.instance_no}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className={cn(actionColor, "text-white text-xs")}>
                    {actionLabel}
                  </Badge>
                </TableCell>
                <TableCell className="text-slate-300 max-w-[200px] truncate">
                  {item.comment || "-"}
                </TableCell>
                <TableCell className="text-slate-400 text-sm">
                  {formatDateTime(item.completed_at)}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      title="查看详情"
                      onClick={() => goToDetail(instanceId)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0 text-slate-400 hover:text-white"
                      title="查看对应通知"
                      onClick={() =>
                        navigate(`/notifications?sourceType=approval&sourceId=${instanceId}`)
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
        message="暂无已处理记录"
      />
    </CardContent>
  </Card>
  );
};

export default ProcessedList;
