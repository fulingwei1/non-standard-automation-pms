import React from 'react';
import PropTypes from 'prop-types';
import { PURCHASE_ORDER_STATUS, PURCHASE_ORDER_URGENCY } from './purchaseOrderConstants';

const PurchaseOrderCard = ({
  order,
  onView,
  onEdit,
  onDelete,
  onSubmit,
  onApprove,
  onReject,
  className = ''
}) => {
  const statusInfo = PURCHASE_ORDER_STATUS[order.status] || { label: 'Unknown', color: 'gray' };
  const urgencyInfo = PURCHASE_ORDER_URGENCY[order.urgency] || { label: 'Normal', color: 'blue' };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  const calculateProgress = () => {
    if (!order.total_quantity || !order.delivered_quantity) return 0;
    return Math.round((order.delivered_quantity / order.total_quantity) * 100);
  };

  const progress = calculateProgress();

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow ${className}`}>
      {/* Header with Status and Urgency */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 text-lg mb-1">
            PO-{order.po_number}
          </h3>
          <p className="text-sm text-gray-600 truncate">
            {order.supplier_name}
          </p>
        </div>

        <div className="flex flex-col items-end space-y-2">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color === 'green' ? 'bg-green-100 text-green-800' : statusInfo.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' : statusInfo.color === 'red' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}
          >
            {statusInfo.label}
          </span>

          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${urgencyInfo.color === 'red' ? 'bg-red-100 text-red-800' : urgencyInfo.color === 'orange' ? 'bg-orange-100 text-orange-800' : 'bg-blue-100 text-blue-800'}`}
          >
            {urgencyInfo.label}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>交付进度</span>
          <span>{progress}% ({order.delivered_quantity || 0}/{order.total_quantity || 0})</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${progress >= 100 ? 'bg-green-500' : progress >= 50 ? 'bg-blue-500' : 'bg-yellow-500'}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Order Information */}
      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        <div>
          <span className="text-gray-500">订单金额:</span>
          <span className="font-medium text-gray-900 ml-1">
            ¥{order.total_amount?.toLocaleString() || '0'}
          </span>
        </div>
        <div>
          <span className="text-gray-500">创建日期:</span>
          <span className="font-medium text-gray-900 ml-1">
            {formatDate(order.created_at)}
          </span>
        </div>
        <div>
          <span className="text-gray-500">期望交期:</span>
          <span className="font-medium text-gray-900 ml-1">
            {formatDate(order.expected_delivery_date)}
          </span>
        </div>
        <div>
          <span className="text-gray-500">最后更新:</span>
          <span className="font-medium text-gray-900 ml-1">
            {formatDate(order.updated_at)}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onView(order)}
          className="px-3 py-1.5 text-xs bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors"
        >
          查看
        </button>

        {order.status === 'draft' && (
          <>
            <button
              onClick={() => onEdit(order)}
              className="px-3 py-1.5 text-xs bg-gray-50 text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
            >
              编辑
            </button>
            <button
              onClick={() => onSubmit(order)}
              className="px-3 py-1.5 text-xs bg-green-50 text-green-600 rounded-md hover:bg-green-100 transition-colors"
            >
              提交
            </button>
          </>
        )}

        {order.status === 'submitted' && (
          <>
            <button
              onClick={() => onApprove(order)}
              className="px-3 py-1.5 text-xs bg-green-50 text-green-600 rounded-md hover:bg-green-100 transition-colors"
            >
              批准
            </button>
            <button
              onClick={() => onReject(order)}
              className="px-3 py-1.5 text-xs bg-red-50 text-red-600 rounded-md hover:bg-red-100 transition-colors"
            >
              拒绝
            </button>
          </>
        )}

        {(order.status === 'draft' || order.status === 'cancelled') && (
          <button
            onClick={() => onDelete(order)}
            className="px-3 py-1.5 text-xs bg-red-50 text-red-600 rounded-md hover:bg-red-100 transition-colors"
          >
            删除
          </button>
        )}
      </div>
    </div>
  );
};

PurchaseOrderCard.propTypes = {
  order: PropTypes.shape({
    id: PropTypes.number.isRequired,
    po_number: PropTypes.string.isRequired,
    supplier_name: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    urgency: PropTypes.string.isRequired,
    total_amount: PropTypes.number,
    total_quantity: PropTypes.number,
    delivered_quantity: PropTypes.number,
    created_at: PropTypes.string,
    updated_at: PropTypes.string,
    expected_delivery_date: PropTypes.string,
  }).isRequired,
  onView: PropTypes.func.isRequired,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  onSubmit: PropTypes.func,
  onApprove: PropTypes.func,
  onReject: PropTypes.func,
  className: PropTypes.string,
};

export default PurchaseOrderCard;