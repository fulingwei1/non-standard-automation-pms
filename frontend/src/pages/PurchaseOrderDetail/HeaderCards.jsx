/**
 * Header summary cards (supplier, status, payment, invoice)
 */

import { motion } from "framer-motion";
import { Card, CardContent, Badge } from "../../components/ui";
import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { statusConfig, paymentStatusConfig, invoiceStatusConfig } from "./constants";

const HeaderCards = ({ po }) => (
  <motion.div
    variants={staggerContainer}
    initial="hidden"
    animate="visible"
    className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
  >
    <motion.div variants={fadeIn}>
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardContent className="pt-6">
          <p className="text-sm text-slate-400">{"\u4f9b\u5e94\u5546"}</p>
          <p className="text-lg font-semibold text-slate-100 mt-2">
            {po.supplier.name}
          </p>
          <p className="text-xs text-slate-500 mt-1">{po.supplier.contact}</p>
          <p className="text-xs text-slate-500">{po.supplier.phone}</p>
        </CardContent>
      </Card>
    </motion.div>

    <motion.div variants={fadeIn}>
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardContent className="pt-6">
          <p className="text-sm text-slate-400">{"\u8ba2\u5355\u72b6\u6001"}</p>
          <div className="mt-2">
            <Badge
              className={cn("text-sm", statusConfig[po.status]?.color || "")}
            >
              {statusConfig[po.status]?.label}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            PO\u91d1\u989d: {formatCurrency(po.totalWithTax)}
          </p>
        </CardContent>
      </Card>
    </motion.div>

    <motion.div variants={fadeIn}>
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardContent className="pt-6">
          <p className="text-sm text-slate-400">{"\u4ed8\u6b3e\u72b6\u6001"}</p>
          <div className="mt-2">
            <Badge
              className={cn(
                "text-sm",
                paymentStatusConfig[po.paymentStatus]?.color || ""
              )}
            >
              {paymentStatusConfig[po.paymentStatus]?.label}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {"\u5df2\u4ed8"}: {formatCurrency(po.paidAmount)}
          </p>
        </CardContent>
      </Card>
    </motion.div>

    <motion.div variants={fadeIn}>
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardContent className="pt-6">
          <p className="text-sm text-slate-400">{"\u5f00\u7968\u72b6\u6001"}</p>
          <div className="mt-2">
            <Badge
              className={cn(
                "text-sm",
                invoiceStatusConfig[po.invoiceStatus]?.color || ""
              )}
            >
              {invoiceStatusConfig[po.invoiceStatus]?.label}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {"\u5df2\u5f00"}: {formatCurrency(po.invoicedAmount)}
          </p>
        </CardContent>
      </Card>
    </motion.div>
  </motion.div>
);

export default HeaderCards;
