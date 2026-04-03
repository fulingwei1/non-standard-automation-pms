import {
  Package,
  BarChart3,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";

const ABC_COLORS = {
  A: 'from-red-600 to-red-400',
  B: 'from-amber-600 to-amber-400',
  C: 'from-emerald-600 to-emerald-400',
};

const ABC_TEXT_COLORS = {
  A: 'text-red-400',
  B: 'text-amber-400',
  C: 'text-emerald-400',
};

const ABC_CARD_STYLES = {
  A: { bg: 'bg-red-950/30 border border-red-900/50', text: 'text-red-400', label: 'A类物料', desc: '占金额70%' },
  B: { bg: 'bg-amber-950/30 border border-amber-900/50', text: 'text-amber-400', label: 'B类物料', desc: '占金额20%' },
  C: { bg: 'bg-emerald-950/30 border border-emerald-900/50', text: 'text-emerald-400', label: 'C类物料', desc: '占金额10%' },
};

const ABC_ICON_COLORS = {
  A: 'text-red-500',
  B: 'text-amber-500',
  C: 'text-emerald-500',
};

export default function AbcAnalysisTab({ abcAnalysisData }) {
  return (
    <div className="space-y-4">
      {abcAnalysisData?.abc_summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">物料总数</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {abcAnalysisData.total_materials || 0}
                  </div>
                </div>
                <Package className="w-10 h-10 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          {['A', 'B', 'C'].map((cls) => {
            const style = ABC_CARD_STYLES[cls];
            return (
              <Card key={cls} className={style.bg}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`text-sm ${style.text}`}>{style.label}</div>
                      <div className={`text-2xl font-bold ${style.text} mt-1`}>
                        {abcAnalysisData.abc_summary[cls].count || 0}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">{style.desc}</div>
                    </div>
                    <BarChart3 className={`w-10 h-10 ${ABC_ICON_COLORS[cls]}`} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* ABC分类分布图 */}
      {abcAnalysisData?.abc_summary && (
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle>ABC分类分布</CardTitle>
            <CardDescription>按采购金额累计占比分类</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {['A', 'B', 'C'].map((cls) => {
                const summary = abcAnalysisData.abc_summary[cls];
                return (
                  <div key={cls} className="flex items-center gap-4">
                    <div className={`w-16 text-lg font-bold ${ABC_TEXT_COLORS[cls]}`}>{cls}类</div>
                    <div className="flex-1 bg-slate-700 rounded-full h-8 overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r ${ABC_COLORS[cls]} flex items-center justify-end pr-3`}
                        style={{ width: `${summary.amount_percent}%` }}
                      >
                        <span className="text-sm font-medium text-white">
                          {summary.amount_percent}%
                        </span>
                      </div>
                    </div>
                    <div className="w-24 text-right text-sm text-slate-400">
                      {summary.count}个
                    </div>
                    <div className="w-24 text-right text-sm text-slate-400">
                      {summary.count_percent}%
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
