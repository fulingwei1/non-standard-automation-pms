/**
 * Acceptance Management — records data table
 */

import { Eye, Edit, ClipboardCheck } from "lucide-react";

import {
  Card,
  CardContent,
  Button,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { STATUS_CONFIG, TYPE_CONFIG } from "./constants";

// ── Badge helpers ────────────────────────────────────────────────────────────

const getStatusBadge = (status) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
  return (
    <Badge variant="outline" className={cn("border", config.color)}>
      {config.label}
    </Badge>
  );
};

const getTypeBadge = (type) => {
  const config = TYPE_CONFIG[type] || TYPE_CONFIG.FAT;
  return (
    <Badge variant="outline" className={cn("border font-medium", config.color)}>
      {config.label}
    </Badge>
  );
};

// ── Component ────────────────────────────────────────────────────────────────

const RecordsTable = ({ loading, filteredRecords, onViewDetail }) => {
  return (
    <Card className="bg-surface-100/50">
      <CardContent className="p-0">
        {loading ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
          </div>
        ) : filteredRecords.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400">
            <ClipboardCheck className="w-16 h-16 mb-4 opacity-50" />
            <p>暂无验收记录</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-24">验收编号</TableHead>
                <TableHead>项目名称</TableHead>
                <TableHead className="w-20">类型</TableHead>
                <TableHead>标题</TableHead>
                <TableHead className="w-24">状态</TableHead>
                <TableHead className="w-28">计划日期</TableHead>
                <TableHead>客户代表</TableHead>
                <TableHead>我方代表</TableHead>
                <TableHead className="w-32">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRecords.map((record) => (
                <TableRow key={record.id}>
                  <TableCell className="font-mono text-sm">
                    {record.acceptance_code}
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-white">{record.project_name || "-"}</p>
                      <p className="text-xs text-slate-400">{record.project_code}</p>
                    </div>
                  </TableCell>
                  <TableCell>{getTypeBadge(record.acceptance_type)}</TableCell>
                  <TableCell className="max-w-[200px] truncate">{record.title}</TableCell>
                  <TableCell>{getStatusBadge(record.status)}</TableCell>
                  <TableCell className="text-sm">{record.scheduled_date || "-"}</TableCell>
                  <TableCell className="text-sm">
                    {record.customer_representative || "-"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {record.our_representative || "-"}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(record.id)}
                      >
                        <Eye size={16} />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit size={16} />
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
};

export default RecordsTable;
