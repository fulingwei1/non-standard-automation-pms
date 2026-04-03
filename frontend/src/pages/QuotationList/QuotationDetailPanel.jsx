import { motion } from "framer-motion";
import {
  X,
  Building2,
  Target,
  Calendar,
  User,
  Copy,
  History,
  Download,
  Send,
  Edit,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { Button, Badge } from "../../components/ui";
import { cn } from "../../lib/utils";
import { statusConfig } from "./statusConfig";

export function QuotationDetailPanel({ quotation, onClose }) {
  const statusConf = statusConfig[quotation.status];
  const profitMargin = (
    ((quotation.finalAmount - quotation.costAmount) /
      quotation.finalAmount) *
    100
  ).toFixed(1);

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold text-white">
                {quotation.name}
              </h2>
              <Badge variant="secondary">V{quotation.version}</Badge>
            </div>
            <p className="text-sm text-slate-400">{quotation.id}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <Badge
            className={cn(
              "text-xs",
              statusConf.textColor,
              "bg-transparent border-0"
            )}
          >
            <div
              className={cn("w-2 h-2 rounded-full mr-1", statusConf.color)}
            />
            {statusConf.label}
          </Badge>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Amount Summary */}
        <div className="p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-400">报价金额</div>
              <div className="text-2xl font-bold text-amber-400">
                ¥{(quotation.finalAmount / 10000).toFixed(2)}万
              </div>
              {quotation.discountPercent > 0 && (
                <div className="text-sm text-slate-500 line-through">
                  原价: ¥{(quotation.totalAmount / 10000).toFixed(2)}万
                </div>
              )}
            </div>
            <div className="text-right">
              {quotation.discountPercent > 0 && (
                <Badge className="bg-red-500/20 text-red-400 mb-2">
                  -{quotation.discountPercent}%折扣
                </Badge>
              )}
              <div className="text-sm text-slate-400">利润率</div>
              <div
                className={cn(
                  "text-lg font-semibold",
                  parseFloat(profitMargin) > 25
                    ? "text-emerald-400"
                    : "text-amber-400"
                )}
              >
                {profitMargin}%
              </div>
            </div>
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">基本信息</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <Building2 className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">客户:</span>
              <span className="text-white">{quotation.customerShort}</span>
            </div>
            <div className="flex items-center gap-3">
              <Target className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">商机:</span>
              <span className="text-blue-400">
                {quotation.opportunityName}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">有效期:</span>
              <span
                className={cn(
                  new Date(quotation.validUntil) < new Date()
                    ? "text-red-400"
                    : "text-white"
                )}
              >
                {quotation.validUntil}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <User className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">创建人:</span>
              <span className="text-white">{quotation.createdBy}</span>
            </div>
          </div>
        </div>

        {/* Items */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">报价明细</h3>
          <div className="border border-white/5 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-surface-50">
                  <th className="text-left p-3 text-slate-400">项目</th>
                  <th className="text-center p-3 text-slate-400">数量</th>
                  <th className="text-right p-3 text-slate-400">单价</th>
                  <th className="text-right p-3 text-slate-400">小计</th>
                </tr>
              </thead>
              <tbody>
                {(quotation.items || []).map((item, index) => (
                  <tr key={index} className="border-t border-white/5">
                    <td className="p-3 text-white">{item.name}</td>
                    <td className="p-3 text-center text-slate-400">
                      {item.qty}
                    </td>
                    <td className="p-3 text-right text-slate-400">
                      ¥{(item.unitPrice / 10000).toFixed(1)}万
                    </td>
                    <td className="p-3 text-right text-white">
                      ¥{((item.unitPrice * item.qty) / 10000).toFixed(1)}万
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-white/5 bg-surface-50">
                  <td colSpan={3} className="p-3 text-right text-slate-400">
                    合计:
                  </td>
                  <td className="p-3 text-right font-semibold text-amber-400">
                    ¥{(quotation.totalAmount / 10000).toFixed(1)}万
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Approval Note */}
        {quotation.approvalNote && (
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-amber-400 text-sm">
              <AlertTriangle className="w-4 h-4" />
              {quotation.approvalNote}
            </div>
          </div>
        )}

        {/* Reject Reason */}
        {quotation.rejectReason && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <XCircle className="w-4 h-4" />
              拒绝原因: {quotation.rejectReason}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">操作</h3>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm" className="justify-start">
              <Copy className="w-4 h-4 mr-2 text-blue-400" />
              复制报价
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <History className="w-4 h-4 mr-2 text-purple-400" />
              版本历史
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <Download className="w-4 h-4 mr-2 text-emerald-400" />
              导出PDF
            </Button>
            {quotation.status === "approved" && (
              <Button variant="outline" size="sm" className="justify-start">
                <Send className="w-4 h-4 mr-2 text-amber-400" />
                发送客户
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        {quotation.status === "draft" && (
          <Button className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            编辑
          </Button>
        )}
      </div>
    </motion.div>
  );
}
