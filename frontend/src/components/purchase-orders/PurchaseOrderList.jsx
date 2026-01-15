import React, { useState, useEffect } from 'react';
import PurchaseOrderCard from './PurchaseOrderCard';

const PurchaseOrderList = ({
  initialOrders = [],
  pageSize = 10,
  onLoadMore
}) => {
  const [orders, setOrders] = useState(initialOrders);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const currentOrders = orders.slice(0, currentPage * pageSize);

  const loadMore = async () => {
    if (isLoading || !hasMore) return;

    setIsLoading(true);
    try {
      const newOrders = await onLoadMore?.(currentPage + 1, pageSize) || [];
      if (newOrders.length < pageSize) {
        setHasMore(false);
      }
      setOrders(prev => [...prev, ...newOrders]);
      setCurrentPage(prev => prev + 1);
    } catch (error) {
      console.error('Failed to load more orders:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setOrders(initialOrders);
    setCurrentPage(1);
    setHasMore(initialOrders.length >= pageSize);
  }, [initialOrders]);

  if (initialOrders.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        <p className="text-lg">暂无采购订单</p>
        <p className="text-sm mt-1">点击新建按钮创建第一个订单</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {currentOrders.map((order) => (
          <PurchaseOrderCard key={order.id} order={order} />
        ))}
      </div>

      {isLoading && (
        <div className="flex justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      )}

      {!isLoading && hasMore && currentOrders.length < orders.length && (
        <div className="flex justify-center py-4">
          <button
            onClick={loadMore}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          >
            加载更多
          </button>
        </div>
      )}

      {!isLoading && !hasMore && currentOrders.length > 0 && (
        <div className="text-center text-sm text-gray-500 py-2">
          已显示全部 {orders.length} 个订单
        </div>
      )}
    </div>
  );
};

export default PurchaseOrderList;