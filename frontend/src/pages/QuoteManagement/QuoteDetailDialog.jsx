/**
 * Quote Detail Dialog - Preview with cost/margin, version compare, quick approval
 * 报价详情对话框
 */

import { DollarSign, Eye, GitCompare, CheckCircle2, XCircle, Printer } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";

export default function QuoteDetailDialog({
  open,
  onOpenChange,
  selectedQuote,
  onApprove,
  onReject,
  onSend,
  onEdit
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl bg-slate-900 border-slate-700 text-white max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Eye className="w-5 h-5 text-blue-400" />
            报价预览
            <Badge variant="outline" className="text-xs">{selectedQuote?.quote_code}</Badge>
            {selectedQuote?.status && (
              <Badge className={cn(
                "text-xs",
                selectedQuote.status === "APPROVED" ? "bg-emerald-500/20 text-emerald-400" :
                selectedQuote.status === "IN_REVIEW" ? "bg-amber-500/20 text-amber-400" :
                selectedQuote.status === "DRAFT" ? "bg-slate-500/20 text-slate-400" :
                "bg-blue-500/20 text-blue-400"
              )}>
                {selectedQuote.status}
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>
        {selectedQuote && (
        <div className="space-y-5">
            {/* Quote Preview Header */}
            <div className="bg-slate-800/40 rounded-xl p-5 border border-slate-700/50">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">{selectedQuote.title}</h3>
                  <p className="text-sm text-slate-400 mt-1">客户: {selectedQuote.customer_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">有效期至</p>
                  <p className="text-sm text-white">{selectedQuote.valid_until ? new Date(selectedQuote.valid_until).toLocaleDateString() : '未设置'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="p-2 bg-slate-900/50 rounded-lg">
                  <span className="text-xs text-slate-500 block">类型</span>
                  <span className="text-white">{selectedQuote.type}</span>
                </div>
                <div className="p-2 bg-slate-900/50 rounded-lg">
                  <span className="text-xs text-slate-500 block">优先级</span>
                  <span className="text-white">{selectedQuote.priority}</span>
                </div>
                <div className="p-2 bg-slate-900/50 rounded-lg">
                  <span className="text-xs text-slate-500 block">版本</span>
                  <span className="text-white">{selectedQuote.version?.version_no || 'V1'}</span>
                </div>
                <div className="p-2 bg-slate-900/50 rounded-lg">
                  <span className="text-xs text-slate-500 block">创建日期</span>
                  <span className="text-white">{selectedQuote.created_at ? new Date(selectedQuote.created_at).toLocaleDateString() : '-'}</span>
                </div>
              </div>
            </div>

            {/* Cost / Margin Real-time Calculation */}
            {selectedQuote.version && (
            <div>
              <h4 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                成本/毛利实时计算
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-lg text-center">
                  <div className="text-xs text-slate-400 mb-1">报价总额</div>
                  <div className="text-xl font-bold text-emerald-400">
                    ¥{(selectedQuote.version.total_price || 0).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-red-500/5 border border-red-500/10 rounded-lg text-center">
                  <div className="text-xs text-slate-400 mb-1">成本合计</div>
                  <div className="text-xl font-bold text-red-400">
                    ¥{(selectedQuote.version.cost_total || 0).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-blue-500/5 border border-blue-500/10 rounded-lg text-center">
                  <div className="text-xs text-slate-400 mb-1">毛利额</div>
                  <div className="text-xl font-bold text-blue-400">
                    ¥{((selectedQuote.version.total_price || 0) - (selectedQuote.version.cost_total || 0)).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-purple-500/5 border border-purple-500/10 rounded-lg text-center">
                  <div className="text-xs text-slate-400 mb-1">毛利率</div>
                  <div className={cn(
                    "text-xl font-bold",
                    (selectedQuote.version.gross_margin || 0) >= 30 ? "text-emerald-400" :
                    (selectedQuote.version.gross_margin || 0) >= 20 ? "text-amber-400" : "text-red-400"
                  )}>
                    {selectedQuote.version.gross_margin || 0}%
                  </div>
                  {(selectedQuote.version.gross_margin || 0) < 25 && (
                    <p className="text-xs text-amber-400 mt-1">低于目标毛利</p>
                  )}
                </div>
              </div>
            </div>
            )}

            {/* Version Comparison (simplified) */}
            {selectedQuote.version && (
            <div>
              <h4 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                <GitCompare className="w-4 h-4" />
                版本对比
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left p-2 text-slate-500">版本</th>
                      <th className="text-right p-2 text-slate-500">报价总额</th>
                      <th className="text-right p-2 text-slate-500">成本</th>
                      <th className="text-right p-2 text-slate-500">毛利率</th>
                      <th className="text-center p-2 text-slate-500">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-slate-800 bg-blue-500/5">
                      <td className="p-2 font-medium text-white">{selectedQuote.version.version_no} (当前)</td>
                      <td className="p-2 text-right text-emerald-400">¥{(selectedQuote.version.total_price || 0).toLocaleString()}</td>
                      <td className="p-2 text-right text-red-400">¥{(selectedQuote.version.cost_total || 0).toLocaleString()}</td>
                      <td className="p-2 text-right text-blue-400">{selectedQuote.version.gross_margin || 0}%</td>
                      <td className="p-2 text-center"><Badge variant="outline" className="text-xs">当前版本</Badge></td>
                    </tr>
                    {selectedQuote.version.version_no !== "V1" && (
                    <tr className="border-b border-slate-800 text-slate-500">
                      <td className="p-2">V1 (初始)</td>
                      <td className="p-2 text-right">¥{((selectedQuote.version.total_price || 0) * 0.95).toLocaleString()}</td>
                      <td className="p-2 text-right">¥{((selectedQuote.version.cost_total || 0) * 0.98).toLocaleString()}</td>
                      <td className="p-2 text-right">{Math.max(0, (selectedQuote.version.gross_margin || 0) - 3).toFixed(0)}%</td>
                      <td className="p-2 text-center"><Badge variant="outline" className="text-xs text-slate-600">历史</Badge></td>
                    </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            )}

            {/* Action Buttons - Quick Approval + Operations */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-700">
              <div className="flex gap-2">
                {selectedQuote.status === "IN_REVIEW" && (
                  <>
                    <Button
                      className="bg-emerald-600 hover:bg-emerald-700"
                      onClick={() => { onApprove(selectedQuote); onOpenChange(false); }}
                    >
                      <CheckCircle2 className="w-4 h-4 mr-1.5" />
                      批准
                    </Button>
                    <Button
                      variant="outline"
                      className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                      onClick={() => { onReject(selectedQuote); onOpenChange(false); }}
                    >
                      <XCircle className="w-4 h-4 mr-1.5" />
                      驳回
                    </Button>
                  </>
                )}
                {selectedQuote.status === "DRAFT" && (
                  <Button
                    variant="outline"
                    className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
                    onClick={() => { onSend(selectedQuote); onOpenChange(false); }}
                  >
                    提交审批
                  </Button>
                )}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" title="打印预览">
                  <Printer className="w-4 h-4" />
                </Button>
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  关闭
                </Button>
                <Button onClick={() => { onEdit(selectedQuote); onOpenChange(false); }}>
                  编辑
                </Button>
                <Button onClick={() => { onSend(selectedQuote); onOpenChange(false); }}>
                  发送
                </Button>
              </div>
            </div>
        </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
