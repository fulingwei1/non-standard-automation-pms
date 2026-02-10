/**
 * InvoiceList - 发票列表容器组件（可复用 UI 组件）
 *
 * ARCHITECTURE NOTE:
 * This is a list wrapper component that composes InvoiceRow instances with
 * bulk action controls. It exists only in components/invoice-management/
 * (no page-level duplicate). The pages/invoice/InvoiceManagement.jsx currently
 * inlines similar markup, but could be refactored to use this component.
 */

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent, Button } from "../ui";
import { Send, Download, X } from "lucide-react";
import { staggerContainer } from "../../lib/animations";
import InvoiceRow from "./InvoiceRow";

const InvoiceList = ({
 invoices,
 onView,
 onEdit,
 onDelete,
 onIssue,
 onReceivePayment,
 selectedInvoice: _selectedInvoice,
 setSelectedInvoice: _setSelectedInvoice
}) => {
 return (
 <>
 <Card>
 <CardHeader>
 <CardTitle>发票列表</CardTitle>
 <p className="mt-2 text-sm text-slate-400">
 共 {invoices.length} 份发票
 </p>
 </CardHeader>
 <CardContent>
 <motion.div
 variants={staggerContainer}
 initial="hidden"
  animate="visible"
 className="space-y-2"
 >
 <AnimatePresence>
 {invoices.length > 0 ? (
  invoices.map((invoice) => (
  <InvoiceRow
 key={invoice.id}
 invoice={invoice}
 onView={onView}
  onEdit={onEdit}
 onDelete={onDelete}
 onIssue={onIssue}
 onReceivePayment={onReceivePayment}
 />
  ))
 ) : (
 <motion.div
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 className="py-12 text-center"
 >
 <p className="text-slate-400">没有符合条件的发票</p>
  </motion.div>
 )}
  </AnimatePresence>
 </motion.div>
 </CardContent>
 </Card>

 {/* Bulk Actions */}
 {invoices.length > 0 && (
 <Card className="bg-blue-500/10 border-blue-500/30">
 <CardContent className="pt-6">
 <div className="flex items-center justify-between">
 <p className="text-sm text-slate-300">
 已选择 0 / {invoices.length} 份发票
 </p>
 <div className="flex gap-2">
 <Button variant="ghost" size="sm" className="gap-2">
  <Send className="h-4 w-4" />
  批量发送
 </Button>
  <Button variant="ghost" size="sm" className="gap-2">
 <Download className="h-4 w-4" />
 批量下载
  </Button>
  <Button
  variant="ghost"
  size="sm"
  className="gap-2 text-red-400 hover:text-red-300"
  >
  <X className="h-4 w-4" />
 取消选择
 </Button>
 </div>
  </div>
 </CardContent>
 </Card>
 )}
 </>
 );
};

export default InvoiceList;
