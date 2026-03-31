import { Download, RefreshCw } from "lucide-react";
import { Button } from "../../components/ui/button";
import { toast } from "../../components/ui/toast";
import { PERIOD_OPTIONS } from "./constants";
import { handleExport } from "./exportUtils";

/**
 * Toolbar rendered inside the PageHeader `actions` slot.
 *
 * Props:
 *   analytics  – current analytics object (may be null)
 *   period     – active period value
 *   setPeriod  – period setter
 *   loading    – true while a fetch is in-flight
 *   onRefresh  – callback to trigger a data reload
 */
export function AnalyticsToolbar({ analytics, period, setPeriod, loading, onRefresh }) {
  const handleRefresh = () => {
    onRefresh();
    toast.success("数据已刷新");
  };

  return (
    <div className="flex gap-2">
      {/* Period selector */}
      <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
        {PERIOD_OPTIONS.map(({ value, label }) => (
          <Button
            key={value}
            variant={period === value ? "default" : "ghost"}
            size="sm"
            onClick={() => setPeriod(value)}
          >
            {label}
          </Button>
        ))}
      </div>

      {/* Refresh */}
      <Button
        variant="outline"
        size="sm"
        className="gap-2"
        onClick={handleRefresh}
        disabled={loading}
      >
        <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        刷新
      </Button>

      {/* Export buttons */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => handleExport(analytics, period, "csv")}
        >
          <Download className="w-4 h-4" />
          导出CSV
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => handleExport(analytics, period, "excel")}
        >
          <Download className="w-4 h-4" />
          导出Excel
        </Button>
      </div>
    </div>
  );
}
