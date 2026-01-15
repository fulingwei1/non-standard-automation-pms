/**
 * 支付列表表格组件
 * 显示支付记录的表格视图
 */
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Eye } from 'lucide-react';
import { Card, CardContent, Badge, Button } from '../ui';
import { cn } from '../../lib/utils';
import { getPaymentStatus, getPaymentType, formatCurrency } from './paymentManagementConstants';

/**
 * 支付表格组件
 * @param {object} props
 * @param {array} props.payments - 支付列表
 * @param {function} props.onInvoice - 开票回调
 * @param {function} props.onViewDetail - 查看详情回调
 */
export default function PaymentTable({ payments, onInvoice, onViewDetail }) {
  if (payments.length === 0) {
    return (
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardContent className="p-12 text-center">
          <div className="text-slate-400">暂无付款记录</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left p-4 text-slate-400">客户</th>
              <th className="text-left p-4 text-slate-400">项目</th>
              <th className="text-left p-4 text-slate-400">类型</th>
              <th className="text-right p-4 text-slate-400">金额</th>
              <th className="text-left p-4 text-slate-400">到期日</th>
              <th className="text-left p-4 text-slate-400">状态</th>
              <th className="text-right p-4 text-slate-400">操作</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence>
              {payments.map((payment, index) => {
                const paymentType = getPaymentType(payment.type);
                const paymentStatus = getPaymentStatus(payment.status);
                const StatusIcon = paymentStatus.icon;

                return (
                  <motion.tr
                    key={payment.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.02 }}
                    className="border-b border-slate-700/50"
                  >
                    <td className="p-4">
                      <div>
                        <div className="text-white font-medium">
                          {payment.customerName}
                        </div>
                        <div className="text-slate-400 text-sm">
                          {payment.contractNo}
                        </div>
                      </div>
                    </td>
                    <td className="p-4 text-white">{payment.projectName}</td>
                    <td className="p-4">
                      <Badge
                        variant="outline"
                        className={cn(
                          'border',
                          paymentType.borderColor,
                          paymentType.textColor,
                        )}
                      >
                        {paymentType.label}
                      </Badge>
                    </td>
                  <td className="p-4 text-right font-medium text-white">
                    {formatCurrency(payment.amount)}
                  </td>
                  <td className="p-4 text-white">
                    {payment.dueDate
                      ? new Date(payment.dueDate).toLocaleDateString()
                      : '-'}
                  </td>
                  <td className="p-4">
                    <Badge
                      variant="outline"
                      className={cn(
                        'border',
                        paymentStatus.borderColor,
                        paymentStatus.textColor
                      )}
                    >
                      {StatusIcon && (
                        <StatusIcon className="w-3 h-3 mr-1" />
                      )}
                      {paymentStatus.label}
                    </Badge>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center justify-end gap-2">
                      {payment.status !== 'paid' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onInvoice && onInvoice(payment)}
                        >
                          <FileText className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail && onViewDetail(payment)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                  </motion.tr>
                );
              })}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </Card>
  );
}
