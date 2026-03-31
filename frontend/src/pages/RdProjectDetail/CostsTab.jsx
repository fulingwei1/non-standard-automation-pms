import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  Button,
  Badge,
} from "../../components/ui";
import { formatDate, formatCurrency } from "../../lib/utils";

export default function CostsTab({ id, costs, costSummary }) {
  const navigate = useNavigate();

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">费用归集</h3>
        <Button onClick={() => navigate(`/rd-projects/${id}/costs/entry`)}>
          录入费用
        </Button>
      </div>

      {/* Cost Summary */}
      {costSummary && (
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              费用汇总
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg bg-white/[0.03]">
                <p className="text-sm text-slate-400 mb-1">总费用</p>
                <p className="text-xl font-semibold text-white">
                  {formatCurrency(costSummary.total_cost || 0)}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-white/[0.03]">
                <p className="text-sm text-slate-400 mb-1">人工费用</p>
                <p className="text-xl font-semibold text-emerald-400">
                  {formatCurrency(costSummary.labor_cost || 0)}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-white/[0.03]">
                <p className="text-sm text-slate-400 mb-1">材料费用</p>
                <p className="text-xl font-semibold text-blue-400">
                  {formatCurrency(costSummary.material_cost || 0)}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-white/[0.03]">
                <p className="text-sm text-slate-400 mb-1">加计扣除</p>
                <p className="text-xl font-semibold text-primary">
                  {formatCurrency(costSummary.deductible_amount || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cost List */}
      <Card>
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            费用明细
          </h3>
          {costs.length > 0 ? (
            <div className="space-y-3">
              {(costs || []).map((cost) => (
                <div
                  key={cost.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-white">
                        {cost.cost_no}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {cost.cost_date ? formatDate(cost.cost_date) : ""}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-400">
                      {cost.cost_description || "无描述"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-white">
                      {formatCurrency(cost.cost_amount || 0)}
                    </p>
                    {cost.deductible_amount && (
                      <p className="text-xs text-primary">
                        扣除: {formatCurrency(cost.deductible_amount)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              暂无费用记录
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
