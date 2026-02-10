/**
 * InvoiceRow - 发票行组件（可复用 UI 组件）
 *
 * ARCHITECTURE NOTE:
 * This is the authoritative implementation of the invoice row component.
 * Located in components/invoice-management/ as a reusable UI component.
 * The pages/invoice/InvoiceRow.jsx re-exports this component.
 * Constants are imported from the shared lib/constants/finance.js.
 */

import { motion } from "framer-motion";
import {
 FileText,
 Edit,
 X,
 Send,
 DollarSign,
 Download
} from "lucide-react";
import { Button, Badge } from "../../components/ui";
import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { statusConfig, paymentStatusConfig } from "../../lib/constants/finance";

const InvoiceRow = ({
 invoice,
 onView,
 onEdit,
 onDelete,
 onIssue,
 onReceivePayment
}) => {
 const invoiceConfig = statusConfig[invoice.status] || statusConfig.draft;
 const paymentConfig = paymentStatusConfig[invoice.paymentStatus] || paymentStatusConfig.pending;
 const InvoiceIcon = invoiceConfig.icon;
 const PaymentIcon = paymentConfig.icon;

 return (
 <motion.div
 variants={fadeIn}
 className="group flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 transition-all hover:border-slate-600 hover:bg-slate-800/60"
 >
 <div className="flex flex-1 items-center gap-4">
 {/* Checkbox */}
 <input type="checkbox" className="h-4 w-4 rounded cursor-pointer" />

 {/* Invoice Info */}
 <div className="flex-1">
 <div className="flex items-center gap-3">
  <span className="font-semibold text-slate-100">{invoice.id}</span>
 <span className="text-sm text-slate-400">
 {invoice.projectName}
 </span>
 </div>
 <div className="mt-1 flex items-center gap-3 text-sm">
 <span className="text-slate-500">{invoice.customerName}</span>
 <span className="text-slate-600">|</span>
 <span className="text-slate-500">{invoice.invoiceType}</span>
 {invoice.issueDate && (
 <>
 <span className="text-slate-600">|</span>
  <span className="text-slate-500">{invoice.issueDate}</span>
  </>
 )}
 </div>
 </div>

 {/* Amount */}
 <div className="flex flex-col items-end gap-1">
  <p className="font-semibold text-amber-400">
 {formatCurrency(invoice.totalAmount)}
 </p>
  <p className="text-xs text-slate-500">含税</p>
 </div>

 {/* Status Badges */}
 <div className="ml-4 flex flex-col gap-2">
 <Badge className={cn("text-xs", invoiceConfig.color)}>
 <InvoiceIcon className="mr-1 h-3 w-3" />
  {invoiceConfig.label}
 </Badge>
 <Badge className={cn("text-xs", paymentConfig.color)}>
 <PaymentIcon className="mr-1 h-3 w-3" />
 {paymentConfig.label}
 </Badge>
 </div>

 {/* Actions */}
 <div className="ml-4 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
 <Button
 size="sm"
 variant="ghost"
 className="h-8 w-8 p-0"
 onClick={() => onView(invoice)}
 >
 <FileText className="h-4 w-4 text-blue-400" />
 </Button>
 {invoice.status === "draft" && (
 <>
 <Button
 size="sm"
 variant="ghost"
 className="h-8 w-8 p-0"
  onClick={() => onEdit(invoice)}
 title="编辑"
 >
 <Edit className="h-4 w-4 text-amber-400" />
 </Button>
 <Button
 size="sm"
 variant="ghost"
 className="h-8 w-8 p-0"
 onClick={() => onDelete(invoice)}
 title="删除"
 >
 <X className="h-4 w-4 text-red-400" />
 </Button>
 </>
 )}
 {invoice.status === "approved" && onIssue && (
 <Button
 size="sm"
 variant="ghost"
 className="h-8 w-8 p-0"
 onClick={() => onIssue(invoice)}
 >
 <Send className="h-4 w-4 text-purple-400" />
 </Button>
 )}
 {invoice.status === "issued" &&
 invoice.paymentStatus !== "paid" &&
 onReceivePayment && (
 <Button
  size="sm"
  variant="ghost"
 className="h-8 w-8 p-0"
 onClick={() => onReceivePayment(invoice)}
  title="记录收款"
 >
 <DollarSign className="h-4 w-4 text-emerald-400" />
 </Button>
 )}
 <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
 <Download className="h-4 w-4 text-slate-400" />
 </Button>
 </div>
 </div>
 </motion.div>
 );
};

export default InvoiceRow;
