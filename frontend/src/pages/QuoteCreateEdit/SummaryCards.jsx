/**
 * SummaryCards - 价格汇总、成本汇总、利润分析
 */
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { cn, formatCurrency } from "../../lib/utils";

export default function SummaryCards({ versionData, setVersionData, costStructure, grossMargin }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* 价格汇总 */}
      <Card>
        <CardHeader>
          <CardTitle>价格汇总</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">总价:</span>
              <span className="font-bold text-lg">
                {formatCurrency(versionData.total_price || 0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">税率:</span>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={versionData.tax_rate ?? ""}
                  onChange={(e) => {
                    const rate = parseFloat(e.target.value) || 0;
                    setVersionData({
                      ...versionData,
                      tax_rate: rate,
                      tax_amount: versionData.total_price * (rate / 100),
                      amount_with_tax: versionData.total_price * (1 + rate / 100),
                    });
                  }}
                  className="w-20"
                />
                <span>%</span>
              </div>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">税额:</span>
              <span className="font-medium">
                {formatCurrency(versionData.tax_amount || 0)}
              </span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span className="text-slate-500">含税总额:</span>
              <span className="font-bold text-xl text-emerald-600">
                {formatCurrency(versionData.amount_with_tax || 0)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 成本汇总 */}
      <Card>
        <CardHeader>
          <CardTitle>成本汇总</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">总成本:</span>
              <span className="font-bold text-lg">
                {formatCurrency(versionData.cost_total || 0)}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">材料成本:</span>
              <span>{formatCurrency(costStructure.material)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">人工成本:</span>
              <span>{formatCurrency(costStructure.labor)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">制造费用:</span>
              <span>{formatCurrency(costStructure.overhead)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 利润分析 */}
      <Card>
        <CardHeader>
          <CardTitle>利润分析</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">毛利:</span>
              <span className="font-medium">
                {formatCurrency(
                  (versionData.total_price || 0) - (versionData.cost_total || 0),
                )}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">毛利率:</span>
              <Badge
                className={cn(
                  parseFloat(grossMargin) >= 20 && "bg-emerald-500",
                  parseFloat(grossMargin) >= 15 &&
                    parseFloat(grossMargin) < 20 &&
                    "bg-amber-500",
                  parseFloat(grossMargin) < 15 && "bg-red-500",
                  "bg-slate-500",
                )}
              >
                {grossMargin}%
              </Badge>
            </div>
            {parseFloat(grossMargin) < 15 && (
              <div className="text-xs text-red-600 mt-2">
                ⚠️ 毛利率低于15%，存在盈利风险
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
