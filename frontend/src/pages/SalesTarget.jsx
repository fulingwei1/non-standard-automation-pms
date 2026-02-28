/**
 * Sales Target Management Page
 * Features: Create sales targets (personal/team/department), Track progress, View target statistics
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Target,
  Plus,
  Edit,
  Trash2,
  TrendingUp,
  TrendingDown,
  Calendar,
  Users,
  Building2,
  User,
  Filter,
  Search,
  BarChart3,
  CheckCircle2,
  Clock,
  XCircle,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Label,
} from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { salesTargetApi, salesTeamApi } from "../services/api";
import { toast } from "sonner";
import { formatCurrencyCompact as formatCurrency } from "../lib/formatters";


const targetScopeOptions = [
  { value: "PERSONAL", label: "个人目标", icon: User },
  { value: "TEAM", label: "团队目标", icon: Users },
  { value: "DEPARTMENT", label: "部门目标", icon: Building2 },
];

const targetTypeOptions = [
  { value: "LEAD_COUNT", label: "线索数量", unit: "个" },
  { value: "OPPORTUNITY_COUNT", label: "商机数量", unit: "个" },
  { value: "CONTRACT_AMOUNT", label: "合同金额", unit: "元" },
  { value: "COLLECTION_AMOUNT", label: "回款金额", unit: "元" },
];

const targetPeriodOptions = [
  { value: "MONTHLY", label: "月度" },
  { value: "QUARTERLY", label: "季度" },
  { value: "YEARLY", label: "年度" },
];

export default function SalesTarget() {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    target_scope: "",
    target_type: "",
    target_period: "",
    status: "",
  });

  // Form state
  const [formData, setFormData] = useState({
    target_scope: "PERSONAL",
    user_id: null,
    department_id: null,
    team_id: null,
    target_type: "CONTRACT_AMOUNT",
    target_period: "MONTHLY",
    period_value: "",
    target_value: "",
    description: "",
  });

  // Fetch targets
  useEffect(() => {
    loadTargets();
  }, [filters]);

  const loadTargets = async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 100,
        ...filters,
      };
      const res = await salesTargetApi.list(params);
      if (res.data?.items) {
        setTargets(res.data.items);
      }
    } catch (err) {
      console.error("Failed to load targets:", err);
      toast.error("加载目标列表失败");
    } finally {
      setLoading(false);
    }
  };

  // Load team members for selection
  const [teamMembers, setTeamMembers] = useState([]);
  useEffect(() => {
    const loadTeamMembers = async () => {
      try {
        const res = await salesTeamApi.getTeam();
        if (res.data?.team_members) {
          setTeamMembers(res.data.team_members);
        }
      } catch (err) {
        console.error("Failed to load team members:", err);
      }
    };
    loadTeamMembers();
  }, []);

  // Generate period value based on period type
  const generatePeriodValue = (periodType) => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;

    if (periodType === "MONTHLY") {
      return `${year}-${String(month).padStart(2, "0")}`;
    } else if (periodType === "QUARTERLY") {
      const quarter = Math.ceil(month / 3);
      return `${year}-Q${quarter}`;
    } else if (periodType === "YEARLY") {
      return String(year);
    }
    return "";
  };

  // Update period value when period type changes
  useEffect(() => {
    if (formData.target_period) {
      setFormData((prev) => ({
        ...prev,
        period_value: generatePeriodValue(formData.target_period),
      }));
    }
  }, [formData.target_period]);

  const handleCreate = async () => {
    try {
      await salesTargetApi.create(formData);
      toast.success("创建目标成功");
      setShowCreateDialog(false);
      resetForm();
      loadTargets();
    } catch (err) {
      console.error("Failed to create target:", err);
      toast.error(err.response?.data?.message || "创建目标失败");
    }
  };

  const handleUpdate = async () => {
    if (!selectedTarget) {return;}
    try {
      await salesTargetApi.update(selectedTarget.id, {
        target_value: formData.target_value,
        description: formData.description,
        status: formData.status,
      });
      toast.success("更新目标成功");
      setShowEditDialog(false);
      setSelectedTarget(null);
      resetForm();
      loadTargets();
    } catch (err) {
      console.error("Failed to update target:", err);
      toast.error(err.response?.data?.message || "更新目标失败");
    }
  };

  const handleEdit = (target) => {
    setSelectedTarget(target);
    setFormData({
      target_scope: target.target_scope,
      user_id: target.user_id,
      department_id: target.department_id,
      team_id: target.team_id,
      target_type: target.target_type,
      target_period: target.target_period,
      period_value: target.period_value,
      target_value: target.target_value,
      description: target.description || "",
      status: target.status,
    });
    setShowEditDialog(true);
  };

  const resetForm = () => {
    setFormData({
      target_scope: "PERSONAL",
      user_id: null,
      department_id: null,
      team_id: null,
      target_type: "CONTRACT_AMOUNT",
      target_period: "MONTHLY",
      period_value: generatePeriodValue("MONTHLY"),
      target_value: "",
      description: "",
    });
  };

  const filteredTargets = useMemo(() => {
    let result = targets;
    if (searchTerm) {
      result = (result || []).filter(
        (t) =>
          (t.user_name || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          (t.department_name || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          (t.period_value || "").includes(searchTerm),
      );
    }
    return result;
  }, [targets, searchTerm]);

  const getTargetTypeLabel = (type) => {
    const option = (targetTypeOptions || []).find((opt) => opt.value === type);
    return option?.label || type;
  };

  const getTargetPeriodLabel = (period) => {
    const option = (targetPeriodOptions || []).find((opt) => opt.value === period);
    return option?.label || period;
  };

  const getStatusBadge = (status) => {
    const configs = {
      ACTIVE: {
        label: "进行中",
        color: "bg-blue-500",
        textColor: "text-blue-400",
      },
      COMPLETED: {
        label: "已完成",
        color: "bg-emerald-500",
        textColor: "text-emerald-400",
      },
      CANCELLED: {
        label: "已取消",
        color: "bg-slate-500",
        textColor: "text-slate-400",
      },
    };
    const config = configs[status] || configs.ACTIVE;
    return (
      <Badge variant="outline" className={cn("text-xs", config.textColor)}>
        {config.label}
      </Badge>
    );
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="销售目标管理"
        description="创建和管理销售目标，跟踪目标完成进度"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button
              className="flex items-center gap-2"
              onClick={() => {
                resetForm();
                setShowCreateDialog(true);
              }}
            >
              <Plus className="w-4 h-4" />
              创建目标
            </Button>
          </motion.div>
        }
      />

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="flex-1 relative">
                <Input
                  placeholder="搜索目标..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              </div>
              <Select
                value={filters.target_scope}
                onValueChange={(value) =>
                  setFilters((prev) => ({ ...prev, target_scope: value || "" }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="目标范围" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部范围</SelectItem>
                  <SelectItem value="PERSONAL">个人目标</SelectItem>
                  <SelectItem value="TEAM">团队目标</SelectItem>
                  <SelectItem value="DEPARTMENT">部门目标</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={filters.target_type}
                onValueChange={(value) =>
                  setFilters((prev) => ({ ...prev, target_type: value || "" }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="目标类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部类型</SelectItem>
                  <SelectItem value="LEAD_COUNT">线索数量</SelectItem>
                  <SelectItem value="OPPORTUNITY_COUNT">商机数量</SelectItem>
                  <SelectItem value="CONTRACT_AMOUNT">合同金额</SelectItem>
                  <SelectItem value="COLLECTION_AMOUNT">回款金额</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={filters.target_period}
                onValueChange={(value) =>
                  setFilters((prev) => ({
                    ...prev,
                    target_period: value || "",
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="目标周期" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部周期</SelectItem>
                  <SelectItem value="MONTHLY">月度</SelectItem>
                  <SelectItem value="QUARTERLY">季度</SelectItem>
                  <SelectItem value="YEARLY">年度</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={filters.status}
                onValueChange={(value) =>
                  setFilters((prev) => ({ ...prev, status: value || "" }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="ACTIVE">进行中</SelectItem>
                  <SelectItem value="COMPLETED">已完成</SelectItem>
                  <SelectItem value="CANCELLED">已取消</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Targets List */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-400" />
              销售目标列表 ({filteredTargets.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredTargets.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                暂无目标数据
              </div>
            ) : (
              <div className="space-y-4">
                {(filteredTargets || []).map((target) => {
                  const completionRate = target.completion_rate || 0;
                  const isCompleted = completionRate >= 100;
                  const isWarning = completionRate < 70;

                  return (
                    <div
                      key={target.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-white">
                              {getTargetTypeLabel(target.target_type)}
                            </span>
                            {getStatusBadge(target.status)}
                            <Badge
                              variant="outline"
                              className="text-xs bg-slate-700/40"
                            >
                              {getTargetPeriodLabel(target.target_period)}
                            </Badge>
                            <span className="text-sm text-slate-400">
                              {target.period_value}
                            </span>
                          </div>
                          <div className="text-sm text-slate-400 mb-2">
                            {target.target_scope === "PERSONAL" &&
                              target.user_name && (
                                <span>负责人: {target.user_name}</span>
                              )}
                            {target.target_scope === "DEPARTMENT" &&
                              target.department_name && (
                                <span>部门: {target.department_name}</span>
                              )}
                            {target.description && (
                              <span className="ml-4">
                                描述: {target.description}
                              </span>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(target)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      </div>

                      {/* Progress */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">目标值</span>
                          <span className="text-white font-medium">
                            {target.target_type.includes("AMOUNT")
                              ? formatCurrency(target.target_value)
                              : `${target.target_value} 个`}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">实际完成</span>
                          <span
                            className={cn(
                              "font-medium",
                              isCompleted
                                ? "text-emerald-400"
                                : isWarning
                                  ? "text-red-400"
                                  : "text-amber-400",
                            )}
                          >
                            {target.target_type.includes("AMOUNT")
                              ? formatCurrency(target.actual_value || 0)
                              : `${target.actual_value || 0} 个`}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-slate-400">完成率</span>
                          <span
                            className={cn(
                              "font-medium",
                              isCompleted
                                ? "text-emerald-400"
                                : isWarning
                                  ? "text-red-400"
                                  : "text-amber-400",
                            )}
                          >
                            {completionRate.toFixed(1)}%
                          </span>
                        </div>
                        <Progress
                          value={Math.min(completionRate, 100)}
                          className={cn(
                            "h-2",
                            isCompleted && "bg-emerald-500/20",
                            isWarning && "bg-red-500/20",
                          )}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建销售目标</DialogTitle>
            <DialogDescription>设置个人、团队或部门销售目标</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>目标范围</Label>
                <Select
                  value={formData.target_scope}
                  onValueChange={(value) =>
                    setFormData((prev) => ({ ...prev, target_scope: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(targetScopeOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {formData.target_scope === "PERSONAL" && (
                <div>
                  <Label>负责人</Label>
                  <Select
                    value={formData.user_id?.toString() || ""}
                    onValueChange={(value) =>
                      setFormData((prev) => ({
                        ...prev,
                        user_id: parseInt(value),
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择负责人" />
                    </SelectTrigger>
                    <SelectContent>
                      {(teamMembers || []).map((member) => (
                        <SelectItem
                          key={member.user_id}
                          value={member.user_id.toString()}
                        >
                          {member.user_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <Label>目标类型</Label>
                <Select
                  value={formData.target_type}
                  onValueChange={(value) =>
                    setFormData((prev) => ({ ...prev, target_type: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(targetTypeOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>目标周期</Label>
                <Select
                  value={formData.target_period}
                  onValueChange={(value) =>
                    setFormData((prev) => ({ ...prev, target_period: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(targetPeriodOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>周期值</Label>
                <Input
                  value={formData.period_value}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      period_value: e.target.value,
                    }))
                  }
                  placeholder="如: 2025-01, 2025-Q1, 2025"
                />
              </div>
              <div>
                <Label>目标值</Label>
                <Input
                  type="number"
                  value={formData.target_value}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      target_value: e.target.value,
                    }))
                  }
                  placeholder="输入目标值"
                />
              </div>
            </div>
            <div>
              <Label>描述</Label>
              <Input
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                placeholder="目标描述（可选）"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑销售目标</DialogTitle>
            <DialogDescription>修改目标值和状态</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>目标值</Label>
              <Input
                type="number"
                value={formData.target_value}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    target_value: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <Label>描述</Label>
              <Input
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <Label>状态</Label>
              <Select
                value={formData.status}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, status: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACTIVE">进行中</SelectItem>
                  <SelectItem value="COMPLETED">已完成</SelectItem>
                  <SelectItem value="CANCELLED">已取消</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
