/**
 * PurchaseOrderList - 采购订单列表容器组件
 * 展示订单卡片网格，处理空状态和加载状态
 */

import { motion, AnimatePresence } from "framer-motion";
import { Package } from "lucide-react";
import { Button } from "../../ui/button";
import { fadeIn } from "../../../lib/animations";
import OrderCard from "./OrderCard";

export default function PurchaseOrderList({
  orders = [],
  loading = false,
  onView,
  onEdit,
  onDelete,
  onSubmit,
  onApprove,
  onCreateNew,
}) {
  // 加载状态
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div
            key={i}
            className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-4 animate-pulse"
          >
            <div className="h-4 bg-slate-700/50 rounded mb-3 w-1/3" />
            <div className="h-3 bg-slate-700/50 rounded mb-2" />
            <div className="h-3 bg-slate-700/50 rounded mb-4 w-2/3" />
            <div className="h-2 bg-slate-700/50 rounded mb-1" />
            <div className="h-8 bg-slate-700/30 rounded" />
          </div>
        ))}
      </div>
    );
  }

  // 空状态
  if (orders.length === 0) {
    return (
      <div className="text-center py-12">
        <Package className="h-16 w-16 text-slate-500 mx-auto mb-4 opacity-50" />
        <h3 className="text-lg font-medium text-white mb-2">暂无采购订单</h3>
        <p className="text-slate-400 mb-4">还没有创建任何采购订单</p>
        {onCreateNew && (
          <Button
            onClick={onCreateNew}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            <Package className="h-4 w-4 mr-2" />
            创建第一个采购订单
          </Button>
        )}
      </div>
    );
  }

  // 订单列表
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <AnimatePresence mode="popLayout">
        {orders.map((order) => (
          <motion.div
            key={order.id}
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={fadeIn}
            layout
          >
            <OrderCard
              order={order}
              onView={onView}
              onEdit={onEdit}
              onDelete={onDelete}
              onSubmit={onSubmit}
              onApprove={onApprove}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
