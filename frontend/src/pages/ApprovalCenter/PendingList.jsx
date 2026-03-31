import { Eye, Check, X, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";
import { cn } from "../../lib/utils";
import { formatDateTime } from "@/lib/formatters";
import { URGENCY_CONFIG, ENTITY_TYPE_CONFIG } from "./configMaps";
import EmptyState from "./EmptyState";

const PendingList = ({ items, loading, goToDetail, openQuickApproval }) => (
  <Card className="bg-slate-800/50 border-slate-700">
    <CardContent className="p-0">
      <Table>
        <TableHeader>
          <TableRow className="border-slate-700 hover:bg-slate-800/50">
            <TableHead className="text-slate-300">审批信息</TableHead>
            <TableHead className="text-slate-300">类型</TableHead>
            <TableHead className="text-slate-300">紧急度</TableHead>
            <TableHead className="text-slate-300">当前节点</TableHead>
            <TableHead className="text-slate-300">发起人</TableHead>
            <TableHead className="text-slate-300">发起时间</TableHead>
            <TableHead className="text-slate-300">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(items || []).map((item) => {
            const urgencyConfig = URGENCY_CONFIG[item.instance_urgency] || URGENCY_CONFIG.NORMAL;
            const entityConfig = ENTITY_TYPE_CONFIG[item.instance?.entity_type] || {};
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
                  {entityConfig.label && (
                    <Badge className={cn(entityConfig.color, "text-white text-xs")}>
                      {entityConfig.label}
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  <Badge className={cn(urgencyConfig.color, "text-white text-xs")}>
                    {urgencyConfig.label}
                  </Badge>
                </TableCell>
                <TableCell className="text-slate-300">
                  {item.node_name || "-"}
                </TableCell>
                <TableCell className="text-slate-300">
                  {item.instance?.initiator_name || "-"}
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
                      onClick={() => goToDetail(instanceId)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0 text-emerald-500 hover:text-emerald-400"
                      onClick={() => openQuickApproval(item, "approve")}
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0 text-red-500 hover:text-red-400"
                      onClick={() => openQuickApproval(item, "reject")}
                    >
                      <X className="h-4 w-4" />
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
        icon={CheckCircle2}
        message="暂无待审批任务"
      />
    </CardContent>
  </Card>
);

export default PendingList;
