/**
 * 工单列表组件
 * 显示工单的网格或列表视图
 */
import WorkOrderCard from './WorkOrderCard';

/**
 * 工单列表组件
 * @param {object} props
 * @param {array} props.orders - 工单列表
 * @param {boolean} props.loading - 加载状态
 * @param {function} props.onAction - 操作回调
 */
export default function WorkOrderList({ orders, loading, onAction }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-slate-400 mb-2">暂无工单</div>
        <div className="text-sm text-slate-500">请等待分配工单或联系管理员</div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {orders.map((order) => (
        <WorkOrderCard
          key={order.id}
          order={order}
          onAction={onAction}
        />
      ))}
    </div>
  );
}
