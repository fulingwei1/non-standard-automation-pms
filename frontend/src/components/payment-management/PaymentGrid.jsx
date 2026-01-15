/**
 * 支付列表网格组件
 * 显示支付记录的网格视图
 */
import PaymentCard from './PaymentCard';

/**
 * 支付网格组件
 * @param {object} props
 * @param {array} props.payments - 支付列表
 * @param {function} props.onInvoice - 开票回调
 * @param {function} props.onViewDetail - 查看详情回调
 */
export default function PaymentGrid({ payments, onInvoice, onViewDetail }) {
  if (payments.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        暂无付款记录
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {payments.map((payment) => (
        <PaymentCard
          key={payment.id}
          payment={payment}
          onInvoice={onInvoice}
          onViewDetail={onViewDetail}
        />
      ))}
    </div>
  );
}
