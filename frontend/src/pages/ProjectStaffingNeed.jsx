// -*- coding: utf-8 -*-
/**
 * 项目人员需求页面
 * 管理项目的人员配置需求
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Plus,
  Search,
  Edit3,
  Rocket,
  Users,
  RefreshCw,
  Calendar,
  Target,
  ChevronRight,
  Save,
  X,
  Clock,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { cn } from "../lib/utils";
import { staffMatchingApi, projectApi } from "../services/api";

// 优先级配置
import { confirmAction } from "@/lib/confirmAction";
const PRIORITY_OPTIONS = [
  { value: "P1", label: "P1 - 紧急", color: "red", threshold: 85 },
  { value: "P2", label: "P2 - 高", color: "orange", threshold: 75 },
  { value: "P3", label: "P3 - 中", color: "blue", threshold: 65 },
  { value: "P4", label: "P4 - 低", color: "green", threshold: 55 },
  { value: "P5", label: "P5 - 最低", color: "slate", threshold: 50 },
];

// 状态配置
const STATUS_OPTIONS = [
  { value: "OPEN", label: "开放", color: "blue" },
  { value: "MATCHING", label: "匹配中", color: "yellow" },
  { value: "FILLED", label: "已填满", color: "green" },
  { value: "CANCELLED", label: "已取消", color: "slate" },
];

// 角色配置
const ROLE_OPTIONS = [
  { value: "PM", label: "项目经理" },
  { value: "ME", label: "机械工程师" },
  { value: "EE", label: "电气工程师" },
  { value: "SW", label: "软件工程师" },
  { value: "TE", label: "测试工程师" },
  { value: "ASSY", label: "装配技工" },
];

// 模拟数据
// Mock data - 已移除，使用真实API
// Mock data - 已移除，使用真实API
// Mock data - 已移除，使用真实API
export default function ProjectStaffingNeed() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [needs, setNeeds] = useState([]);
  const [projects, setProjects] = useState([]);
  const [tags, setTags] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [showDialog, setShowDialog] = useState(false);
  const [editingNeed, setEditingNeed] = useState(null);
  const [formData, setFormData] = useState({
    project_id: "",
    role_code: "",
    headcount: 1,
    required_skill_ids: [],
    priority: "P3",
    start_date: "",
    end_date: "",
    allocation_pct: 100,
    remark: "",
  });

  // 加载数据
  const loadNeeds = useCallback(async () => {
    setLoading(true);
    try {
      const response = await staffMatchingApi.getStaffingNeeds({
        page_size: 100,
      });
      if (response.data?.items) {
        setNeeds(response.data.items);
      }
    } catch (error) {
      console.error("加载人员需求失败:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({ status: "active", limit: 100 });
      if (response.data?.items) {
        setProjects(response.data.items);
      }
    } catch (error) {
      console.error("加载项目失败:", error);
    }
  }, []);

  const loadTags = useCallback(async () => {
    try {
      const response = await staffMatchingApi.getTags({
        tag_type: "SKILL",
        is_active: true,
        page_size: 100,
      });
      if (response.data?.items) {
        setTags(response.data.items);
      }
    } catch (error) {
      console.error("加载标签失败:", error);
    }
  }, []);

  useEffect(() => {
    loadNeeds();
    loadProjects();
    loadTags();
  }, [loadNeeds, loadProjects, loadTags]);

  // 统计
  const stats = {
    open: needs.filter((n) => n.status === "OPEN").length,
    matching: needs.filter((n) => n.status === "MATCHING").length,
    filled: needs.filter((n) => n.status === "FILLED").length,
  };

  // 过滤
  const filteredNeeds = needs.filter((need) => {
    const matchKeyword =
      !searchKeyword ||
      need.project_name?.includes(searchKeyword) ||
      need.role_name?.includes(searchKeyword);
    const matchStatus = filterStatus === "all" || need.status === filterStatus;
    return matchKeyword && matchStatus;
  });

  // 打开新建对话框
  const handleCreate = () => {
    setEditingNeed(null);
    setFormData({
      project_id: "",
      role_code: "",
      headcount: 1,
      required_skill_ids: [],
      priority: "P3",
      start_date: "",
      end_date: "",
      allocation_pct: 100,
      remark: "",
    });
    setShowDialog(true);
  };

  // 打开编辑对话框
  const handleEdit = (need) => {
    setEditingNeed(need);
    setFormData({
      project_id: need.project_id,
      role_code: need.role_code,
      headcount: need.headcount,
      required_skill_ids: need.required_skills?.map((s) => s.tag_id) || [],
      priority: need.priority,
      start_date: need.start_date || "",
      end_date: need.end_date || "",
      allocation_pct: need.allocation_pct || 100,
      remark: need.remark || "",
    });
    setShowDialog(true);
  };

  // 保存
  const handleSave = async () => {
    try {
      const data = {
        project_id: formData.project_id,
        role_code: formData.role_code,
        role_name: ROLE_OPTIONS.find((r) => r.value === formData.role_code)
          ?.label,
        headcount: formData.headcount,
        required_skills: formData.required_skill_ids.map((id) => ({
          tag_id: id,
          min_score: 3,
        })),
        priority: formData.priority,
        start_date: formData.start_date,
        end_date: formData.end_date,
        allocation_pct: formData.allocation_pct,
        remark: formData.remark,
      };

      if (editingNeed) {
        await staffMatchingApi.updateStaffingNeed(editingNeed.id, data);
      } else {
        await staffMatchingApi.createStaffingNeed(data);
      }
      setShowDialog(false);
      loadNeeds();
    } catch (error) {
      console.error("保存失败:", error);
      // 本地更新用于演示
      const newNeed = editingNeed
        ? {
            ...editingNeed,
            ...formData,
            role_name: ROLE_OPTIONS.find((r) => r.value === formData.role_code)
              ?.label,
          }
        : {
            id: Date.now(),
            ...formData,
            role_name: ROLE_OPTIONS.find((r) => r.value === formData.role_code)
              ?.label,
            project_name: projects.find((p) => p.id === formData.project_id)
              ?.name,
            status: "OPEN",
            filled_count: 0,
            required_skills: formData.required_skill_ids.map((id) => ({
              tag_id: id,
              tag_name: tags.find((t) => t.id === id)?.tag_name,
            })),
            created_at: new Date().toISOString(),
          };

      setNeeds((prev) =>
        editingNeed
          ? prev.map((n) => (n.id === editingNeed.id ? newNeed : n))
          : [...prev, newNeed],
      );
      setShowDialog(false);
    }
  };

  // 取消需求
  const handleCancel = async (need) => {
    if (
      !await confirmAction(
        `确定要取消需求"${need.project_name} - ${need.role_name}"吗？`,
      )
    )
      {return;}

    try {
      await staffMatchingApi.cancelStaffingNeed(need.id);
      loadNeeds();
    } catch (error) {
      console.error("取消失败:", error);
      setNeeds((prev) =>
        prev.map((n) => (n.id === need.id ? { ...n, status: "CANCELLED" } : n)),
      );
    }
  };

  // 去匹配
  const handleGoToMatching = (needId) => {
    navigate(`/staff-matching/matching?need_id=${needId}`);
  };

  // 获取优先级样式
  const getPriorityBadge = (priority) => {
    const opt = PRIORITY_OPTIONS.find((p) => p.value === priority);
    const colors = {
      red: "bg-red-500/20 text-red-400 border-red-500/30",
      orange: "bg-orange-500/20 text-orange-400 border-orange-500/30",
      blue: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      green: "bg-green-500/20 text-green-400 border-green-500/30",
      slate: "bg-slate-500/20 text-slate-400 border-slate-500/30",
    };
    return colors[opt?.color] || colors.slate;
  };

  // 获取状态样式
  const getStatusBadge = (status) => {
    const colors = {
      OPEN: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      MATCHING: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      FILLED: "bg-green-500/20 text-green-400 border-green-500/30",
      CANCELLED: "bg-slate-500/20 text-slate-400 border-slate-500/30",
    };
    return colors[status] || colors.CANCELLED;
  };

  const getStatusLabel = (status) => {
    return STATUS_OPTIONS.find((s) => s.value === status)?.label || status;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="项目人员需求"
        description="管理项目的人员配置需求，发起智能匹配"
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-blue-500/10">
                <Target className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-400">
                  {stats.open}
                </div>
                <div className="text-sm text-slate-400">开放需求</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-yellow-500/10">
                <Rocket className="h-6 w-6 text-yellow-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-400">
                  {stats.matching}
                </div>
                <div className="text-sm text-slate-400">匹配中</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-green-500/10">
                <Users className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-green-400">
                  {stats.filled}
                </div>
                <div className="text-sm text-slate-400">已填满</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 列表 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>需求列表</CardTitle>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索项目/角色..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-9 w-64"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
            >
              <option value="all">全部状态</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
            <Button variant="outline" size="icon" onClick={loadNeeds}>
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            </Button>
            <Button onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-2" />
              新增需求
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12 text-slate-400">加载中...</div>
          ) : filteredNeeds.length === 0 ? (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          ) : (
            <div className="space-y-3">
              {filteredNeeds.map((need) => (
                <motion.div
                  key={need.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "p-4 rounded-lg border transition-colors",
                    need.status === "CANCELLED"
                      ? "border-white/5 bg-white/[0.02] opacity-50"
                      : "border-white/10 bg-white/5 hover:bg-white/10",
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="font-medium text-white">
                          {need.project_name}
                        </span>
                        <ChevronRight className="h-4 w-4 text-slate-500" />
                        <span className="text-slate-300">{need.role_name}</span>
                        <Badge className={getPriorityBadge(need.priority)}>
                          {need.priority} (≥
                          {
                            PRIORITY_OPTIONS.find(
                              (p) => p.value === need.priority,
                            )?.threshold
                          }
                          分)
                        </Badge>
                        <Badge className={getStatusBadge(need.status)}>
                          {getStatusLabel(need.status)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-6 mt-2 text-sm text-slate-400">
                        <span className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          需求 {need.headcount} 人，已填{" "}
                          {need.filled_count || 0} 人
                        </span>
                        {need.start_date && (
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {need.start_date} ~ {need.end_date}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          投入 {need.allocation_pct}%
                        </span>
                      </div>
                      {need.required_skills?.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {need.required_skills
                            .slice(0, 3)
                            .map((skill, idx) => (
                              <Badge
                                key={idx}
                                variant="secondary"
                                className="text-xs"
                              >
                                {skill.tag_name}
                              </Badge>
                            ))}
                          {need.required_skills.length > 3 && (
                            <Badge variant="secondary" className="text-xs">
                              +{need.required_skills.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {need.status === "OPEN" && (
                        <Button
                          size="sm"
                          onClick={() => handleGoToMatching(need.id)}
                        >
                          <Rocket className="h-4 w-4 mr-1" />
                          匹配
                        </Button>
                      )}
                      {need.status === "MATCHING" && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleGoToMatching(need.id)}
                        >
                          查看匹配
                        </Button>
                      )}
                      {(need.status === "OPEN" ||
                        need.status === "MATCHING") && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => handleEdit(need)}
                          >
                            <Edit3 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-400 hover:text-red-300"
                            onClick={() => handleCancel(need)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 新建/编辑对话框 */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingNeed ? "编辑人员需求" : "新增人员需求"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>项目</Label>
              <select
                value={formData.project_id}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    project_id: Number(e.target.value),
                  })
                }
                className="w-full h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
              >
                <option value="">选择项目</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>角色</Label>
                <select
                  value={formData.role_code}
                  onChange={(e) =>
                    setFormData({ ...formData, role_code: e.target.value })
                  }
                  className="w-full h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
                >
                  <option value="">选择角色</option>
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>需求人数</Label>
                <Input
                  type="number"
                  min={1}
                  max={10}
                  value={formData.headcount}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      headcount: parseInt(e.target.value) || 1,
                    })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>所需技能（多选）</Label>
              <div className="flex flex-wrap gap-2 p-3 rounded-md border border-white/10 bg-white/5 min-h-[60px]">
                {tags.map((tag) => {
                  const isSelected = formData.required_skill_ids.includes(
                    tag.id,
                  );
                  return (
                    <Badge
                      key={tag.id}
                      className={cn(
                        "cursor-pointer transition-colors",
                        isSelected
                          ? "bg-primary/20 text-primary border-primary/30"
                          : "bg-white/5 text-slate-400 border-white/10 hover:bg-white/10",
                      )}
                      onClick={() => {
                        setFormData((prev) => ({
                          ...prev,
                          required_skill_ids: isSelected
                            ? prev.required_skill_ids.filter(
                                (id) => id !== tag.id,
                              )
                            : [...prev.required_skill_ids, tag.id],
                        }));
                      }}
                    >
                      {tag.tag_name}
                    </Badge>
                  );
                })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>优先级</Label>
                <select
                  value={formData.priority}
                  onChange={(e) =>
                    setFormData({ ...formData, priority: e.target.value })
                  }
                  className="w-full h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
                >
                  {PRIORITY_OPTIONS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label} (最低{p.threshold}分)
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>投入比例 (%)</Label>
                <Input
                  type="number"
                  min={10}
                  max={100}
                  step={10}
                  value={formData.allocation_pct}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      allocation_pct: parseInt(e.target.value) || 100,
                    })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>开始日期</Label>
                <Input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) =>
                    setFormData({ ...formData, start_date: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>结束日期</Label>
                <Input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) =>
                    setFormData({ ...formData, end_date: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>备注</Label>
              <textarea
                value={formData.remark}
                onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="备注信息..."
                className="w-full h-20 px-3 py-2 rounded-md border border-white/10 bg-white/5 text-sm resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSave}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
