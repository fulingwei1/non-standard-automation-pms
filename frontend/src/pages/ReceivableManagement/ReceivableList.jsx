import { motion } from "framer-motion";
import { CreditCard, Eye } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { paymentStatusConfig } from "./constants";

/**
 * ReceivableList — renders the paginated list of receivable rows plus
 * pagination controls.
 *
 * @param {{
 *   loading: boolean,
 *   receivables: Array,
 *   total: number,
 *   page: number,
 *   pageSize: number,
 *   onPageChange: (p: number) => void,
 *   onRecordPayment: (receivable: object) => void,
 *   formatCurrency: (v: any) => string,
 * }} props
 */
export function ReceivableList({
  loading,
  receivables,
  total,
  page,
  pageSize,
  onPageChange,
  onRecordPayment,
  formatCurrency,
}) {
  if (loading) {
    return (
      <div className="text-center py-12 text-slate-400">加载中...</div>
    );
  }

  if (receivables.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-slate-400">暂无应收账款数据</p>
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>应收账款列表</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {(receivables || []).map((receivable) => {
              const invoiceAmount =
                receivable.invoice_amount || receivable.total_amount || 0;
              const paidAmount = receivable.paid_amount || 0;
              const unpaidAmount =
                receivable.unpaid_amount || invoiceAmount - paidAmount;
              const paymentProgress =
                invoiceAmount > 0
                  ? (paidAmount / invoiceAmount) * 100
                  : 0;

              return (
                <motion.div
                  key={receivable.id}
                  variants={fadeIn}
                  className="group flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 transition-all hover:border-slate-600 hover:bg-slate-800/60"
                >
                  <div className="flex flex-1 items-center gap-4">
                    <div className="flex-1">
                      {/* Header row */}
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-slate-100">
                          {receivable.invoice_code}
                        </span>
                        <Badge
                          className={cn(
                            paymentStatusConfig[receivable.payment_status]
                              ?.color
                          )}
                        >
                          {paymentStatusConfig[receivable.payment_status]
                            ?.label || receivable.payment_status}
                        </Badge>
                        {receivable.overdue_days > 0 && (
                          <Badge className="bg-red-500">
                            逾期 {receivable.overdue_days} 天
                          </Badge>
                        )}
                      </div>

                      {/* Meta row */}
                      <div className="mt-1 flex items-center gap-3 text-sm">
                        <span className="text-slate-500">
                          {receivable.customer_name}
                        </span>
                        <span className="text-slate-600">|</span>
                        <span className="text-slate-500">
                          {receivable.contract_code}
                        </span>
                        {receivable.due_date && (
                          <>
                            <span className="text-slate-600">|</span>
                            <span className="text-slate-500">
                              到期: {receivable.due_date}
                            </span>
                          </>
                        )}
                      </div>

                      {/* Progress row */}
                      <div className="mt-2">
                        <Progress
                          value={paymentProgress || "unknown"}
                          className="h-2"
                        />
                        <div className="flex items-center justify-between mt-1 text-xs text-slate-400">
                          <span>
                            已收: {formatCurrency(paidAmount)} /{" "}
                            {formatCurrency(invoiceAmount)}
                          </span>
                          <span>待收: {formatCurrency(unpaidAmount)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Unpaid amount */}
                    <div className="flex flex-col items-end gap-1">
                      <p className="font-semibold text-amber-400">
                        {formatCurrency(unpaidAmount)}
                      </p>
                      <p className="text-xs text-slate-500">待收金额</p>
                    </div>

                    {/* Action buttons */}
                    <div className="ml-4 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      {receivable.payment_status !== "PAID" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onRecordPayment(receivable)}
                        >
                          <CreditCard className="h-4 w-4 mr-2" />
                          记录收款
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          window.open(
                            `/sales/invoices/${receivable.id}`,
                            "_blank"
                          )
                        }
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => onPageChange(page - 1)}
          >
            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {totalPages} 页
          </span>
          <Button
            variant="outline"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}
    </>
  );
}
