import { useState, useEffect, useCallback as _useCallback } from "react";
import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import {
  Plus,
  Edit,
  Trash2,
  Users,
  Briefcase,
  Settings,
  UserPlus } from
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter } from
"../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import { Label } from "../components/ui/label";
import { projectRoleApi, userApi } from "../services/api";
import { fadeIn } from "../lib/animations";

import { confirmAction } from "@/lib/confirmAction";
export default function ProjectRoles() {
  const { id } = useParams();
  const projectId = id ? parseInt(id) : null;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [roleOverview, setRoleOverview] = useState([]);
  const [roleConfigs, setRoleConfigs] = useState([]);
  const [leads, setLeads] = useState([]);
  const [users, setUsers] = useState([]);

  // 对话框状态
  const [leadDialogOpen, setLeadDialogOpen] = useState(false);
  const [teamMemberDialogOpen, setTeamMemberDialogOpen] = useState(false);
  const [selectedRoleType, setSelectedRoleType] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);

  // 表单数据
  const [leadForm, setLeadForm] = useState({
    role_type_id: "",
    user_id: "",
    allocation_pct: 100
  });
  const [teamMemberForm, setTeamMemberForm] = useState({
    user_id: "",
    allocation_pct: 100
  });

  useEffect(() => {
    if (projectId) {
      loadRoleOverview();
      loadRoleConfigs();
      loadLeads();
      loadUsers();
    }
  }, [projectId]);

  const loadUsers = async () => {
    try {
      const response = await userApi.list({
        page: 1,
        page_size: 100,
        is_active: true
      });
      const data = response.data?.data || response.data || response;
      setUsers(data.items || []);
    } catch (err) {
      console.error("Failed to load users:", err);
    }
  };

  const loadRoleOverview = async () => {
    if (!projectId) {return;}
    try {
      setLoading(true);
      const response = await projectRoleApi.getOverview(projectId);
      const data = response.data?.data || response.data || response;
      setRoleOverview(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load role overview:", err);
      setError(err.response?.data?.detail || err.message || "加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  const loadRoleConfigs = async () => {
    if (!projectId) {return;}
    try {
      const response = await projectRoleApi.configs.get(projectId);
      const data = response.data?.data || response.data || response;
      setRoleConfigs(data.items || []);
    } catch (err) {
      console.error("Failed to load role configs:", err);
    }
  };

  const loadLeads = async () => {
    if (!projectId) {return;}
    try {
      const response = await projectRoleApi.leads.list(projectId, false);
      const data = response.data?.data || response.data || response;
      setLeads(data.items || []);
    } catch (err) {
      console.error("Failed to load leads:", err);
    }
  };

  const handleInitConfigs = async () => {
    if (!projectId) {return;}
    try {
      setLoading(true);
      await projectRoleApi.configs.init(projectId);
      loadRoleConfigs();
      loadRoleOverview();
    } catch (err) {
      console.error("Failed to init configs:", err);
      setError(err.response?.data?.detail || err.message || "初始化失败");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLead = (roleType) => {
    setSelectedRoleType(roleType);
    setLeadForm({
      role_type_id: roleType.id,
      user_id: "",
      allocation_pct: 100
    });
    setLeadDialogOpen(true);
  };

  const handleSaveLead = async () => {
    if (!projectId) {return;}
    try {
      setLoading(true);
      setError(null);
      await projectRoleApi.leads.create(projectId, leadForm);
      setLeadDialogOpen(false);
      loadLeads();
      loadRoleOverview();
    } catch (err) {
      console.error("Failed to create lead:", err);
      setError(err.response?.data?.detail || err.message || "创建失败");
    } finally {
      setLoading(false);
    }
  };

  const handleAddTeamMember = (lead) => {
    setSelectedLead(lead);
    setTeamMemberForm({
      user_id: "",
      allocation_pct: 100
    });
    setTeamMemberDialogOpen(true);
  };

  const handleSaveTeamMember = async () => {
    if (!projectId || !selectedLead) {return;}
    try {
      setLoading(true);
      setError(null);
      await projectRoleApi.team.add(
        projectId,
        selectedLead.id,
        teamMemberForm
      );
      setTeamMemberDialogOpen(false);
      loadLeads();
      loadRoleOverview();
    } catch (err) {
      console.error("Failed to add team member:", err);
      setError(err.response?.data?.detail || err.message || "添加失败");
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveLead = async (memberId) => {
    if (!projectId) {return;}
    if (!await confirmAction("确定要移除这个负责人吗？")) {
      return;
    }
    try {
      setLoading(true);
      await projectRoleApi.leads.delete(projectId, memberId);
      loadLeads();
      loadRoleOverview();
    } catch (err) {
      console.error("Failed to remove lead:", err);
      setError(err.response?.data?.detail || err.message || "移除失败");
    } finally {
      setLoading(false);
    }
  };

  if (!projectId) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={fadeIn}
        className="space-y-6">

        <PageHeader title="项目角色管理" />
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-gray-500">
              请从项目详情页面进入项目角色管理
            </div>
          </CardContent>
        </Card>
      </motion.div>);

  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="space-y-6">

      <PageHeader title="项目角色管理" />

      {/* 错误提示 */}
      {error &&
      <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
      </div>
      }

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">角色概览</TabsTrigger>
          <TabsTrigger value="configs">角色配置</TabsTrigger>
          <TabsTrigger value="leads">负责人管理</TabsTrigger>
        </TabsList>

        {/* 角色概览 */}
        <TabsContent value="overview">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>项目角色概览</CardTitle>
              {roleConfigs.length === 0 &&
              <Button onClick={handleInitConfigs} disabled={loading}>
                  <Settings className="h-4 w-4 mr-2" />
                  初始化角色配置
              </Button>
              }
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="text-center py-8">加载中...</div> :
              roleOverview.length === 0 ?
              <div className="text-center py-8 text-gray-500">
                  暂无角色配置
              </div> :

              <div className="space-y-4">
                  {roleOverview.map((overview) =>
                <Card key={overview.role_type?.id}>
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Briefcase className="h-5 w-5 text-blue-500" />
                              <h3 className="font-semibold text-lg">
                                {overview.role_type?.role_name}
                              </h3>
                              {overview.is_required &&
                          <Badge variant="destructive">必需</Badge>
                          }
                              {overview.is_enabled &&
                          <Badge variant="default">启用</Badge>
                          }
                            </div>
                            <p className="text-sm text-gray-600 mb-4">
                              {overview.role_type?.description}
                            </p>

                            {overview.lead &&
                        <div className="mt-4 p-3 bg-blue-50 rounded">
                                <div className="flex items-center gap-2 mb-2">
                                  <Users className="h-4 w-4" />
                                  <span className="font-semibold">负责人</span>
                                </div>
                                <div className="text-sm">
                                  {overview.lead.user?.real_name ||
                            overview.lead.user?.username ||
                            "未知"}
                                </div>
                                {overview.lead.team_count > 0 &&
                          <div className="text-sm text-gray-600 mt-1">
                                    团队成员: {overview.lead.team_count} 人
                          </div>
                          }
                        </div>
                        }

                            {!overview.has_lead && overview.is_required &&
                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                                <div className="text-sm text-yellow-800 mb-2">
                                  该角色为必需角色，尚未指定负责人
                                </div>
                                <Button
                            size="sm"
                            onClick={() =>
                            handleCreateLead(overview.role_type)
                            }>

                                  <UserPlus className="h-4 w-4 mr-2" />
                                  指定负责人
                                </Button>
                        </div>
                        }

                            {!overview.has_lead &&
                        !overview.is_required &&
                        overview.is_enabled &&
                        <div className="mt-4">
                                  <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                            handleCreateLead(overview.role_type)
                            }>

                                    <UserPlus className="h-4 w-4 mr-2" />
                                    指定负责人
                                  </Button>
                        </div>
                        }
                          </div>
                        </div>
                      </CardContent>
                </Card>
                )}
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 角色配置 */}
        <TabsContent value="configs">
          <Card>
            <CardHeader>
              <CardTitle>角色配置</CardTitle>
            </CardHeader>
            <CardContent>
              {roleConfigs.length === 0 ?
              <div className="text-center py-8">
                  <div className="text-gray-500 mb-4">尚未初始化角色配置</div>
                  <Button onClick={handleInitConfigs} disabled={loading}>
                    <Settings className="h-4 w-4 mr-2" />
                    初始化角色配置
                  </Button>
              </div> :

              <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">角色名称</th>
                        <th className="text-left p-2">是否启用</th>
                        <th className="text-left p-2">是否必需</th>
                        <th className="text-left p-2">备注</th>
                      </tr>
                    </thead>
                    <tbody>
                      {roleConfigs.map((config) =>
                    <tr
                      key={config.id}
                      className="border-b hover:bg-gray-50">

                          <td className="p-2">
                            {config.role_type?.role_name || "-"}
                          </td>
                          <td className="p-2">
                            <Badge
                          variant={
                          config.is_enabled ? "default" : "secondary"
                          }>

                              {config.is_enabled ? "启用" : "禁用"}
                            </Badge>
                          </td>
                          <td className="p-2">
                            <Badge
                          variant={
                          config.is_required ? "destructive" : "outline"
                          }>

                              {config.is_required ? "必需" : "可选"}
                            </Badge>
                          </td>
                          <td className="p-2 text-sm text-gray-600">
                            {config.remark || "-"}
                          </td>
                    </tr>
                    )}
                    </tbody>
                  </table>
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 负责人管理 */}
        <TabsContent value="leads">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>项目负责人</CardTitle>
              {roleOverview.length > 0 &&
              <Button
                onClick={() => {
                  const availableRole = roleOverview.find(
                    (r) => !r.has_lead && r.is_enabled
                  );
                  if (availableRole) {
                    handleCreateLead(availableRole.role_type);
                  }
                }}>

                  <Plus className="h-4 w-4 mr-2" />
                  添加负责人
              </Button>
              }
            </CardHeader>
            <CardContent>
              {leads.length === 0 ?
              <div className="text-center py-8 text-gray-500">暂无负责人</div> :

              <div className="space-y-4">
                  {leads.map((lead) =>
                <Card key={lead.id}>
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Users className="h-5 w-5 text-blue-500" />
                              <h3 className="font-semibold">
                                {lead.role_type?.role_name || lead.role_code}
                              </h3>
                            </div>
                            <div className="text-sm text-gray-600 mb-2">
                              负责人:{" "}
                              {lead.user?.real_name ||
                          lead.user?.username ||
                          "未知"}
                            </div>
                            {lead.team_count > 0 &&
                        <div className="text-sm text-gray-600 mb-2">
                                团队成员: {lead.team_count} 人
                        </div>
                        }
                            {lead.role_type?.can_have_team &&
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAddTeamMember(lead)}
                          className="mt-2">

                                <UserPlus className="h-4 w-4 mr-2" />
                                添加团队成员
                        </Button>
                        }
                          </div>
                          <div className="flex gap-2">
                            <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveLead(lead.id)}>

                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                </Card>
                )}
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 创建负责人对话框 */}
      <Dialog open={leadDialogOpen} onOpenChange={setLeadDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>指定项目负责人</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {selectedRoleType &&
            <div>
                <Label>角色类型</Label>
                <Input value={selectedRoleType.role_name} disabled />
            </div>
            }
            <div>
              <Label>选择用户 *</Label>
              <Select
                value={leadForm.user_id?.toString() || ""}
                onValueChange={(value) =>
                setLeadForm({ ...leadForm, user_id: parseInt(value) })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择用户" />
                </SelectTrigger>
                <SelectContent>
                  {users.map((user) =>
                  <SelectItem key={user.id} value={user.id.toString()}>
                      {user.real_name || user.username} (
                      {user.department || "未分配部门"})
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>分配比例 (%)</Label>
              <Input
                type="number"
                min="0"
                max="100"
                value={leadForm.allocation_pct}
                onChange={(e) =>
                setLeadForm({
                  ...leadForm,
                  allocation_pct: parseInt(e.target.value) || 0
                })
                } />

            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLeadDialogOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleSaveLead}
              disabled={loading || !leadForm.user_id}>

              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 添加团队成员对话框 */}
      <Dialog
        open={teamMemberDialogOpen}
        onOpenChange={setTeamMemberDialogOpen}>

        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>添加团队成员</DialogTitle>
          </DialogHeader>
          {selectedLead &&
          <div className="space-y-4">
              <div>
                <Label>负责人</Label>
                <Input
                value={`${selectedLead.role_type?.role_name || selectedLead.role_code} - ${selectedLead.user?.real_name || selectedLead.user?.username || "未知"}`}
                disabled />

              </div>
              <div>
                <Label>选择用户 *</Label>
                <Select
                value={teamMemberForm.user_id?.toString() || ""}
                onValueChange={(value) =>
                setTeamMemberForm({
                  ...teamMemberForm,
                  user_id: parseInt(value)
                })
                }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择用户" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.map((user) =>
                  <SelectItem key={user.id} value={user.id.toString()}>
                        {user.real_name || user.username} (
                        {user.department || "未分配部门"})
                  </SelectItem>
                  )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>分配比例 (%)</Label>
                <Input
                type="number"
                min="0"
                max="100"
                value={teamMemberForm.allocation_pct}
                onChange={(e) =>
                setTeamMemberForm({
                  ...teamMemberForm,
                  allocation_pct: parseInt(e.target.value) || 0
                })
                } />

              </div>
          </div>
          }
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setTeamMemberDialogOpen(false)}>

              取消
            </Button>
            <Button
              onClick={handleSaveTeamMember}
              disabled={loading || !teamMemberForm.user_id}>

              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}