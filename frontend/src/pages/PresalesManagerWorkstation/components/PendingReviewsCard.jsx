

import { fadeIn } from "../../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../../lib/formatters";
import { SOLUTION_CENTER_PATH } from "../constants";

export default function PendingReviewsCard({ pendingReviews }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileCheck className="h-5 w-5 text-amber-400" />
              待审核方案
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-amber-500/20 text-amber-400 border-amber-500/30">
              {pendingReviews.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {(!pendingReviews || pendingReviews.length === 0) && (
            <div className="py-6 text-center text-sm text-slate-500">暂无待审核方案</div>
          )}
          {(pendingReviews || []).map((item) =>
            <div
              key={item.id}
              className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {item.priority === "high" &&
                      <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                        紧急
                      </Badge>
                    }
                    {item.daysWaiting > 1 &&
                      <Badge className="text-xs bg-orange-500/20 text-orange-400 border-orange-500/30">
                        待处理 {item.daysWaiting} 天
                      </Badge>
                    }
                  </div>
                  <p className="font-medium text-white text-sm">
                    {item.title}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {item.customer}
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs mt-2">
                <span className="text-slate-400">
                  {item.author} · {item.version} · {item.submitTimeLabel}
                </span>
                <span className="font-medium text-amber-400">
                  {formatCurrency(item.amount)}
                </span>
              </div>
            </div>
          )}
          <Link to={SOLUTION_CENTER_PATH}>
            <Button variant="outline" className="w-full mt-3">
              查看全部方案
            </Button>
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  );
}
