/**
 * AI 自动组队页面
 * 功能：
 * - AI 生成项目组方案
 * - 查看推荐工程师
 * - 调整团队成员
 * - 提交审批
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Users,
  Sparkles,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  RefreshCw,
  Save,
  Send,
  Edit2,
  Trash2,
  Plus,
  UserPlus,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer } from "../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Textarea,
  Input,
  Label,
} from "../components/ui";
import { teamGenerationApi } from "../services/api";

export default function TeamGeneration() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [teamPlan, setTeamPlan] = useState(null);
  const [members, setMembers] = useState([]);
  const [showAdjustDialog, setShowAdjustDialog] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [approvalComments, setApprovalComments] = useState("");

  const generateTeam = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await teamGenerationApi.generateTeam(projectId);
      const data = res.data || res;
      
      setTeamPlan(data);
      setMembers(
        Object.entries(data.role_assignments || {}).map(([role, assignment]) => ({
          ...assignment,
          role,
          editMode: false,
        }))
      );
    } catch (error) {
      console.error("生成失败:", error);
      alert("生成失败：" + error.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    generateTeam();
  }, [generateTeam]);

  const handleSave = async () => {
    try {
      const roleAssignments = {};
      members.forEach(m => {
        roleAssignments[m.role] = m;
      });
      
      await teamGenerationApi.saveTeamPlan(projectId, {
        ...teamPlan,
        role_assignments: roleAssignments,
      });
      alert("方案已保存");
    } catch (error) {
      alert("保存失败：" + error.message);
    }
  };

  const handleSubmit = async () => {
    try {
      const roleAssignments = {};
      members.forEach(m => {
        roleAssignments[m.role] = m;
      });
      
      const saved = await teamGenerationApi.saveTeamPlan(projectId, {
        ...teamPlan,
        role_assignments: roleAssignments,
      });
      
      await teamGenerationApi.submitTeamPlan(saved.plan_id);
      alert("方案已提交审批");
      navigate("/team-plans");
    } catch (error) {
      alert("提交失败：" + error.message);
    }
  };

  const handleAdjustMember = (member) => {
    setSelectedMember(member);
    setShowAdjustDialog(true);
  };

  const handleRemoveMember = (role) => {
    setMembers(members.filter(m => m.role !== role));
  };

  const handleAddMember = () => {
    // TODO: 打开选择工程师对话框
    alert("功能开发中...");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Sparkles className="w-6 h-6 animate-pulse text-purple-500 mr-2" />
        <span className="text-slate-400">AI 生成团队方案中...</span>
      </div>
    );
  }

  if (!teamPlan) {
    return (
      <div className="text-center py-12 text-slate-400">
        生成失败
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader
            title="AI 智能组队"
            description="根据项目需求自动匹配工程师，生成项目组方案"
            actions={
              <div className="flex gap-2">
                <Button onClick={generateTeam} variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  重新生成
                </Button>
                <Button onClick={handleSave} variant="outline">
                  <Save className="w-4 h-4 mr-2" />
                  保存方案
                </Button>
                <Button onClick={handleSubmit}>
                  <Send className="w-4 h-4 mr-2" />
                  提交审批
                </Button>
              </div>
            }
          />

          {/* 方案概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <Users className="w-8 h-8 text-blue-500" />
                  <div>
                    <div className="text-sm text-slate-400">团队人数</div>
                    <div className="text-2xl font-bold">{teamPlan.total_members}人</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-8 h-8 text-green-500" />
                  <div>
                    <div className="text-sm text-slate-400">综合评分</div>
                    <div className="text-2xl font-bold">{teamPlan.overall_score}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <Sparkles className="w-8 h-8 text-purple-500" />
                  <div>
                    <div className="text-sm text-slate-400">总工时</div>
                    <div className="text-2xl font-bold">{teamPlan.total_estimated_hours.toFixed(0)}h</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-8 h-8 text-orange-500" />
                  <div>
                    <div className="text-sm text-slate-400">预计工期</div>
                    <div className="text-2xl font-bold">{teamPlan.estimated_duration_days}天</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 方案评分 */}
          <Card>
            <CardHeader>
              <CardTitle>方案评分</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">技能覆盖率</span>
                    <span className="text-sm font-medium">{teamPlan.skill_coverage}%</span>
                  </div>
                  <Progress value={teamPlan.skill_coverage} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">负载均衡度</span>
                    <span className="text-sm font-medium">{teamPlan.capacity_balance}%</span>
                  </div>
                  <Progress value={teamPlan.capacity_balance} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">成本效率</span>
                    <span className="text-sm font-medium">{teamPlan.cost_efficiency}%</span>
                  </div>
                  <Progress value={teamPlan.cost_efficiency} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 团队成员 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>团队成员</CardTitle>
                  <CardDescription>
                    AI 推荐的工程师，可调整
                  </CardDescription>
                </div>
                <Button onClick={handleAddMember} variant="outline" size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  添加成员
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>角色</TableHead>
                    <TableHead>工程师</TableHead>
                    <TableHead>匹配度</TableHead>
                    <TableHead>工时</TableHead>
                    <TableHead>投入比例</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {members.map((member, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{member.role_name}</div>
                          <div className="text-xs text-slate-400">{member.role}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{member.engineer_name}</div>
                          <div className="text-xs text-slate-400">{member.department}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Badge className={
                            member.match_score >= 90 ? "bg-green-500" :
                            member.match_score >= 75 ? "bg-blue-500" :
                            member.match_score >= 60 ? "bg-yellow-500" : "bg-red-500"
                          }>
                            {member.match_score}
                          </Badge>
                          <div className="text-xs text-slate-400 max-w-[200px] truncate">
                            {member.match_reason}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{member.estimated_hours.toFixed(0)}h</TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          defaultValue={member.allocation_percentage || 100}
                          className="w-20"
                          min="0"
                          max="100"
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAdjustMember(member)}
                          >
                            <Edit2 className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRemoveMember(member.role)}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* 优势与风险 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-500">
                  <CheckCircle className="w-5 h-5" />
                  方案优势
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {(teamPlan.advantages || []).map((adv, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                      <span className="text-slate-300">{adv}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-500">
                  <AlertCircle className="w-5 h-5" />
                  潜在风险
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {(teamPlan.risks || []).map((risk, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5" />
                      <span className="text-slate-300">{risk}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* 调整成员对话框 */}
          <Dialog open={showAdjustDialog} onOpenChange={setShowAdjustDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>调整成员 - {selectedMember?.role_name}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>工程师</Label>
                  <Input defaultValue={selectedMember?.engineer_name} />
                </div>
                <div>
                  <Label>投入比例 (%)</Label>
                  <Input
                    type="number"
                    defaultValue={selectedMember?.allocation_percentage || 100}
                    min="0"
                    max="100"
                  />
                </div>
                <div>
                  <Label>备注</Label>
                  <Textarea rows={3} placeholder="备注信息..." />
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => setShowAdjustDialog(false)}>取消</Button>
                <Button onClick={() => setShowAdjustDialog(false)}>保存</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    </div>
  );
}
