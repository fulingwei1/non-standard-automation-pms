import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { pmoApi, projectApi } from "../services/api";
import { formatDate, formatCurrency } from "../lib/utils";
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
  FileText,
  ArrowRight,
  Eye,
  Edit,
  Award,
  DollarSign,
  Clock,
  Target,
  TrendingUp,
  TrendingDown } from
"lucide-react";

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  }
};

const _staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const getStatusBadge = (status) => {
  const badges = {
    DRAFT: { label: "草稿", variant: "secondary" },
    SUBMITTED: { label: "已提交", variant: "info" },
    REVIEWED: { label: "已评审", variant: "success" }
  };
  return badges[status] || badges.DRAFT;
};

export default function ProjectClosureManagement() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [closure, setClosure] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState(
    projectId ? parseInt(projectId) : null
  );
  const [projectSearch, setProjectSearch] = useState("");
  const [projectList, setProjectList] = useState([]);
  const [showProjectSelect, setShowProjectSelect] = useState(!projectId);

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [reviewDialog, setReviewDialog] = useState({
    open: false,
    closureId: null
  });
  const [lessonsDialog, setLessonsDialog] = useState({
    open: false,
    closureId: null
  });
  const [detailDialog, setDetailDialog] = useState({
    open: false,
    closure: null
  });

  useEffect(() => {
    if (selectedProjectId) {
      fetchProjectData();
      fetchClosure();
    } else {
      fetchProjectList();
    }
  }, [selectedProjectId]);

  const fetchProjectData = async () => {
    if (!selectedProjectId) return;
    try {
      const res = await projectApi.get(selectedProjectId);
      const data = res.data || res;
      setProject(data);
    } catch (err) {
      console.error("Failed to fetch project:", err);
    }
  };

  const fetchClosure = async () => {
    if (!selectedProjectId) return;
    try {
      setLoading(true);
      const res = await pmoApi.closures.get(selectedProjectId);
      const data = res.data || res;
      setClosure(data);
    } catch (err) {
      if (err.response?.status === 404) {
        setClosure(null);
      } else {
        console.error("Failed to fetch closure:", err);
      }
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
      setProjectList(data.items || data || []);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setProjectList([]);
    }
  };

  const handleCreate = async (formData) => {
    try {
      await pmoApi.closures.create(selectedProjectId, formData);
      setCreateDialogOpen(false);
      fetchClosure();
    } catch (err) {
      console.error("Failed to create closure:", err);
      alert("创建失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleReview = async (closureId, data) => {
    try {
      await pmoApi.closures.review(closureId, data);
      setReviewDialog({ open: false, closureId: null });
      fetchClosure();
    } catch (err) {
      console.error("Failed to review closure:", err);
      alert("评审失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleLessons = async (closureId, data) => {
    try {
      await pmoApi.closures.updateLessons(closureId, data);
      setLessonsDialog({ open: false, closureId: null });
      fetchClosure();
    } catch (err) {
      console.error("Failed to update lessons:", err);
      alert("更新失败: " + (err.response?.data?.detail || err.message));
    }
  };

  if (showProjectSelect) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}>

        <PageHeader title="项目结项管理" description="选择项目以进行结项管理" />

        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-6">
            <div className="mb-4">
              <Input
                placeholder="搜索项目名称或编码..."
                value={projectSearch}
                onChange={(e) => {
                  setProjectSearch(e.target.value);
                  fetchProjectList();
                }}
                className="w-full"
                icon={Search} />

            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {projectList.map((proj) =>
              <div
                key={proj.id}
                onClick={() => {
                  setSelectedProjectId(proj.id);
                  setShowProjectSelect(false);
                  navigate(`/pmo/closure/${proj.id}`);
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
        title="项目结项管理"
        description={
        project ? `${project.project_name} - 项目结项` : "项目结项"
        }
        action={
        <div className="flex items-center gap-2">
            <Button
            variant="outline"
            onClick={() => {
              setShowProjectSelect(true);
              navigate("/pmo/closure");
            }}>

              <ArrowLeft className="h-4 w-4 mr-2" />
              选择项目
            </Button>
            {!closure &&
          <Button
            onClick={() => setCreateDialogOpen(true)}
            className="gap-2">

                <FileText className="h-4 w-4" />
                创建结项申请
              </Button>
          }
          </div>
        } />


      {loading ?
      <div className="grid grid-cols-1 gap-4">
          <SkeletonCard />
        </div> :
      closure ?
      <div className="space-y-6">
          {/* Status Card */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/10 ring-1 ring-emerald-500/20">
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">结项状态</h3>
                    <p className="text-sm text-slate-400">
                      {getStatusBadge(closure.status).label}
                    </p>
                  </div>
                </div>
                <Badge variant={getStatusBadge(closure.status).variant}>
                  {getStatusBadge(closure.status).label}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Performance Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Cost Variance */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">成本偏差</span>
                  {closure.cost_variance !== null &&
                closure.cost_variance !== undefined &&
                <div
                  className={cn(
                    "flex items-center gap-1",
                    closure.cost_variance >= 0 ?
                    "text-red-400" :
                    "text-emerald-400"
                  )}>

                        {closure.cost_variance >= 0 ?
                  <TrendingUp className="h-4 w-4" /> :

                  <TrendingDown className="h-4 w-4" />
                  }
                        <span className="text-sm font-medium">
                          {closure.cost_variance >= 0 ? "+" : ""}
                          {formatCurrency(closure.cost_variance)}
                        </span>
                      </div>
                }
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">预算</span>
                    <span className="text-white">
                      {closure.final_budget ?
                    formatCurrency(closure.final_budget) :
                    "未设置"}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">实际</span>
                    <span className="text-white">
                      {closure.final_cost ?
                    formatCurrency(closure.final_cost) :
                    "未设置"}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Hours Variance */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">工时偏差</span>
                  {closure.hours_variance !== null &&
                closure.hours_variance !== undefined &&
                <div
                  className={cn(
                    "flex items-center gap-1",
                    closure.hours_variance >= 0 ?
                    "text-red-400" :
                    "text-emerald-400"
                  )}>

                        {closure.hours_variance >= 0 ?
                  <TrendingUp className="h-4 w-4" /> :

                  <TrendingDown className="h-4 w-4" />
                  }
                        <span className="text-sm font-medium">
                          {closure.hours_variance >= 0 ? "+" : ""}
                          {closure.hours_variance} 小时
                        </span>
                      </div>
                }
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">计划</span>
                    <span className="text-white">
                      {closure.final_planned_hours || 0} 小时
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">实际</span>
                    <span className="text-white">
                      {closure.final_actual_hours || 0} 小时
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Schedule Variance */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">进度偏差</span>
                  {closure.schedule_variance !== null &&
                closure.schedule_variance !== undefined &&
                <div
                  className={cn(
                    "flex items-center gap-1",
                    closure.schedule_variance >= 0 ?
                    "text-red-400" :
                    "text-emerald-400"
                  )}>

                        {closure.schedule_variance >= 0 ?
                  <TrendingUp className="h-4 w-4" /> :

                  <TrendingDown className="h-4 w-4" />
                  }
                        <span className="text-sm font-medium">
                          {closure.schedule_variance >= 0 ? "+" : ""}
                          {closure.schedule_variance} 天
                        </span>
                      </div>
                }
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">计划工期</span>
                    <span className="text-white">
                      {closure.plan_duration || 0} 天
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">实际工期</span>
                    <span className="text-white">
                      {closure.actual_duration || 0} 天
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Acceptance Info */}
          <Card>
            <CardContent className="p-5">
              <h3 className="text-lg font-semibold text-white mb-4">
                验收信息
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-slate-400">验收日期</span>
                  <p className="text-white mt-1">
                    {closure.acceptance_date ?
                  formatDate(closure.acceptance_date) :
                  "未设置"}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-slate-400">验收结果</span>
                  <p className="text-white mt-1">
                    {closure.acceptance_result || "未设置"}
                  </p>
                </div>
                {closure.acceptance_notes &&
              <div className="col-span-2">
                    <span className="text-sm text-slate-400">验收说明</span>
                    <p className="text-white mt-1 whitespace-pre-wrap">
                      {closure.acceptance_notes}
                    </p>
                  </div>
              }
              </div>
            </CardContent>
          </Card>

          {/* Project Summary */}
          {closure.project_summary &&
        <Card>
              <CardContent className="p-5">
                <h3 className="text-lg font-semibold text-white mb-4">
                  项目总结
                </h3>
                <p className="text-white whitespace-pre-wrap">
                  {closure.project_summary}
                </p>
              </CardContent>
            </Card>
        }

          {/* Achievement */}
          {closure.achievement &&
        <Card>
              <CardContent className="p-5">
                <h3 className="text-lg font-semibold text-white mb-4">
                  项目成果
                </h3>
                <p className="text-white whitespace-pre-wrap">
                  {closure.achievement}
                </p>
              </CardContent>
            </Card>
        }

          {/* Lessons Learned */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">经验教训</h3>
                {closure.status !== "REVIEWED" &&
              <Button
                size="sm"
                variant="outline"
                onClick={() =>
                setLessonsDialog({ open: true, closureId: closure.id })
                }>

                    <Edit className="h-4 w-4 mr-2" />
                    编辑
                  </Button>
              }
              </div>
              {closure.lessons_learned ?
            <p className="text-white whitespace-pre-wrap">
                  {closure.lessons_learned}
                </p> :

            <p className="text-slate-500">暂无经验教训记录</p>
            }
              {closure.improvement_suggestions &&
            <div className="mt-4">
                  <h4 className="text-sm font-medium text-white mb-2">
                    改进建议
                  </h4>
                  <p className="text-white whitespace-pre-wrap">
                    {closure.improvement_suggestions}
                  </p>
                </div>
            }
            </CardContent>
          </Card>

          {/* Quality & Satisfaction */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardContent className="p-5">
                <h3 className="text-lg font-semibold text-white mb-4">
                  质量评分
                </h3>
                {closure.quality_score !== null &&
              closure.quality_score !== undefined ?
              <div className="flex items-center gap-4">
                    <div className="text-4xl font-bold text-primary">
                      {closure.quality_score}
                    </div>
                    <div className="flex-1">
                      <Progress value={closure.quality_score} />
                    </div>
                  </div> :

              <p className="text-slate-500">未评分</p>
              }
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <h3 className="text-lg font-semibold text-white mb-4">
                  客户满意度
                </h3>
                {closure.customer_satisfaction !== null &&
              closure.customer_satisfaction !== undefined ?
              <div className="flex items-center gap-4">
                    <div className="text-4xl font-bold text-emerald-400">
                      {closure.customer_satisfaction}
                    </div>
                    <div className="flex-1">
                      <Progress value={closure.customer_satisfaction} />
                    </div>
                  </div> :

              <p className="text-slate-500">未评分</p>
              }
              </CardContent>
            </Card>
          </div>

          {/* Review Info */}
          {closure.status === "REVIEWED" &&
        <Card>
              <CardContent className="p-5">
                <h3 className="text-lg font-semibold text-white mb-4">
                  评审信息
                </h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-slate-400">评审结果</span>
                    <p className="text-white mt-1">{closure.review_result}</p>
                  </div>
                  {closure.review_notes &&
              <div>
                      <span className="text-sm text-slate-400">评审记录</span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {closure.review_notes}
                      </p>
                    </div>
              }
                </div>
              </CardContent>
            </Card>
        }

          {/* Actions */}
          {closure.status !== "REVIEWED" &&
        <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-2">
                  {closure.status === "DRAFT" &&
              <Button
                onClick={() =>
                setReviewDialog({ open: true, closureId: closure.id })
                }>

                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      提交评审
                    </Button>
              }
                  <Button
                variant="outline"
                onClick={() => setDetailDialog({ open: true, closure })}>

                    <Eye className="h-4 w-4 mr-2" />
                    查看详情
                  </Button>
                </div>
              </CardContent>
            </Card>
        }
        </div> :

      <Card>
          <CardContent className="p-12 text-center">
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 inline-block mx-auto">
                <FileText className="h-12 w-12 text-slate-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  该项目尚未创建结项申请
                </h3>
                <p className="text-slate-400 mb-4">
                  创建结项申请以记录项目完成情况和经验教训
                </p>
                <Button onClick={() => setCreateDialogOpen(true)}>
                  <FileText className="h-4 w-4 mr-2" />
                  创建结项申请
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      }

      {/* Create Dialog */}
      <CreateClosureDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreate} />


      {/* Review Dialog */}
      <ReviewClosureDialog
        open={reviewDialog.open}
        onOpenChange={(open) => setReviewDialog({ open, closureId: null })}
        onSubmit={(data) => handleReview(reviewDialog.closureId, data)} />


      {/* Lessons Dialog */}
      <LessonsClosureDialog
        open={lessonsDialog.open}
        onOpenChange={(open) => setLessonsDialog({ open, closureId: null })}
        onSubmit={(data) => handleLessons(lessonsDialog.closureId, data)}
        closure={closure} />


      {/* Detail Dialog */}
      <ClosureDetailDialog
        open={detailDialog.open}
        onOpenChange={(open) => setDetailDialog({ open, closure: null })}
        closure={detailDialog.closure} />

    </motion.div>);

}

// Create Closure Dialog
function CreateClosureDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    acceptance_date: "",
    acceptance_result: "",
    acceptance_notes: "",
    project_summary: "",
    achievement: "",
    lessons_learned: "",
    improvement_suggestions: "",
    quality_score: "",
    customer_satisfaction: ""
  });

  const handleSubmit = () => {
    onSubmit(formData);
    setFormData({
      acceptance_date: "",
      acceptance_result: "",
      acceptance_notes: "",
      project_summary: "",
      achievement: "",
      lessons_learned: "",
      improvement_suggestions: "",
      quality_score: "",
      customer_satisfaction: ""
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建结项申请</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Acceptance */}
            <div>
              <h4 className="text-sm font-medium text-white mb-3">验收信息</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white mb-2">
                    验收日期
                  </label>
                  <Input
                    type="date"
                    value={formData.acceptance_date}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      acceptance_date: e.target.value
                    })
                    } />

                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-2">
                    验收结果
                  </label>
                  <Input
                    value={formData.acceptance_result}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      acceptance_result: e.target.value
                    })
                    }
                    placeholder="如：通过、有条件通过等" />

                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-white mb-2">
                  验收说明
                </label>
                <textarea
                  value={formData.acceptance_notes}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    acceptance_notes: e.target.value
                  })
                  }
                  placeholder="请输入验收说明"
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows={3} />

              </div>
            </div>

            {/* Summary */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                项目总结
              </label>
              <textarea
                value={formData.project_summary}
                onChange={(e) =>
                setFormData({ ...formData, project_summary: e.target.value })
                }
                placeholder="请总结项目整体情况"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4} />

            </div>

            {/* Achievement */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                项目成果
              </label>
              <textarea
                value={formData.achievement}
                onChange={(e) =>
                setFormData({ ...formData, achievement: e.target.value })
                }
                placeholder="请描述项目取得的成果"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4} />

            </div>

            {/* Lessons */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                经验教训
              </label>
              <textarea
                value={formData.lessons_learned}
                onChange={(e) =>
                setFormData({ ...formData, lessons_learned: e.target.value })
                }
                placeholder="请总结项目经验教训"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4} />

            </div>

            {/* Improvement */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                改进建议
              </label>
              <textarea
                value={formData.improvement_suggestions}
                onChange={(e) =>
                setFormData({
                  ...formData,
                  improvement_suggestions: e.target.value
                })
                }
                placeholder="请提出改进建议"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3} />

            </div>

            {/* Scores */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  质量评分 (0-100)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.quality_score}
                  onChange={(e) =>
                  setFormData({ ...formData, quality_score: e.target.value })
                  }
                  placeholder="请输入质量评分" />

              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  客户满意度 (0-100)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.customer_satisfaction}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    customer_satisfaction: e.target.value
                  })
                  }
                  placeholder="请输入客户满意度" />

              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

// Review Closure Dialog
function ReviewClosureDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    review_result: "",
    review_notes: ""
  });

  const handleSubmit = () => {
    if (!formData.review_result.trim()) {
      alert("请填写评审结果");
      return;
    }
    onSubmit(formData);
    setFormData({ review_result: "", review_notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>结项评审</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                评审结果 <span className="text-red-400">*</span>
              </label>
              <Input
                value={formData.review_result}
                onChange={(e) =>
                setFormData({ ...formData, review_result: e.target.value })
                }
                placeholder="请输入评审结果" />

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

// Lessons Closure Dialog
function LessonsClosureDialog({ open, onOpenChange, onSubmit, closure }) {
  const [formData, setFormData] = useState({
    lessons_learned: closure?.lessons_learned || "",
    improvement_suggestions: closure?.improvement_suggestions || ""
  });

  useEffect(() => {
    if (closure) {
      setFormData({
        lessons_learned: closure.lessons_learned || "",
        improvement_suggestions: closure.improvement_suggestions || ""
      });
    }
  }, [closure]);

  const handleSubmit = () => {
    onSubmit(formData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>编辑经验教训</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                经验教训
              </label>
              <textarea
                value={formData.lessons_learned}
                onChange={(e) =>
                setFormData({ ...formData, lessons_learned: e.target.value })
                }
                placeholder="请总结项目经验教训"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={5} />

            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                改进建议
              </label>
              <textarea
                value={formData.improvement_suggestions}
                onChange={(e) =>
                setFormData({
                  ...formData,
                  improvement_suggestions: e.target.value
                })
                }
                placeholder="请提出改进建议"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4} />

            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

// Closure Detail Dialog
function ClosureDetailDialog({ open, onOpenChange, closure }) {
  if (!closure) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>结项详情</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-6">
            {/* All closure details in a comprehensive view */}
            <div className="text-sm text-slate-400">详细内容请查看主页面</div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}