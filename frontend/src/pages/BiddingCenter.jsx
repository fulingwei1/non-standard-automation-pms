/**
 * 投标中心
 * 管理投标项目、技术标书、竞争分析
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Target,
  Search,
  Filter,
  Plus,
  Calendar,
  Clock,
  Users,
  Building2,
  FileText,
  Eye,
  Edit,
  Trash2,
  MoreHorizontal,
  ChevronRight,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Timer,
  DollarSign,
  TrendingUp,
  Award,
  ThumbsDown,
  Paperclip,
  Upload,
  X,
  User,
  Briefcase,
  GitBranch,
  Send,
  FileCheck,
  Shield,
  Swords,
  Flag,
  Bell,
  Download,
  Calculator,
  MessageSquare } from
"lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger } from
"../components/ui/dropdown-menu";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi } from "../services/api";

// 投标阶段配置
const biddingStages = [
{ id: "tracking", name: "跟踪中", color: "bg-slate-500" },
{ id: "preparing", name: "准备中", color: "bg-blue-500" },
{ id: "submitted", name: "已投标", color: "bg-violet-500" },
{ id: "evaluating", name: "待开标", color: "bg-amber-500" },
{ id: "won", name: "已中标", color: "bg-emerald-500" },
{ id: "lost", name: "未中标", color: "bg-red-500" }];


// Mock 投标数据
// Mock data - 已移除，使用真实API
// 获取阶段样式
const getStageStyle = (stage) => {
  const config = biddingStages.find((s) => s.id === stage);
  return config?.color || "bg-slate-500";
};

// 获取阶段名称
const getStageName = (stage) => {
  const config = biddingStages.find((s) => s.id === stage);
  return config?.name || stage;
};

// 投标卡片组件
function BiddingCard({ bidding, onClick }) {
  const isUrgent = bidding.daysLeft > 0 && bidding.daysLeft <= 7;
  const isOverdue =
  bidding.daysLeft === 0 && !["won", "lost"].includes(bidding.stage);

  return (
    <motion.div
      variants={fadeIn}
      className={cn(
        "p-4 rounded-xl bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group",
        isUrgent && "border-amber-500/30",
        isOverdue && "border-red-500/30"
      )}
      onClick={() => onClick(bidding)}>

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", getStageStyle(bidding.stage))}>
              {getStageName(bidding.stage)}
            </Badge>
            {isUrgent &&
            <Badge className="text-xs bg-amber-500">
                <Timer className="w-3 h-3 mr-1" />
                紧急
            </Badge>
            }
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors line-clamp-2">
            {bidding.name}
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">{bidding.code}</p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}>

              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem>
              <FileText className="w-4 h-4 mr-2" />
              查看方案
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <Building2 className="w-3 h-3" />
          {bidding.customer}
        </span>
        <span className="flex items-center gap-1">
          <DollarSign className="w-3 h-3" />¥{bidding.amount}万
        </span>
      </div>

      {bidding.stage !== "won" && bidding.stage !== "lost" &&
      <div className="space-y-1 mb-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">准备进度</span>
            <span className="text-white">{bidding.progress}%</span>
          </div>
          <Progress value={bidding.progress} className="h-1.5" />
      </div>
      }

      {bidding.competitors.length > 0 &&
      <div className="flex items-center gap-2 mb-3">
          <Swords className="w-3 h-3 text-red-400" />
          <span className="text-xs text-slate-500">
            {bidding.competitors.length} 个竞争对手
          </span>
      </div>
      }

      <div className="flex items-center justify-between text-xs pt-3 border-t border-white/5">
        <span className="text-slate-500 flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          {bidding.deadline}
        </span>
        {bidding.daysLeft > 0 && !["won", "lost"].includes(bidding.stage) &&
        <span
          className={cn(
            "flex items-center gap-1",
            isUrgent ? "text-amber-400" : "text-slate-400"
          )}>

            <Timer className="w-3 h-3" />
            剩余 {bidding.daysLeft} 天
        </span>
        }
        {bidding.stage === "won" &&
        <span className="flex items-center gap-1 text-emerald-400">
            <Award className="w-3 h-3" />
            已中标
        </span>
        }
        {bidding.stage === "lost" &&
        <span className="flex items-center gap-1 text-red-400">
            <ThumbsDown className="w-3 h-3" />
            未中标
        </span>
        }
      </div>
    </motion.div>);

}

// 投标详情面板
function BiddingDetailPanel({ bidding, onClose }) {
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
                <Button variant="ghost" size="sm">
                  <Eye className="w-4 h-4" />
                </Button>
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
                onClick={() => {
                  // 申请成本支持
                  const _updatedBidding = {
                    ...bidding,
                    costSupport: {
                      status: "requested",
                      requestedAt: new Date().toISOString().split("T")[0],
                      requestedBy: "当前用户",
                      estimatedCost: null,
                      submittedAt: null,
                      submittedBy: null
                    }
                  };
                  // 这里应该调用API更新
                  alert("成本支持申请已提交，售前技术工程师将尽快处理");
                }}>

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
              {bidding.documents.map((doc, index) =>
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
          {bidding.competitors.length > 0 &&
          <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Swords className="w-4 h-4 text-red-400" />
                竞争分析
              </h4>
              <div className="space-y-2">
                {bidding.competitors.map((competitor, index) =>
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
              {bidding.timeline.map((item, index) =>
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
                    {index < bidding.timeline.length - 1 &&
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

export default function BiddingCenter() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedBidding, setSelectedBidding] = useState(null);
  const [biddings, setBiddings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Map backend status to frontend stage
  const mapTenderStatus = (backendStatus) => {
    const statusMap = {
      TRACKING: "tracking",
      PREPARING: "preparing",
      SUBMITTED: "submitted",
      EVALUATING: "evaluating",
      WON: "won",
      LOST: "lost"
    };
    return statusMap[backendStatus] || "tracking";
  };

  // Load tenders from API
  const loadTenders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100
      };

      if (searchTerm) {
        params.keyword = searchTerm;
      }

      const response = await presaleApi.tenders.list(params);
      const tendersData = response.data?.items || response.data?.items || response.data || [];

      // Transform tenders
      const transformedTenders = tendersData.map((tender) => {
        const deadline = tender.submission_deadline ?
        new Date(tender.submission_deadline) :
        null;
        const now = new Date();
        const daysLeft = deadline ?
        Math.ceil((deadline - now) / (1000 * 60 * 60 * 24)) :
        0;

        return {
          id: tender.id,
          code: tender.tender_no || `BID-${tender.id}`,
          name: tender.tender_name || tender.project_name || "",
          customer: tender.customer_name || "",
          customerId: tender.customer_id,
          stage: mapTenderStatus(tender.status),
          deadline: deadline ? deadline.toISOString().split("T")[0] : "",
          daysLeft: daysLeft > 0 ? daysLeft : 0,
          amount: tender.budget ? tender.budget / 10000 : 0,
          engineer: tender.responsible_name || "",
          salesPerson: tender.sales_person_name || "",
          progress: tender.progress || 0,
          solution: tender.solution_id ? `SOL-${tender.solution_id}` : null,
          solutionName: tender.solution_name || null,
          techRequirements:
          tender.tech_requirements || tender.description || "",
          competitors: [],
          documents: [],
          timeline: [],
          notes: tender.notes || "",
          costSupport: {
            status: "none",
            requestedAt: null,
            requestedBy: null,
            estimatedCost: null,
            submittedAt: null,
            submittedBy: null
          }
        };
      });

      setBiddings(transformedTenders);
    } catch (err) {
      console.error("Failed to load tenders:", err);
      setError(err.response?.data?.detail || err.message || "加载投标项目失败");
      setBiddings([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  useEffect(() => {
    loadTenders();
  }, [loadTenders]);

  // 筛选投标
  const filteredBiddings = biddings.filter((bidding) => {
    const searchLower = searchTerm.toLowerCase();
    const name = (bidding.name || "").toLowerCase();
    const customer = (bidding.customer || "").toLowerCase();
    const code = (bidding.code || "").toLowerCase();

    return (
      name.includes(searchLower) ||
      customer.includes(searchLower) ||
      code.includes(searchLower));

  });

  // 按阶段分组（看板视图）
  const biddingsByStage = biddingStages.map((stage) => ({
    ...stage,
    biddings: filteredBiddings.filter((b) => b.stage === stage.id)
  }));

  // 统计数据
  const stats = {
    total: biddings.length,
    active: biddings.filter((b) => !["won", "lost"].includes(b.stage)).length,
    won: biddings.filter((b) => b.stage === "won").length,
    totalAmount: biddings.
    filter((b) => b.stage === "won").
    reduce((acc, b) => acc + b.amount, 0)
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 页面头部 */}
      <PageHeader
        title="投标中心"
        description="管理投标项目、技术标书、竞争分析"
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              新建投标
            </Button>
        </motion.div>
        } />


      {/* 统计卡片 */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4">

        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-500/10 flex items-center justify-center">
                <Target className="w-5 h-5 text-slate-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">全部项目</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Clock className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">进行中</p>
                <p className="text-2xl font-bold text-blue-400">
                  {stats.active}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <Award className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">已中标</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {stats.won}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-violet-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">中标金额</p>
                <p className="text-2xl font-bold text-violet-400">
                  ¥{stats.totalAmount}万
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4">

        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 搜索 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder="搜索项目名称、客户、编号..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full" />

          </div>
        </div>
      </motion.div>

      {/* 加载状态 */}
      {loading &&
      <div className="text-center py-16 text-slate-400">
          <Target className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
      </div>
      }

      {/* 错误提示 */}
      {error && !loading &&
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
      </div>
      }

      {/* 看板视图 */}
      {!loading && !error &&
      <motion.div
        variants={fadeIn}
        className="flex overflow-x-auto custom-scrollbar pb-4 -mx-6 px-6 gap-4">

          {biddingsByStage.map((column) =>
        <div key={column.id} className="flex-shrink-0 w-80">
              <Card className="bg-surface-50/70 backdrop-blur-sm border border-white/5 shadow-md">
                <CardHeader className="py-3 px-4 border-b border-white/5">
                  <CardTitle className="text-base font-semibold text-white flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <span
                    className={cn("w-2 h-2 rounded-full", column.color)} />

                      {column.name}
                    </span>
                    <Badge variant="secondary" className="bg-white/10">
                      {column.biddings.length}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 space-y-3 min-h-[300px] max-h-[calc(100vh-400px)] overflow-y-auto custom-scrollbar">
                  {column.biddings.length > 0 ?
              column.biddings.map((bidding) =>
              <BiddingCard
                key={bidding.id}
                bidding={bidding}
                onClick={setSelectedBidding} />

              ) :

              <div className="text-center py-8 text-slate-400">
                      <Target className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                      <p className="text-sm">暂无项目</p>
              </div>
              }
                </CardContent>
              </Card>
        </div>
        )}
      </motion.div>
      }

      {/* 投标详情面板 */}
      {selectedBidding &&
      <BiddingDetailPanel
        bidding={selectedBidding}
        onClose={() => setSelectedBidding(null)} />

      }
    </motion.div>);

}