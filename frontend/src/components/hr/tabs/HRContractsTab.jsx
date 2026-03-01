/**
 * HRContractsTab Component
 * 合同管理 Tab 组件
 */
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
  FileText,
  Bell,
  Search,
  Plus,
  AlertTriangle,
  RefreshCw,
  Eye,
} from "lucide-react";
import { cn, formatDate } from "../../../lib/utils";
import { useHRContracts } from "../hooks/useHRContracts";
import { hrApi } from "../../../services/api";
import { toast } from "../../ui/toast";

export default function HRContractsTab() {
  const {
    contracts,
    reminders,
    loading,
    activeSubTab,
    setActiveSubTab,
    filter,
    setFilter,
    contractTypeMap,
    contractStatusMap,
    reminderTypeMap,
    loadContracts,
    loadReminders,
  } = useHRContracts();

  // 处理合同续签
  const handleRenewContract = async (contract) => {
    try {
      await hrApi.contracts.renew(contract.id, {
        new_end_date: null, // 由后端计算
        duration_months: 36,
      });
      toast.success("合同续签成功");
      loadContracts();
      loadReminders();
    } catch {
      toast.error("续签失败");
    }
  };

  // 处理提醒操作
  const handleReminderAction = async (reminder, action) => {
    try {
      await hrApi.reminders.handle(reminder.id, {
        handle_action: action,
        handle_remark: action === "renew" ? "同意续签" : "不续签",
      });
      toast.success("处理成功");
      loadReminders();
    } catch {
      toast.error("操作失败");
    }
  };

  // 生成提醒
  const generateReminders = async () => {
    try {
      const response = await hrApi.reminders.generate();
      toast.success(`生成了 ${response.data?.created_count || 0} 条提醒`);
      loadReminders();
    } catch {
      toast.error("生成提醒失败");
    }
  };

  return (
    <div className="space-y-6">
      {/* Sub Tabs */}
      <div className="flex gap-2">
        <Button
          variant={activeSubTab === "all" ? "default" : "outline"}
          onClick={() => setActiveSubTab("all")}
          className={activeSubTab === "all" ? "bg-blue-600" : "border-white/10"}
        >
          <FileText className="w-4 h-4 mr-2" />
          全部合同
        </Button>
        <Button
          variant={activeSubTab === "expiring" ? "default" : "outline"}
          onClick={() => setActiveSubTab("expiring")}
          className={
            activeSubTab === "expiring" ? "bg-amber-600" : "border-white/10"
          }
        >
          <Bell className="w-4 h-4 mr-2" />
          到期提醒
          {reminders.length > 0 && (
            <Badge className="ml-2 bg-red-500 text-white">
              {reminders.length}
            </Badge>
          )}
        </Button>
      </div>

      {activeSubTab === "all" ? (
        <>
          {/* Filter */}
          <Card className="bg-surface-50 border-white/10">
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-4 items-center justify-between">
                <div className="flex flex-wrap gap-3 items-center">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索员工或合同编号..."
                      value={filter.searchText}
                      onChange={(e) =>
                        setFilter({ ...filter, searchText: e.target.value })
                      }
                      className="pl-9 w-64 bg-surface-100 border-white/10"
                    />
                  </div>
                  <select
                    value={filter.status}
                    onChange={(e) =>
                      setFilter({ ...filter, status: e.target.value })
                    }
                    className="px-3 py-2 rounded-md bg-surface-100 border border-white/10 text-white text-sm"
                  >
                    <option value="all">全部状态</option>
                    {Object.entries(contractStatusMap).map(([key, config]) => (
                      <option key={key} value={key || "unknown"}>
                        {config.label}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  className="bg-blue-600 hover:bg-blue-700"
                  onClick={() => {
                    toast.info("新建合同功能待实现");
                  }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  新建合同
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Contracts List */}
          <Card className="bg-surface-50 border-white/10">
            <CardHeader>
              <CardTitle className="text-white">合同列表</CardTitle>
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
              ) : contracts.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="暂无合同"
                  description="没有符合条件的合同记录"
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          合同编号
                        </th>
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          员工
                        </th>
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          合同类型
                        </th>
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          起始日期
                        </th>
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          到期日期
                        </th>
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          基本工资
                        </th>
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          状态
                        </th>
                        <th className="text-left py-3 px-4 text-slate-400 font-medium text-sm">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {(contracts || []).map((contract) => {
                        const statusConfig =
                          contractStatusMap[contract.status] || {};
                        return (
                          <tr
                            key={contract.id}
                            className="border-b border-white/5 hover:bg-surface-100/50"
                          >
                            <td className="py-3 px-4 text-white font-mono text-sm">
                              {contract.contract_no || "-"}
                            </td>
                            <td className="py-3 px-4">
                              <div>
                                <span className="text-white">
                                  {contract.employee?.name || "-"}
                                </span>
                                <span className="text-xs text-slate-400 ml-2">
                                  {contract.employee?.employee_code}
                                </span>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {contractTypeMap[contract.contract_type] ||
                                contract.contract_type}
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {formatDate(contract.start_date)}
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {contract.end_date
                                ? formatDate(contract.end_date)
                                : "无固定期限"}
                            </td>
                            <td className="py-3 px-4 text-white">
                              ¥{contract.base_salary?.toLocaleString() || "-"}
                            </td>
                            <td className="py-3 px-4">
                              <Badge
                                className={cn(
                                  "text-xs",
                                  `bg-${statusConfig.color || "slate"}-500/20 text-${statusConfig.color || "slate"}-400`,
                                )}
                              >
                                {statusConfig.label || contract.status}
                              </Badge>
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-blue-400 hover:text-blue-300"
                                  onClick={() => {
                                    toast.info("查看合同详情功能待实现");
                                  }}
                                >
                                  <Eye className="w-4 h-4" />
                                </Button>
                                {contract.status === "active" &&
                                  contract.end_date && (
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      className="text-emerald-400 hover:text-emerald-300"
                                      onClick={() =>
                                        handleRenewContract(contract)
                                      }
                                    >
                                      <RefreshCw className="w-4 h-4" />
                                    </Button>
                                  )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : (
        /* Expiring Contracts Tab */
        <>
          {/* Actions */}
          <Card className="bg-surface-50 border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  <span className="text-white">
                    合同到期提醒（提前60天自动生成）
                  </span>
                </div>
                <Button
                  className="bg-blue-600 hover:bg-blue-700"
                  onClick={generateReminders}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  生成提醒
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Reminders List */}
          <Card className="bg-surface-50 border-white/10">
            <CardHeader>
              <CardTitle className="text-white">到期提醒列表</CardTitle>
            </CardHeader>
            <CardContent>
              {reminders.length === 0 ? (
                <EmptyState
                  icon={Bell}
                  title="暂无到期提醒"
                  description="当前没有需要处理的合同到期提醒"
                />
              ) : (
                <div className="space-y-3">
                  {(reminders || []).map((reminder) => {
                    const typeConfig =
                      reminderTypeMap[reminder.reminder_type] || {};
                    return (
                      <div
                        key={reminder.id}
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
                              <Bell
                                className={cn(
                                  "w-5 h-5",
                                  `text-${typeConfig.color || "slate"}-400`,
                                )}
                              />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-white">
                                  {reminder.employee?.name || "未知员工"}
                                </span>
                                <span className="text-xs text-slate-400">
                                  {reminder.employee?.employee_code}
                                </span>
                                <Badge
                                  className={cn(
                                    "text-xs",
                                    `bg-${typeConfig.color || "slate"}-500/20 text-${typeConfig.color || "slate"}-400`,
                                  )}
                                >
                                  {typeConfig.label || reminder.reminder_type}
                                </Badge>
                              </div>
                              <p className="text-sm text-slate-400 mt-1">
                                合同到期日:{" "}
                                {formatDate(reminder.contract_end_date)}
                                {reminder.days_until_expiry > 0
                                  ? ` (还剩 ${reminder.days_until_expiry} 天)`
                                  : " (已到期)"}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700"
                              onClick={() =>
                                handleReminderAction(reminder, "renew")
                              }
                            >
                              续签
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-slate-500/30 text-slate-400 hover:bg-slate-500/10"
                              onClick={() =>
                                handleReminderAction(reminder, "terminate")
                              }
                            >
                              不续签
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
