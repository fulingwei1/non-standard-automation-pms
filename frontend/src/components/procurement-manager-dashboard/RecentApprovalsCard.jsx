import { motion } from "framer-motion";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
} from "../../components/ui";
import { FileCheck } from "lucide-react";
import { cn, formatCurrency } from "../../lib/utils";
import { getPriorityColor } from "./utils";

export default function RecentApprovalsCard({ approvals }) {
  return (
    <Card className="lg:col-span-2 bg-surface-50 border-white/10">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-primary" />
            待审批订单
          </CardTitle>
          <Button variant="outline" size="sm">
            查看全部
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {(approvals || []).map((approval, index) => (
          <motion.div
            key={approval.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <Badge
                  className={cn(
                    "text-xs",
                    getPriorityColor(approval.priority)
                  )}
                >
                  {approval.priority === "high"
                    ? "紧急"
                    : approval.priority === "medium"
                    ? "中等"
                    : "普通"}
                </Badge>
                <span className="text-sm font-semibold text-white">
                  {approval.orderNo}
                </span>
                <span className="text-sm text-slate-400">
                  {approval.supplier}
                </span>
              </div>
              <span className="text-sm font-semibold text-amber-400">
                {formatCurrency(approval.amount)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm text-slate-400">
              <span>{approval.items}</span>
              <span>
                {approval.submitter} · {approval.submitTime}
              </span>
            </div>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
}
