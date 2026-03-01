import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn as _cn } from "../lib/utils";
import { pmoApi, projectApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Progress,
  Input,
  SkeletonCard } from
"../components/ui";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui";
import {
  ArrowLeft,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Target,
  FileCheck,
  ArrowRight,
  Play,
  Eye,
  Calendar } from
"lucide-react";

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  }
};

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const getStatusBadge = (status) => {
  const badges = {
    PENDING: { label: "待开始", variant: "secondary", color: "text-slate-400" },
    IN_PROGRESS: { label: "进行中", variant: "info", color: "text-blue-400" },
    COMPLETED: {
      label: "已完成",
      variant: "success",
      color: "text-emerald-400"
    },
    SKIPPED: { label: "已跳过", variant: "secondary", color: "text-slate-500" }
  };
  return badges[status] || badges.PENDING;
};

const getReviewResultBadge = (result) => {
  const badges = {
    PASSED: { label: "通过", variant: "success", color: "text-emerald-400" },
    CONDITIONAL: {
      label: "有条件通过",
      variant: "warning",
      color: "text-yellow-400"
    },
    FAILED: { label: "未通过", variant: "danger", color: "text-red-400" }
  };
  return badges[result] || null;
};

export default function ProjectPhaseManagement() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [project, setProject] = useState(null);
  const [phases, setPhases] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(
    projectId ? parseInt(projectId) : null
  );
  const [projectSearch, setProjectSearch] = useState("");
  const [projectList, setProjectList] = useState([]);
  const [showProjectSelect, setShowProjectSelect] = useState(!projectId);

  // Dialogs
  const [entryCheckDialog, setEntryCheckDialog] = useState({
    open: false,
    phaseId: null
  });
  const [exitCheckDialog, setExitCheckDialog] = useState({
    open: false,
    phaseId: null
  });
  const [reviewDialog, setReviewDialog] = useState({
    open: false,
    phaseId: null
  });
  const [advanceDialog, setAdvanceDialog] = useState({
    open: false,
    phaseId: null
  });
  const [detailDialog, setDetailDialog] = useState({
    open: false,
    phase: null
  });

  useEffect(() => {
    if (selectedProjectId) {
      fetchProjectData();
      fetchPhases();
    } else {
      fetchProjectList();
    }
  }, [selectedProjectId]);

  const fetchProjectData = async () => {
    if (!selectedProjectId) {return;}
    try {
      const res = await projectApi.get(selectedProjectId);
      const data = res.data || res;
      setProject(data);
    } catch (err) {
      console.error("Failed to fetch project:", err);
      setError(err.response?.data?.detail || err.message || "加载项目信息失败");
    }
  };

  const fetchPhases = async () => {
    if (!selectedProjectId) {return;}
    try {
      setLoading(true);
      setError(null);
      const res = await pmoApi.phases.list(selectedProjectId);
      const data = res.data || res;
      setPhases(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch phases:", err);
      setError(err.response?.data?.detail || err.message || "加载阶段数据失败");
      setPhases([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectList = async () => {
    try {
      const res = await projectApi.list({
        page: 1,
        page_size: 50,
        keyword: projectSearch
      });
      const data = res.data || res;
      // Handle PaginatedResponse format
      if (data && typeof data === "object" && "items" in data) {
        setProjectList(data.items || []);
      } else if (Array.isArray(data)) {
        setProjectList(data);
      } else {
        setProjectList([]);
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setProjectList([]);
    }
  };

  const handleEntryCheck = async (phaseId, data) => {
    try {
      await pmoApi.phases.entryCheck(phaseId, data);
      setEntryCheckDialog({ open: false, phaseId: null });
      fetchPhases();
    } catch (err) {
      console.error("Failed to entry check:", err);
      alert("入口检查失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleExitCheck = async (phaseId, data) => {
    try {
      await pmoApi.phases.exitCheck(phaseId, data);
      setExitCheckDialog({ open: false, phaseId: null });
      fetchPhases();
    } catch (err) {
      console.error("Failed to exit check:", err);
      alert("出口检查失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleReview = async (phaseId, data) => {
    try {
      await pmoApi.phases.review(phaseId, data);
      setReviewDialog({ open: false, phaseId: null });
      fetchPhases();
    } catch (err) {
      console.error("Failed to review:", err);
      alert("评审失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleAdvance = async (phaseId, data) => {
    try {
      await pmoApi.phases.advance(phaseId, data);
      setAdvanceDialog({ open: false, phaseId: null });
      fetchPhases();
    } catch (err) {
      console.error("Failed to advance:", err);
      alert("推进失败: " + (err.response?.data?.detail || err.message));
    }
  };

  if (showProjectSelect) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}>

        <PageHeader title="项目阶段管理" description="选择项目以管理其阶段" />

        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-6">
            <div className="mb-4">
              <Input
                placeholder="搜索项目名称或编码..."
                value={projectSearch || "unknown"}
                onChange={(e) => {
                  setProjectSearch(e.target.value);
                  fetchProjectList();
                }}
                className="w-full"
                icon={Search} />

            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(projectList || []).map((proj) =>
              <div
                key={proj.id}
                onClick={() => {
                  setSelectedProjectId(proj.id);
                  setShowProjectSelect(false);
                  navigate(`/pmo/phases/${proj.id}`);
                }}
                className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.06] hover:border-white/10 cursor-pointer transition-all">

                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-white">
                        {proj.project_name}
                      </h3>
                      <p className="text-sm text-slate-400">
                        {proj.project_code}
                      </p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-slate-500" />
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>);

  }

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <PageHeader
        title="项目阶段管理"
        description={
        project ? `${project.project_name} - 阶段门控管理` : "阶段门控管理"
        }
        action={
        <Button
          variant="outline"
          onClick={() => {
            setShowProjectSelect(true);
            navigate("/pmo/phases");
          }}>

            <ArrowLeft className="h-4 w-4 mr-2" />
            选择项目
        </Button>
        } />


      {/* Error Message */}
      {error &&
      <Card className="mb-6 border-red-500/30 bg-red-500/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-red-400">
                <XCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
              <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setError(null);
                if (selectedProjectId) {
                  fetchProjectData();
                  fetchPhases();
                }
              }}
              className="border-red-500/30 text-red-400 hover:bg-red-500/20">

                重试
              </Button>
            </div>
          </CardContent>
      </Card>
      }

      {loading ?
      <div className="grid grid-cols-1 gap-4">
          {Array(3).
        fill(null).
        map((_, i) =>
        <SkeletonCard key={i} />
        )}
      </div> :
      error ? null : phases.length > 0 ?
      <div className="space-y-4">
          {(phases || []).map((phase, _index) => {
          const statusBadge = getStatusBadge(phase.status);
          const reviewBadge = phase.review_result ?
          getReviewResultBadge(phase.review_result) :
          null;

          return (
            <motion.div key={phase.id} variants={staggerChild}>
                <Card className="hover:bg-white/[0.02] transition-colors">
                  <CardContent className="p-5">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-indigo-500/10 ring-1 ring-primary/20">
                          <Target className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-white">
                              {phase.phase_name}
                            </h3>
                            <Badge variant={statusBadge.variant}>
                              {statusBadge.label}
                            </Badge>
                            {reviewBadge &&
                          <Badge variant={reviewBadge.variant}>
                                {reviewBadge.label}
                          </Badge>
                          }
                          </div>
                          <p className="text-xs text-slate-500 mt-1">
                            {phase.phase_code} • 顺序: {phase.phase_order}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Timeline */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-slate-400">计划开始</span>
                        <p className="text-white mt-1">
                          {phase.plan_start_date ?
                        formatDate(phase.plan_start_date) :
                        "未设置"}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">计划结束</span>
                        <p className="text-white mt-1">
                          {phase.plan_end_date ?
                        formatDate(phase.plan_end_date) :
                        "未设置"}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">实际开始</span>
                        <p className="text-white mt-1">
                          {phase.actual_start_date ?
                        formatDate(phase.actual_start_date) :
                        "未开始"}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">实际结束</span>
                        <p className="text-white mt-1">
                          {phase.actual_end_date ?
                        formatDate(phase.actual_end_date) :
                        "未结束"}
                        </p>
                      </div>
                    </div>

                    {/* Progress */}
                    <div className="mb-4">
                      <div className="flex justify-between text-xs mb-2">
                        <span className="text-slate-400">阶段进度</span>
                        <span className="text-white font-medium">
                          {phase.progress || 0}%
                        </span>
                      </div>
                      <Progress value={phase.progress || 0} />
                    </div>

                    {/* Criteria */}
                    {(phase.entry_criteria || phase.exit_criteria) &&
                  <div className="mb-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                        {phase.entry_criteria &&
                    <div className="mb-2">
                            <span className="text-xs text-slate-400">
                              入口条件:
                            </span>
                            <p className="text-sm text-white mt-1">
                              {phase.entry_criteria}
                            </p>
                    </div>
                    }
                        {phase.exit_criteria &&
                    <div>
                            <span className="text-xs text-slate-400">
                              出口条件:
                            </span>
                            <p className="text-sm text-white mt-1">
                              {phase.exit_criteria}
                            </p>
                    </div>
                    }
                  </div>
                  }

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <div className="flex items-center gap-2 flex-wrap">
                        {phase.status === "PENDING" &&
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                        setEntryCheckDialog({
                          open: true,
                          phaseId: phase.id
                        })
                        }>

                            <FileCheck className="h-4 w-4 mr-2" />
                            入口检查
                      </Button>
                      }
                        {phase.status === "IN_PROGRESS" &&
                      <>
                            <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                          setExitCheckDialog({
                            open: true,
                            phaseId: phase.id
                          })
                          }>

                              <FileCheck className="h-4 w-4 mr-2" />
                              出口检查
                            </Button>
                            {phase.review_required &&
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                          setReviewDialog({
                            open: true,
                            phaseId: phase.id
                          })
                          }>

                                <CheckCircle2 className="h-4 w-4 mr-2" />
                                阶段评审
                        </Button>
                        }
                      </>
                      }
                        {phase.status !== "COMPLETED" &&
                      phase.status !== "SKIPPED" &&
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                        setAdvanceDialog({
                          open: true,
                          phaseId: phase.id
                        })
                        }>

                              <Play className="h-4 w-4 mr-2" />
                              推进阶段
                      </Button>
                      }
                      </div>
                      <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setDetailDialog({ open: true, phase })}>

                        <Eye className="h-4 w-4 mr-2" />
                        查看详情
                      </Button>
                    </div>
                  </CardContent>
                </Card>
            </motion.div>);

        })}
      </div> :

      <Card>
          <CardContent className="p-12 text-center text-slate-500">
            该项目暂无阶段数据
          </CardContent>
      </Card>
      }

      {/* Entry Check Dialog */}
      <EntryCheckDialog
        open={entryCheckDialog.open}
        onOpenChange={(open) => setEntryCheckDialog({ open, phaseId: null })}
        onSubmit={(data) => handleEntryCheck(entryCheckDialog.phaseId, data)} />


      {/* Exit Check Dialog */}
      <ExitCheckDialog
        open={exitCheckDialog.open}
        onOpenChange={(open) => setExitCheckDialog({ open, phaseId: null })}
        onSubmit={(data) => handleExitCheck(exitCheckDialog.phaseId, data)} />


      {/* Review Dialog */}
      <ReviewDialog
        open={reviewDialog.open}
        onOpenChange={(open) => setReviewDialog({ open, phaseId: null })}
        onSubmit={(data) => handleReview(reviewDialog.phaseId, data)} />


      {/* Advance Dialog */}
      <AdvanceDialog
        open={advanceDialog.open}
        onOpenChange={(open) => setAdvanceDialog({ open, phaseId: null })}
        onSubmit={(data) => handleAdvance(advanceDialog.phaseId, data)} />


      {/* Detail Dialog */}
      <PhaseDetailDialog
        open={detailDialog.open}
        onOpenChange={(open) => setDetailDialog({ open, phase: null })}
        phase={detailDialog.phase} />

    </motion.div>);

}

// Entry Check Dialog
function EntryCheckDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    check_result: "",
    notes: ""
  });

  const handleSubmit = () => {
    if (!formData.check_result.trim()) {
      alert("请填写检查结果");
      return;
    }
    onSubmit(formData);
    setFormData({ check_result: "", notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>阶段入口检查</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                检查结果 <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.check_result}
                onChange={(e) =>
                setFormData({ ...formData, check_result: e.target.value })
                }
                placeholder="请输入检查结果"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4} />

            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                检查说明
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="请输入检查说明（可选）"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3} />

            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

// Exit Check Dialog
function ExitCheckDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    check_result: "",
    notes: ""
  });

  const handleSubmit = () => {
    if (!formData.check_result.trim()) {
      alert("请填写检查结果");
      return;
    }
    onSubmit(formData);
    setFormData({ check_result: "", notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>阶段出口检查</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                检查结果 <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.check_result}
                onChange={(e) =>
                setFormData({ ...formData, check_result: e.target.value })
                }
                placeholder="请输入检查结果"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4} />

            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                检查说明
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="请输入检查说明（可选）"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3} />

            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

// Review Dialog
function ReviewDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    review_result: "PASSED",
    review_notes: ""
  });

  const handleSubmit = () => {
    onSubmit(formData);
    setFormData({ review_result: "PASSED", review_notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>阶段评审</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                评审结果 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.review_result}
                onChange={(e) =>
                setFormData({ ...formData, review_result: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary">

                <option value="PASSED">通过</option>
                <option value="CONDITIONAL">有条件通过</option>
                <option value="FAILED">未通过</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                评审记录
              </label>
              <textarea
                value={formData.review_notes}
                onChange={(e) =>
                setFormData({ ...formData, review_notes: e.target.value })
                }
                placeholder="请输入评审记录"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4} />

            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

// Advance Dialog
function AdvanceDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    actual_start_date: "",
    notes: ""
  });

  const handleSubmit = () => {
    onSubmit(formData);
    setFormData({ actual_start_date: "", notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>推进阶段</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                实际开始日期
              </label>
              <Input
                type="date"
                value={formData.actual_start_date}
                onChange={(e) =>
                setFormData({
                  ...formData,
                  actual_start_date: e.target.value
                })
                } />

            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                推进说明
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="请输入推进说明（可选）"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3} />

            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

// Phase Detail Dialog
function PhaseDetailDialog({ open, onOpenChange, phase }) {
  if (!phase) {return null;}

  const statusBadge = getStatusBadge(phase.status);
  const reviewBadge = phase.review_result ?
  getReviewResultBadge(phase.review_result) :
  null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>阶段详情 - {phase.phase_name}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-slate-400">阶段编码</span>
                <p className="text-white font-medium">{phase.phase_code}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">阶段顺序</span>
                <p className="text-white font-medium">{phase.phase_order}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">状态</span>
                <p className="mt-1">
                  <Badge variant={statusBadge.variant}>
                    {statusBadge.label}
                  </Badge>
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-400">进度</span>
                <p className="text-white font-medium">{phase.progress || 0}%</p>
              </div>
            </div>

            {/* Timeline */}
            <div>
              <h4 className="text-sm font-medium text-white mb-3">时间计划</h4>
              <div className="grid grid-cols-2 gap-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <div>
                  <span className="text-xs text-slate-400">计划开始</span>
                  <p className="text-white">
                    {phase.plan_start_date ?
                    formatDate(phase.plan_start_date) :
                    "未设置"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">计划结束</span>
                  <p className="text-white">
                    {phase.plan_end_date ?
                    formatDate(phase.plan_end_date) :
                    "未设置"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">实际开始</span>
                  <p className="text-white">
                    {phase.actual_start_date ?
                    formatDate(phase.actual_start_date) :
                    "未开始"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">实际结束</span>
                  <p className="text-white">
                    {phase.actual_end_date ?
                    formatDate(phase.actual_end_date) :
                    "未结束"}
                  </p>
                </div>
              </div>
            </div>

            {/* Criteria */}
            {(phase.entry_criteria || phase.exit_criteria) &&
            <div>
                <h4 className="text-sm font-medium text-white mb-3">
                  门控条件
                </h4>
                <div className="space-y-3">
                  {phase.entry_criteria &&
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">入口条件</span>
                      <p className="text-white mt-1">{phase.entry_criteria}</p>
                </div>
                }
                  {phase.exit_criteria &&
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">出口条件</span>
                      <p className="text-white mt-1">{phase.exit_criteria}</p>
                </div>
                }
                </div>
            </div>
            }

            {/* Check Results */}
            {(phase.entry_check_result || phase.exit_check_result) &&
            <div>
                <h4 className="text-sm font-medium text-white mb-3">
                  检查结果
                </h4>
                <div className="space-y-3">
                  {phase.entry_check_result &&
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">
                        入口检查结果
                      </span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {phase.entry_check_result}
                      </p>
                </div>
                }
                  {phase.exit_check_result &&
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">
                        出口检查结果
                      </span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {phase.exit_check_result}
                      </p>
                </div>
                }
                </div>
            </div>
            }

            {/* Review */}
            {phase.review_required &&
            <div>
                <h4 className="text-sm font-medium text-white mb-3">
                  评审信息
                </h4>
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
                  {reviewBadge &&
                <div>
                      <span className="text-xs text-slate-400">评审结果</span>
                      <p className="mt-1">
                        <Badge variant={reviewBadge.variant}>
                          {reviewBadge.label}
                        </Badge>
                      </p>
                </div>
                }
                  {phase.review_date &&
                <div>
                      <span className="text-xs text-slate-400">评审日期</span>
                      <p className="text-white">
                        {formatDate(phase.review_date)}
                      </p>
                </div>
                }
                  {phase.review_notes &&
                <div>
                      <span className="text-xs text-slate-400">评审记录</span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {phase.review_notes}
                      </p>
                </div>
                }
                </div>
            </div>
            }
          </div>
        </DialogBody>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}