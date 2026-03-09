/**
 * 目标设置弹窗组件
 * 从销售预测页面触发，用于创建和管理销售目标
 */

import { useState, useEffect, useMemo } from "react";
import {
  Target,
  Plus,
  Edit,
  Users,
  Building2,
  User,
  Search,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Badge,
  Progress,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Label,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../ui";
import { cn } from "../../lib/utils";
import { salesTargetApi, salesTeamApi } from "../../services/api";
import { toast } from "sonner";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

// 目标范围选项
const targetScopeOptions = [
  { value: "PERSONAL", label: "个人目标", icon: User },
  { value: "TEAM", label: "团队目标", icon: Users },
  { value: "DEPARTMENT", label: "部门目标", icon: Building2 },
];

// 目标类型选项
const targetTypeOptions = [
  { value: "LEAD_COUNT", label: "线索数量", unit: "个" },
  { value: "OPPORTUNITY_COUNT", label: "商机数量", unit: "个" },
  { value: "CONTRACT_AMOUNT", label: "合同金额", unit: "元" },
  { value: "COLLECTION_AMOUNT", label: "回款金额", unit: "元" },
];

// 目标周期选项
const targetPeriodOptions = [
  { value: "MONTHLY", label: "月度" },
  { value: "QUARTERLY", label: "季度" },
  { value: "YEARLY", label: "年度" },
];

// 生成周期值
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

// 解析 meta 数据
const parseMeta = (description) => {
  if (!description || !description.includes("[meta]")) return {};
  try {
    const raw = description.split("[meta]")[1];
    return JSON.parse(raw);
  } catch {
    return {};
  }
};

// 构建带 meta 的描述
const buildDescriptionWithMeta = (description, meta) => {
  const base = (description || "").split("[meta]")[0].trim();
  const packed = JSON.stringify(meta);
  return `${base}${base ? " " : ""}[meta]${packed}`;
};

export default function TargetSettingModal({ open, onOpenChange, onTargetsChange }) {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("list");
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  // 当前用户 ID
  const currentUserId = useMemo(() => {
    try {
      const raw = localStorage.getItem("user");
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return parsed?.id ? Number(parsed.id) : null;
    } catch {
      return null;
    }
  }, []);

  // 表单状态
  const [formData, setFormData] = useState({
    target_scope: "PERSONAL",
    user_id: currentUserId,
    department_id: null,
    team_id: null,
    target_type: "CONTRACT_AMOUNT",
    target_period: "QUARTERLY",
    period_value: "",
    target_value: "",
    manager_group: "",
    director_group: "",
    industry: "",
    region: "",
    target_customer: "",
    description: "",
    status: "ACTIVE",
  });

  // 团队成员
  const [teamMembers, setTeamMembers] = useState([]);

  // 加载目标列表
  const loadTargets = async () => {
    setLoading(true);
    try {
      const res = await salesTargetApi.list({ page: 1, page_size: 100 });
      if (res.data?.items) {
        const normalized = res.data.items.map((t) => {
          const meta = parseMeta(t.description);
          const targetValue = Number(t.target_value || 0);
          const actualValue = Number(t.actual_value || meta.actual_value || 0);
          const completionRate = Number(
            t.completion_rate || (targetValue > 0 ? (actualValue / targetValue) * 100 : 0)
          );
          return {
            ...t,
            meta,
            actual_value: actualValue,
            completion_rate: completionRate,
          };
        });
        setTargets(normalized);
        // 通知父组件目标数据已更新
        onTargetsChange?.(normalized);
      }
    } catch (err) {
      console.error("Failed to load targets:", err);
      toast.error("加载目标列表失败");
    } finally {
      setLoading(false);
    }
  };

  // 加载团队成员
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
    if (open) {
      loadTeamMembers();
      loadTargets();
    }
  }, [open]);

  // 周期值自动生成
  useEffect(() => {
    if (formData.target_period && activeTab === "create") {
      setFormData((prev) => ({
        ...prev,
        period_value: generatePeriodValue(formData.target_period),
      }));
    }
  }, [formData.target_period, activeTab]);

  // 重置表单
  const resetForm = () => {
    setFormData({
      target_scope: "PERSONAL",
      user_id: currentUserId,
      department_id: null,
      team_id: null,
      target_type: "CONTRACT_AMOUNT",
      target_period: "QUARTERLY",
      period_value: generatePeriodValue("QUARTERLY"),
      target_value: "",
      manager_group: "",
      director_group: "",
      industry: "",
      region: "",
      target_customer: "",
      description: "",
      status: "ACTIVE",
    });
    setSelectedTarget(null);
  };

  // 创建目标
  const handleCreate = async () => {
    const normalizedTargetValue = Number(formData.target_value || 0);
    if (normalizedTargetValue <= 0) {
      toast.error("目标值必须大于 0");
      return;
    }

    if (formData.target_scope === "PERSONAL" && !formData.user_id) {
      toast.error("个人目标必须选择负责人");
      return;
    }

    try {
      const payload = {
        ...formData,
        target_value: normalizedTargetValue,
        user_id:
          formData.target_scope === "PERSONAL"
            ? Number(formData.user_id)
            : formData.user_id,
        description: buildDescriptionWithMeta(formData.description, {
          manager_group: formData.manager_group,
          director_group: formData.director_group,
          industry: formData.industry,
          region: formData.region,
          target_customer: formData.target_customer,
        }),
      };
      await salesTargetApi.create(payload);
      toast.success("创建目标成功");
      resetForm();
      setActiveTab("list");
      loadTargets();
    } catch (err) {
      console.error("Failed to create target:", err);
      const detail = err?.response?.data?.detail;
      toast.error(detail || err.response?.data?.message || "创建目标失败");
    }
  };

  // 更新目标
  const handleUpdate = async () => {
    if (!selectedTarget) return;
    try {
      await salesTargetApi.update(selectedTarget.id, {
        target_value: Number(formData.target_value),
        description: buildDescriptionWithMeta(formData.description, {
          manager_group: formData.manager_group,
          director_group: formData.director_group,
          industry: formData.industry,
          region: formData.region,
          target_customer: formData.target_customer,
        }),
        status: formData.status,
      });
      toast.success("更新目标成功");
      resetForm();
      setActiveTab("list");
      loadTargets();
    } catch (err) {
      console.error("Failed to update target:", err);
      toast.error(err.response?.data?.message || "更新目标失败");
    }
  };

  // 编辑目标
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
      manager_group: target.meta?.manager_group || "",
      director_group: target.meta?.director_group || "",
      industry: target.meta?.industry || "",
      region: target.meta?.region || "",
      target_customer: target.meta?.target_customer || "",
      description: (target.description || "").split("[meta]")[0].trim(),
      status: target.status,
    });
    setActiveTab("edit");
  };

  // 过滤目标
  const filteredTargets = useMemo(() => {
    if (!searchTerm) return targets;
    return targets.filter(
      (t) =>
        (t.user_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        (t.department_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        (t.period_value || "").includes(searchTerm)
    );
  }, [targets, searchTerm]);

  // 获取目标类型标签
  const getTargetTypeLabel = (type) => {
    const option = targetTypeOptions.find((opt) => opt.value === type);
    return option?.label || type;
  };

  // 获取目标周期标签
  const getTargetPeriodLabel = (period) => {
    const option = targetPeriodOptions.find((opt) => opt.value === period);
    return option?.label || period;
  };

  // 状态徽章
  const getStatusBadge = (status) => {
    const configs = {
      ACTIVE: { label: "进行中", color: "text-blue-400" },
      COMPLETED: { label: "已完成", color: "text-emerald-400" },
      CANCELLED: { label: "已取消", color: "text-slate-400" },
    };
    const config = configs[status] || configs.ACTIVE;
    return (
      <Badge variant="outline" className={cn("text-xs", config.color)}>
        {config.label}
      </Badge>
    );
  };

  // 表单内容
  const renderForm = (isEdit = false) => (
    <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>目标范围</Label>
          <Select
            value={formData.target_scope}
            onValueChange={(value) =>
              setFormData((prev) => ({ ...prev, target_scope: value }))
            }
            disabled={isEdit}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {targetScopeOptions.map((opt) => (
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
                setFormData((prev) => ({ ...prev, user_id: parseInt(value) }))
              }
              disabled={isEdit}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择负责人" />
              </SelectTrigger>
              <SelectContent>
                {teamMembers.map((member) => (
                  <SelectItem key={member.user_id} value={member.user_id.toString()}>
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
            disabled={isEdit}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {targetTypeOptions.map((opt) => (
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
            disabled={isEdit}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {targetPeriodOptions.map((opt) => (
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
              setFormData((prev) => ({ ...prev, period_value: e.target.value }))
            }
            placeholder="如: 2025-01, 2025-Q1, 2025"
            disabled={isEdit}
          />
        </div>

        <div>
          <Label>目标值</Label>
          <Input
            type="number"
            value={formData.target_value}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, target_value: e.target.value }))
            }
            placeholder="输入目标值"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>项目经理小组</Label>
          <Input
            value={formData.manager_group}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, manager_group: e.target.value }))
            }
            placeholder="如：华南PM一组"
          />
        </div>
        <div>
          <Label>总监小组</Label>
          <Input
            value={formData.director_group}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, director_group: e.target.value }))
            }
            placeholder="如：华南销售总监组"
          />
        </div>
        <div>
          <Label>行业</Label>
          <Input
            value={formData.industry}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, industry: e.target.value }))
            }
            placeholder="如：汽车电子"
          />
        </div>
        <div>
          <Label>大区</Label>
          <Input
            value={formData.region}
            onChange={(e) => setFormData((prev) => ({ ...prev, region: e.target.value }))}
            placeholder="如：华东"
          />
        </div>
      </div>

      <div>
        <Label>目标客户</Label>
        <Input
          value={formData.target_customer}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, target_customer: e.target.value }))
          }
          placeholder="如：比亚迪/立讯"
        />
      </div>

      <div>
        <Label>描述</Label>
        <Input
          value={formData.description}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, description: e.target.value }))
          }
          placeholder="目标描述（可选）"
        />
      </div>

      {isEdit && (
        <div>
          <Label>状态</Label>
          <Select
            value={formData.status}
            onValueChange={(value) => setFormData((prev) => ({ ...prev, status: value }))}
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
      )}
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-500" />
            销售目标管理
          </DialogTitle>
          <DialogDescription>创建和管理个人、团队、部门销售目标</DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="list">目标列表</TabsTrigger>
            <TabsTrigger value="create">创建目标</TabsTrigger>
            <TabsTrigger value="edit" disabled={!selectedTarget}>
              编辑目标
            </TabsTrigger>
          </TabsList>

          {/* 目标列表 */}
          <TabsContent value="list" className="mt-4">
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                  <Input
                    placeholder="搜索目标..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                </div>
                <Button onClick={() => setActiveTab("create")}>
                  <Plus className="w-4 h-4 mr-2" />
                  新建
                </Button>
              </div>

              <div className="max-h-[50vh] overflow-y-auto space-y-3">
                {loading ? (
                  <div className="text-center py-8 text-slate-400">加载中...</div>
                ) : filteredTargets.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">暂无目标数据</div>
                ) : (
                  filteredTargets.map((target) => {
                    const completionRate = Number(target.completion_rate || 0);
                    const isCompleted = completionRate >= 100;
                    const isWarning = completionRate < 70;

                    return (
                      <div
                        key={target.id}
                        className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-white">
                                {getTargetTypeLabel(target.target_type)}
                              </span>
                              {getStatusBadge(target.status)}
                              <Badge variant="outline" className="text-xs bg-slate-700/40">
                                {getTargetPeriodLabel(target.target_period)}
                              </Badge>
                              <span className="text-sm text-slate-400">
                                {target.period_value}
                              </span>
                            </div>
                            <div className="text-sm text-slate-400">
                              {target.target_scope === "PERSONAL" && target.user_name && (
                                <span>负责人: {target.user_name}</span>
                              )}
                              {target.target_scope === "DEPARTMENT" &&
                                target.department_name && (
                                  <span>部门: {target.department_name}</span>
                                )}
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(target)}>
                            <Edit className="w-4 h-4" />
                          </Button>
                        </div>

                        <div className="flex items-center gap-4 text-sm">
                          <div>
                            <span className="text-slate-400">目标：</span>
                            <span className="text-white font-medium">
                              {target.target_type.includes("AMOUNT")
                                ? formatCurrency(target.target_value)
                                : `${target.target_value} 个`}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400">实际：</span>
                            <span
                              className={cn(
                                "font-medium",
                                isCompleted
                                  ? "text-emerald-400"
                                  : isWarning
                                  ? "text-red-400"
                                  : "text-amber-400"
                              )}
                            >
                              {target.target_type.includes("AMOUNT")
                                ? formatCurrency(target.actual_value || 0)
                                : `${target.actual_value || 0} 个`}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400">完成率：</span>
                            <span
                              className={cn(
                                "font-medium",
                                isCompleted
                                  ? "text-emerald-400"
                                  : isWarning
                                  ? "text-red-400"
                                  : "text-amber-400"
                              )}
                            >
                              {completionRate.toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        <Progress
                          value={Math.min(completionRate, 100)}
                          className={cn(
                            "h-1.5 mt-2",
                            isCompleted && "bg-emerald-500/20",
                            isWarning && "bg-red-500/20"
                          )}
                        />
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </TabsContent>

          {/* 创建目标 */}
          <TabsContent value="create" className="mt-4">
            {renderForm(false)}
            <DialogFooter className="mt-4">
              <Button
                variant="outline"
                onClick={() => {
                  resetForm();
                  setActiveTab("list");
                }}
              >
                取消
              </Button>
              <Button onClick={handleCreate}>创建目标</Button>
            </DialogFooter>
          </TabsContent>

          {/* 编辑目标 */}
          <TabsContent value="edit" className="mt-4">
            {renderForm(true)}
            <DialogFooter className="mt-4">
              <Button
                variant="outline"
                onClick={() => {
                  resetForm();
                  setActiveTab("list");
                }}
              >
                取消
              </Button>
              <Button onClick={handleUpdate}>保存修改</Button>
            </DialogFooter>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
