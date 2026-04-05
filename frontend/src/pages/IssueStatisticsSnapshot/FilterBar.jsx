/**
 * FilterBar — 日期过滤器、查询按钮和导出按钮
 */
import { Download } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { CSV_EXPORT_HEADERS } from "./constants";

/**
 * @param {{
 *   startDate: string,
 *   endDate: string,
 *   onStartDateChange: (v: string) => void,
 *   onEndDateChange: (v: string) => void,
 *   onQuery: () => void,
 *   snapshots: object[],
 * }} props
 */
export function FilterBar({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  onQuery,
  snapshots,
}) {
  const handleExport = () => {
    const rows = (snapshots || []).map((s) => [
      s.snapshot_date,
      s.total_issues,
      s.open_issues,
      s.processing_issues,
      s.resolved_issues,
      s.closed_issues,
      s.blocking_issues,
      s.overdue_issues,
    ]);

    const csv = [
      CSV_EXPORT_HEADERS.join(","),
      ...(rows || []).map((row) => row.join(",")),
    ].join("\n");

    const blob = new Blob(["\ufeff" + csv], {
      type: "text/csv;charset=utf-8;",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `问题统计快照_${startDate}_${endDate}.csv`;
    link.click();
  };

  return (
    <Card className="bg-surface-50 border-white/5">
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm text-slate-400 mb-1 block">
              开始日期
            </label>
            <Input
              type="date"
              value={startDate || "unknown"}
              onChange={(e) => onStartDateChange(e.target.value)}
              className="bg-surface-100 border-white/10 text-white"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 block">
              结束日期
            </label>
            <Input
              type="date"
              value={endDate || "unknown"}
              onChange={(e) => onEndDateChange(e.target.value)}
              className="bg-surface-100 border-white/10 text-white"
            />
          </div>
          <div className="flex items-end">
            <Button
              onClick={onQuery}
              className="bg-primary hover:bg-primary/90 w-full"
            >
              查询
            </Button>
          </div>
          <div className="flex items-end">
            <Button
              onClick={handleExport}
              variant="outline"
              className="border-white/10 text-slate-300 w-full"
            >
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
