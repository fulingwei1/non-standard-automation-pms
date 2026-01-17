/**
 * 项目复盘报告详情页面 - 重构版
 * 展示复盘报告的完整信息，包括经验教训和最佳实践
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { projectReviewApi, projectApi as _projectApi } from "../services/api";
import { formatDate as _formatDate, formatCurrency as _formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Progress,
  SkeletonCard,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui";
import { Input, InputWithLabel, Textarea } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Checkbox } from "../components/ui/checkbox";
import {
  ArrowLeft,
  Edit,
  Trash2,
  CheckCircle2,
  Archive,
  Plus,
  FileText,
  TrendingUp,
  TrendingDown,
  Clock,
  DollarSign,
  Target,
  AlertCircle,
  Lightbulb,
  BookOpen,
  Users,
  Calendar } from
"lucide-react";

// 导入重构的组件
import {
  ProjectReviewOverview,
  REVIEW_STATUS,
  REVIEW_TYPES,
  LESSON_TYPES,
  getReviewStatus,
  getReviewType,
  getLessonType } from
"../components/project-review";

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

export default function ProjectReviewDetail() {
  const { reviewId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [_error, setError] = useState("");
  const [review, setReview] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [bestPractices, setBestPractices] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");

  // Dialog states
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [lessonDialog, setLessonDialog] = useState({
    open: false,
    lesson: null
  });
  const [practiceDialog, setPracticeDialog] = useState({
    open: false,
    practice: null
  });

  // Form states
  const [lessonForm, setLessonForm] = useState({
    title: "",
    description: "",
    category: "",
    impact: "",
    actions: "",
    tags: []
  });
  const [practiceForm, setPracticeForm] = useState({
    title: "",
    description: "",
    category: "",
    applicability: "",
    benefits: "",
    implementation: "",
    tags: []
  });

  const [deleteLessonDialog, setDeleteLessonDialog] = useState({
    open: false,
    lessonId: null
  });
  const [deletePracticeDialog, setDeletePracticeDialog] = useState({
    open: false,
    practiceId: null
  });

  // 加载评审详情
  const fetchReviewDetail = async () => {
    try {
      setLoading(true);
      const response = await projectReviewApi.get(reviewId);
      setReview(response.data);
    } catch (err) {
      console.error("Failed to fetch review:", err);
      setError("加载评审详情失败");
    } finally {
      setLoading(false);
    }
  };

  // 加载经验教训
  const fetchLessons = async () => {
    try {
      const response = await projectReviewApi.lessons.list({
        review: reviewId
      });
      setLessons(response.data?.results || response.data || []);
    } catch (err) {
      console.error("Failed to fetch lessons:", err);
    }
  };

  // 加载最佳实践
  const fetchBestPractices = async () => {
    try {
      const response = await projectReviewApi.practices.list({
        review: reviewId
      });
      setBestPractices(response.data?.results || response.data || []);
    } catch (err) {
      console.error("Failed to fetch best practices:", err);
    }
  };

  // 发布评审
  const handlePublish = async () => {
    if (!confirm("确定要发布这个评审报告吗？")) return;

    try {
      setSaving(true);
      await projectReviewApi.update(reviewId, { status: "PUBLISHED" });
      setReview({ ...review, status: "PUBLISHED" });
    } catch (err) {
      console.error("Failed to publish review:", err);
      alert("发布失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // 归档评审
  const handleArchive = async () => {
    if (!confirm("确定要归档这个评审报告吗？")) return;

    try {
      setSaving(true);
      await projectReviewApi.update(reviewId, { status: "ARCHIVED" });
      setReview({ ...review, status: "ARCHIVED" });
    } catch (err) {
      console.error("Failed to archive review:", err);
      alert("归档失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // 删除评审
  const handleDelete = async () => {
    try {
      setSaving(true);
      await projectReviewApi.delete(reviewId);
      navigate("/projects/reviews");
    } catch (err) {
      console.error("Failed to delete review:", err);
      alert("删除失败: " + (err.response?.data?.detail || err.message));
      setDeleteDialog(false);
    } finally {
      setSaving(false);
    }
  };

  // 保存经验教训
  const handleSaveLesson = async () => {
    try {
      setSaving(true);

      if (lessonDialog.lesson) {
        // Update existing lesson
        await projectReviewApi.lessons.update(lessonDialog.lesson.id, lessonForm);
      } else {
        // Create new lesson
        await projectReviewApi.lessons.create({
          ...lessonForm,
          review: reviewId
        });
      }

      setLessonDialog({ open: false, lesson: null });
      setLessonForm({
        title: "",
        description: "",
        category: "",
        impact: "",
        actions: "",
        tags: []
      });
      fetchLessons();
    } catch (err) {
      console.error("Failed to save lesson:", err);
      alert("保存失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // 保存最佳实践
  const handleSavePractice = async () => {
    try {
      setSaving(true);

      if (practiceDialog.practice) {
        // Update existing practice
        await projectReviewApi.practices.update(
          practiceDialog.practice.id,
          practiceForm
        );
      } else {
        // Create new practice
        await projectReviewApi.practices.create({
          ...practiceForm,
          review: reviewId
        });
      }

      setPracticeDialog({ open: false, practice: null });
      setPracticeForm({
        title: "",
        description: "",
        category: "",
        applicability: "",
        benefits: "",
        implementation: "",
        tags: []
      });
      fetchBestPractices();
    } catch (err) {
      console.error("Failed to save practice:", err);
      alert("保存失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // 删除经验教训
  const handleDeleteLesson = async () => {
    try {
      setSaving(true);
      await projectReviewApi.lessons.delete(deleteLessonDialog.lessonId);
      setDeleteLessonDialog({ open: false, lessonId: null });
      fetchLessons();
    } catch (err) {
      console.error("Failed to delete lesson:", err);
      alert("删除失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // 删除最佳实践
  const handleDeletePractice = async () => {
    try {
      setSaving(true);
      await projectReviewApi.practices.delete(deletePracticeDialog.practiceId);
      setDeletePracticeDialog({ open: false, practiceId: null });
      fetchBestPractices();
    } catch (err) {
      console.error("Failed to delete practice:", err);
      alert("删除失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // 初始化
  useEffect(() => {
    if (reviewId) {
      fetchReviewDetail();
      fetchLessons();
      fetchBestPractices();
    }
  }, [reviewId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>);

  }

  if (!review) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-slate-400">复盘报告不存在</p>
          <Button
            onClick={() => navigate("/projects/reviews")}
            className="mt-4">

            <ArrowLeft className="h-4 w-4 mr-2" />
            返回列表
          </Button>
        </CardContent>
      </Card>);

  }

  const _statusInfo = getReviewStatus(review.status);
  const typeInfo = getReviewType(review.review_type);

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <PageHeader
        title={`项目复盘报告 - ${review.project_name || review.project_code}`}
        description={`复盘编号: ${review.review_no} | ${typeInfo.label}`}
        action={
        <div className="flex items-center gap-2">
            <Button
            variant="outline"
            onClick={() => navigate("/projects/reviews")}>

              <ArrowLeft className="h-4 w-4 mr-2" />
              返回列表
            </Button>
            {review.status === "DRAFT" &&
          <>
                <Button
              variant="outline"
              onClick={() => navigate(`/projects/reviews/${reviewId}/edit`)}>

                  <Edit className="h-4 w-4 mr-2" />
                  编辑
                </Button>
                <Button onClick={handlePublish} disabled={saving}>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  发布
                </Button>
                <Button
              variant="destructive"
              onClick={() => setDeleteDialog(true)}
              disabled={saving}>

                  <Trash2 className="h-4 w-4 mr-2" />
                  删除
                </Button>
              </>
          }
            {review.status === "PUBLISHED" &&
          <Button variant="outline" onClick={handleArchive} disabled={saving}>
                <Archive className="h-4 w-4 mr-2" />
                归档
              </Button>
          }
          </div>
        } />


      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6">

        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="lessons">经验教训 ({lessons.length})</TabsTrigger>
          <TabsTrigger value="practices">
            最佳实践 ({bestPractices.length})
          </TabsTrigger>
        </TabsList>

        {/* 概览标签页 */}
        <TabsContent value="overview" className="space-y-6">
          <ProjectReviewOverview
            review={review}
            editable={review.status === "DRAFT"}
            onEdit={() => navigate(`/projects/reviews/${reviewId}/edit`)}
            onPublish={handlePublish}
            onArchive={handleArchive}
            onDelete={() => setDeleteDialog(true)} />

        </TabsContent>

        {/* 经验教训标签页 */}
        <TabsContent value="lessons" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">经验教训</h3>
            <Button
              onClick={() =>
              setLessonDialog({ open: true, lesson: null })
              }
              disabled={review.status !== "DRAFT"}>

              <Plus className="h-4 w-4 mr-2" />
              添加经验教训
            </Button>
          </div>

          {lessons.length === 0 ?
          <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="p-12 text-center">
                <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-400">暂无经验教训</p>
                {review.status === "DRAFT" &&
              <Button
                onClick={() =>
                setLessonDialog({ open: true, lesson: null })
                }
                className="mt-4">

                    <Plus className="h-4 w-4 mr-2" />
                    添加第一条经验教训
                  </Button>
              }
              </CardContent>
            </Card> :

          <div className="grid gap-4">
              {lessons.map((lesson) => {
              const lessonType = getLessonType(lesson.type);
              const Icon = lessonType.icon;

              return (
                <motion.div
                  key={lesson.id}
                  variants={staggerChild}
                  className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">

                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <div className={`p-2 rounded-lg ${lessonType.bgColor}`}>
                            <Icon className={`w-4 h-4 ${lessonType.textColor}`} />
                          </div>
                          <div>
                            <h4 className="text-white font-medium">
                              {lesson.title}
                            </h4>
                            <Badge
                            variant="outline"
                            className={cn(
                              "border",
                              lessonType.borderColor,
                              lessonType.textColor
                            )}>

                              {lessonType.label}
                            </Badge>
                          </div>
                        </div>
                        <p className="text-slate-300 mb-3">
                          {lesson.description}
                        </p>
                        {lesson.actions &&
                      <div>
                            <h5 className="text-sm font-medium text-white mb-2">
                              改进措施:
                            </h5>
                            <p className="text-slate-400 text-sm">
                              {lesson.actions}
                            </p>
                          </div>
                      }
                      </div>
                      {review.status === "DRAFT" &&
                    <div className="flex items-center gap-2 ml-4">
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setLessonDialog({ open: true, lesson });
                          setLessonForm({
                            title: lesson.title,
                            description: lesson.description,
                            category: lesson.category,
                            impact: lesson.impact,
                            actions: lesson.actions,
                            tags: lesson.tags || []
                          });
                        }}>

                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                        setDeleteLessonDialog({
                          open: true,
                          lessonId: lesson.id
                        })
                        }>

                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                    }
                    </div>
                  </motion.div>);

            })}
            </div>
          }
        </TabsContent>

        {/* 最佳实践标签页 */}
        <TabsContent value="practices" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">最佳实践</h3>
            <Button
              onClick={() =>
              setPracticeDialog({ open: true, practice: null })
              }
              disabled={review.status !== "DRAFT"}>

              <Plus className="h-4 w-4 mr-2" />
              添加最佳实践
            </Button>
          </div>

          {bestPractices.length === 0 ?
          <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="p-12 text-center">
                <BookOpen className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-400">暂无最佳实践</p>
                {review.status === "DRAFT" &&
              <Button
                onClick={() =>
                setPracticeDialog({ open: true, practice: null })
                }
                className="mt-4">

                    <Plus className="h-4 w-4 mr-2" />
                    添加第一条最佳实践
                  </Button>
              }
              </CardContent>
            </Card> :

          <div className="grid gap-4">
              {bestPractices.map((practice) =>
            <motion.div
              key={practice.id}
              variants={staggerChild}
              className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">

                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 rounded-lg bg-green-500/20">
                          <BookOpen className="w-4 h-4 text-green-400" />
                        </div>
                        <div>
                          <h4 className="text-white font-medium">
                            {practice.title}
                          </h4>
                          <Badge variant="outline" className="border-green-500/30 text-green-400">
                            {practice.category || "通用实践"}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-slate-300 mb-3">
                        {practice.description}
                      </p>
                      {practice.applicability &&
                  <div className="mb-3">
                          <h5 className="text-sm font-medium text-white mb-1">
                            适用范围:
                          </h5>
                          <p className="text-slate-400 text-sm">
                            {practice.applicability}
                          </p>
                        </div>
                  }
                      {practice.benefits &&
                  <div className="mb-3">
                          <h5 className="text-sm font-medium text-white mb-1">
                            预期收益:
                          </h5>
                          <p className="text-slate-400 text-sm">
                            {practice.benefits}
                          </p>
                        </div>
                  }
                      {practice.implementation &&
                  <div>
                          <h5 className="text-sm font-medium text-white mb-1">
                            实施要点:
                          </h5>
                          <p className="text-slate-400 text-sm">
                            {practice.implementation}
                          </p>
                        </div>
                  }
                    </div>
                    {review.status === "DRAFT" &&
                <div className="flex items-center gap-2 ml-4">
                        <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setPracticeDialog({ open: true, practice });
                      setPracticeForm({
                        title: practice.title,
                        description: practice.description,
                        category: practice.category,
                        applicability: practice.applicability,
                        benefits: practice.benefits,
                        implementation: practice.implementation,
                        tags: practice.tags || []
                      });
                    }}>

                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                    setDeletePracticeDialog({
                      open: true,
                      practiceId: practice.id
                    })
                    }>

                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                }
                  </div>
                </motion.div>
            )}
            </div>
          }
        </TabsContent>
      </Tabs>

      {/* 删除评审确认对话框 */}
      <Dialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-300">
              确定要删除这个复盘报告吗？此操作不可撤销。
            </p>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialog(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={saving}>

              {saving ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 经验教训编辑对话框 */}
      <Dialog
        open={lessonDialog.open}
        onOpenChange={(open) => setLessonDialog({ open, lesson: null })}>

        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {lessonDialog.lesson ? "编辑经验教训" : "添加经验教训"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <Label htmlFor="lessonTitle">标题</Label>
              <Input
                id="lessonTitle"
                value={lessonForm.title}
                onChange={(e) =>
                setLessonForm({ ...lessonForm, title: e.target.value })
                }
                placeholder="请输入经验教训标题" />

            </div>
            <div>
              <Label htmlFor="lessonDescription">描述</Label>
              <Textarea
                id="lessonDescription"
                value={lessonForm.description}
                onChange={(e) =>
                setLessonForm({ ...lessonForm, description: e.target.value })
                }
                placeholder="请详细描述经验教训"
                rows={4} />

            </div>
            <div>
              <Label htmlFor="lessonCategory">类别</Label>
              <Input
                id="lessonCategory"
                value={lessonForm.category}
                onChange={(e) =>
                setLessonForm({ ...lessonForm, category: e.target.value })
                }
                placeholder="如：项目管理、技术实现、团队协作等" />

            </div>
            <div>
              <Label htmlFor="lessonImpact">影响</Label>
              <Input
                id="lessonImpact"
                value={lessonForm.impact}
                onChange={(e) =>
                setLessonForm({ ...lessonForm, impact: e.target.value })
                }
                placeholder="对项目的影响" />

            </div>
            <div>
              <Label htmlFor="lessonActions">改进措施</Label>
              <Textarea
                id="lessonActions"
                value={lessonForm.actions}
                onChange={(e) =>
                setLessonForm({ ...lessonForm, actions: e.target.value })
                }
                placeholder="具体的改进措施和行动计划"
                rows={3} />

            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setLessonDialog({ open: false, lesson: null })}>

              取消
            </Button>
            <Button onClick={handleSaveLesson} disabled={saving}>
              {saving ? "保存中..." : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 最佳实践编辑对话框 */}
      <Dialog
        open={practiceDialog.open}
        onOpenChange={(open) => setPracticeDialog({ open, practice: null })}>

        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {practiceDialog.practice ? "编辑最佳实践" : "添加最佳实践"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <Label htmlFor="practiceTitle">标题</Label>
              <Input
                id="practiceTitle"
                value={practiceForm.title}
                onChange={(e) =>
                setPracticeForm({ ...practiceForm, title: e.target.value })
                }
                placeholder="请输入最佳实践标题" />

            </div>
            <div>
              <Label htmlFor="practiceDescription">描述</Label>
              <Textarea
                id="practiceDescription"
                value={practiceForm.description}
                onChange={(e) =>
                setPracticeForm({ ...practiceForm, description: e.target.value })
                }
                placeholder="请详细描述最佳实践"
                rows={4} />

            </div>
            <div>
              <Label htmlFor="practiceCategory">类别</Label>
              <Input
                id="practiceCategory"
                value={practiceForm.category}
                onChange={(e) =>
                setPracticeForm({ ...practiceForm, category: e.target.value })
                }
                placeholder="如：项目管理、技术实践、团队协作等" />

            </div>
            <div>
              <Label htmlFor="practiceApplicability">适用范围</Label>
              <Textarea
                id="practiceApplicability"
                value={practiceForm.applicability}
                onChange={(e) =>
                setPracticeForm({
                  ...practiceForm,
                  applicability: e.target.value
                })
                }
                placeholder="这个实践适用的项目类型或场景"
                rows={2} />

            </div>
            <div>
              <Label htmlFor="practiceBenefits">预期收益</Label>
              <Textarea
                id="practiceBenefits"
                value={practiceForm.benefits}
                onChange={(e) =>
                setPracticeForm({ ...practiceForm, benefits: e.target.value })
                }
                placeholder="实施这个实践预期带来的收益"
                rows={2} />

            </div>
            <div>
              <Label htmlFor="practiceImplementation">实施要点</Label>
              <Textarea
                id="practiceImplementation"
                value={practiceForm.implementation}
                onChange={(e) =>
                setPracticeForm({
                  ...practiceForm,
                  implementation: e.target.value
                })
                }
                placeholder="实施这个实践的关键步骤和注意事项"
                rows={3} />

            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setPracticeDialog({ open: false, practice: null })}>

              取消
            </Button>
            <Button onClick={handleSavePractice} disabled={saving}>
              {saving ? "保存中..." : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除经验教训确认对话框 */}
      <Dialog
        open={deleteLessonDialog.open}
        onOpenChange={(open) =>
        setDeleteLessonDialog({ open, lessonId: null })
        }>

        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-300">确定要删除这个经验教训吗？</p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() =>
              setDeleteLessonDialog({ open: false, lessonId: null })
              }>

              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteLesson}
              disabled={saving}>

              {saving ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除最佳实践确认对话框 */}
      <Dialog
        open={deletePracticeDialog.open}
        onOpenChange={(open) =>
        setDeletePracticeDialog({ open, practiceId: null })
        }>

        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-300">确定要删除这个最佳实践吗？</p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() =>
              setDeletePracticeDialog({ open: false, practiceId: null })
              }>

              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeletePractice}
              disabled={saving}>

              {saving ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}