/**
 * Acceptance Management (客户验收管理 FAT/SAT)
 * 验收记录管理 - 检查清单 + 问题追踪 + 签收
 */

import { useState, useEffect, useMemo } from "react";

import { motion } from "framer-motion";
import {
  ClipboardCheck,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Eye,
  Edit,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Clock,
  FileText,
  TrendingUp,
  Calendar,
  MapPin,
  Users,
  ClipboardList
} from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
  toast
} from "../components/ui";
import { cn } from "../lib/utils";
import { PageHeader } from "../components/layout";

import { acceptanceApi } from "../services/api/acceptance";
import { projectApi } from "../services/api/projects";

// 状态配置
const STATUS_CONFIG = {
  draft: { label: "草稿", color: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
  in_progress: { label: "进行中", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  passed: { label: "通过", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  failed: { label: "失败", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  signed: { label: "已签收", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
};

// 类型配置
const TYPE_CONFIG = {
  FAT: { label: "FAT", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  SAT: { label: "SAT", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
};

// 结果配置
const RESULT_CONFIG = {
  pass: { label: "通过", color: "bg-emerald-500/20 text-emerald-400" },
  fail: { label: "失败", color: "bg-red-500/20 text-red-400" },
  conditional: { label: "有条件通过", color: "bg-amber-500/20 text-amber-400" },
};

const AcceptanceManagement = () => {
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState({ total: 0, passed: 0, failed: 0, pending: 0 });
  const [searchText, setSearchText] = useState("");
  const [filters, setFilters] = useState({ type: "", status: "" });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // 加载项目列表
  useEffect(() => {
    loadProjects();
  }, []);

  // 加载验收记录
  useEffect(() => {
    loadRecords();
  }, [filters]);

  const loadProjects = async () => {
    try {
      const res = await projectApi.list({ page: 1, page_size: 200 });
      const items = res?.data?.items || res?.data || [];
      setProjects(items);
    } catch (_err) {
      setProjects([]);
    }
  };

  const loadRecords = async () => {
    setLoading(true);
    try {
      const params = { page: 1, page_size: 100 };
      if (filters.type) params.acceptance_type = filters.type;
      if (filters.status) params.status = filters.status;

      const res = await acceptanceApi.list(params);
      const items = res?.data?.items || [];
      setRecords(items);

      // 计算统计
      const total = items.length;
      const passed = items.filter(r => r.status === "passed" || r.status === "signed").length;
      const failed = items.filter(r => r.status === "failed").length;
      const pending = items.filter(r => r.status === "draft" || r.status === "in_progress").length;

      setStats({ total, passed, failed, pending });
    } catch (_err) {
      toast({
        title: "错误",
        description: "加载验收记录失败",
        variant: "destructive"
      });
      setRecords([]);
      setStats({ total: 0, passed: 0, failed: 0, pending: 0 });
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredRecords = useMemo(() => {
    return records.filter((record) => {
      const searchLower = (searchText || "").toLowerCase();
      const matchesSearch = !searchText ||
        (record.title || "").toLowerCase().includes(searchLower) ||
        (record.project_name || "").toLowerCase().includes(searchLower) ||
        (record.acceptance_code || "").toLowerCase().includes(searchLower) ||
        (record.customer_representative || "").toLowerCase().includes(searchLower);

      return matchesSearch;
    });
  }, [records, searchText]);

  const handleCreate = async (formData) => {
    try {
      await acceptanceApi.create(formData);
      toast({ title: "成功", description: "创建成功" });
      setShowCreateDialog(false);
      loadRecords();
    } catch (_err) {
      toast({ title: "错误", description: "创建失败", variant: "destructive" });
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const res = await acceptanceApi.detail(id);
      setSelectedRecord(res?.data || res);
      setShowDetailDialog(true);
    } catch (_err) {
      toast({ title: "错误", description: "加载详情失败", variant: "destructive" });
    }
  };

  const getStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
    return (
      <Badge variant="outline" className={cn("border", config.color)}>
        {config.label}
      </Badge>
    );
  };

  const getTypeBadge = (type) => {
    const config = TYPE_CONFIG[type] || TYPE_CONFIG.FAT;
    return (
      <Badge variant="outline" className={cn("border font-medium", config.color)}>
        {config.label}
    </Badge>
    );
  };

  // 创建表单组件
  const CreateForm = () => {
    const [formData, setFormData] = useState({
      project_id: "",
      acceptance_type: "FAT",
      title: "",
      scheduled_date: "",
      location: "",
      customer_representative: "",
      our_representative: "",
      notes: "",
    });
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async () => {
      if (!formData.project_id) {
        toast({ title: "警告", description: "请选择项目", variant: "destructive" });
        return;
      }
      if (!formData.title) {
        toast({ title: "警告", description: "请填写验收标题", variant: "destructive" });
        return;
      }

      setSubmitting(true);
      await handleCreate(formData);
      setSubmitting(false);
    };

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">选择项目 *</label>
            <Select value={formData.project_id} onValueChange={(v) => setFormData({ ...formData, project_id: v })}>
              <SelectTrigger className="bg-surface-100 border-white/10">
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>
                    {p.project_name || p.project_code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-slate-400">验收类型 *</label>
            <Select value={formData.acceptance_type} onValueChange={(v) => setFormData({ ...formData, acceptance_type: v })}>
              <SelectTrigger className="bg-surface-100 border-white/10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FAT">FAT - 工厂验收测试</SelectItem>
                <SelectItem value="SAT">SAT - 现场验收测试</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="col-span-2 space-y-2">
            <label className="text-sm text-slate-400">验收标题 *</label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="例如：XX 项目 FAT 验收"
              className="bg-surface-100 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-slate-400">计划日期</label>
            <Input
              type="date"
              value={formData.scheduled_date}
              onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
              className="bg-surface-100 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-slate-400">验收地点</label>
            <Input
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="例如：公司装配车间"
              className="bg-surface-100 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-slate-400">客户代表</label>
            <Input
              value={formData.customer_representative}
              onChange={(e) => setFormData({ ...formData, customer_representative: e.target.value })}
              placeholder="客户方负责人"
              className="bg-surface-100 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-slate-400">我方代表</label>
            <Input
              value={formData.our_representative}
              onChange={(e) => setFormData({ ...formData, our_representative: e.target.value })}
              placeholder="我方负责人"
              className="bg-surface-100 border-white/10"
            />
          </div>

          <div className="col-span-2 space-y-2">
            <label className="text-sm text-slate-400">备注</label>
            <textarea
              rows={3}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="备注信息"
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "创建中..." : "创建"}
          </Button>
        </DialogFooter>
      </div>
    );
  };

  // 详情对话框组件
  const DetailDialog = () => {
    if (!selectedRecord) return null;

    const record = selectedRecord;
    const checklist = record.checklist || [];
    const issues = record.issues || [];

    return (
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5" />
            {record.acceptance_code} - {record.title}
          </DialogTitle>
          <DialogDescription>
            {record.project_name} | {TYPE_CONFIG[record.acceptance_type]?.label}验收
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 基本信息 */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-slate-400">状态</p>
              <div className="mt-1">{getStatusBadge(record.status)}</div>
            </div>
            <div>
              <p className="text-sm text-slate-400">计划日期</p>
              <p className="text-white mt-1">{record.scheduled_date || "-"}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">验收地点</p>
              <p className="text-white mt-1">{record.location || "-"}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">客户代表</p>
              <p className="text-white mt-1">{record.customer_representative || "-"}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">我方代表</p>
              <p className="text-white mt-1">{record.our_representative || "-"}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">总体结果</p>
              <p className="text-white mt-1">
                {record.overall_result ? (
                  <Badge className={RESULT_CONFIG[record.overall_result]?.color}>
                    {RESULT_CONFIG[record.overall_result]?.label}
                  </Badge>
                ) : "-"}
              </p>
            </div>
          </div>

          {/* 检查清单统计 */}
          {record.checklist_stats && (
            <Card className="bg-surface-100/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <ClipboardList className="w-4 h-4" />
                  检查清单
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-white">{record.checklist_stats.total}</p>
                    <p className="text-xs text-slate-400">总计</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-emerald-400">{record.checklist_stats.passed}</p>
                    <p className="text-xs text-slate-400">通过</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-400">{record.checklist_stats.failed}</p>
                    <p className="text-xs text-slate-400">失败</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-slate-400">{record.checklist_stats.pending}</p>
                    <p className="text-xs text-slate-400">待检</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 检查清单项 */}
          {checklist.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400">检查项目</h4>
              <div className="max-h-48 overflow-y-auto space-y-2">
                {checklist.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 bg-surface-100 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="text-xs">
                        {item.item_no}
                      </Badge>
                      <span className="text-sm text-white">{item.check_item}</span>
                    </div>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        item.status === "pass" && "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                        item.status === "fail" && "bg-red-500/20 text-red-400 border-red-500/30",
                        item.status === "pending" && "bg-slate-500/20 text-slate-400 border-slate-500/30",
                        item.status === "na" && "bg-slate-500/20 text-slate-500 border-slate-500/30"
                      )}
                    >
                      {item.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 问题统计 */}
          {record.issues_stats && (
            <Card className="bg-surface-100/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  问题追踪
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-white">{record.issues_stats.total}</p>
                    <p className="text-xs text-slate-400">总计</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-amber-400">{record.issues_stats.open}</p>
                    <p className="text-xs text-slate-400">待处理</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-400">{record.issues_stats.fixing}</p>
                    <p className="text-xs text-slate-400">修复中</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-emerald-400">{record.issues_stats.closed}</p>
                    <p className="text-xs text-slate-400">已关闭</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 问题列表 */}
          {issues.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400">问题列表</h4>
              <div className="max-h-48 overflow-y-auto space-y-2">
                {issues.map((issue) => (
                  <div key={issue.id} className="flex items-center justify-between p-3 bg-surface-100 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-xs",
                          issue.severity === "critical" && "bg-red-500/20 text-red-400 border-red-500/30",
                          issue.severity === "major" && "bg-amber-500/20 text-amber-400 border-amber-500/30",
                          issue.severity === "minor" && "bg-slate-500/20 text-slate-400 border-slate-500/30"
                        )}
                      >
                        {issue.severity}
                      </Badge>
                      <span className="text-sm text-white">{issue.description}</span>
                    </div>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        issue.status === "open" && "bg-amber-500/20 text-amber-400 border-amber-500/30",
                        issue.status === "fixing" && "bg-blue-500/20 text-blue-400 border-blue-500/30",
                        issue.status === "resolved" && "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                        issue.status === "closed" && "bg-slate-500/20 text-slate-400 border-slate-500/30"
                      )}
                    >
                      {issue.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="p-6 bg-slate-900 min-h-screen"
    >
      {/* 页面头部 */}
      <PageHeader
        icon={ClipboardCheck}
        title="验收管理"
        description="客户验收管理 (FAT/SAT) - 检查清单 + 问题追踪 + 签收"
      />

      {/* 统计卡片 */}
      <motion.div  initial="hidden" animate="visible" className="grid grid-cols-4 gap-4 mb-6">
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总记录数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <FileText className="w-8 h-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已通过</p>
                <p className="text-2xl font-bold text-emerald-400">{stats.passed}</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已失败</p>
                <p className="text-2xl font-bold text-red-400">{stats.failed}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">进行中</p>
                <p className="text-2xl font-bold text-amber-400">{stats.pending}</p>
              </div>
              <Clock className="w-8 h-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 搜索和筛选 */}
      <Card className="mb-4 bg-surface-100/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="搜索验收编号、项目名称、客户代表..."
                value={searchText || "unknown"}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10 bg-surface-100 border-white/10"
              />
            </div>

            <Select value={filters.type} onValueChange={(v) => setFilters({ ...filters, type: v })}>
              <SelectTrigger className="w-32 bg-surface-100 border-white/10">
                <SelectValue placeholder="验收类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部</SelectItem>
                <SelectItem value="FAT">FAT</SelectItem>
                <SelectItem value="SAT">SAT</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filters.status} onValueChange={(v) => setFilters({ ...filters, status: v })}>
              <SelectTrigger className="w-32 bg-surface-100 border-white/10">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部</SelectItem>
                <SelectItem value="draft">草稿</SelectItem>
                <SelectItem value="in_progress">进行中</SelectItem>
                <SelectItem value="passed">通过</SelectItem>
                <SelectItem value="failed">失败</SelectItem>
                <SelectItem value="signed">已签收</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex-1" />

            <Button
              className="flex items-center gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus size={16} />
              新建验收
            </Button>

            <Button variant="outline" className="flex items-center gap-2" onClick={loadRecords}>
              <RefreshCw size={16} />
              刷新
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 数据表格 */}
      <Card className="bg-surface-100/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400">
              <ClipboardCheck className="w-16 h-16 mb-4 opacity-50" />
              <p>暂无验收记录</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">验收编号</TableHead>
                  <TableHead>项目名称</TableHead>
                  <TableHead className="w-20">类型</TableHead>
                  <TableHead>标题</TableHead>
                  <TableHead className="w-24">状态</TableHead>
                  <TableHead className="w-28">计划日期</TableHead>
                  <TableHead>客户代表</TableHead>
                  <TableHead>我方代表</TableHead>
                  <TableHead className="w-32">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRecords.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell className="font-mono text-sm">{record.acceptance_code}</TableCell>
                    <TableCell>
                      <div>
                        <p className="text-white">{record.project_name || "-"}</p>
                        <p className="text-xs text-slate-400">{record.project_code}</p>
                      </div>
                    </TableCell>
                    <TableCell>{getTypeBadge(record.acceptance_type)}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{record.title}</TableCell>
                    <TableCell>{getStatusBadge(record.status)}</TableCell>
                    <TableCell className="text-sm">{record.scheduled_date || "-"}</TableCell>
                    <TableCell className="text-sm">{record.customer_representative || "-"}</TableCell>
                    <TableCell className="text-sm">{record.our_representative || "-"}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(record.id)}
                        >
                          <Eye size={16} />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Edit size={16} />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 创建对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建验收记录</DialogTitle>
            <DialogDescription>
              创建新的 FAT/SAT 验收记录
            </DialogDescription>
          </DialogHeader>
          <CreateForm />
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DetailDialog />
      </Dialog>
    </motion.div>
  );
};

export default AcceptanceManagement;
