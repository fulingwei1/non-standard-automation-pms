import React from "react";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { formatCurrency } from "../../lib/utils";

export function CostCheck({ costCheck }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>成本完整性检查</CardTitle>
        <CardDescription>
          检查成本拆解的完整性和毛利率是否符合要求
        </CardDescription>
      </CardHeader>
      <CardContent>
        {costCheck ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge
                className={
                  costCheck.is_complete ? "bg-green-500" : "bg-amber-500"
                }
              >
                {costCheck.is_complete ? "检查通过" : "存在问题"}
              </Badge>
              <span className="text-sm text-slate-400">
                总价: {formatCurrency(costCheck.total_price)} | 总成本:{" "}
                {formatCurrency(costCheck.total_cost)} | 毛利率:{" "}
                {costCheck.gross_margin?.toFixed(2)}%
              </span>
            </div>

            <div className="space-y-2">
              {costCheck.checks?.map((check, index) => (
                <Alert
                  key={index}
                  className={
                    check.status === "PASS"
                      ? "border-green-500"
                      : check.status === "WARNING"
                      ? "border-amber-500"
                      : "border-red-500"
                  }
                >
                  <div className="flex items-center gap-2">
                    {check.status === "PASS" && (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    )}
                    {check.status === "WARNING" && (
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                    )}
                    {check.status === "FAIL" && (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <AlertDescription>
                      <strong>{check.check_item}:</strong> {check.message}
                    </AlertDescription>
                  </div>
                </Alert>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">
            点击"成本检查"按钮进行检查
          </div>
        )}
      </CardContent>
    </Card>
  );
}
