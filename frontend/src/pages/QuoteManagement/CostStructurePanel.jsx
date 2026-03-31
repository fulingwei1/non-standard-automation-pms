/**
 * Cost Structure & Supplier Panel (right 1/3 sidebar)
 * 成本结构与供应商面板
 */

import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { formatCurrency } from "../../lib/utils";

export default function CostStructurePanel({
  categories,
  suppliers,
  totalCostForRatio,
  costLoading
}) {
  return (
    <Card className="bg-slate-900/60 border-slate-800 text-white">
      <CardHeader>
        <CardTitle className="text-lg">成本结构与供应商</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {costLoading ? (
          <div className="space-y-4 animate-pulse">
            {[...Array(4)].map((_, idx) => (
              <div key={idx} className="h-14 rounded-lg bg-slate-800" />
            ))}
          </div>
        ) : (
          <>
            <div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-slate-300">成本构成</p>
                <Badge variant="secondary" className="bg-blue-500/10 text-blue-300">
                  TOP 分类
                </Badge>
              </div>
              {categories?.length === 0 ? (
                <p className="text-sm text-slate-500">暂无成本分类数据</p>
              ) : (
                <div className="space-y-3">
                  {(categories || []).map((cat) => {
                    const percent = totalCostForRatio
                      ? Math.round((cat.amount / totalCostForRatio) * 100)
                      : 0;
                    return (
                      <div key={cat.name} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span>{cat.name}</span>
                          <span className="text-slate-300">
                            {formatCurrency(cat.amount || 0)}
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{ width: `${Math.min(Math.max(percent, 3), 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-slate-300">优选供应商</p>
                <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-300">
                  TOP 供应商
                </Badge>
              </div>
              {suppliers.length === 0 ? (
                <p className="text-sm text-slate-500">暂无供应商数据</p>
              ) : (
                <div className="space-y-3">
                  {(suppliers || []).map((supplier, index) => (
                    <div
                      key={supplier.name}
                      className="flex items-center justify-between rounded-lg border border-slate-800 px-3 py-2"
                    >
                      <div>
                        <p className="text-sm text-white font-medium">
                          {supplier.name}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          采购额 {formatCurrency(supplier.amount || 0)}
                        </p>
                      </div>
                      <Badge variant="outline" className="border-slate-700 text-slate-300">
                        TOP {index + 1}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
