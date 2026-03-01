import { motion } from "framer-motion";
import {
  Input,
  Card,
  CardContent,
  Badge,
  Button,
} from "../../components/ui";
import { Eye, CheckCircle2, XCircle } from "lucide-react";
import { cn, formatCurrency } from "../../lib/utils";
import { getPriorityColor } from "./utils";

export default function ApprovalsTab({
  searchQuery,
  setSearchQuery,
  filterStatus,
  setFilterStatus,
  approvals,
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Input
              placeholder="搜索订单号或供应商..."
              value={searchQuery || "unknown"}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-64 bg-surface-100 border-white/10"
            />
          </div>
          <select
            value={filterStatus || "unknown"}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 rounded-lg bg-surface-100 border border-white/10 text-white text-sm"
          >
            <option value="all">全部优先级</option>
            <option value="high">紧急</option>
            <option value="medium">中等</option>
            <option value="low">普通</option>
          </select>
        </div>
      </div>

      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-100 border-b border-white/10">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    订单号
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    供应商
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    物料
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    金额
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    提交人
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    提交时间
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    优先级
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {(approvals || []).map((approval, index) => (
                  <motion.tr
                    key={approval.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-white/[0.02]"
                  >
                    <td className="px-6 py-4 text-sm font-semibold text-white">
                      {approval.orderNo}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {approval.supplier}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {approval.items}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-amber-400">
                      {formatCurrency(approval.amount)}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {approval.submitter}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {approval.submitTime}
                    </td>
                    <td className="px-6 py-4">
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
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-emerald-400"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-400"
                        >
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
