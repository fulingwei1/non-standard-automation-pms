import React from "react";
import { Search } from "lucide-react";
import { Card, CardContent, Input, Button } from "../ui";
import { cn } from "../../lib/utils";
import { statusConfig, paymentStatusConfig } from "./constants";

const InvoiceFilters = ({
  searchText,
  setSearchText,
  filterStatus,
  setFilterStatus,
  filterPayment,
  setFilterPayment
}) => {
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
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filterStatus === "all" ? "default" : "ghost"}
              size="sm"
              onClick={() => setFilterStatus("all")}
            >
              全部状态
            </Button>
            {Object.entries(statusConfig).map(([key, config]) => (
              <Button
                key={key}
                variant={filterStatus === key ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterStatus(key)}
                className={cn(filterStatus === key && config.color)}
              >
                {config.label}
              </Button>
            ))}
            <div className="w-full border-t border-slate-700/30" />
            <Button
              variant={filterPayment === "all" ? "default" : "ghost"}
              size="sm"
              onClick={() => setFilterPayment("all")}
            >
              全部收款状态
            </Button>
            {Object.entries(paymentStatusConfig).map(([key, config]) => (
              <Button
                key={key}
                variant={filterPayment === key ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterPayment(key)}
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
