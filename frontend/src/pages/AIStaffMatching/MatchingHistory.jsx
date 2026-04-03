// -*- coding: utf-8 -*-
import { motion } from "framer-motion";
import { Check, X, Clock, ChevronRight, RefreshCw } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { getScoreColor } from "./utils";

export default function MatchingHistory({
  matchingHistory,
  historyLoading,
  loadMatchingHistory
}) {
  return (
    <motion.div
      key="history"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}>

      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-slate-300">
          匹配历史记录
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={loadMatchingHistory}>
          <RefreshCw
            className={cn(
              "h-4 w-4",
              historyLoading && "animate-spin"
            )} />
        </Button>
      </div>

      {historyLoading ?
        <div className="text-center py-12 text-slate-400">
          加载中...
        </div> :
        matchingHistory.length === 0 ?
          <div className="text-center py-12 text-slate-400">
            暂无历史记录
          </div> :
          <div className="space-y-3">
            {(matchingHistory || []).map((history) =>
              <motion.div
                key={history.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 rounded-lg border border-white/10 bg-white/5">

                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-white">
                        {history.project_name}
                      </span>
                      <ChevronRight className="h-4 w-4 text-slate-500" />
                      <span className="text-slate-300">
                        {history.role_name}
                      </span>
                      <ChevronRight className="h-4 w-4 text-slate-500" />
                      <span className="text-white">
                        {history.employee_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        匹配时间: {history.matching_time}
                      </span>
                      {history.accept_time &&
                        <span className="flex items-center gap-1">
                          <Check className="h-3 w-3" />
                          采纳时间: {history.accept_time}
                        </span>
                      }
                      {history.acceptor_name &&
                        <span>处理人: {history.acceptor_name}</span>
                      }
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div
                        className={cn(
                          "text-lg font-bold",
                          getScoreColor(history.total_score)
                        )}>
                        {history.total_score?.toFixed(1)}
                      </div>
                      <div className="text-xs text-slate-500">
                        匹配得分
                      </div>
                    </div>
                    {history.is_accepted === true ?
                      <Badge className="bg-green-500/20 text-green-400">
                        <Check className="h-3 w-3 mr-1" />
                        已采纳
                      </Badge> :
                      history.is_accepted === false ?
                        <Badge
                          className="bg-red-500/20 text-red-400"
                          title={history.reject_reason}>
                          <X className="h-3 w-3 mr-1" />
                          已拒绝
                        </Badge> :
                        <Badge variant="secondary">待处理</Badge>
                    }
                  </div>
                </div>
              </motion.div>
            )}
          </div>
      }
    </motion.div>
  );
}
