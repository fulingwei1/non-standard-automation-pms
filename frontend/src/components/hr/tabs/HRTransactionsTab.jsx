/**
 * HRTransactionsTab Component
 * 人事事务 Tab 组件
 */
import { useMemo } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  EmptyState,
} from "../../ui";
import {
  UserPlus,
  UserMinus,
  UserCheck,
  TrendingUp,
  ArrowRightLeft,
  BadgeDollarSign,
  FileText,
  Search,
  Plus,
} from "lucide-react";
import { cn, formatDate } from "../../../lib/utils";
import { useHRTransactions } from "../hooks/useHRTransactions";
import { hrApi } from "../../../services/api";
import { toast } from "../../ui/toast";

// 动态导入图标组件
const iconMap = {
  UserPlus,
  UserMinus,
  UserCheck,
  TrendingUp,
  ArrowRightLeft,
  BadgeDollarSign,
  FileText,
};

export default function HRTransactionsTab() {
  const {
    transactions,
    statistics,
    loading,
    filter,
    setFilter,
    transactionTypeMap,
    statusMap,
    loadTransactions,
  } = useHRTransactions();

  // 处理审批
  const handleApprove = async (transaction, action) => {
    try {
      await hrApi.transactions.approve(transaction.id, {
        status: action === "approve" ? "approved" : "rejected",
        approval_remark: action === "approve" ? "同意" : "拒绝",
      });
      toast.success(action === "approve" ? "审批通过" : "已拒绝");
      loadTransactions();
    } catch {
      toast.error("操作失败");
    }
  };

  // 筛选事务
  const filteredTransactions = useMemo(() => {
    return transactions.filter((t) => {
      if (filter.searchText) {
        const search = filter.searchText.toLowerCase();
        const name = t.employee?.name?.toLowerCase() || "";
        const code = t.employee?.employee_code?.toLowerCase() || "";
        if (!name.includes(search) && !code.includes(search)) return false;
      }
      return true;
    });
  }, [transactions, filter.searchText]);

  // 获取图标组件
  const getIcon = (iconName) => {
    return iconMap[iconName] || FileText;
  };

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Object.entries(transactionTypeMap).map(([type, config]) => {
          const Icon = getIcon(config.icon);
          const count = statistics?.by_type?.[type] || 0;
          return (
            <Card key={type} className="bg-surface-50 border-white/10">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "p-2 rounded-lg",
                      `bg-${config.color}-500/20`,
                    )}
                  >
                    <Icon
                      className={cn("w-5 h-5", `text-${config.color}-400`)}
                    />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{count}</p>
                    <p className="text-xs text-slate-400">{config.label}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Filter and Actions */}
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex flex-wrap gap-3 items-center">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="搜索员工姓名或工号..."
                  value={filter.searchText}
                  onChange={(e) =>
                    setFilter({ ...filter, searchText: e.target.value })
                  }
                  className="pl-9 w-64 bg-surface-100 border-white/10"
                />
              </div>
              <select
                value={filter.type}
                onChange={(e) => setFilter({ ...filter, type: e.target.value })}
                className="px-3 py-2 rounded-md bg-surface-100 border border-white/10 text-white text-sm"
              >
                <option value="all">全部类型</option>
                {Object.entries(transactionTypeMap).map(([key, config]) => (
                  <option key={key} value={key}>
                    {config.label}
                  </option>
                ))}
              </select>
              <select
                value={filter.status}
                onChange={(e) =>
                  setFilter({ ...filter, status: e.target.value })
                }
                className="px-3 py-2 rounded-md bg-surface-100 border border-white/10 text-white text-sm"
              >
                <option value="all">全部状态</option>
                {Object.entries(statusMap).map(([key, config]) => (
                  <option key={key} value={key}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>
            <Button
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => {
                // TODO: 打开新建事务对话框
                toast.info("新建事务功能待实现");
              }}
            >
              <Plus className="w-4 h-4 mr-2" />
              新建事务
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Transactions List */}
      <Card className="bg-surface-50 border-white/10">
        <CardHeader>
          <CardTitle className="text-white">人事事务列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 bg-surface-100 rounded-lg animate-pulse"
                />
              ))}
            </div>
          ) : filteredTransactions.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="暂无人事事务"
              description="没有符合条件的人事事务记录"
            />
          ) : (
            <div className="space-y-3">
              {filteredTransactions.map((transaction) => {
                const typeConfig =
                  transactionTypeMap[transaction.transaction_type] || {};
                const statusConfig = statusMap[transaction.status] || {};
                const TypeIcon = getIcon(typeConfig.icon) || FileText;

                return (
                  <div
                    key={transaction.id}
                    className="p-4 bg-surface-100 rounded-lg border border-white/5 hover:border-white/10 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div
                          className={cn(
                            "p-2 rounded-lg",
                            `bg-${typeConfig.color || "slate"}-500/20`,
                          )}
                        >
                          <TypeIcon
                            className={cn(
                              "w-5 h-5",
                              `text-${typeConfig.color || "slate"}-400`,
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-white">
                              {transaction.employee?.name || "未知员工"}
                            </span>
                            <span className="text-xs text-slate-400">
                              {transaction.employee?.employee_code}
                            </span>
                            <Badge
                              className={cn(
                                "text-xs",
                                `bg-${typeConfig.color || "slate"}-500/20 text-${typeConfig.color || "slate"}-400`,
                              )}
                            >
                              {typeConfig.label || transaction.transaction_type}
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-400 mt-1">
                            {transaction.transaction_type === "onboarding" && (
                              <>
                                入职部门:{" "}
                                {transaction.initial_department || "-"} / 职位:{" "}
                                {transaction.initial_position || "-"}
                              </>
                            )}
                            {transaction.transaction_type === "resignation" && (
                              <>
                                离职原因:{" "}
                                {transaction.resignation_reason || "-"} /
                                最后工作日:{" "}
                                {transaction.last_working_date || "-"}
                              </>
                            )}
                            {transaction.transaction_type ===
                              "confirmation" && (
                              <>
                                转正日期: {transaction.confirmation_date || "-"}
                              </>
                            )}
                            {transaction.transaction_type ===
                              "salary_adjustment" && (
                              <>
                                薪资调整: ¥
                                {transaction.from_salary?.toLocaleString() || 0}{" "}
                                → ¥
                                {transaction.to_salary?.toLocaleString() || 0}
                              </>
                            )}
                            {transaction.transaction_type === "promotion" && (
                              <>
                                晋升: {transaction.from_level || "-"} →{" "}
                                {transaction.to_level || "-"}
                              </>
                            )}
                            {transaction.transaction_type === "transfer" && (
                              <>
                                调岗: {transaction.from_department || "-"} →{" "}
                                {transaction.to_department || "-"}
                              </>
                            )}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <Badge
                            className={cn(
                              "text-xs",
                              `bg-${statusConfig.color || "slate"}-500/20 text-${statusConfig.color || "slate"}-400`,
                            )}
                          >
                            {statusConfig.label || transaction.status}
                          </Badge>
                          <p className="text-xs text-slate-500 mt-1">
                            {formatDate(transaction.transaction_date)}
                          </p>
                        </div>
                        {transaction.status === "pending" && (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700"
                              onClick={() =>
                                handleApprove(transaction, "approve")
                              }
                            >
                              通过
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                              onClick={() =>
                                handleApprove(transaction, "reject")
                              }
                            >
                              拒绝
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
