import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Edit3,
  Trash2,
  Users,
  UserPlus,
  Settings,
  ClipboardList,
  Wrench,
  Zap,
  Code,
  Package,
  Headphones,
  ClipboardCheck,
  UserCog,
  Calendar,
  Percent,
  ChevronDown,
  ChevronUp,
  X,
  Check,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../ui/dialog";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Switch } from "../ui/switch";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";
import { cn } from "../../lib/utils";
import { projectRoleApi, userApi } from "../../services/api";

// 角色编码对应的图标
import { confirmAction } from "@/lib/confirmAction";
const ROLE_ICONS = {
  PM: ClipboardList,
  TECH_LEAD: Settings,
  ME_LEAD: Wrench,
  EE_LEAD: Zap,
  SW_LEAD: Code,
  PROC_LEAD: Package,
  CS_LEAD: Headphones,
  QA_LEAD: ClipboardCheck,
  PMC_LEAD: UserCog,
  INSTALL_LEAD: Users,
};

// 角色分类颜色
const CATEGORY_COLORS = {
  MANAGEMENT: {
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    text: "text-purple-400",
    icon: "text-purple-400",
  },
  TECHNICAL: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    text: "text-blue-400",
    icon: "text-blue-400",
  },
  SUPPORT: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    icon: "text-emerald-400",
  },
  GENERAL: {
    bg: "bg-slate-500/10",
    border: "border-slate-500/30",
    text: "text-slate-400",
    icon: "text-slate-400",
  },
};

export default function ProjectLeadsPanel({ projectId, editable = true }) {
  const [loading, setLoading] = useState(false);
  const [roleOverview, setRoleOverview] = useState([]);
  const [users, setUsers] = useState([]);

  // 对话框状态
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showTeamDialog, setShowTeamDialog] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);

  // 表单数据
  const [assignForm, setAssignForm] = useState({
    user_id: "",
    role_type_id: "",
    allocation_pct: 100,
    start_date: "",
    end_date: "",
    remark: "",
  });

  const [teamMemberForm, setTeamMemberForm] = useState({
    user_id: "",
    allocation_pct: 100,
    start_date: "",
    end_date: "",
    remark: "",
  });

  // 角色配置列表
  const [roleConfigs, setRoleConfigs] = useState([]);

  // 展开的负责人卡片（显示团队成员）
  const [expandedLeads, setExpandedLeads] = useState(new Set());

  // 加载项目角色概览
  const loadRoleOverview = useCallback(async () => {
    if (!projectId) {return;}
    setLoading(true);
    try {
      const response = await projectRoleApi.getOverview(projectId);
      setRoleOverview(response.data || []);
    } catch (error) {
      console.error("加载项目角色概览失败:", error);
      setRoleOverview([]);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // 加载用户列表
  const loadUsers = async () => {
    try {
      const response = await userApi.list({
        page: 1,
        page_size: 100,
        is_active: true,
      });
      setUsers(response.data?.items || []);
    } catch (error) {
      console.error("加载用户列表失败:", error);
      setUsers([]);
    }
  };

  useEffect(() => {
    loadRoleOverview();
    loadUsers();
  }, [loadRoleOverview]);

  // 打开配置对话框
  const handleConfigClick = () => {
    setRoleConfigs(
      roleOverview.map((ro) => ({
        role_type_id: ro.role_type.id,
        role_name: ro.role_type.role_name,
        role_code: ro.role_type.role_code,
        is_enabled: ro.is_enabled,
        is_required: ro.is_required,
      })),
    );
    setShowConfigDialog(true);
  };

  // 保存角色配置
  const handleSaveConfig = async () => {
    try {
      await projectRoleApi.configs.batchUpdate(projectId, {
        configs: roleConfigs,
      });
      setShowConfigDialog(false);
      loadRoleOverview();
    } catch (error) {
      console.error("保存配置失败:", error);
      // Update locally for demo
      setShowConfigDialog(false);
    }
  };

  // 打开指定负责人对话框
  const handleAssignClick = (roleOverviewItem) => {
    setSelectedRole(roleOverviewItem);
    setAssignForm({
      user_id: "",
      role_type_id: roleOverviewItem.role_type.id,
      allocation_pct: 100,
      start_date: "",
      end_date: "",
      remark: "",
    });
    setShowAssignDialog(true);
  };

  // 指定负责人
  const handleAssign = async () => {
    try {
      await projectRoleApi.leads.create(projectId, assignForm);
      setShowAssignDialog(false);
      loadRoleOverview();
    } catch (error) {
      console.error("指定负责人失败:", error);
      alert("指定失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 移除负责人
  const handleRemoveLead = async (lead) => {
    if (
      !await confirmAction(`确定要移除 ${lead.user?.real_name || "该负责人"} 吗？`)
    )
      {return;}
    try {
      await projectRoleApi.leads.delete(projectId, lead.id);
      loadRoleOverview();
    } catch (error) {
      console.error("移除负责人失败:", error);
    }
  };

  // 打开团队管理对话框
  const handleTeamClick = (roleOverviewItem) => {
    setSelectedRole(roleOverviewItem);
    setSelectedLead(roleOverviewItem.lead);
    setTeamMemberForm({
      user_id: "",
      allocation_pct: 100,
      start_date: "",
      end_date: "",
      remark: "",
    });
    setShowTeamDialog(true);
  };

  // 添加团队成员
  const handleAddTeamMember = async () => {
    try {
      await projectRoleApi.team.add(projectId, selectedLead.id, teamMemberForm);
      loadRoleOverview();
      setTeamMemberForm({
        user_id: "",
        allocation_pct: 100,
        start_date: "",
        end_date: "",
        remark: "",
      });
    } catch (error) {
      console.error("添加团队成员失败:", error);
    }
  };

  // 移除团队成员
  const handleRemoveTeamMember = async (memberId) => {
    try {
      await projectRoleApi.team.remove(projectId, selectedLead.id, memberId);
      loadRoleOverview();
    } catch (error) {
      console.error("移除团队成员失败:", error);
    }
  };

  // 切换展开状态
  const toggleExpand = (leadId) => {
    setExpandedLeads((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(leadId)) {
        newSet.delete(leadId);
      } else {
        newSet.add(leadId);
      }
      return newSet;
    });
  };

  const getRoleIcon = (roleCode) => {
    const IconComponent = ROLE_ICONS[roleCode] || Users;
    return IconComponent;
  };

  const getCategoryColor = (category) => {
    return CATEGORY_COLORS[category] || CATEGORY_COLORS.GENERAL;
  };

  const enabledRoles = roleOverview.filter((ro) => ro.is_enabled);
  const disabledRoles = roleOverview.filter((ro) => !ro.is_enabled);

  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-violet-500/10">
            <Users className="h-5 w-5 text-violet-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">项目负责人</h3>
            <p className="text-sm text-slate-400">
              已配置 {enabledRoles.filter((ro) => ro.has_lead).length}/
              {enabledRoles.length} 个角色
            </p>
          </div>
        </div>
        {editable && (
          <Button variant="secondary" size="sm" onClick={handleConfigClick}>
            <Settings className="h-4 w-4 mr-2" />
            配置角色
          </Button>
        )}
      </div>

      {/* 角色卡片网格 */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card
              key={i}
              className="bg-surface-100 border-white/5 animate-pulse"
            >
              <CardContent className="p-4 h-[180px]" />
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnimatePresence mode="popLayout">
            {enabledRoles.map((roleItem, index) => {
              const IconComponent = getRoleIcon(roleItem.role_type.role_code);
              const categoryColor = getCategoryColor(
                roleItem.role_type.role_category,
              );
              const isExpanded =
                roleItem.lead && expandedLeads.has(roleItem.lead.id);
              const teamMembers = roleItem.lead?.team_members || [];

              return (
                <motion.div
                  key={roleItem.role_type.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className={cn(
                      "bg-surface-100 border transition-all duration-200",
                      roleItem.has_lead
                        ? "border-white/10 hover:border-white/20"
                        : "border-dashed border-white/10 hover:border-white/20",
                    )}
                  >
                    <CardContent className="p-4">
                      {/* 角色头部 */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div
                            className={cn("p-2 rounded-xl", categoryColor.bg)}
                          >
                            <IconComponent
                              className={cn("h-5 w-5", categoryColor.icon)}
                            />
                          </div>
                          <div>
                            <h4 className="font-medium text-white">
                              {roleItem.role_type.role_name}
                            </h4>
                            <div className="flex items-center gap-2 mt-0.5">
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs border",
                                  categoryColor.border,
                                  categoryColor.text,
                                )}
                              >
                                {roleItem.role_type.role_code}
                              </Badge>
                              {roleItem.is_required && (
                                <Badge className="bg-amber-500/20 text-amber-400 text-xs">
                                  必需
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* 负责人信息 */}
                      {roleItem.has_lead && roleItem.lead ? (
                        <div className="space-y-3">
                          <div className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02]">
                            <Avatar className="h-10 w-10">
                              <AvatarImage src={roleItem.lead.user?.avatar} />
                              <AvatarFallback className="bg-violet-500/20 text-violet-400">
                                {
                                  (roleItem.lead.user?.real_name ||
                                    roleItem.lead.user?.username ||
                                    "?")[0]
                                }
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-white truncate">
                                {roleItem.lead.user?.real_name ||
                                  roleItem.lead.user?.username}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-slate-400">
                                <span className="flex items-center gap-1">
                                  <Percent className="h-3 w-3" />
                                  {roleItem.lead.allocation_pct}%
                                </span>
                                {roleItem.lead.start_date && (
                                  <span className="flex items-center gap-1">
                                    <Calendar className="h-3 w-3" />
                                    {roleItem.lead.start_date}
                                  </span>
                                )}
                              </div>
                            </div>
                            {editable && (
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleRemoveLead(roleItem.lead)}
                                className="text-slate-400 hover:text-red-400"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            )}
                          </div>

                          {/* 团队成员 */}
                          {roleItem.role_type.can_have_team &&
                            teamMembers.length > 0 && (
                              <div>
                                <button
                                  onClick={() => toggleExpand(roleItem.lead.id)}
                                  className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors w-full"
                                >
                                  <Users className="h-4 w-4" />
                                  <span>团队成员 ({teamMembers.length})</span>
                                  {isExpanded ? (
                                    <ChevronUp className="h-4 w-4 ml-auto" />
                                  ) : (
                                    <ChevronDown className="h-4 w-4 ml-auto" />
                                  )}
                                </button>
                                <AnimatePresence>
                                  {isExpanded && (
                                    <motion.div
                                      initial={{ height: 0, opacity: 0 }}
                                      animate={{ height: "auto", opacity: 1 }}
                                      exit={{ height: 0, opacity: 0 }}
                                      className="overflow-hidden"
                                    >
                                      <div className="mt-2 space-y-1 pl-6">
                                        {teamMembers.map((member) => (
                                          <div
                                            key={member.id}
                                            className="flex items-center gap-2 text-sm text-slate-300 py-1"
                                          >
                                            <Avatar className="h-6 w-6">
                                              <AvatarFallback className="bg-white/5 text-slate-400 text-xs">
                                                {
                                                  (member.user?.real_name ||
                                                    "?")[0]
                                                }
                                              </AvatarFallback>
                                            </Avatar>
                                            <span>
                                              {member.user?.real_name}
                                            </span>
                                            <span className="text-xs text-slate-500">
                                              {member.allocation_pct}%
                                            </span>
                                          </div>
                                        ))}
                                      </div>
                                    </motion.div>
                                  )}
                                </AnimatePresence>
                              </div>
                            )}

                          {/* 操作按钮 */}
                          {editable && roleItem.role_type.can_have_team && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full mt-2 text-slate-400 hover:text-white"
                              onClick={() => handleTeamClick(roleItem)}
                            >
                              <UserPlus className="h-4 w-4 mr-2" />
                              管理团队
                            </Button>
                          )}
                        </div>
                      ) : (
                        <div className="flex flex-col items-center justify-center py-4 text-center">
                          <div className="p-3 rounded-full bg-white/5 mb-2">
                            <AlertCircle className="h-6 w-6 text-slate-500" />
                          </div>
                          <p className="text-sm text-slate-500 mb-3">
                            尚未指定负责人
                          </p>
                          {editable && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleAssignClick(roleItem)}
                            >
                              <UserPlus className="h-4 w-4 mr-2" />
                              指定负责人
                            </Button>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {/* 已禁用的角色（折叠显示） */}
      {disabledRoles.length > 0 && (
        <div className="mt-6">
          <p className="text-sm text-slate-500 mb-2">
            未启用的角色 ({disabledRoles.length})：
            {disabledRoles.map((ro) => ro.role_type.role_name).join("、")}
          </p>
        </div>
      )}

      {/* 角色配置对话框 */}
      <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-violet-400" />
              配置项目角色
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <p className="text-sm text-slate-400">
              选择此项目需要的角色类型，已启用的角色可以指定负责人。
            </p>
            <div className="space-y-2">
              {roleConfigs.map((config, index) => (
                <div
                  key={config.role_type_id}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5"
                >
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={config.is_enabled}
                      onCheckedChange={(checked) => {
                        const newConfigs = [...roleConfigs];
                        newConfigs[index].is_enabled = checked;
                        if (!checked) {newConfigs[index].is_required = false;}
                        setRoleConfigs(newConfigs);
                      }}
                    />
                    <div>
                      <p className="font-medium text-white">
                        {config.role_name}
                      </p>
                      <code className="text-xs text-slate-500">
                        {config.role_code}
                      </code>
                    </div>
                  </div>
                  {config.is_enabled && (
                    <div className="flex items-center gap-2">
                      <Label className="text-xs text-slate-400">必需</Label>
                      <Switch
                        checked={config.is_required}
                        onCheckedChange={(checked) => {
                          const newConfigs = [...roleConfigs];
                          newConfigs[index].is_required = checked;
                          setRoleConfigs(newConfigs);
                        }}
                        className="data-[state=checked]:bg-amber-500"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setShowConfigDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleSaveConfig}>保存配置</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 指定负责人对话框 */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5 text-violet-400" />
              指定{selectedRole?.role_type?.role_name}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="space-y-2">
              <Label>选择人员 *</Label>
              <Select
                value={assignForm.user_id?.toString()}
                onValueChange={(v) =>
                  setAssignForm((prev) => ({ ...prev, user_id: parseInt(v) }))
                }
              >
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue placeholder="请选择人员" />
                </SelectTrigger>
                <SelectContent>
                  {users.map((user) => (
                    <SelectItem key={user.id} value={user.id.toString()}>
                      {user.real_name || user.username}
                      {user.department && ` (${user.department})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>分配比例 (%)</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={assignForm.allocation_pct}
                  onChange={(e) =>
                    setAssignForm((prev) => ({
                      ...prev,
                      allocation_pct: parseInt(e.target.value) || 0,
                    }))
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>开始日期</Label>
                <Input
                  type="date"
                  value={assignForm.start_date}
                  onChange={(e) =>
                    setAssignForm((prev) => ({
                      ...prev,
                      start_date: e.target.value,
                    }))
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>结束日期</Label>
              <Input
                type="date"
                value={assignForm.end_date}
                onChange={(e) =>
                  setAssignForm((prev) => ({
                    ...prev,
                    end_date: e.target.value,
                  }))
                }
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>备注</Label>
              <Input
                placeholder="可选备注..."
                value={assignForm.remark}
                onChange={(e) =>
                  setAssignForm((prev) => ({ ...prev, remark: e.target.value }))
                }
                className="bg-white/5 border-white/10"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setShowAssignDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleAssign} disabled={!assignForm.user_id}>
              确定指定
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 团队管理对话框 */}
      <Dialog open={showTeamDialog} onOpenChange={setShowTeamDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-violet-400" />
              管理{selectedRole?.role_type?.role_name}团队
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            {/* 负责人信息 */}
            {selectedLead && (
              <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-violet-500/20 text-violet-400">
                      {(selectedLead.user?.real_name || "?")[0]}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium text-white">
                      {selectedLead.user?.real_name} (负责人)
                    </p>
                    <p className="text-xs text-slate-400">
                      分配比例: {selectedLead.allocation_pct}%
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 当前团队成员 */}
            <div>
              <Label className="text-slate-400 mb-2 block">团队成员</Label>
              {(selectedLead?.team_members || []).length > 0 ? (
                <div className="space-y-2">
                  {(selectedLead?.team_members || []).map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] border border-white/5"
                    >
                      <div className="flex items-center gap-2">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="bg-white/5 text-slate-400 text-xs">
                            {(member.user?.real_name || "?")[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm text-white">
                            {member.user?.real_name}
                          </p>
                          <p className="text-xs text-slate-500">
                            {member.allocation_pct}%
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => handleRemoveTeamMember(member.id)}
                        className="text-slate-400 hover:text-red-400"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 text-center py-4">
                  暂无团队成员
                </p>
              )}
            </div>

            {/* 添加成员表单 */}
            <div className="border-t border-white/5 pt-4">
              <Label className="text-slate-400 mb-2 block">添加成员</Label>
              <div className="grid grid-cols-2 gap-3">
                <Select
                  value={teamMemberForm.user_id?.toString()}
                  onValueChange={(v) =>
                    setTeamMemberForm((prev) => ({
                      ...prev,
                      user_id: parseInt(v),
                    }))
                  }
                >
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue placeholder="选择人员" />
                  </SelectTrigger>
                  <SelectContent>
                    {users
                      .filter(
                        (u) =>
                          u.id !== selectedLead?.user_id &&
                          !(selectedLead?.team_members || []).some(
                            (m) => m.user_id === u.id,
                          ),
                      )
                      .map((user) => (
                        <SelectItem key={user.id} value={user.id.toString()}>
                          {user.real_name || user.username}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    placeholder="分配%"
                    value={teamMemberForm.allocation_pct}
                    onChange={(e) =>
                      setTeamMemberForm((prev) => ({
                        ...prev,
                        allocation_pct: parseInt(e.target.value) || 0,
                      }))
                    }
                    className="bg-white/5 border-white/10 w-20"
                  />
                  <Button
                    onClick={handleAddTeamMember}
                    disabled={!teamMemberForm.user_id}
                    size="icon"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setShowTeamDialog(false)}
            >
              完成
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}