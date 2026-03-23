/**
 * Milestone Management Page - 里程碑管理页面
 * Features: 里程碑列表、创建、更新、完成、时间线展示
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp } from
"lucide-react";






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
  const [projects, setProjects] = useState([]);
  const [milestones, setMilestones] = useState([]);
  // 全局模式：是否有项目ID参数
  const isGlobalMode = !id;
  // Filters
  const [filterStatus, setFilterStatus] = useState("");
  const [filterProjectId, setFilterProjectId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
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
    auto_invoice: false,
    project_id: ""
  });
  // 加载项目列表（全局模式）
  useEffect(() => {
    if (isGlobalMode) {
      fetchProjects();
      fetchAllMilestones();
    } else {
      fetchProject();
      fetchMilestones();
    }
  }, [id, filterStatus, filterProjectId]);
  // 获取项目列表（全局模式用）
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 200 });
      const list = res?.data?.items ?? res?.items ?? res?.data ?? res ?? [];
      setProjects(Array.isArray(list) ? list : []);
    } catch (_error) {
      // 非关键操作失败时静默降级
    }
  };
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id);
      setProject(res.data || res);
    } catch (_error) {
      // 非关键操作失败时静默降级
    }
  };
  // 获取所有里程碑（全局模式）
  const fetchAllMilestones = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterStatus && filterStatus !== "all") params.status = filterStatus;
      if (filterProjectId && filterProjectId !== "all") params.project_id = filterProjectId;
      // 假设 milestoneApi.listAll 存在，否则需要调用 /milestones 接口
      const res = await milestoneApi.listAll ? milestoneApi.listAll(params) : milestoneApi.list(null, params);
      const milestoneList = res?.data?.items ?? res?.data ?? res ?? [];
      setMilestones(Array.isArray(milestoneList) ? milestoneList : []);
    } catch (error) {
      setMilestones([]);
    } finally {
      setLoading(false);
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
    } catch (_error) {
      // 非关键操作失败时静默降级
    } finally {
      setLoading(false);
    }
  };
  // 筛选后的里程碑
  const filteredMilestones = milestones.filter((m) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      (m.milestone_name || "").toLowerCase().includes(query) ||
      (m.project_name || "").toLowerCase().includes(query)
    );
  });
  const handleCreateMilestone = async () => {
    const projectIdToUse = isGlobalMode ? newMilestone.project_id : id;
    if (!newMilestone.milestone_name || !newMilestone.planned_date) {
      alert("请填写里程碑名称和计划日期");
      return;
    }
    if (isGlobalMode && !projectIdToUse) {
      alert("请选择项目");
      return;
    }
    try {
      await milestoneApi.create({
        ...newMilestone,
        project_id: parseInt(projectIdToUse)
      });
      setShowCreateDialog(false);
      setNewMilestone({
        milestone_name: "",
        milestone_type: "PROJECT",
        planned_date: "",
        target_amount: 0,
        description: "",
        auto_invoice: false,
        project_id: ""
      });
      if (isGlobalMode) {
        fetchAllMilestones();
      } else {
        fetchMilestones();
      }
    } catch (error) {
      alert(
        "创建里程碑失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };
  const handleCompleteMilestone = async (milestoneId) => {
    if (!await confirmAction("确认完成此里程碑？")) {return;}
    try {
      await milestoneApi.complete(milestoneId);
      if (isGlobalMode) {
        fetchAllMilestones();
      } else {
        fetchMilestones();
      }
    } catch (error) {
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
    } catch (_error) {
      // 非关键操作失败时静默降级
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
          {!isGlobalMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/projects/${id}`)}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目
            </Button>
          )}
          <PageHeader
            title={isGlobalMode ? "里程碑管理" : `${project?.project_name || "项目"} - 里程碑管理`}
            description={isGlobalMode ? "全局里程碑视图，支持筛选和搜索" : "里程碑列表、创建、完成、时间线展示"} />
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建里程碑
        </Button>
      </div>
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* 搜索框 */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="搜索里程碑..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            {/* 项目筛选（仅全局模式） */}
            {isGlobalMode && (
              <Select value={filterProjectId || "all"} onValueChange={setFilterProjectId}>
                <SelectTrigger>
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部项目</SelectItem>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {p.name || p.project_name || `项目 ${p.id}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {/* 状态筛选 */}
            <Select value={filterStatus || "all"} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
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
          filteredMilestones.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无里程碑</div> :

          <div className="space-y-4">
              {(filteredMilestones || []).map((milestone, _index) => {
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
                          {isGlobalMode && milestone.project_name &&
                        <Badge variant="secondary" className="bg-blue-500/20 text-blue-400">
                              {milestone.project_name}
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
              {/* 全局模式需要选择项目 */}
              {isGlobalMode && (
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    所属项目 *
                  </label>
                  <Select
                    value={newMilestone.project_id}
                    onValueChange={(val) =>
                    setNewMilestone({ ...newMilestone, project_id: val })
                    }>
                    <SelectTrigger>
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      {projects.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>
                          {p.name || p.project_name || `项目 ${p.id}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
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