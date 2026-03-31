/**
 * SnapshotDetailDialog — 快照详情对话框
 * 展示基本信息、状态分布饼图、严重程度柱状图、详细统计和处理时间统计
 */
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { formatDate } from "../../lib/utils";
import {
  SimplePieChart,
  SimpleBarChart,
} from "../../components/administrative/StatisticsCharts";

/**
 * @param {{
 *   open: boolean,
 *   onOpenChange: (v: boolean) => void,
 *   snapshot: object | null,
 * }} props
 */
export function SnapshotDetailDialog({ open, onOpenChange, snapshot }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-surface-50 border-white/10 max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white">快照详情</DialogTitle>
        </DialogHeader>

        {snapshot && (
          <div className="space-y-6">
            {/* 基本信息 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-slate-400 mb-1">快照日期</div>
                <div className="text-white">
                  {snapshot.snapshot_date
                    ? formatDate(snapshot.snapshot_date)
                    : "-"}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-400 mb-1">总问题数</div>
                <div className="text-2xl font-bold text-white">
                  {snapshot.total_issues || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-400 mb-1">阻塞问题</div>
                <div className="text-2xl font-bold text-red-400">
                  {snapshot.blocking_issues || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-400 mb-1">逾期问题</div>
                <div className="text-2xl font-bold text-orange-400">
                  {snapshot.overdue_issues || 0}
                </div>
              </div>
            </div>

            {/* 状态分布 */}
            {snapshot.status_distribution && (
              <Card className="bg-surface-100 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white text-lg">状态分布</CardTitle>
                </CardHeader>
                <CardContent>
                  <SimplePieChart
                    data={Object.entries(snapshot.status_distribution).map(
                      ([key, value], idx) => ({
                        label: key,
                        value: value,
                        color: `hsl(${idx * 60}, 70%, 50%)`,
                      }),
                    )}
                    size={250}
                  />
                </CardContent>
              </Card>
            )}

            {/* 严重程度分布 */}
            {snapshot.severity_distribution && (
              <Card className="bg-surface-100 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white text-lg">
                    严重程度分布
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <SimpleBarChart
                    data={Object.entries(snapshot.severity_distribution).map(
                      ([key, value]) => ({ label: key, value }),
                    )}
                    height={200}
                    color="bg-red-500"
                  />
                </CardContent>
              </Card>
            )}

            {/* 详细统计 */}
            <Card className="bg-surface-100 border-white/10">
              <CardHeader>
                <CardTitle className="text-white text-lg">详细统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-slate-400">待处理</div>
                    <div className="text-xl font-bold text-blue-400">
                      {snapshot.open_issues || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">处理中</div>
                    <div className="text-xl font-bold text-yellow-400">
                      {snapshot.processing_issues || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">已解决</div>
                    <div className="text-xl font-bold text-green-400">
                      {snapshot.resolved_issues || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">已关闭</div>
                    <div className="text-xl font-bold text-slate-300">
                      {snapshot.closed_issues || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">已取消</div>
                    <div className="text-xl font-bold text-slate-300">
                      {snapshot.cancelled_issues || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">已延期</div>
                    <div className="text-xl font-bold text-slate-300">
                      {snapshot.deferred_issues || 0}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 处理时间统计 */}
            {(snapshot.avg_resolve_time || snapshot.avg_response_time) && (
              <Card className="bg-surface-100 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white text-lg">
                    处理时间统计
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    {snapshot.avg_response_time && (
                      <div>
                        <div className="text-sm text-slate-400">平均响应时间</div>
                        <div className="text-xl font-bold text-white">
                          {snapshot.avg_response_time.toFixed(1)} 小时
                        </div>
                      </div>
                    )}
                    {snapshot.avg_resolve_time && (
                      <div>
                        <div className="text-sm text-slate-400">平均解决时间</div>
                        <div className="text-xl font-bold text-white">
                          {snapshot.avg_resolve_time.toFixed(1)} 小时
                        </div>
                      </div>
                    )}
                    {snapshot.avg_verify_time && (
                      <div>
                        <div className="text-sm text-slate-400">平均验证时间</div>
                        <div className="text-xl font-bold text-white">
                          {snapshot.avg_verify_time.toFixed(1)} 小时
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-white/10 text-slate-300"
          >
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
