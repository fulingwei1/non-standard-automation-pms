import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button
} from "../../components/ui";
import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

const typeConfig = {
  contract: {
    label: "合同审批",
    textColor: "text-blue-400",
    bgColor: "bg-blue-500/20"
  },
  opportunity: {
    label: "商机审批",
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/20"
  },
  payment: {
    label: "回款审批",
    textColor: "text-amber-400",
    bgColor: "bg-amber-500/20"
  }
};


const formatTimelineLabel = (value) => {
  if (!value) return "刚刚";
  try {
    return new Date(value).toLocaleString("zh-CN", { hour12: false });
  } catch (_err) {
    return value;
  }
};

export function PendingApprovalsCard({ pendingApprovals }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
              待审批事项
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-amber-500/20 text-amber-400 border-amber-500/30"
            >
              {pendingApprovals.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {pendingApprovals && pendingApprovals.length > 0 ? (
            pendingApprovals.map((item) => {
              const typeInfo = typeConfig[item.type];
              return (
                <div
                  key={item.id}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant="outline"
                          className={cn("text-xs", typeInfo.textColor)}
                        >
                          {typeInfo.label}
                        </Badge>
                        {item.priority === "high" && (
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                            紧急
                          </Badge>
                        )}
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
                      {item.submitter} · {formatTimelineLabel(item.submitTime)}
                    </span>
                    <span className="font-medium text-amber-400">
                      {formatCurrency(item.amount)}
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>暂无待审批事项</p>
            </div>
          )}
          <Button variant="outline" className="w-full mt-3">
            查看全部审批
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}
