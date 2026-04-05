/**
 * SnapshotTable — 快照列表表格 + 分页控件
 */
import { Eye } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { formatDate } from "../../lib/utils";

/**
 * @param {{
 *   loading: boolean,
 *   snapshots: object[],
 *   total: number,
 *   page: number,
 *   pageSize: number,
 *   onPageChange: (p: number) => void,
 *   onViewDetail: (id: any) => void,
 * }} props
 */
export function SnapshotTable({
  loading,
  snapshots,
  total,
  page,
  pageSize,
  onPageChange,
  onViewDetail,
}) {
  const totalPages = Math.ceil(total / pageSize);

  return (
    <Card className="bg-surface-50 border-white/5">
      <CardHeader>
        <CardTitle className="text-white">快照列表</CardTitle>
        <CardDescription className="text-slate-400">
          共 {total} 条记录
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : snapshots.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无快照数据</div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow className="border-white/10">
                  <TableHead className="text-slate-300">快照日期</TableHead>
                  <TableHead className="text-slate-300">总问题数</TableHead>
                  <TableHead className="text-slate-300">待处理</TableHead>
                  <TableHead className="text-slate-300">处理中</TableHead>
                  <TableHead className="text-slate-300">已解决</TableHead>
                  <TableHead className="text-slate-300">已关闭</TableHead>
                  <TableHead className="text-slate-300">阻塞问题</TableHead>
                  <TableHead className="text-slate-300">逾期问题</TableHead>
                  <TableHead className="text-slate-300">今日新增</TableHead>
                  <TableHead className="text-slate-300">今日解决</TableHead>
                  <TableHead className="text-right text-slate-300">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(snapshots || []).map((snapshot) => (
                  <TableRow
                    key={snapshot.id}
                    className="border-white/10 hover:bg-surface-100/50"
                  >
                    <TableCell className="text-white font-medium">
                      {snapshot.snapshot_date
                        ? formatDate(snapshot.snapshot_date)
                        : "-"}
                    </TableCell>
                    <TableCell className="text-slate-300">
                      {snapshot.total_issues || 0}
                    </TableCell>
                    <TableCell className="text-blue-400">
                      {snapshot.open_issues || 0}
                    </TableCell>
                    <TableCell className="text-yellow-400">
                      {snapshot.processing_issues || 0}
                    </TableCell>
                    <TableCell className="text-green-400">
                      {snapshot.resolved_issues || 0}
                    </TableCell>
                    <TableCell className="text-slate-300">
                      {snapshot.closed_issues || 0}
                    </TableCell>
                    <TableCell className="text-red-400">
                      {snapshot.blocking_issues || 0}
                    </TableCell>
                    <TableCell className="text-orange-400">
                      {snapshot.overdue_issues || 0}
                    </TableCell>
                    <TableCell className="text-slate-300">
                      {snapshot.new_issues_today || 0}
                    </TableCell>
                    <TableCell className="text-slate-300">
                      {snapshot.resolved_today || 0}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(snapshot.id)}
                        className="text-slate-300 hover:text-white"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* 分页 */}
            {total > pageSize && (
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-slate-400">
                  第 {page} 页，共 {totalPages} 页
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onPageChange(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="border-white/10 text-slate-300"
                  >
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onPageChange(Math.min(totalPages, page + 1))}
                    disabled={page >= totalPages}
                    className="border-white/10 text-slate-300"
                  >
                    下一页
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
