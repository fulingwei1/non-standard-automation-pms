/**
 * Purchase Order Line Item row component
 */

import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { statusConfig } from "./constants";

const POLineItem = ({ item, idx: _idx }) => (
  <motion.div
    variants={fadeIn}
    className="flex items-center border-b border-slate-700/30 py-3"
  >
    <div className="w-12 text-center text-sm text-slate-500">
      {item.itemNo}
    </div>
    <div className="flex-1">
      <p className="font-medium text-slate-100">{item.description}</p>
      <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
        <span>{item.materialCode}</span>
        <span>|</span>
        <span>{item.specification}</span>
      </div>
    </div>
    <div className="w-24 text-right">
      <p className="text-sm text-slate-300">{item.quantity}</p>
      <p className="text-xs text-slate-500">{item.unit}</p>
    </div>
    <div className="w-24 text-right">
      <p className="font-medium text-slate-100">
        {formatCurrency(item.unitPrice)}
      </p>
      <p className="text-xs text-slate-500">\u5355\u4ef7</p>
    </div>
    <div className="w-28 text-right">
      <p className="font-semibold text-amber-400">
        {formatCurrency(item.amount)}
      </p>
    </div>
    <div className="w-20">
      <Badge className={cn("text-xs", statusConfig[item.status]?.color || "")}>
        {statusConfig[item.status]?.label || item.status}
      </Badge>
    </div>
  </motion.div>
);

export default POLineItem;
