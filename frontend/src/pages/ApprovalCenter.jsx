/**
 * Approval Center - 审批中心页面
 * 使用 shadcn/ui 组件，深色主题
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  ClipboardCheck,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  FileText,
  Package,
  Users,
  Wrench,
  Eye,
  Check,
  X,
  Plus,
  RefreshCw,
  Download,
  Settings,
  TrendingUp,
  Filter,
} from "lucide-react";

import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "../components/ui/dialog";
import { cn } from "../lib/utils";

// 常量定义
const APPROVAL_TYPES = {
  PURCHASE: { label: "采购申请", color: "bg-blue-500", icon: Package },
  EXPENSE: { label: "费用报销", color: "bg-green-500", icon: FileText },
  LEAVE: { label: "请假申请", color: "bg-purple-500", icon: Users },
  CONTRACT: { label: "合同审批", color: "bg-orange-500", icon: FileText },
  OTHER: { label: "其他", color: "bg-slate-500", icon: Wrench },
};

const APPROVAL_STATUS = {
  PENDING: { label: "待审批", color: "bg-yellow-500", textColor: "text-yellow-500" },
  APPROVED: { label: "已通过", color: "bg-green-500", textColor: "text-green-500" },
  REJECTED: { label: "已拒绝", color: "bg-red-500", textColor: "text-red-500" },
  RETURNED: { label: "已退回", color: "bg-orange-500", textColor: "text-orange-500" },
};

const APPROVAL_PRIORITY = {
  URGENT: { label: "紧急", color: "bg-red-500" },
  HIGH: { label: "高", color: "bg-orange-500" },
  NORMAL: { label: "普通", color: "bg-blue-500" },
  LOW: { label: "低", color: "bg-slate-500" },
};

const ApprovalCenter = () => {
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [searchText, setSearchText] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterPriority, setFilterPriority] = useState("all");
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState(null);

  // 模拟数据
  const mockApprovals = [
    {
      id: 1,
      title: "服务器采购申请",
      type: "PURCHASE",
      status: "PENDING",
      priority: "HIGH",
      amount: 50000,
      initiator: "张三",
      initiatorRole: "技术经理",
      approver: "李四",
      approverRole: "部门总监",
      createdAt: "2024-01-18 09:30",
      deadline: "2024-01-20 18:00",
      description: "采购2台高性能服务器用于扩展云计算资源",
    },
    {
      id: 2,
      title: "办公设备采购",
      type: "PURCHASE",
      status: "APPROVED",
      priority: "NORMAL",
      amount: 15000,
      initiator: "王五",
      initiatorRole: "行政专员",
      approver: "李四",
      approverRole: "部门总监",
      createdAt: "2024-01-17 14:20",
      deadline: "2024-01-19 18:00",
      description: "采购办公电脑5台",
    },
    {
      id: 3,
      title: "差旅费用报销",
      type: "EXPENSE",
      status: "PENDING",
      priority: "NORMAL",
      amount: 3500,
      initiator: "赵六",
      initiatorRole: "销售经理",
      approver: "李四",
      approverRole: "部门总监",
      createdAt: "2024-01-18 10:15",
      deadline: "2024-01-22 18:00",
      description: "上海出差差旅费用报销",
    },
    {
      id: 4,
      title: "年假申请",
      type: "LEAVE",
      status: "REJECTED",
      priority: "LOW",
      amount: 0,
      initiator: "钱七",
      initiatorRole: "工程师",
      approver: "张三",
      approverRole: "技术经理",
      createdAt: "2024-01-16 09:00",
      deadline: "2024-01-18 18:00",
      description: "申请年假5天",
    },
    {
      id: 5,
      title: "供应商合同审批",
      type: "CONTRACT",
      status: "PENDING",
      priority: "URGENT",
      amount: 200000,
      initiator: "孙八",
      initiatorRole: "采购经理",
      approver: "总经理",
      approverRole: "总经理",
      createdAt: "2024-01-18 11:30",
      deadline: "2024-01-19 12:00",
      description: "新供应商年度框架合同",
    },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setTimeout(() => {
      setApprovals(mockApprovals);
      setLoading(false);
    }, 500);
  };

  // 过滤数据
  const filteredApprovals = useMemo(() => {
    return approvals.filter((approval) => {
      const matchesSearch =
        !searchText ||
        approval.title.toLowerCase().includes(searchText.toLowerCase()) ||
        approval.initiator?.toLowerCase().includes(searchText.toLowerCase());
      const matchesType = filterType === "all" || approval.type === filterType;
      const matchesStatus = filterStatus === "all" || approval.status === filterStatus;
      const matchesPriority = filterPriority === "all" || approval.priority === filterPriority;
      return matchesSearch && matchesType && matchesStatus && matchesPriority;
    });
  }, [approvals, searchText, filterType, filterStatus, filterPriority]);

  // 统计数据
  const stats = useMemo(() => {
    const pending = approvals.filter((a) => a.status === "PENDING").length;
    const approved = approvals.filter((a) => a.status === "APPROVED").length;
    const rejected = approvals.filter((a) => a.status === "REJECTED").length;
    const urgent = approvals.filter((a) => a.priority === "URGENT" && a.status === "PENDING").length;
    const total = approvals.length;
    const approvalRate = total > 0 ? ((approved / total) * 100).toFixed(1) : 0;
    return { pending, approved, rejected, urgent, total, approvalRate };
  }, [approvals]);

  const handleApprove = (id) => {
    setApprovals((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "APPROVED" } : a))
    );
  };

  const handleReject = (id) => {
    setApprovals((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "REJECTED" } : a))
    );
  };

  const renderStatCard = (title, value, icon, color, subText) => {
    const Icon = icon;
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">{title}</p>
              <p className={cn("text-3xl font-bold mt-1", color)}>{value}</p>
              {subText && (
                <p className="text-xs text-slate-500 mt-1">{subText}</p>
              )}
            </div>
            <div className={cn("p-3 rounded-lg", color.replace("text-", "bg-").replace("500", "500/20"))}>
              <Icon className={cn("h-6 w-6", color)} />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderStatCard("待审批", stats.pending, Clock, "text-yellow-500", `共 ${stats.total} 项`)}
        {renderStatCard("已通过", stats.approved, CheckCircle2, "text-green-500", `通过率 ${stats.approvalRate}%`)}
        {renderStatCard("已拒绝", stats.rejected, XCircle, "text-red-500", null)}
        {renderStatCard("紧急待办", stats.urgent, AlertCircle, "text-orange-500", "需立即处理")}
      </div>

      {/* 待办列表 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Clock className="h-5 w-5 text-yellow-500" />
            待处理审批
          </CardTitle>
          <CardDescription>需要您审批的事项</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredApprovals
              .filter((a) => a.status === "PENDING")
              .slice(0, 5)
              .map((approval) => {
                const TypeIcon = APPROVAL_TYPES[approval.type]?.icon || FileText;
                const priorityConfig = APPROVAL_PRIORITY[approval.priority];
                return (
                  <div
                    key={approval.id}
                    className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className={cn("p-2 rounded-lg", APPROVAL_TYPES[approval.type]?.color + "/20")}>
                        <TypeIcon className={cn("h-5 w-5", APPROVAL_TYPES[approval.type]?.color.replace("bg-", "text-"))} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{approval.title}</span>
                          <Badge className={cn("text-xs", priorityConfig?.color)}>
                            {priorityConfig?.label}
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {approval.initiator} · ¥{approval.amount?.toLocaleString()} · {approval.createdAt}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-slate-600 hover:bg-slate-700"
                        onClick={() => {
                          setSelectedApproval(approval);
                          setShowDetailModal(true);
                        }}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        查看
                      </Button>
                      <Button
                        size="sm"
                        className="bg-green-600 hover:bg-green-700"
                        onClick={() => handleApprove(approval.id)}
                      >
                        <Check className="h-4 w-4 mr-1" />
                        通过
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleReject(approval.id)}
                      >
                        <X className="h-4 w-4 mr-1" />
                        拒绝
                      </Button>
                    </div>
                  </div>
                );
              })}
            {filteredApprovals.filter((a) => a.status === "PENDING").length === 0 && (
              <div className="text-center py-8 text-slate-400">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-500" />
                <p>暂无待处理的审批</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 最近审批记录 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-500" />
            最近审批记录
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredApprovals
              .filter((a) => a.status !== "PENDING")
              .slice(0, 5)
              .map((approval) => {
                const statusConfig = APPROVAL_STATUS[approval.status];
                return (
                  <div
                    key={approval.id}
                    className="flex items-center justify-between p-3 bg-slate-900/30 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn("w-2 h-2 rounded-full", statusConfig?.color)} />
                      <div>
                        <span className="text-white">{approval.title}</span>
                        <span className="text-slate-400 text-sm ml-2">
                          {approval.initiator}
                        </span>
                      </div>
                    </div>
                    <Badge className={cn(statusConfig?.color, "text-white")}>
                      {statusConfig?.label}
                    </Badge>
                  </div>
                );
              })}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderList = () => (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-slate-800/50">
              <TableHead className="text-slate-300">审批信息</TableHead>
              <TableHead className="text-slate-300">类型</TableHead>
              <TableHead className="text-slate-300">状态</TableHead>
              <TableHead className="text-slate-300">优先级</TableHead>
              <TableHead className="text-slate-300">金额</TableHead>
              <TableHead className="text-slate-300">发起人</TableHead>
              <TableHead className="text-slate-300">时间</TableHead>
              <TableHead className="text-slate-300">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredApprovals.map((approval) => {
              const typeConfig = APPROVAL_TYPES[approval.type];
              const statusConfig = APPROVAL_STATUS[approval.status];
              const priorityConfig = APPROVAL_PRIORITY[approval.priority];
              const TypeIcon = typeConfig?.icon || FileText;
              return (
                <TableRow key={approval.id} className="border-slate-700 hover:bg-slate-800/50">
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <TypeIcon className="h-4 w-4 text-slate-400" />
                      <span className="text-white font-medium">{approval.title}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={cn(typeConfig?.color, "text-white text-xs")}>
                      {typeConfig?.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={cn(statusConfig?.color, "text-white text-xs")}>
                      {statusConfig?.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={cn("text-xs", priorityConfig?.color.replace("bg-", "border-"), priorityConfig?.color.replace("bg-", "text-"))}>
                      {priorityConfig?.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    ¥{approval.amount?.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-slate-300">{approval.initiator}</TableCell>
                  <TableCell className="text-slate-400 text-sm">{approval.createdAt}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => {
                          setSelectedApproval(approval);
                          setShowDetailModal(true);
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {approval.status === "PENDING" && (
                        <>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 w-8 p-0 text-green-500 hover:text-green-400"
                            onClick={() => handleApprove(approval.id)}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 w-8 p-0 text-red-500 hover:text-red-400"
                            onClick={() => handleReject(approval.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
        {filteredApprovals.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <FileText className="h-12 w-12 mx-auto mb-2" />
            <p>暂无审批记录</p>
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <PageHeader
        title="审批中心"
        description="各类业务申请的统一审批管理平台"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={loadData} disabled={loading}>
              <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
              刷新
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              发起申请
            </Button>
          </div>
        }
      />

      {/* 搜索和筛选 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索审批标题、发起人..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10 bg-slate-900/50 border-slate-700"
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[140px] bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="审批类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(APPROVAL_TYPES).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[120px] bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(APPROVAL_STATUS).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger className="w-[120px] bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="优先级" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部优先级</SelectItem>
                {Object.entries(APPROVAL_PRIORITY).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800/50 border border-slate-700">
          <TabsTrigger value="overview" className="data-[state=active]:bg-slate-700">
            <ClipboardCheck className="h-4 w-4 mr-2" />
            概览
          </TabsTrigger>
          <TabsTrigger value="pending" className="data-[state=active]:bg-slate-700">
            <Clock className="h-4 w-4 mr-2" />
            待审批
            {stats.pending > 0 && (
              <Badge className="ml-2 bg-yellow-500 text-white">{stats.pending}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="all" className="data-[state=active]:bg-slate-700">
            <FileText className="h-4 w-4 mr-2" />
            全部记录
          </TabsTrigger>
          <TabsTrigger value="statistics" className="data-[state=active]:bg-slate-700">
            <TrendingUp className="h-4 w-4 mr-2" />
            统计分析
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverview()}
        </TabsContent>

        <TabsContent value="pending" className="mt-6">
          {renderList()}
        </TabsContent>

        <TabsContent value="all" className="mt-6">
          {renderList()}
        </TabsContent>

        <TabsContent value="statistics" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">审批类型分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(APPROVAL_TYPES).map(([key, config]) => {
                    const count = approvals.filter((a) => a.type === key).length;
                    const percentage = approvals.length > 0 ? (count / approvals.length) * 100 : 0;
                    return (
                      <div key={key} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-300">{config.label}</span>
                          <span className="text-slate-400">{count} 项 ({percentage.toFixed(1)}%)</span>
                        </div>
                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={cn("h-full rounded-full", config.color)}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">审批状态统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(APPROVAL_STATUS).map(([key, config]) => {
                    const count = approvals.filter((a) => a.status === key).length;
                    const percentage = approvals.length > 0 ? (count / approvals.length) * 100 : 0;
                    return (
                      <div key={key} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-300">{config.label}</span>
                          <span className="text-slate-400">{count} 项 ({percentage.toFixed(1)}%)</span>
                        </div>
                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={cn("h-full rounded-full", config.color)}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* 详情弹窗 */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white">{selectedApproval?.title}</DialogTitle>
            <DialogDescription>审批详情</DialogDescription>
          </DialogHeader>
          {selectedApproval && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-900/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">金额</p>
                  <p className="text-2xl font-bold text-white">
                    ¥{selectedApproval.amount?.toLocaleString()}
                  </p>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">优先级</p>
                  <Badge className={cn("mt-1", APPROVAL_PRIORITY[selectedApproval.priority]?.color)}>
                    {APPROVAL_PRIORITY[selectedApproval.priority]?.label}
                  </Badge>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">状态</p>
                  <Badge className={cn("mt-1", APPROVAL_STATUS[selectedApproval.status]?.color)}>
                    {APPROVAL_STATUS[selectedApproval.status]?.label}
                  </Badge>
                </div>
              </div>

              <div className="bg-slate-900/50 p-4 rounded-lg">
                <p className="text-slate-400 text-sm mb-2">申请描述</p>
                <p className="text-white">{selectedApproval.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-400">发起人</p>
                  <p className="text-white">{selectedApproval.initiator} ({selectedApproval.initiatorRole})</p>
                </div>
                <div>
                  <p className="text-slate-400">当前审批人</p>
                  <p className="text-white">{selectedApproval.approver} ({selectedApproval.approverRole})</p>
                </div>
                <div>
                  <p className="text-slate-400">创建时间</p>
                  <p className="text-white">{selectedApproval.createdAt}</p>
                </div>
                <div>
                  <p className="text-slate-400">截止时间</p>
                  <p className="text-orange-400">{selectedApproval.deadline}</p>
                </div>
              </div>

              {selectedApproval.status === "PENDING" && (
                <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                  <Button
                    variant="outline"
                    className="border-slate-600"
                    onClick={() => setShowDetailModal(false)}
                  >
                    取消
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => {
                      handleReject(selectedApproval.id);
                      setShowDetailModal(false);
                    }}
                  >
                    <X className="h-4 w-4 mr-2" />
                    拒绝
                  </Button>
                  <Button
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => {
                      handleApprove(selectedApproval.id);
                      setShowDetailModal(false);
                    }}
                  >
                    <Check className="h-4 w-4 mr-2" />
                    通过
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </motion.div>
  );
};

export default ApprovalCenter;
