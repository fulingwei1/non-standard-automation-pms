import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "../ui";
import { formatCurrency } from "../../lib/utils";
import { staggerContainer } from "../../lib/animations";

const InvoiceStats = ({ stats }) => {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
    >
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <p className="text-sm text-slate-400">发票总数</p>
            <p className="text-3xl font-bold text-blue-400">
              {stats.totalInvoices}
            </p>
            <p className="text-xs text-slate-500">份</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <p className="text-sm text-slate-400">发票总金额</p>
            <p className="text-2xl font-bold text-amber-400">
              {formatCurrency(stats.totalAmount)}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <p className="text-sm text-slate-400">已收款</p>
            <p className="text-2xl font-bold text-emerald-400">
              {formatCurrency(stats.paidAmount)}
            </p>
            <p className="text-xs text-slate-500">
              {stats.totalAmount > 0 
                ? (stats.paidAmount / stats.totalAmount * 100).toFixed(1) 
                : 0}%
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <p className="text-sm text-slate-400">待收款</p>
            <p className="text-2xl font-bold text-red-400">
              {formatCurrency(stats.pendingAmount)}
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default InvoiceStats;
