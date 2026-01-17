/**
 * Finance Manager Dashboard - Main dashboard for finance department manager
 * Features: Financial overview, Budget control, Payment approval, Cost analysis, Team management
 * Core Functions: Financial team management, Budget monitoring, Financial analysis, Cash flow management
 */

import { useState, useMemo, useEffect, useCallback as _useCallback } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Briefcase,
  BarChart3,
  PieChart,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Building2,
  FileText,
  CreditCard,
  Receipt,
  Award,
  Activity,
  Zap,
  Search,
  Filter,
  Plus,
  Eye,
  Edit,
  Trash2,
  RefreshCw,
  Download } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter } from
"../components/ui/dialog";
import { cn as _cn, formatDate, formatCurrency } from "../lib/utils";
import { financeApi, userApi, budgetApi } from "../services/api";
import { toast } from "../components/ui/toast";
import {
  FINANCE_STATUS,
  FINANCE_TYPE,
  FINANCE_STATUS_LABELS,
  FINANCE_TYPE_LABELS,
  FINANCE_STATUS_COLORS,
  FINANCE_TYPE_COLORS,
  STATUS_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS,
  getFinanceStatusLabel,
  getFinanceTypeLabel,
  getFinanceStatusColor,
  getFinanceTypeColor,
  getIncomeExpenseStats,
  getFinanceStatusStats,
  getPendingApprovals,
  getOverduePayments } from
"../components/finance-dashboard";

export default function FinanceManagerDashboard() {
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [team, setTeam] = useState([]);
  const [searchQuery, _setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, _setFilterType] = useState("");
  const [selectedPeriod, _setSelectedPeriod] = useState("month");
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedPeriod, searchQuery, filterStatus, filterType]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const params = {
        period: selectedPeriod,
        search: searchQuery,
        status: filterStatus || undefined,
        type: filterType || undefined
      };

      const [transactionsRes, budgetsRes, teamRes] = await Promise.all([
      financeApi.list(params),
      budgetApi.list(params),
      userApi.list({ department: 'finance' })]
      );

      setTransactions(transactionsRes.data || []);
      setBudgets(budgetsRes.data || []);
      setTeam(teamRes.data || []);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      toast.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  // 计算财务统计数据
  const financialStats = useMemo(() => {
    const incomeExpenseStats = getIncomeExpenseStats(transactions);
    const statusStats = getFinanceStatusStats(transactions);
    const pendingApprovals = getPendingApprovals(transactions);
    const overduePayments = getOverduePayments(transactions);

    return {
      ...incomeExpenseStats,
      ...statusStats,
      pendingApprovals: pendingApprovals.length,
      overduePayments: overduePayments.length
    };
  }, [transactions]);

  // 计算预算统计
  const budgetStats = useMemo(() => {
    let totalBudget = 0;
    let totalSpent = 0;

    budgets.forEach((budget) => {
      totalBudget += parseFloat(budget.amount) || 0;
      totalSpent += parseFloat(budget.spent) || 0;
    });

    return {
      totalBudget,
      totalSpent,
      utilization: totalBudget > 0 ? Math.round(totalSpent / totalBudget * 100) : 0
    };
  }, [budgets]);

  // 获取最近交易
  const recentTransactions = useMemo(() => {
    return transactions.
    sort((a, b) => new Date(b.date) - new Date(a.date)).
    slice(0, 5);
  }, [transactions]);

  // 获取紧急任务
  const urgentTasks = useMemo(() => {
    return transactions.filter((transaction) =>
    transaction.priority === 'urgent' &&
    transaction.status === FINANCE_STATUS.PENDING
    );
  }, [transactions]);

  const getStatusBadge = (status) => {
    return (
      <Badge
        variant="secondary"
        className="border-0"
        style={{
          backgroundColor: getFinanceStatusColor(status) + '20',
          color: getFinanceStatusColor(status)
        }}>

        {getFinanceStatusLabel(status)}
      </Badge>);

  };

  const getTypeBadge = (type) => {
    return (
      <Badge
        variant="secondary"
        className="border-0"
        style={{
          backgroundColor: getFinanceTypeColor(type) + '20',
          color: getFinanceTypeColor(type)
        }}>

        {getFinanceTypeLabel(type)}
      </Badge>);

  };

  const handleApproval = async (transactionId, approved) => {
    try {
      const newStatus = approved ? FINANCE_STATUS.APPROVED : FINANCE_STATUS.REJECTED;
      await financeApi.updateStatus(transactionId, { status: newStatus });
      toast.success(`交易已${approved ? '批准' : '拒绝'}`);
      fetchDashboardData();
    } catch (error) {
      console.error("Failed to update transaction:", error);
      toast.error("操作失败");
    }
  };

  const handleViewTransaction = (transaction) => {
    setSelectedTransaction(transaction);
    setShowDetailDialog(true);
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'createTransaction':
        toast.info('创建交易功能开发中...');
        break;
      case 'pendingApprovals':
        setFilterStatus(FINANCE_STATUS.PENDING);
        break;
      case 'budgetAnalysis':
        toast.info('预算分析功能开发中...');
        break;
      case 'teamManagement':
        toast.info('团队管理功能开发中...');
        break;
      default:
        break;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) =>
          <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          )}
        </div>
      </div>);

  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6">

      <PageHeader
        title="财务管理仪表板"
        description="财务概览、预算控制、支付审批、成本分析"
        actions={
        <div className="flex space-x-2">
            <Button variant="outline" onClick={fetchDashboardData}>
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              导出报表
            </Button>
          </div>
        } />


      {/* 财务概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总收入</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(financialStats.totalIncome)}
            </div>
            <p className="text-xs text-muted-foreground">
              本期收入
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总支出</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(financialStats.totalExpenses)}
            </div>
            <p className="text-xs text-muted-foreground">
              本期支出
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">净利润</CardTitle>
            <DollarSign className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${financialStats.netProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(financialStats.netProfit)}
            </div>
            <p className="text-xs text-muted-foreground">
              本期净利润
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">预算使用</CardTitle>
            <Target className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {budgetStats.utilization}%
            </div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(budgetStats.totalSpent)} / {formatCurrency(budgetStats.totalBudget)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 待处理和逾期提醒 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>待审批交易</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {transactions.
              filter((t) => t.status === FINANCE_STATUS.PENDING).
              slice(0, 5).
              map((transaction) =>
              <div key={transaction.id} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex-1">
                      <p className="font-medium">{transaction.description}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        {getTypeBadge(transaction.type)}
                        <span className="text-sm text-muted-foreground">
                          {formatCurrency(transaction.amount)}
                        </span>
                      </div>
                    </div>
                    <div className="flex space-x-1">
                      <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleApproval(transaction.id, true)}>

                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleApproval(transaction.id, false)}>

                        <X className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </div>
              )}
              {financialStats.pendingApprovals === 0 &&
              <p className="text-center text-muted-foreground py-4">暂无待审批交易</p>
              }
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>紧急提醒</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium">逾期支付</span>
                </div>
                <Badge variant="destructive">{financialStats.overduePayments}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">紧急交易</span>
                </div>
                <Badge variant="secondary">{urgentTasks.length}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Briefcase className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">团队待办</span>
                </div>
                <Badge variant="outline">{team.length}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 最近交易 */}
      <Card>
        <CardHeader>
          <CardTitle>最近交易</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>日期</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>金额</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTransactions.map((transaction) =>
                <TableRow key={transaction.id}>
                    <TableCell>{formatDate(transaction.date)}</TableCell>
                    <TableCell className="font-medium">{transaction.description}</TableCell>
                    <TableCell>{getTypeBadge(transaction.type)}</TableCell>
                    <TableCell className={transaction.type === FINANCE_TYPE.INCOME ? 'text-green-600' : 'text-red-600'}>
                      {transaction.type === FINANCE_TYPE.INCOME ? '+' : '-'}
                      {formatCurrency(transaction.amount)}
                    </TableCell>
                    <TableCell>{getStatusBadge(transaction.status)}</TableCell>
                    <TableCell>
                      <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewTransaction(transaction)}>

                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                )}
                {recentTransactions.length === 0 &&
                <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      暂无交易记录
                    </TableCell>
                  </TableRow>
                }
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* 快速操作 */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => handleQuickAction('createTransaction')}>

              <Plus className="h-6 w-6" />
              <span className="text-sm">新建交易</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => handleQuickAction('pendingApprovals')}>

              <Clock className="h-6 w-6" />
              <span className="text-sm">待审批</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => handleQuickAction('budgetAnalysis')}>

              <BarChart3 className="h-6 w-6" />
              <span className="text-sm">预算分析</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => handleQuickAction('teamManagement')}>

              <Users className="h-6 w-6" />
              <span className="text-sm">团队管理</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>交易详情</DialogTitle>
          </DialogHeader>
          {selectedTransaction &&
          <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">交易编号</p>
                  <p className="font-medium">{selectedTransaction.id}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">交易日期</p>
                  <p className="font-medium">{formatDate(selectedTransaction.date)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">描述</p>
                  <p className="font-medium">{selectedTransaction.description}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">类型</p>
                  <div className="mt-1">{getTypeBadge(selectedTransaction.type)}</div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">金额</p>
                  <p className={`font-medium ${selectedTransaction.type === FINANCE_TYPE.INCOME ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedTransaction.type === FINANCE_TYPE.INCOME ? '+' : '-'}
                    {formatCurrency(selectedTransaction.amount)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">状态</p>
                  <div className="mt-1">{getStatusBadge(selectedTransaction.status)}</div>
                </div>
              </div>
              
              {selectedTransaction.notes &&
            <div>
                  <p className="text-sm text-muted-foreground">备注</p>
                  <p className="font-medium">{selectedTransaction.notes}</p>
                </div>
            }
            </div>
          }
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}