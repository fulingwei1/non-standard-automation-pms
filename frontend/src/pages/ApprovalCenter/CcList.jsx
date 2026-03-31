import { Eye, Mail, MailOpen } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";
import { cn } from "../../lib/utils";
import { formatDateTime } from "@/lib/formatters";
import EmptyState from "./EmptyState";

const CcList = ({ items, loading, goToDetail, handleMarkRead }) => (
  <Card className="bg-slate-800/50 border-slate-700">
    <CardContent className="p-0">
      <Table>
        <TableHeader>
          <TableRow className="border-slate-700 hover:bg-slate-800/50">
            <TableHead className="text-slate-300">审批信息</TableHead>
            <TableHead className="text-slate-300">发起人</TableHead>
            <TableHead className="text-slate-300">状态</TableHead>
            <TableHead className="text-slate-300">抄送时间</TableHead>
            <TableHead className="text-slate-300">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(items || []).map((item) => {
            const isRead = item.is_read;

            return (
              <TableRow
                key={item.id}
                className={cn(
                  "border-slate-700 hover:bg-slate-800/50",
                  !isRead && "bg-slate-800/30"
                )}
              >
                <TableCell>
                  <div className="flex items-center gap-2">
                    {!isRead && (
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                    )}
                    <div className="space-y-1">
                      <span className="text-white font-medium block">
                        {item.instance_title}
                      </span>
                      <span className="text-xs text-slate-500">
                        {item.instance_no}
                      </span>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-slate-300">
                  {item.initiator_name || "-"}
                </TableCell>
                <TableCell>
                  <Badge variant={isRead ? "secondary" : "info"}>
                    {isRead ? "已读" : "未读"}
                  </Badge>
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
                      onClick={() => goToDetail(item.instance_id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    {!isRead && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-blue-500 hover:text-blue-400"
                        onClick={() => handleMarkRead(item)}
                      >
                        <MailOpen className="h-4 w-4" />
                      </Button>
                    )}
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
        icon={Mail}
        message="暂无抄送记录"
      />
    </CardContent>
  </Card>
);

export default CcList;
