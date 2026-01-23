/**
 * Quotation List Page - Sales quotation management
 * Features: Quotation list, creation, approval, version history
 */

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Search,
  Plus,
  Filter,
  List,
  LayoutGrid,
  Calendar,
  DollarSign,
  Building2,
  User,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Send,
  Copy,
  Edit,
  Eye,
  Download,
  ChevronRight,
  X,
  History,
  Percent,
  Target } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter } from
"../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";

// Status configuration
const statusConfig = {
  draft: { label: "草稿", color: "bg-slate-500", textColor: "text-slate-400" },
  pending_approval: {
    label: "待审批",
    color: "bg-amber-500",
    textColor: "text-amber-400"
  },
  approved: {
    label: "已审批",
    color: "bg-blue-500",
    textColor: "text-blue-400"
  },
  sent: {
    label: "已发送",
    color: "bg-purple-500",
    textColor: "text-purple-400"
  },
  accepted: {
    label: "已接受",
    color: "bg-emerald-500",
    textColor: "text-emerald-400"
  },
  rejected: { label: "已拒绝", color: "bg-red-500", textColor: "text-red-400" },
  expired: {
    label: "已过期",
    color: "bg-slate-600",
    textColor: "text-slate-500"
  }
};

// Mock quotation data
// Mock data - 已移除，使用真实API
export default function QuotationList() {
  const mockQuotations = [];
  const [viewMode, setViewMode] = useState("list");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedQuotation, setSelectedQuotation] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Filter quotations
  const filteredQuotations = useMemo(() => {
    return mockQuotations.filter((quote) => {
      const searchLower = (searchTerm || "").toLowerCase();
    const matchesSearch =
      !searchTerm ||
      (quote.name || "").toLowerCase().includes(searchLower) ||
      (quote.id || "").toLowerCase().includes(searchLower) ||
      (quote.customerShort || "").toLowerCase().includes(searchLower);

      const matchesStatus =
      selectedStatus === "all" || quote.status === selectedStatus;

      return matchesSearch && matchesStatus;
    });
  }, [searchTerm, selectedStatus]);

  // Stats
  const stats = useMemo(() => {
    if (mockQuotations.length === 0) {
      return {
        total: 0,
        pending: 0,
        accepted: 0,
        rejected: 0,
        totalValue: 0,
        avgDiscount: "0.0"
      };
    }

    return {
      total: mockQuotations.length,
      pending: mockQuotations.filter(
        (q) => q.status === "sent" || q.status === "pending_approval"
      ).length,
      accepted: mockQuotations.filter((q) => q.status === "accepted").length,
      rejected: mockQuotations.filter((q) => q.status === "rejected").length,
      totalValue: mockQuotations.reduce((sum, q) => sum + q.finalAmount, 0),
      avgDiscount: (
      mockQuotations.reduce((sum, q) => sum + q.discountPercent, 0) /
      mockQuotations.length).
      toFixed(1)
    };
  }, []);

  const handleQuotationClick = (quotation) => {
    setSelectedQuotation(quotation);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="报价管理"
        description="创建和管理销售报价单"
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button
            className="flex items-center gap-2"
            onClick={() => setShowCreateDialog(true)}>

              <Plus className="w-4 h-4" />
              新建报价
            </Button>
        </motion.div>
        } />


      {/* Stats Row */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4">

        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <FileText className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-xs text-slate-400">报价总数</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.pending}</p>
              <p className="text-xs text-slate-400">待确认</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.accepted}</p>
              <p className="text-xs text-slate-400">已接受</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Percent className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {stats.avgDiscount}%
              </p>
              <p className="text-xs text-slate-400">平均折扣</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div
        variants={fadeIn}
        className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">

        <div className="flex flex-wrap gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索报价单号、名称..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64" />

          </div>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">

            <option value="all">全部状态</option>
            {Object.entries(statusConfig).map(([key, val]) =>
            <option key={key} value={key}>
                {val.label}
            </option>
            )}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">
            共 {filteredQuotations.length} 个报价
          </span>
          <div className="flex border border-white/10 rounded-lg overflow-hidden">
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode("list")}>

              <List className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode("grid")}>

              <LayoutGrid className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Content */}
      <motion.div variants={fadeIn}>
        {viewMode === "list" ?
        <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      报价单
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      客户
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      关联商机
                    </th>
                    <th className="text-right p-4 text-sm font-medium text-slate-400">
                      报价金额
                    </th>
                    <th className="text-center p-4 text-sm font-medium text-slate-400">
                      折扣
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      有效期
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      状态
                    </th>
                    <th className="text-center p-4 text-sm font-medium text-slate-400">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQuotations.map((quote) => {
                  const statusConf = statusConfig[quote.status];
                  const isExpired =
                  new Date(quote.validUntil) < new Date() &&
                  quote.status !== "accepted";

                  return (
                    <tr
                      key={quote.id}
                      onClick={() => handleQuotationClick(quote)}
                      className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors">

                        <td className="p-4">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white">
                                {quote.name}
                              </span>
                              <Badge variant="secondary" className="text-xs">
                                V{quote.version}
                              </Badge>
                            </div>
                            <div className="text-xs text-slate-500">
                              {quote.id}
                            </div>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-slate-400">
                          {quote.customerShort}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-1 text-sm text-blue-400">
                            <Target className="w-3 h-3" />
                            {quote.opportunityName}
                          </div>
                        </td>
                        <td className="p-4 text-right">
                          <div className="text-amber-400 font-medium">
                            ¥{(quote.finalAmount / 10000).toFixed(0)}万
                          </div>
                          {quote.discountPercent > 0 &&
                        <div className="text-xs text-slate-500 line-through">
                              ¥{(quote.totalAmount / 10000).toFixed(0)}万
                        </div>
                        }
                        </td>
                        <td className="p-4 text-center">
                          {quote.discountPercent > 0 ?
                        <Badge
                          variant="secondary"
                          className="text-xs bg-red-500/20 text-red-400">

                              -{quote.discountPercent}%
                        </Badge> :

                        <span className="text-slate-500">-</span>
                        }
                        </td>
                        <td className="p-4">
                          <span
                          className={cn(
                            "text-sm",
                            isExpired ? "text-red-400" : "text-slate-400"
                          )}>

                            {quote.validUntil}
                          </span>
                        </td>
                        <td className="p-4">
                          <Badge
                          className={cn(
                            "text-xs",
                            statusConf.textColor,
                            "bg-transparent border-0"
                          )}>

                            <div
                            className={cn(
                              "w-2 h-2 rounded-full mr-1",
                              statusConf.color
                            )} />

                            {statusConf.label}
                          </Badge>
                        </td>
                        <td className="p-4">
                          <div className="flex justify-center gap-1">
                            <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8">

                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8">

                              <Copy className="w-4 h-4" />
                            </Button>
                            {quote.status === "approved" &&
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8">

                                <Send className="w-4 h-4 text-blue-400" />
                          </Button>
                          }
                          </div>
                        </td>
                    </tr>);

                })}
                </tbody>
              </table>
            </CardContent>
        </Card> :

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredQuotations.map((quote) => {
            const statusConf = statusConfig[quote.status];
            const isExpired =
            new Date(quote.validUntil) < new Date() &&
            quote.status !== "accepted";

            return (
              <Card
                key={quote.id}
                onClick={() => handleQuotationClick(quote)}
                className="cursor-pointer hover:border-primary/30 transition-colors">

                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-white">
                            {quote.name}
                          </h3>
                          <Badge variant="secondary" className="text-xs">
                            V{quote.version}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-500">{quote.id}</div>
                      </div>
                      <Badge
                      className={cn(
                        "text-xs",
                        statusConf.textColor,
                        "bg-transparent border-0"
                      )}>

                        <div
                        className={cn(
                          "w-2 h-2 rounded-full mr-1",
                          statusConf.color
                        )} />

                        {statusConf.label}
                      </Badge>
                    </div>

                    <div className="space-y-2 mb-3">
                      <div className="flex items-center gap-2 text-sm text-slate-400">
                        <Building2 className="w-4 h-4" />
                        {quote.customerShort}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-blue-400">
                        <Target className="w-4 h-4" />
                        {quote.opportunityName}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-white/5">
                      <div>
                        <div className="text-lg font-semibold text-amber-400">
                          ¥{(quote.finalAmount / 10000).toFixed(0)}万
                        </div>
                        {quote.discountPercent > 0 &&
                      <div className="text-xs text-red-400">
                            -{quote.discountPercent}%折扣
                      </div>
                      }
                      </div>
                      <div className="text-right">
                        <div
                        className={cn(
                          "text-xs",
                          isExpired ? "text-red-400" : "text-slate-400"
                        )}>

                          有效期: {quote.validUntil}
                        </div>
                      </div>
                    </div>
                  </CardContent>
              </Card>);

          })}
        </div>
        }

        {filteredQuotations.length === 0 &&
        <div className="text-center py-16">
            <FileText className="w-12 h-12 mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">暂无报价</h3>
            <p className="text-slate-400 mb-4">没有找到符合条件的报价单</p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新建报价
            </Button>
        </div>
        }
      </motion.div>

      {/* Quotation Detail Panel */}
      <AnimatePresence>
        {selectedQuotation &&
        <QuotationDetailPanel
          quotation={selectedQuotation}
          onClose={() => setSelectedQuotation(null)} />

        }
      </AnimatePresence>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建报价</DialogTitle>
            <DialogDescription>创建新的销售报价单</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="col-span-2 space-y-2">
              <label className="text-sm text-slate-400">报价名称 *</label>
              <Input placeholder="请输入报价名称" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">关联商机</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="">请选择商机</option>
                <option value="OPP001">BMS老化测试设备 - 深圳新能源</option>
                <option value="OPP003">ICT在线测试设备 - 惠州储能</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">有效期</label>
              <Input type="date" />
            </div>
            <div className="col-span-2 space-y-2">
              <label className="text-sm text-slate-400">报价明细</label>
              <div className="border border-white/10 rounded-lg p-4 bg-surface-50">
                <p className="text-sm text-slate-400 text-center">
                  保存基本信息后添加报价明细
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={() => setShowCreateDialog(false)}>创建报价</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}

// Quotation Detail Panel
function QuotationDetailPanel({ quotation, onClose }) {
  const statusConf = statusConfig[quotation.status];
  const profitMargin = (
  (quotation.finalAmount - quotation.costAmount) / quotation.finalAmount *
  100).
  toFixed(1);

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col">

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
            )}>

            <div
              className={cn("w-2 h-2 rounded-full mr-1", statusConf.color)} />

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
              {quotation.discountPercent > 0 &&
              <div className="text-sm text-slate-500 line-through">
                  原价: ¥{(quotation.totalAmount / 10000).toFixed(2)}万
              </div>
              }
            </div>
            <div className="text-right">
              {quotation.discountPercent > 0 &&
              <Badge className="bg-red-500/20 text-red-400 mb-2">
                  -{quotation.discountPercent}%折扣
              </Badge>
              }
              <div className="text-sm text-slate-400">利润率</div>
              <div
                className={cn(
                  "text-lg font-semibold",
                  parseFloat(profitMargin) > 25 ?
                  "text-emerald-400" :
                  "text-amber-400"
                )}>

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
              <span className="text-blue-400">{quotation.opportunityName}</span>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">有效期:</span>
              <span
                className={cn(
                  new Date(quotation.validUntil) < new Date() ?
                  "text-red-400" :
                  "text-white"
                )}>

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
                {quotation.items.map((item, index) =>
                <tr key={index} className="border-t border-white/5">
                    <td className="p-3 text-white">{item.name}</td>
                    <td className="p-3 text-center text-slate-400">
                      {item.qty}
                    </td>
                    <td className="p-3 text-right text-slate-400">
                      ¥{(item.unitPrice / 10000).toFixed(1)}万
                    </td>
                    <td className="p-3 text-right text-white">
                      ¥{(item.unitPrice * item.qty / 10000).toFixed(1)}万
                    </td>
                </tr>
                )}
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
        {quotation.approvalNote &&
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-amber-400 text-sm">
              <AlertTriangle className="w-4 h-4" />
              {quotation.approvalNote}
            </div>
        </div>
        }

        {/* Reject Reason */}
        {quotation.rejectReason &&
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <XCircle className="w-4 h-4" />
              拒绝原因: {quotation.rejectReason}
            </div>
        </div>
        }

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
            {quotation.status === "approved" &&
            <Button variant="outline" size="sm" className="justify-start">
                <Send className="w-4 h-4 mr-2 text-amber-400" />
                发送客户
            </Button>
            }
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        {quotation.status === "draft" &&
        <Button className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            编辑
        </Button>
        }
      </div>
    </motion.div>);

}
