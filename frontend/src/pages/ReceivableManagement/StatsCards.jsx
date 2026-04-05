import { FileText, DollarSign, AlertTriangle, Clock } from "lucide-react";
import { Card, CardContent } from "../../components/ui";

/**
 * StatsCards — four summary metric tiles at the top of the receivable page.
 *
 * @param {{ stats: { total: number, totalUnpaid: number, totalOverdue: number, overdueCount: number }, formatCurrency: (v: any) => string }} props
 */
export function StatsCards({ stats, formatCurrency }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">应收账款总数</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
            <FileText className="h-8 w-8 text-blue-400" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">待收金额</p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(stats.totalUnpaid)}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-amber-400" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">逾期金额</p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(stats.totalOverdue)}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-400" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">逾期笔数</p>
              <p className="text-2xl font-bold text-white">
                {stats.overdueCount}
              </p>
            </div>
            <Clock className="h-8 w-8 text-red-400" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
