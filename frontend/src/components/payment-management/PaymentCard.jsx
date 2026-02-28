/**
 * 支付卡片组件
 * 显示单个支付记录的详细信息
 */
import { motion } from 'framer-motion';
import { DollarSign, FileText, Eye } from 'lucide-react';
import { Button, Badge } from '../ui';
import { cn } from '../../lib/utils';
import { getPaymentStatus, getPaymentType, formatCurrency } from '@/lib/constants/finance';

/**
 * 支付卡片组件
 * @param {object} props
 * @param {object} props.payment - 支付数据
 * @param {function} props.onInvoice - 开票回调
 * @param {function} props.onViewDetail - 查看详情回调
 */
export default function PaymentCard({ payment, onInvoice, onViewDetail }) {
  const statusInfo = getPaymentStatus(payment.status);
  const typeInfo = getPaymentType(payment.type);
  const isOverdue = payment.status === 'overdue';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'rounded-xl border overflow-hidden transition-all hover:shadow-lg',
        isOverdue
          ? 'bg-red-500/5 border-red-500/30'
          : payment.status === 'paid'
          ? 'bg-emerald-500/5 border-emerald-500/30'
          : 'bg-slate-800/50 border-slate-700/50'
      )}
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 rounded-lg ${typeInfo.color}`}>
                <DollarSign className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-lg font-semibold text-white">
                  {payment.customerName}
                </h4>
                <p className="text-sm text-slate-400">{payment.projectName}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className={cn(
                  'border',
                  typeInfo.borderColor,
                  typeInfo.textColor
                )}
              >
                {typeInfo.label}
              </Badge>
              <Badge
                variant="outline"
                className={cn(
                  'border',
                  statusInfo.borderColor,
                  statusInfo.textColor
                )}
              >
                (() => { const DynIcon = statusInfo.icon; return <DynIcon className="w-3 h-3 mr-1"  />; })()
                {statusInfo.label}
              </Badge>
              {isOverdue && (
                <Badge variant="destructive">
                  逾期{payment.overdueDay}天
                </Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">
              {formatCurrency(payment.amount)}
            </div>
            {payment.paidAmount > 0 && (
              <div className="text-sm text-slate-400">
                已付: {formatCurrency(payment.paidAmount)}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="text-slate-400">
            <span>合同号: {payment.contractNo}</span>
            {payment.dueDate && (
              <span className="ml-4">
                到期日: {new Date(payment.dueDate).toLocaleDateString()}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {payment.status !== 'paid' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onInvoice && onInvoice(payment)}
              >
                <FileText className="w-3 h-3 mr-1" />
                开票
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewDetail && onViewDetail(payment)}
            >
              <Eye className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
