import { motion } from "framer-motion";
import { Clock, DollarSign, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent } from "../../components/ui";
import { staggerContainer } from "../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

export function ApprovalStatsCards({ pendingApprovals, approvalHistory }) {
  const pendingTotal = (pendingApprovals || []).reduce(
    (sum, a) => sum + (a.totalAmount || 0),
    0
  );
  const approvedCount = (approvalHistory || []).filter(
    (h) => h.status === "approved"
  ).length;
  const rejectedCount = (approvalHistory || []).filter(
    (h) => h.status === "rejected"
  ).length;

  return (
    <motion.div
      variants={staggerContainer}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      {/* Pending count */}
      <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400">待审批</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">
                {pendingApprovals.length}
              </p>
              <p className="text-xs text-slate-500 mt-1">项待处理</p>
            </div>
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pending amount */}
      <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400">待审批金额</p>
              <p className="text-2xl font-bold text-white mt-1">
                {formatCurrency(pendingTotal)}
              </p>
              <p className="text-xs text-slate-500 mt-1">合同总金额</p>
            </div>
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-blue-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Approved */}
      <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400">已批准</p>
              <p className="text-2xl font-bold text-white mt-1">
                {approvedCount}
              </p>
              <p className="text-xs text-slate-500 mt-1">本月已批准</p>
            </div>
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rejected */}
      <Card className="bg-gradient-to-br from-red-500/10 to-pink-500/5 border-red-500/20">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400">已拒绝</p>
              <p className="text-2xl font-bold text-white mt-1">
                {rejectedCount}
              </p>
              <p className="text-xs text-slate-500 mt-1">本月已拒绝</p>
            </div>
            <div className="p-2 bg-red-500/20 rounded-lg">
              <XCircle className="w-5 h-5 text-red-400" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
