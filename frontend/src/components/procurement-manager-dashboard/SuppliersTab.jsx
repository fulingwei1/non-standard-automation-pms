import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  Progress,
  Button,
} from "../../components/ui";
import { Eye, Edit } from "lucide-react";
import { formatCurrency } from "../../lib/utils";

export default function SuppliersTab({ suppliers }) {
  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-100 border-b border-white/10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  供应商
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  类别
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  评分
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  订单数
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  累计金额
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  按期率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  质量率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {(suppliers || []).map((supplier, index) => (
                <motion.tr
                  key={supplier.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-white/[0.02]"
                >
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-sm font-semibold text-white">
                        {supplier.name}
                      </p>
                      <p className="text-xs text-slate-400">
                        最后订单: {supplier.lastOrder}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {supplier.category}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1">
                      <span className="text-sm font-semibold text-amber-400">
                        {supplier.rating}
                      </span>
                      <span className="text-xs text-slate-400">
                        /5.0
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {supplier.totalOrders}
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold text-white">
                    {formatCurrency(supplier.totalAmount)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Progress
                        value={supplier.onTimeRate}
                        className="h-2 w-16"
                      />
                      <span className="text-sm text-slate-400">
                        {supplier.onTimeRate}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Progress
                        value={supplier.qualityRate}
                        className="h-2 w-16"
                      />
                      <span className="text-sm text-slate-400">
                        {supplier.qualityRate}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="w-4 h-4" />
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
  );
}
