/**
 * Project Settlement Page - Project financial settlement management
 * Features: Settlement creation, Settlement query, Settlement approval, Settlement statistics
 */

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Receipt,
  Search,
  Filter,
  Plus,
  Download,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  DollarSign,
  Briefcase,
  Calendar,
  FileText,
  Eye,
  Edit,
  Check,
  X,
  Building2,
  CreditCard,
  TrendingUp,
  TrendingDown,
  BarChart3 } from
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
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";
import { cn, formatCurrency, formatDate as _formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { settlementApi } from "../services/api";

// Mock data - 已移除，使用真实API
const statusConfig = {
  DRAFT: {
    label: "草稿",
    color: "bg-slate-500/20 text-slate-400",
    icon: FileText
  },
  PENDING: {
    label: "待确认",
    color: "bg-amber-500/20 text-amber-400",
    icon: Clock
  },
  CONFIRMED: {
    label: "已确认",
    color: "bg-blue-500/20 text-blue-400",
    icon: CheckCircle2
  },
  SETTLED: {
    label: "已结算",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: CheckCircle2
  }
};

export default function ProjectSettlement() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedSettlement, setSelectedSettlement] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [_loading, setLoading] = useState(false);
  const [_error, setError] = useState(null);
  const [settlements, setSettlements] = useState([]);

  // Fetch settlements from API
  useEffect(() => {
    const fetchSettlements = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await settlementApi.list();
        const data = res.data?.items || res.data || [];
        setSettlements(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to load settlements:", err);
        setError("加载结算数据失败");
      } finally {
        setLoading(false);
      }
    };
    fetchSettlements();
  }, []);

  // Filter settlements
  const filteredSettlements = useMemo(() => {
    return settlements.filter((settlement) => {
      const matchesSearch =
      !searchTerm ||
      settlement.settlementNo.
      toLowerCase().
      includes(searchTerm.toLowerCase()) ||
      settlement.projectName.
      toLowerCase().
      includes(searchTerm.toLowerCase()) ||
      settlement.customerName.
      toLowerCase().
      includes(searchTerm.toLowerCase()) ||
      settlement.contractNo.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus =
      selectedStatus === "all" || settlement.status === selectedStatus;

      return matchesSearch && matchesStatus;
    });
  }, [settlements, searchTerm, selectedStatus]);

  // Statistics
  const stats = useMemo(() => {
    return {
      total: filteredSettlements.length,
      totalContractAmount: filteredSettlements.reduce(
        (sum, s) => sum + s.contractAmount,
        0
      ),
      totalCost: filteredSettlements.reduce((sum, s) => sum + s.totalCost, 0),
      totalProfit: filteredSettlements.reduce(
        (sum, s) => sum + s.grossProfit,
        0
      ),
      averageMargin:
      filteredSettlements.length > 0 ?
      filteredSettlements.reduce((sum, s) => sum + s.grossMargin, 0) /
      filteredSettlements.length :
      0,
      totalReceived: filteredSettlements.reduce(
        (sum, s) => sum + s.receivedAmount,
        0
      ),
      totalReceivable: filteredSettlements.reduce(
        (sum, s) => sum + s.receivableAmount,
        0
      )
    };
  }, [filteredSettlements]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="项目结算"
        description="项目财务结算、成本核算、利润分析"
        icon={Receipt}
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出报表
            </Button>
            <Button
            className="flex items-center gap-2"
            onClick={() => setShowCreateDialog(true)}>

              <Plus className="w-4 h-4" />
              创建结算
            </Button>
          </motion.div>
        } />


      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">合同总额</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(stats.totalContractAmount)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {stats.total}个项目
                </p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">总成本</p>
                <p className="text-2xl font-bold text-red-400">
                  {formatCurrency(stats.totalCost)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {stats.totalContractAmount > 0 ?
                  (
                  stats.totalCost / stats.totalContractAmount *
                  100).
                  toFixed(1) :
                  0}
                  %占比
                </p>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <TrendingDown className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">总利润</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {formatCurrency(stats.totalProfit)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  平均利润率: {stats.averageMargin.toFixed(1)}%
                </p>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">回款率</p>
                <p className="text-2xl font-bold text-cyan-400">
                  {stats.totalContractAmount > 0 ?
                  (
                  stats.totalReceived / stats.totalContractAmount *
                  100).
                  toFixed(1) :
                  0}
                  %
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  待收: {formatCurrency(stats.totalReceivable)}
                </p>
              </div>
              <div className="p-2 bg-cyan-500/20 rounded-lg">
                <CreditCard className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="搜索结算单号、项目、客户、合同号..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10" />

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
          </CardContent>
        </Card>
      </motion.div>

      {/* Settlement List */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Receipt className="h-5 w-5 text-purple-400" />
                结算单列表
              </CardTitle>
              <Badge variant="outline" className="bg-slate-700/40">
                {filteredSettlements.length}条
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredSettlements.map((settlement) => {
                const statusConf = statusConfig[settlement.status];
                const StatusIcon = statusConf?.icon || FileText;
                return (
                  <div
                    key={settlement.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    onClick={() => setSelectedSettlement(settlement)}>

                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-white">
                            {settlement.settlementNo}
                          </span>
                          <Badge
                            variant="outline"
                            className={cn("text-xs", statusConf?.color)}>

                            <StatusIcon className="w-3 h-3 mr-1" />
                            {settlement.statusLabel}
                          </Badge>
                        </div>
                        <div className="font-medium text-white text-sm mb-1">
                          {settlement.projectName}
                        </div>
                        <div className="text-xs text-slate-400 space-y-1">
                          <div>客户: {settlement.customerName}</div>
                          <div>
                            合同: {settlement.contractNo} · 合同金额:{" "}
                            {formatCurrency(settlement.contractAmount)}
                          </div>
                          {settlement.settlementDate &&
                          <div>
                              结算日期: {settlement.settlementDate} · 结算人:{" "}
                              {settlement.settledBy}
                            </div>
                          }
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-lg font-bold text-amber-400 mb-1">
                          {formatCurrency(settlement.contractAmount)}
                        </div>
                        <div className="text-sm text-emerald-400 mb-1">
                          利润: {formatCurrency(settlement.grossProfit)}
                        </div>
                        <div className="text-xs text-slate-400">
                          利润率: {settlement.grossMargin.toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {/* Cost Breakdown */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3 pt-3 border-t border-slate-700/50">
                      <div>
                        <div className="text-xs text-slate-400 mb-1">
                          材料成本
                        </div>
                        <div className="text-sm font-medium text-white">
                          {formatCurrency(settlement.materialCost)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 mb-1">
                          人工成本
                        </div>
                        <div className="text-sm font-medium text-white">
                          {formatCurrency(settlement.laborCost)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 mb-1">
                          外协费用
                        </div>
                        <div className="text-sm font-medium text-white">
                          {formatCurrency(settlement.outsourcingCost)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 mb-1">
                          其他费用
                        </div>
                        <div className="text-sm font-medium text-white">
                          {formatCurrency(
                            settlement.expenseCost + settlement.otherCost
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 mb-1">
                          总成本
                        </div>
                        <div className="text-sm font-bold text-red-400">
                          {formatCurrency(settlement.totalCost)}
                        </div>
                      </div>
                    </div>

                    {/* Payment Progress */}
                    <div className="pt-3 border-t border-slate-700/50">
                      <div className="flex items-center justify-between text-xs mb-2">
                        <span className="text-slate-400">回款进度</span>
                        <span className="text-white">
                          已收: {formatCurrency(settlement.receivedAmount)} /
                          待收: {formatCurrency(settlement.receivableAmount)}
                        </span>
                      </div>
                      <Progress
                        value={
                        settlement.receivedAmount /
                        settlement.contractAmount *
                        100
                        }
                        className="h-2 bg-slate-700/50" />

                    </div>
                  </div>);

              })}
              {filteredSettlements.length === 0 &&
              <div className="text-center py-12 text-slate-500">
                  暂无结算单
                </div>
              }
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Settlement Detail Dialog */}
      <Dialog
        open={!!selectedSettlement}
        onOpenChange={() => setSelectedSettlement(null)}>

        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>结算单详情</DialogTitle>
          </DialogHeader>
          {selectedSettlement &&
          <div className="py-4 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">结算单号</label>
                  <p className="text-white font-medium">
                    {selectedSettlement.settlementNo}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">项目</label>
                  <p className="text-white font-medium">
                    {selectedSettlement.projectName}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">客户</label>
                  <p className="text-white">
                    {selectedSettlement.customerName}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">合同号</label>
                  <p className="text-white">{selectedSettlement.contractNo}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">合同金额</label>
                  <p className="text-amber-400 font-bold text-lg">
                    {formatCurrency(selectedSettlement.contractAmount)}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">总成本</label>
                  <p className="text-red-400 font-bold text-lg">
                    {formatCurrency(selectedSettlement.totalCost)}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">利润</label>
                  <p className="text-emerald-400 font-bold text-lg">
                    {formatCurrency(selectedSettlement.grossProfit)}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">利润率</label>
                  <p className="text-emerald-400 font-bold text-lg">
                    {selectedSettlement.grossMargin.toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Cost Breakdown */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-3">
                  成本明细
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="p-3 bg-slate-800/40 rounded-lg">
                    <div className="text-xs text-slate-400 mb-1">材料成本</div>
                    <div className="text-lg font-bold text-white">
                      {formatCurrency(selectedSettlement.materialCost)}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-800/40 rounded-lg">
                    <div className="text-xs text-slate-400 mb-1">人工成本</div>
                    <div className="text-lg font-bold text-white">
                      {formatCurrency(selectedSettlement.laborCost)}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-800/40 rounded-lg">
                    <div className="text-xs text-slate-400 mb-1">外协费用</div>
                    <div className="text-lg font-bold text-white">
                      {formatCurrency(selectedSettlement.outsourcingCost)}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-800/40 rounded-lg">
                    <div className="text-xs text-slate-400 mb-1">其他费用</div>
                    <div className="text-lg font-bold text-white">
                      {formatCurrency(
                      selectedSettlement.expenseCost +
                      selectedSettlement.otherCost
                    )}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-800/40 rounded-lg border-2 border-red-500/30">
                    <div className="text-xs text-slate-400 mb-1">总成本</div>
                    <div className="text-lg font-bold text-red-400">
                      {formatCurrency(selectedSettlement.totalCost)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Payment Milestones */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-3">
                  收款节点
                </h3>
                <div className="space-y-2">
                  {selectedSettlement.milestones.map((milestone, index) =>
                <div
                  key={index}
                  className={cn(
                    "p-3 rounded-lg border",
                    milestone.received ?
                    "bg-emerald-500/10 border-emerald-500/30" :
                    "bg-slate-800/40 border-slate-700/50"
                  )}>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {milestone.received ?
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" /> :

                      <Clock className="w-5 h-5 text-slate-400" />
                      }
                          <div>
                            <div className="font-medium text-white">
                              {milestone.name}
                            </div>
                            {milestone.received ?
                        <div className="text-xs text-slate-400">
                                已收 · {milestone.receivedDate}
                              </div> :

                        <div className="text-xs text-slate-400">
                                待收 · 到期: {milestone.dueDate}
                              </div>
                        }
                          </div>
                        </div>
                        <div className="text-right">
                          <div
                        className={cn(
                          "font-bold",
                          milestone.received ?
                          "text-emerald-400" :
                          "text-amber-400"
                        )}>

                            {formatCurrency(milestone.amount)}
                          </div>
                        </div>
                      </div>
                    </div>
                )}
                </div>
              </div>
            </div>
          }
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectedSettlement(null)}>

              关闭
            </Button>
            {selectedSettlement?.status === "PENDING" &&
            <Button>确认结算</Button>
            }
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Settlement Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建结算单</DialogTitle>
            <DialogDescription>为项目创建财务结算单</DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-400">选择项目 *</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="">请选择项目</option>
                <option value="PJ250108001">BMS老化测试设备</option>
                <option value="PJ250106002">EOL功能测试设备</option>
                <option value="PJ250103003">ICT在线测试设备</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-slate-400">结算开始日期</label>
                <Input type="date" />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-slate-400">结算结束日期</label>
                <Input type="date" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">备注</label>
              <textarea
                placeholder="请输入备注信息..."
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-20" />

            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={() => setShowCreateDialog(false)}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}