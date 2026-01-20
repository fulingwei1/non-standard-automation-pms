/**
 * Invoice Filters Component
 */

import { Search } from "lucide-react";
import { Card, CardContent, Button, Input } from "../../components/ui";
import { cn } from "../../lib/utils";
import { statusConfig, paymentStatusConfig } from "./constants";

export default function InvoiceFilters({
  searchText,
  onSearchChange,
  filterStatus,
  onStatusChange,
  filterPayment,
  onPaymentChange
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
            <Input
              placeholder="搜索发票号、项目名、客户名..."
              value={searchText}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filterStatus === "all" ? "default" : "ghost"}
              size="sm"
              onClick={() => onStatusChange("all")}
            >
              全部状态
            </Button>
            {Object.entries(statusConfig).map(([key, config]) => (
              <Button
                key={key}
                variant={filterStatus === key ? "default" : "ghost"}
                size="sm"
                onClick={() => onStatusChange(key)}
                className={cn(filterStatus === key && config.color)}
              >
                {config.label}
              </Button>
            ))}
            <div className="w-full border-t border-slate-700/30" />
            <Button
              variant={filterPayment === "all" ? "default" : "ghost"}
              size="sm"
              onClick={() => onPaymentChange("all")}
            >
              全部收款状态
            </Button>
            {Object.entries(paymentStatusConfig).map(([key, config]) => (
              <Button
                key={key}
                variant={filterPayment === key ? "default" : "ghost"}
                size="sm"
                onClick={() => onPaymentChange(key)}
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
}
