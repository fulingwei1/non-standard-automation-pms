/**
 * Milestone Management Page - 里程碑管理页面
 * Features: 里程碑列表、创建、更新、完成、时间线展示
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Target,
  TrendingUp,
  Edit,
  Eye } from
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
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { cn, formatDate } from "../lib/utils";
import { milestoneApi, projectApi } from "../services/api";
import { confirmAction } from "@/lib/confirmAction";
const statusConfigs = {
  PENDING: { label: "待开始", color: "bg-slate-500", icon: Clock },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500", icon: TrendingUp },
  COMPLETED: { label: "已完成", color: "bg-emerald-500", icon: CheckCircle2 },
  OVERDUE: { label: "已逾期", color: "bg-red-500", icon: AlertTriangle }
};
export default function MilestoneManagement() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [milestones, setMilestones] = useState([]);
  // Filters
  const [filterStatus, setFilterStatus] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedMilestone, setSelectedMilestone] = useState(null);
  // Form state
  const [newMilestone, setNewMilestone] = useState({
    milestone_name: "",
    milestone_type: "PROJECT",
    planned_date: "",
    target_amount: 0,
    description: "",
    auto_invoice: false
  });
  useEffect(() => {
    if (id) {
      fetchProject();
      fetchMilestones();
    }
  }, [id, filterStatus]);
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id);
      setProject(res.data || res);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };
  const fetchMilestones = async () => {
    try {
      setLoading(true);
      const params = { project_id: id };
      if (filterStatus) {params.status = filterStatus;}
      const res = await milestoneApi.list(id);
      const milestoneList = res.data || res || [];
      setMilestones(milestoneList);
    } catch (error) {
      console.error("Failed to fetch milestones:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleCreateMilestone = async () => {
    if (!newMilestone.milestone_name || !newMilestone.planned_date) {
      alert("请填写里程碑名称和计划日期");
      return;
    }
    try {
      await milestoneApi.create({
        ...newMilestone,
        project_id: parseInt(id)
      });
      setShowCreateDialog(false);
      setNewMilestone({
        milestone_name: "",
        milestone_type: "PROJECT",
        planned_date: "",
        target_amount: 0,
        description: "",
        auto_invoice: false
      });
      fetchMilestones();
    } catch (error) {
      console.error("Failed to create milestone:", error);
      alert(
        "创建里程碑失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };
  const handleCompleteMilestone = async (milestoneId) => {
    if (!await confirmAction("确认完成此里程碑？")) {return;}
    try {
      await milestoneApi.complete(milestoneId);
      fetchMilestones();
    } catch (error) {
      console.error("Failed to complete milestone:", error);
      alert(
        "完成里程碑失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };
  const handleViewDetail = async (milestoneId) => {
    try {
      const res = await milestoneApi.get(milestoneId);
      setSelectedMilestone(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch milestone detail:", error);
    }
  };
  const getStatusIcon = (status) => {
    const config = statusConfigs[status];
    const Icon = config?.icon || Clock;
    return <Icon className="w-4 h-4" />;
  };
  const isOverdue = (milestone) => {
    if (milestone.status === "COMPLETED") {return false;}
    if (!milestone.planned_date) {return false;}
    return new Date(milestone.planned_date) < new Date();
  };
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${id}`)}>

            <ArrowLeft className="w-4 h-4 mr-2" />
            返回项目
          </Button>
          <PageHeader
            title={`${project?.project_name || "项目"} - 里程碑管理`}
            description="里程碑列表、创建、完成、时间线展示" />

        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建里程碑
        </Button>
      </div>
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select value={filterStatus || "unknown"} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key || "unknown"}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Milestone Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>里程碑时间线</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          milestones.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无里程碑</div> :

          <div className="space-y-4">
              {(milestones || []).map((milestone, _index) => {
              const overdue = isOverdue(milestone);
              const status = overdue ? "OVERDUE" : milestone.status;
              const config = statusConfigs[status] || statusConfigs.PENDING;
              return (
                <div
                  key={milestone.id}
                  className="relative border-l-2 border-slate-200 pl-6 pb-6 last:pb-0">

                    <div className="absolute -left-2.5 top-0">
                      <div
                      className={cn(
                        "w-5 h-5 rounded-full border-2 border-white",
                        config.color
                      )}>

                        {getStatusIcon(status)}
                      </div>
                    </div>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-medium">
                            {milestone.milestone_name}
                          </h3>
                          <Badge className={config.color}>{config.label}</Badge>
                          {milestone.milestone_type &&
                        <Badge variant="outline">
                              {milestone.milestone_type}
                        </Badge>
                        }
                          {overdue &&
                        <Badge className="bg-red-500">
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              逾期
                        </Badge>
                        }
                        </div>
                        {milestone.description &&
                      <p className="text-sm text-slate-500 mb-2">
                            {milestone.description}
                      </p>
                      }
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {milestone.planned_date ?
                          formatDate(milestone.planned_date) :
                          "-"}
                          </div>
                          {milestone.target_amount > 0 &&
                        <div className="flex items-center gap-1">
                              <Target className="w-4 h-4" />
                              目标金额: ¥
                              {milestone.target_amount.toLocaleString()}
                        </div>
                        }
                          {milestone.completed_date &&
                        <div className="flex items-center gap-1 text-emerald-600">
                              <CheckCircle2 className="w-4 h-4" />
                              完成时间: {formatDate(milestone.completed_date)}
                        </div>
                        }
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetail(milestone.id)}>

                          <Eye className="w-4 h-4" />
                        </Button>
                        {milestone.status !== "COMPLETED" &&
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                        handleCompleteMilestone(milestone.id)
                        }>

                            <CheckCircle2 className="w-4 h-4 mr-2" />
                            完成
                      </Button>
                      }
                      </div>
                    </div>
                </div>);

            })}
          </div>
          }
        </CardContent>
      </Card>
      {/* Create Milestone Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建里程碑</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  里程碑名称 *
                </label>
                <Input
                  value={newMilestone.milestone_name}
                  onChange={(e) =>
                  setNewMilestone({
                    ...newMilestone,
                    milestone_name: e.target.value
                  })
                  }
                  placeholder="请输入里程碑名称" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  里程碑类型
                </label>
                <Select
                  value={newMilestone.milestone_type}
                  onValueChange={(val) =>
                  setNewMilestone({ ...newMilestone, milestone_type: val })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PROJECT">项目里程碑</SelectItem>
                    <SelectItem value="PAYMENT">收款节点</SelectItem>
                    <SelectItem value="DELIVERY">交付节点</SelectItem>
                    <SelectItem value="OTHER">其他</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  计划日期 *
                </label>
                <Input
                  type="date"
                  value={newMilestone.planned_date}
                  onChange={(e) =>
                  setNewMilestone({
                    ...newMilestone,
                    planned_date: e.target.value
                  })
                  } />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  目标金额
                </label>
                <Input
                  type="number"
                  value={newMilestone.target_amount}
                  onChange={(e) =>
                  setNewMilestone({
                    ...newMilestone,
                    target_amount: parseFloat(e.target.value) || 0
                  })
                  }
                  placeholder="0.00" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <Input
                  value={newMilestone.description}
                  onChange={(e) =>
                  setNewMilestone({
                    ...newMilestone,
                    description: e.target.value
                  })
                  }
                  placeholder="里程碑描述" />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreateMilestone}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Milestone Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>里程碑详情</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedMilestone &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">
                      里程碑名称
                    </div>
                    <div className="font-medium">
                      {selectedMilestone.milestone_name}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge
                    className={statusConfigs[selectedMilestone.status]?.color}>

                      {statusConfigs[selectedMilestone.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">类型</div>
                    <div>{selectedMilestone.milestone_type || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划日期</div>
                    <div>
                      {selectedMilestone.planned_date ?
                    formatDate(selectedMilestone.planned_date) :
                    "-"}
                    </div>
                  </div>
                  {selectedMilestone.target_amount > 0 &&
                <div>
                      <div className="text-sm text-slate-500 mb-1">
                        目标金额
                      </div>
                      <div className="font-medium">
                        ¥{selectedMilestone.target_amount.toLocaleString()}
                      </div>
                </div>
                }
                  {selectedMilestone.completed_date &&
                <div>
                      <div className="text-sm text-slate-500 mb-1">
                        完成日期
                      </div>
                      <div>{formatDate(selectedMilestone.completed_date)}</div>
                </div>
                }
                </div>
                {selectedMilestone.description &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">描述</div>
                    <div>{selectedMilestone.description}</div>
              </div>
              }
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            {selectedMilestone && selectedMilestone.status !== "COMPLETED" &&
            <Button
              onClick={() => handleCompleteMilestone(selectedMilestone.id)}>

                <CheckCircle2 className="w-4 h-4 mr-2" />
                完成里程碑
            </Button>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}