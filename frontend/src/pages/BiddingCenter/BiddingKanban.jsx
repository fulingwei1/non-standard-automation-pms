/**
 * 投标看板视图组件
 */


import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function BiddingKanban({ biddingsByStage, onSelectBidding }) {
  return (
    <motion.div
      variants={fadeIn}
      className="flex overflow-x-auto custom-scrollbar pb-4 -mx-6 px-6 gap-4">

      {(biddingsByStage || []).map((column) =>
    <div key={column.id} className="flex-shrink-0 w-80">
          <Card className="bg-surface-50/70 backdrop-blur-sm border border-white/5 shadow-md">
            <CardHeader className="py-3 px-4 border-b border-white/5">
              <CardTitle className="text-base font-semibold text-white flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span
                className={cn("w-2 h-2 rounded-full", column.color)} />

                  {column.name}
                </span>
                <Badge variant="secondary" className="bg-white/10">
                  {column.biddings?.length}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 space-y-3 min-h-[300px] max-h-[calc(100vh-400px)] overflow-y-auto custom-scrollbar">
              {column.biddings?.length > 0 ?
          (column.biddings || []).map((bidding) =>
          <BiddingCard
            key={bidding.id}
            bidding={bidding}
            onClick={onSelectBidding} />

          ) :

          <div className="text-center py-8 text-slate-400">
                  <Target className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                  <p className="text-sm">暂无项目</p>
          </div>
          }
            </CardContent>
          </Card>
    </div>
    )}
    </motion.div>
  );
}
