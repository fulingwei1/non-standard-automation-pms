/**
 * 报工记录历史组件
 * 显示工人的报工记录列表
 */
import { Clock, CheckCircle2, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { cn as _cn, formatDate } from '../../lib/utils';
import { REPORT_TYPE, getReportTypeColor } from './workerWorkstationConstants';

/**
 * 报工记录历史组件
 * @param {object} props
 * @param {array} props.reports - 报工记录列表
 * @param {boolean} props.loading - 加载状态
 */
export default function ReportHistory({ reports, loading }) {
  if (loading) {
    return (
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardContent className="p-12">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        </CardContent>
      </Card>);

  }

  if (reports.length === 0) {
    return (
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardContent className="p-12">
          <div className="text-center text-slate-400">暂无报工记录</div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardHeader>
        <CardTitle className="text-white">报工记录</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {reports.map((report) => {
            const typeInfo = REPORT_TYPE[report.report_type] || REPORT_TYPE.START;
            const typeColor = getReportTypeColor(report.report_type);

            return (
              <div
                key={report.id}
                className="p-3 rounded-lg bg-slate-700/30 border border-slate-700/50">

                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge className={typeColor}>
                        {typeInfo.label}
                      </Badge>
                      <span className="text-white font-medium">
                        {report.work_order_no || report.work_order_code}
                      </span>
                    </div>
                    <div className="text-sm text-slate-400">
                      {report.project_name || report.project_code}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-500">
                      {formatDate(report.created_time)}
                    </div>
                  </div>
                </div>

                {/* 报工详情 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  {report.report_type === 'COMPLETE' &&
                  <>
                      <div>
                        <span className="text-slate-500">完成数量: </span>
                        <span className="text-white font-medium">{report.completed_qty || 0}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">合格数量: </span>
                        <span className="text-emerald-400 font-medium">{report.qualified_qty || 0}</span>
                      </div>
                      {report.defect_qty > 0 &&
                    <div>
                          <span className="text-slate-500">次品数量: </span>
                          <span className="text-red-400 font-medium">{report.defect_qty}</span>
                    </div>
                    }
                      {report.work_hours > 0 &&
                    <div>
                          <span className="text-slate-500">工时: </span>
                          <span className="text-white font-medium">{report.work_hours}h</span>
                    </div>
                    }
                  </>
                  }
                  {report.report_type === 'PROGRESS' &&
                  <>
                      <div>
                        <span className="text-slate-500">进度: </span>
                        <span className="text-white font-medium">{report.progress_percent || 0}%</span>
                      </div>
                      {report.current_issues &&
                    <div className="col-span-3">
                          <span className="text-slate-500">问题: </span>
                          <span className="text-amber-400">{report.current_issues}</span>
                    </div>
                    }
                  </>
                  }
                  {report.report_type === 'START' &&
                  <>
                      {report.start_note &&
                    <div className="col-span-2">
                          <span className="text-slate-500">备注: </span>
                          <span className="text-white">{report.start_note}</span>
                    </div>
                    }
                      <div className="col-span-2 text-right">
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4" />
                          设备和物料已检查
                        </span>
                      </div>
                  </>
                  }
                </div>

                {/* 备注 */}
                {report.report_note &&
                <div className="mt-2 pt-2 border-t border-slate-700/50 text-sm text-slate-400">
                    备注: {report.report_note}
                </div>
                }
              </div>);

          })}
        </div>
      </CardContent>
    </Card>);

}