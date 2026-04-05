import { Eye, Edit, User } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { formatDate } from "../../lib/utils";
import { statusConfigs, severityConfigs, typeConfigs } from "./constants";

/**
 * ExceptionTable
 * Renders the paginated exception event list inside a Card.
 */
export function ExceptionTable({
  loading,
  filteredExceptions,
  onViewDetail,
  onOpenHandle,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>异常事件列表</CardTitle>
        <CardDescription>
          共 {filteredExceptions.length} 个异常事件
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredExceptions.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无异常事件</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>异常编号</TableHead>
                <TableHead>异常标题</TableHead>
                <TableHead>项目</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>严重程度</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>发现时间</TableHead>
                <TableHead>责任人</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredExceptions.map((exception) => (
                <TableRow key={exception.id}>
                  <TableCell className="font-mono text-sm">
                    {exception.event_no}
                  </TableCell>
                  <TableCell className="font-medium">
                    {exception.event_title}
                  </TableCell>
                  <TableCell>{exception.project_name || "-"}</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        typeConfigs[exception.event_type]?.color || "bg-slate-500"
                      }
                    >
                      {typeConfigs[exception.event_type]?.label ||
                        exception.event_type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        severityConfigs[exception.severity]?.color ||
                        "bg-slate-500"
                      }
                    >
                      {severityConfigs[exception.severity]?.label ||
                        exception.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        statusConfigs[exception.status]?.color || "bg-slate-500"
                      }
                    >
                      {statusConfigs[exception.status]?.label || exception.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-500 text-sm">
                    {exception.discovered_at
                      ? formatDate(exception.discovered_at)
                      : "-"}
                  </TableCell>
                  <TableCell>
                    {exception.responsible_user_name ? (
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        <span className="text-sm">
                          {exception.responsible_user_name}
                        </span>
                      </div>
                    ) : (
                      <span className="text-slate-400">未分配</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(exception.id)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      {exception.status === "OPEN" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onOpenHandle(exception)}
                        >
                          <Edit className="w-4 h-4" />
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
