/**
 * 投标详情面板组件
 */
import { motion, AnimatePresence } from "framer-motion";
import {
  Clock,
  Building2,
  FileText,
  Eye,
  Edit,
  CheckCircle,
  AlertTriangle,
  X,
  User,
  GitBranch,
  Send,
  Shield,
  Swords,
  Flag,
  Calculator,
  MessageSquare,
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { cn } from "../../lib/utils";
import { getStageStyle, getStageName } from "./constants";

export function BiddingDetailPanel({
  bidding,
  onClose,
  onRequestCostSupport,
  onOpenSolution,
}) {
  if (!bidding) {return null;}

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge className={cn("text-xs", getStageStyle(bidding.stage))}>
                {getStageName(bidding.stage)}
              </Badge>
              <span className="text-xs text-slate-500">{bidding.code}</span>
            </div>
            <h2 className="text-lg font-semibold text-white">{bidding.name}</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5 text-slate-400" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-surface-50 p-3 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">招标单位</p>
              <p className="text-sm text-white flex items-center gap-1">
                <Building2 className="w-4 h-4 text-primary" />
                {bidding.customer}
              </p>
            </div>
            <div className="bg-surface-50 p-3 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">预计金额</p>
              <p className="text-sm text-emerald-400 font-medium">
                ¥{bidding.amount}万
              </p>
            </div>
            <div className="bg-surface-50 p-3 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">负责工程师</p>
              <p className="text-sm text-white flex items-center gap-1">
                <User className="w-4 h-4 text-primary" />
                {bidding.engineer}
              </p>
            </div>
            <div className="bg-surface-50 p-3 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">销售工程师</p>
              <p className="text-sm text-white flex items-center gap-1">
                <User className="w-4 h-4 text-primary" />
                {bidding.salesPerson}
              </p>
            </div>
          </div>

          {/* 截止时间 */}
          {bidding.daysLeft > 0 && !["won", "lost"].includes(bidding.stage) &&
          <div
            className={cn(
              "p-4 rounded-lg border",
              bidding.daysLeft <= 7 ?
              "bg-amber-500/10 border-amber-500/20" :
              "bg-surface-50 border-white/5"
            )}>

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400 mb-1">投标截止</p>
                  <p className="text-lg font-bold text-white">
                    {bidding.deadline}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-400 mb-1">剩余时间</p>
                  <p
                  className={cn(
                    "text-2xl font-bold",
                    bidding.daysLeft <= 7 ? "text-amber-400" : "text-white"
                  )}>

                    {bidding.daysLeft} 天
                  </p>
                </div>
              </div>
          </div>
          }

          {/* 技术要求 */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">技术要求</h4>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {bidding.techRequirements}
            </p>
          </div>

          {/* 关联方案 */}
          {bidding.solutionName &&
          <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400">关联方案</h4>
              <div className="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-primary" />
                  <span className="text-sm text-white">
                    {bidding.solutionName}
                  </span>
                </div>
                {bidding.solutionId && (
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="打开关联方案"
                  onClick={() => onOpenSolution?.(bidding)}
                >
                  <Eye className="w-4 h-4" />
                </Button>
                )}
              </div>
          </div>
          }

          {/* 成本支持 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Calculator className="w-4 h-4 text-primary" />
                成本支持
              </h4>
              {bidding.costSupport?.status === "none" &&
              <Button
                size="sm"
                variant="outline"
                onClick={() => onRequestCostSupport?.(bidding)}>

                  <MessageSquare className="w-4 h-4 mr-2" />
                  申请成本支持
              </Button>
              }
            </div>

            {bidding.costSupport?.status === "none" &&
            <div className="p-3 bg-slate-500/10 border border-slate-500/20 rounded-lg">
                <p className="text-xs text-slate-400">尚未申请成本支持</p>
            </div>
            }

            {bidding.costSupport?.status === "requested" &&
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-white">成本支持申请已提交</span>
                </div>
                <p className="text-xs text-slate-400">
                  申请时间：{bidding.costSupport.requestedAt} | 申请人员：
                  {bidding.costSupport.requestedBy}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  售前技术工程师正在处理中...
                </p>
            </div>
            }

            {bidding.costSupport?.status === "in_progress" &&
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Calculator className="w-4 h-4 text-amber-400" />
                  <span className="text-sm text-white">成本估算进行中</span>
                </div>
                <p className="text-xs text-slate-400">
                  售前技术工程师正在核算成本...
                </p>
            </div>
            }

            {bidding.costSupport?.status === "submitted" &&
            bidding.costSupport.estimatedCost &&
            <div className="space-y-3">
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-sm text-white">
                          成本估算已完成
                        </span>
                      </div>
                      <Badge className="bg-emerald-500/20 text-emerald-400 text-xs">
                        {bidding.costSupport.submittedAt}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div>
                        <p className="text-xs text-slate-400 mb-1">总成本</p>
                        <p className="text-lg font-bold text-white">
                          ¥{bidding.costSupport.estimatedCost.total}万
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">建议报价</p>
                        <p className="text-lg font-bold text-emerald-400">
                          ¥{bidding.costSupport.estimatedCost.suggestedPrice}万
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">毛利率</p>
                        <p
                      className={cn(
                        "text-base font-semibold",
                        bidding.costSupport.estimatedCost.grossMargin >= 30 ?
                        "text-emerald-400" :
                        bidding.costSupport.estimatedCost.grossMargin >=
                        20 ?
                        "text-amber-400" :
                        "text-red-400"
                      )}>

                          {bidding.costSupport.estimatedCost.grossMargin}%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">提交人</p>
                        <p className="text-sm text-white">
                          {bidding.costSupport.submittedBy}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 成本明细 */}
                  <div className="p-3 bg-surface-50 rounded-lg">
                    <p className="text-xs text-slate-400 mb-2">成本明细</p>
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">机械部分</span>
                        <span className="text-white">
                          ¥{bidding.costSupport.estimatedCost.mechanical}万
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">电气部分</span>
                        <span className="text-white">
                          ¥{bidding.costSupport.estimatedCost.electrical}万
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">软件部分</span>
                        <span className="text-white">
                          ¥{bidding.costSupport.estimatedCost.software}万
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">标准件/外购件</span>
                        <span className="text-white">
                          ¥{bidding.costSupport.estimatedCost.standard}万
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">人工成本</span>
                        <span className="text-white">
                          ¥{bidding.costSupport.estimatedCost.labor}万
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">其他费用</span>
                        <span className="text-white">
                          ¥{bidding.costSupport.estimatedCost.other}万
                        </span>
                      </div>
                    </div>
                  </div>
            </div>
            }
          </div>

          {/* 投标文件 */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">投标文件</h4>
            <div className="space-y-2">
              {(bidding.documents || []).map((doc, index) =>
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-surface-50 rounded-lg">

                  <div className="flex items-center gap-3 flex-1">
                    <FileText className="w-4 h-4 text-slate-400" />
                    <div className="flex-1">
                      <p className="text-sm text-white">{doc.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Progress
                        value={doc.progress}
                        className="flex-1 h-1.5" />

                        <span className="text-xs text-slate-400">
                          {doc.progress}%
                        </span>
                      </div>
                    </div>
                  </div>
                  {doc.status === "completed" &&
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                }
                  {doc.status === "in_progress" &&
                <Clock className="w-4 h-4 text-blue-500" />
                }
                  {doc.status === "pending" &&
                <AlertTriangle className="w-4 h-4 text-slate-500" />
                }
              </div>
              )}
            </div>
          </div>

          {/* 竞争分析 */}
          {bidding.competitors?.length > 0 &&
          <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Swords className="w-4 h-4 text-red-400" />
                竞争分析
              </h4>
              <div className="space-y-2">
                {(bidding.competitors || []).map((competitor, index) =>
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-surface-50 rounded-lg">

                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4 text-red-400" />
                      <span className="text-sm text-white">
                        {competitor.name}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {competitor.status === "confirmed" ?
                    "已确认" :
                    competitor.status === "rumored" ?
                    "传闻" :
                    competitor.status === "won" ?
                    "中标" :
                    "未中标"}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-400">
                      {competitor.price}
                    </span>
              </div>
              )}
              </div>
          </div>
          }

          {/* 时间线 */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-primary" />
              投标进程
            </h4>
            <div className="space-y-4">
              {(bidding.timeline || []).map((item, index) =>
              <div key={index} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div
                    className={cn(
                      "w-6 h-6 rounded-full flex items-center justify-center",
                      item.status === "completed" ?
                      "bg-emerald-500" :
                      item.status === "in_progress" ?
                      "bg-blue-500" :
                      "bg-slate-600"
                    )}>

                      {item.status === "completed" ?
                    <CheckCircle className="w-3 h-3 text-white" /> :
                    item.status === "in_progress" ?
                    <Clock className="w-3 h-3 text-white" /> :

                    <Flag className="w-3 h-3 text-white" />
                    }
                    </div>
                    {index < bidding.timeline?.length - 1 &&
                  <div
                    className={cn(
                      "w-px h-8 my-1",
                      item.status === "completed" ?
                      "bg-emerald-500" :
                      "bg-slate-700"
                    )} />

                  }
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-white">{item.event}</p>
                    <p className="text-xs text-slate-500">{item.date}</p>
                  </div>
              </div>
              )}
            </div>
          </div>

          {/* 备注 */}
          {bidding.notes &&
          <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400">备注</h4>
              <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
                {bidding.notes}
              </p>
          </div>
          }
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/5 flex gap-2">
          <Button variant="outline" className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            编辑
          </Button>
          {bidding.stage === "preparing" &&
          <Button className="flex-1">
              <Send className="w-4 h-4 mr-2" />
              提交投标
          </Button>
          }
        </div>
      </motion.div>
    </AnimatePresence>);

}
