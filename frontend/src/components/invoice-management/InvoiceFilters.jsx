/**
 * InvoiceFilters - 发票筛选组件（可复用 UI 组件）
 *
 * ARCHITECTURE NOTE:
 * This is the authoritative implementation of the invoice filters component.
 * Located in components/invoice-management/ as a reusable UI component.
 * The pages/invoice/InvoiceFilters.jsx re-exports this with a prop-name adapter.
 *
 * Accepts both prop naming conventions for flexibility:
 * - setSearchText / setFilterStatus / setFilterPayment (direct state setters)
 * - onSearchChange / onStatusChange / onPaymentChange (callback-style)
 */

import React from "react";
import { Search } from "lucide-react";
import { Card, CardContent, Input, Button } from "../ui";
import { cn } from "../../lib/utils";
import { statusConfig, paymentStatusConfig } from "../../lib/constants/finance";

const InvoiceFilters = ({
 searchText,
 setSearchText,
 filterStatus,
 setFilterStatus,
 filterPayment,
 setFilterPayment,
 // 回调风格的别名（pages/invoice 使用此命名）
  onSearchChange,
 onStatusChange,
 onPaymentChange
}) => {
 // 兼容两种 prop 命名风格
 const handleSearchChange = onSearchChange || setSearchText;
  const handleStatusChange = onStatusChange || setFilterStatus;
 const handlePaymentChange = onPaymentChange || setFilterPayment;

 return (
 <Card>
 <CardContent className="pt-6">
  <div className="space-y-4">
  {/* Search */}
  <div className="relative">
  <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
  <Input
   placeholder="搜索发票号、项目名、客户名..."
   value={searchText || "unknown"}
   onChange={(e) => handleSearchChange(e.target.value)}
   className="pl-10"
  />
  </div>

    {/* Filter Buttons */}
  <div className="flex flex-wrap gap-2">
  <Button
   variant={filterStatus === "all" ? "default" : "ghost"}
     size="sm"
  onClick={() => handleStatusChange("all")}
   >
   全部状态
   </Button>
  {Object.entries(statusConfig).map(([key, config]) => (
    <Button
  key={key}
   variant={filterStatus === key ? "default" : "ghost"}
  size="sm"
   onClick={() => handleStatusChange(key)}
   className={cn(filterStatus === key && config.color)}
  >
     {config.label}
  </Button>
  ))}
  <div className="w-full border-t border-slate-700/30" />
  <Button
   variant={filterPayment === "all" ? "default" : "ghost"}
   size="sm"
    onClick={() => handlePaymentChange("all")}
  >
   全部收款状态
   </Button>
  {Object.entries(paymentStatusConfig).map(([key, config]) => (
  <Button
   key={key}
    variant={filterPayment === key ? "default" : "ghost"}
    size="sm"
   onClick={() => handlePaymentChange(key)}
    className={cn(filterPayment === key && config.color)}
  >
    {config.label}
  </Button>
  ))}
   </div>
  </div>
  </CardContent>
 </Card>
 );
};

export default InvoiceFilters;
