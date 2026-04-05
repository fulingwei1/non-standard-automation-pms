/**
 * ExceptionTable — the main data table listing production exceptions.
 */
import { Eye, Edit, CheckCircle2 } from "lucide-react";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
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
import { statusConfigs, typeConfigs, levelConfigs } from "./constants";

export function ExceptionTable({
  loading,
  filteredExceptions,
  onViewDetail,
  onOpenHandleDialog,
  onClose,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>生产异常列表</CardTitle>
        <CardDescription>共 {filteredExceptions.length} 个异常</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredExceptions.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无异常</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>异常编号</TableHead>
                <TableHead>异常标题</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>级别</TableHead>
                <TableHead>项目</TableHead>
                <TableHead>工单号</TableHead>
                <TableHead>上报时间</TableHead>
                <TableHead>状态</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(filteredExceptions || []).map((exc) => (
                <TableRow key={exc.id}>
                  <TableCell className="font-mono text-sm">
                    {exc.exception_no}
                  </TableCell>
                  <TableCell className="font-medium">{exc.title}</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        typeConfigs[exc.exception_type]?.color || "bg-slate-500"
                      }
                    >
                      {typeConfigs[exc.exception_type]?.label ||
                        exc.exception_type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        levelConfigs[exc.exception_level]?.color ||
                        "bg-slate-500"
                      }
                    >
                      {levelConfigs[exc.exception_level]?.label ||
                        exc.exception_level}
                    </Badge>
                  </TableCell>
                  <TableCell>{exc.project_name || "-"}</TableCell>
                  <TableCell className="font-mono text-sm">
                    {exc.work_order_no || "-"}
                  </TableCell>
                  <TableCell className="text-slate-500 text-sm">
                    {exc.report_time ? formatDate(exc.report_time) : "-"}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        statusConfigs[exc.status]?.color || "bg-slate-500"
                      }
                    >
                      {statusConfigs[exc.status]?.label || exc.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(exc.id)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      {(exc.status === "REPORTED" ||
                        exc.status === "IN_PROGRESS") && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onOpenHandleDialog(exc)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      )}
                      {exc.status === "RESOLVED" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onClose(exc.id)}
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
