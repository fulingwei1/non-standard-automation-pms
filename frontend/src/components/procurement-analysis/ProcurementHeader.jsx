/**
 * 采购分析页面头部组件
 * 包含标题、时间范围筛选和导出按钮
 */
import { Calendar, Download } from 'lucide-react';
import { Button } from '../ui/button';
import { PageHeader } from '../layout';
import { TIME_RANGE_OPTIONS } from './procurementConstants';

/**
 * 采购分析头部组件
 * @param {object} props
 * @param {string} props.timeRange - 当前时间范围
 * @param {function} props.onTimeRangeChange - 时间范围改变回调
 * @param {function} props.onExport - 导出回调
 */
export default function ProcurementHeader({ timeRange, onTimeRangeChange, onExport }) {
  return (
    <div className="flex items-center justify-between">
      <PageHeader
        title="采购分析"
        description="采购成本、价格波动、供应商绩效全面分析"
      />
      <div className="flex items-center gap-3">
        {/* 时间范围筛选 */}
        <div className="flex items-center gap-2 bg-slate-800/50 rounded-lg px-3 py-2">
          <Calendar className="w-4 h-4 text-slate-400" />
          <select
            value={timeRange}
            onChange={(e) => onTimeRangeChange(e.target.value)}
            className="bg-transparent text-sm text-slate-300 outline-none"
          >
            {TIME_RANGE_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <Button onClick={onExport} variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" />
          导出报表
        </Button>
      </div>
    </div>
  );
}
