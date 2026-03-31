/**
 * Items tab - material line items table with summary
 */

import { motion } from "framer-motion";
import { Package } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui";
import { formatCurrency } from "../../lib/utils";
import { staggerContainer } from "../../lib/animations";
import POLineItem from "./POLineItem";

const ItemsTab = ({ po, totalItems }) => (
  <Card className="bg-slate-800/50 border-slate-700/50">
    <CardHeader>
      <div className="flex items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-slate-200">
          <Package className="w-5 h-5 text-blue-400" />
          {"\u8ba2\u5355\u7269\u6599"} ({po.items?.length} {"\u9879"})
        </CardTitle>
      </div>
    </CardHeader>
    <CardContent>
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-0"
      >
        {/* Header */}
        <div className="flex items-center border-b-2 border-slate-600 py-3 text-sm font-medium text-slate-400">
          <div className="w-12" />
          <div className="flex-1">{"\u7269\u6599\u63cf\u8ff0"}</div>
          <div className="w-24 text-right">{"\u6570\u91cf"}</div>
          <div className="w-24 text-right">{"\u5355\u4ef7"}</div>
          <div className="w-28 text-right">{"\u5c0f\u8ba1"}</div>
          <div className="w-20">{"\u72b6\u6001"}</div>
        </div>

        {/* Items */}
        {(po.items || []).map((item, idx) => (
          <POLineItem key={item.id} item={item} idx={idx} />
        ))}

        {/* Summary */}
        <div className="border-t-2 border-slate-600 pt-4 mt-4 space-y-2">
          <div className="flex justify-end gap-24">
            <p className="text-sm text-slate-400">{"\u5c0f\u8ba1"}:</p>
            <p className="w-28 text-right font-semibold text-slate-100">
              {formatCurrency(totalItems)}
            </p>
          </div>
          <div className="flex justify-end gap-24">
            <p className="text-sm text-slate-400">
              {"\u7a0e\u7387"} ({po.taxRate}%):
            </p>
            <p className="w-28 text-right font-semibold text-slate-100">
              {formatCurrency(po.taxAmount)}
            </p>
          </div>
          <div className="flex justify-end gap-24 pt-2 border-t border-slate-700">
            <p className="text-lg font-semibold text-slate-100">{"\u5408\u8ba1"}:</p>
            <p className="w-28 text-right text-2xl font-bold text-amber-400">
              {formatCurrency(po.totalWithTax)}
            </p>
          </div>
        </div>
      </motion.div>
    </CardContent>
  </Card>
);

export default ItemsTab;
