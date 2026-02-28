

import { formatCurrency, formatDate } from "../../lib/utils";
import { Badge, Button, Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, Input, Label } from "../ui";
import { AlertTriangle } from "lucide-react";

export default function CostSuggestionsDialog({
  open,
  onOpenChange,
  costSuggestions,
  items,
  editedSuggestions,
  onSuggestionChange,
  onApply,
  loading = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>成本匹配建议</DialogTitle>
          <DialogDescription>
            AI已生成成本匹配建议，请确认并修改后应用。系统已检查异常情况。
          </DialogDescription>
        </DialogHeader>

        {costSuggestions && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="bg-slate-800 rounded-lg p-4 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">匹配统计</span>
                <div className="flex gap-4 text-sm">
                  <span>
                    总项数: <strong>{costSuggestions.total_items}</strong>
                  </span>
                  <span className="text-green-400">
                    匹配成功: <strong>{costSuggestions.matched_count}</strong>
                  </span>
                  <span className="text-amber-400">
                    未匹配: <strong>{costSuggestions.unmatched_count}</strong>
                  </span>
                </div>
              </div>
              {costSuggestions.summary && (
                <div className="grid grid-cols-3 gap-4 text-sm mt-2">
                  <div>
                    <span className="text-slate-400">当前总成本:</span>
                    <div className="font-medium">
                      {formatCurrency(
                        costSuggestions.summary.current_total_cost || 0
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-400">建议总成本:</span>
                    <div className="font-medium text-blue-400">
                      {formatCurrency(
                        costSuggestions.summary.suggested_total_cost || 0
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-400">建议毛利率:</span>
                    <div className="font-medium text-green-400">
                      {costSuggestions.summary.suggested_margin !== null
                        ? `${costSuggestions.summary.suggested_margin.toFixed(2)}%`
                        : "-"}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Warnings */}
            {costSuggestions.warnings &&
              costSuggestions.warnings?.length > 0 && (
                <div className="bg-amber-900/20 border border-amber-500/50 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-medium text-amber-400 mb-1">
                        整体异常警告
                      </div>
                      <ul className="text-sm text-slate-300 space-y-1">
                        {(costSuggestions.warnings || []).map((warning, idx) => (
                          <li key={idx}>• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

            {/* Suggestions List */}
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {costSuggestions.suggestions?.map((suggestion) => {
                const edited = editedSuggestions[suggestion.item_id] || {};
                const item = (items || []).find((i) => i.id === suggestion.item_id);

                return (
                  <div
                    key={suggestion.item_id}
                    className="border border-slate-700 rounded-lg p-4 space-y-3"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium">{suggestion.item_name}</div>
                        {suggestion.reason && (
                          <div className="text-xs text-slate-400 mt-1">
                            匹配原因: {suggestion.reason}
                            {suggestion.match_score &&
                              ` (匹配度: ${suggestion.match_score}%)`}
                          </div>
                        )}
                      </div>
                      {suggestion.matched_cost_record && (
                        <Badge className="bg-blue-500">
                          来源:{" "}
                          {suggestion.matched_cost_record.supplier_name ||
                            "历史采购"}
                        </Badge>
                      )}
                    </div>

                    {/* Warnings */}
                    {suggestion.warnings &&
                      suggestion.warnings?.length > 0 && (
                        <div className="bg-amber-900/20 border border-amber-500/50 rounded p-2 text-sm">
                          {(suggestion.warnings || []).map((warning, idx) => (
                            <div key={idx} className="text-amber-400">
                              ⚠ {warning}
                            </div>
                          ))}
                        </div>
                      )}

                    {/* Editable Fields */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs">当前成本</Label>
                        <div className="text-sm text-slate-400">
                          {suggestion.current_cost
                            ? formatCurrency(suggestion.current_cost)
                            : "未填写"}
                        </div>
                      </div>
                      <div>
                        <Label className="text-xs">建议成本 *</Label>
                        <Input
                          type="number"
                          value={
                            edited.cost ||
                            suggestion.suggested_cost ||
                            suggestion.current_cost ||
                            ""
                          }
                          onChange={(e) =>
                            onSuggestionChange(
                              suggestion.item_id,
                              "cost",
                              e.target.value
                            )
                          }
                          placeholder="0.00"
                          className="h-8"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">规格型号</Label>
                        <Input
                          value={
                            edited.specification ||
                            suggestion.suggested_specification ||
                            item?.specification ||
                            ""
                          }
                          onChange={(e) =>
                            onSuggestionChange(
                              suggestion.item_id,
                              "specification",
                              e.target.value
                            )
                          }
                          placeholder="规格型号"
                          className="h-8"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">单位</Label>
                        <Input
                          value={
                            edited.unit ||
                            suggestion.suggested_unit ||
                            item?.unit ||
                            ""
                          }
                          onChange={(e) =>
                            onSuggestionChange(
                              suggestion.item_id,
                              "unit",
                              e.target.value
                            )
                          }
                          placeholder="单位"
                          className="h-8"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">交期(天)</Label>
                        <Input
                          type="number"
                          value={
                            edited.lead_time_days ||
                            suggestion.suggested_lead_time_days ||
                            item?.lead_time_days ||
                            ""
                          }
                          onChange={(e) =>
                            onSuggestionChange(
                              suggestion.item_id,
                              "lead_time_days",
                              e.target.value
                            )
                          }
                          placeholder="交期"
                          className="h-8"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">成本分类</Label>
                        <Input
                          value={
                            edited.cost_category ||
                            suggestion.suggested_cost_category ||
                            item?.cost_category ||
                            ""
                          }
                          onChange={(e) =>
                            onSuggestionChange(
                              suggestion.item_id,
                              "cost_category",
                              e.target.value
                            )
                          }
                          placeholder="成本分类"
                          className="h-8"
                        />
                      </div>
                    </div>

                    {/* Matched Cost Record Info */}
                    {suggestion.matched_cost_record && (
                      <div className="text-xs text-slate-500 bg-slate-800/50 rounded p-2">
                        匹配记录: {suggestion.matched_cost_record.material_name}
                        {suggestion.matched_cost_record.specification &&
                          ` (${suggestion.matched_cost_record.specification})`}
                        {suggestion.matched_cost_record.purchase_date &&
                          ` | 采购日期: ${formatDate(suggestion.matched_cost_record.purchase_date)}`}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false);
            }}
          >
            取消
          </Button>
          <Button
            onClick={onApply}
            disabled={
              !costSuggestions || costSuggestions.suggestions?.length === 0 || loading
            }
          >
            确认应用
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
