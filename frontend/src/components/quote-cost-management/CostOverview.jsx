import React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { formatCurrency, cn } from "../../lib/utils";

export function CostOverview({ totals, marginStatus }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-400">
            总价
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatCurrency(totals.totalPrice)}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-400">
            总成本
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatCurrency(totals.totalCost)}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-400">
            毛利率
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={cn("text-2xl font-bold", marginStatus.textColor)}>
            {totals.grossMargin.toFixed(2)}%
          </div>
          <Badge className={cn("mt-2", marginStatus.color)}>
            {marginStatus.label}
          </Badge>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-400">
            利润
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-400">
            {formatCurrency(totals.totalPrice - totals.totalCost)}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
