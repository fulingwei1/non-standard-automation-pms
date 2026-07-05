/**
 * 项目复盘报告详情页面 - 重构版
 * 展示复盘报告的完整信息，包括经验教训和最佳实践
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { projectReviewApi } from "../../services/api";
import { PageHeader } from "../../components/layout/PageHeader";
import DeleteConfirmDialog from "../../components/common/DeleteConfirmDialog";
import {
  Card,
  CardContent,
  Button,
  SkeletonCard,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../../components/ui";
import {
  ArrowLeft,
  Edit,
  Trash2,
  CheckCircle2,
  Archive,
} from "lucide-react";

// 导入重构的组件
import {
  ProjectReviewOverview,
  getReviewStatus,
  getReviewType,
} from "../../components/project-review";

import { confirmAction } from "@/lib/confirmAction";

import { staggerContainer, INITIAL_LESSON_FORM, INITIAL_PRACTICE_FORM } from "./constants";
import LessonDialog from "./LessonDialog";
import PracticeDialog from "./PracticeDialog";
import LessonsTab from "./LessonsTab";
import PracticesTab from "./PracticesTab";

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
  const [lessonForm, setLessonForm] = useState({ ...INITIAL_LESSON_FORM });
  const [practiceForm, setPracticeForm] = useState({ ...INITIAL_PRACTICE_FORM });

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
      setLessons(response.data?.results || response.data?.items || response.data || []);
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
      setBestPractices(response.data?.results || response.data?.items || response.data || []);
    } catch (err) {
      console.error("Failed to fetch best practices:", err);
    }
  };

  // 发布评审
  const handlePublish = async () => {
    if (!await confirmAction("确定要发布这个评审报告吗？")) {return;}

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
    if (!await confirmAction("确定要归档这个评审报告吗？")) {return;}

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
        await projectReviewApi.lessons.update(lessonDialog.lesson.id, lessonForm);
      } else {
        await projectReviewApi.lessons.create({
          ...lessonForm,
          review: reviewId
        });
      }

      setLessonDialog({ open: false, lesson: null });
      setLessonForm({ ...INITIAL_LESSON_FORM });
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
        await projectReviewApi.practices.update(
          practiceDialog.practice.id,
          practiceForm
        );
      } else {
        await projectReviewApi.practices.create({
          ...practiceForm,
          review: reviewId
        });
      }

      setPracticeDialog({ open: false, practice: null });
      setPracticeForm({ ...INITIAL_PRACTICE_FORM });
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
          <LessonsTab
            lessons={lessons}
            review={review}
            setLessonDialog={setLessonDialog}
            setLessonForm={setLessonForm}
            setDeleteLessonDialog={setDeleteLessonDialog}
          />
        </TabsContent>

        {/* 最佳实践标签页 */}
        <TabsContent value="practices" className="space-y-4">
          <PracticesTab
            bestPractices={bestPractices}
            review={review}
            setPracticeDialog={setPracticeDialog}
            setPracticeForm={setPracticeForm}
            setDeletePracticeDialog={setDeletePracticeDialog}
          />
        </TabsContent>
      </Tabs>

      {/* 删除评审确认对话框 */}
      <DeleteConfirmDialog
        open={deleteDialog}
        onOpenChange={setDeleteDialog}
        title="确认删除"
        description="确定要删除这个复盘报告吗？此操作不可撤销。"
        confirmText={saving ? "删除中..." : "确认删除"}
        confirmDisabled={saving}
        onConfirm={handleDelete}
      />

      {/* 经验教训编辑对话框 */}
      <LessonDialog
        lessonDialog={lessonDialog}
        setLessonDialog={setLessonDialog}
        lessonForm={lessonForm}
        setLessonForm={setLessonForm}
        saving={saving}
        onSave={handleSaveLesson}
      />

      {/* 最佳实践编辑对话框 */}
      <PracticeDialog
        practiceDialog={practiceDialog}
        setPracticeDialog={setPracticeDialog}
        practiceForm={practiceForm}
        setPracticeForm={setPracticeForm}
        saving={saving}
        onSave={handleSavePractice}
      />

      {/* 删除经验教训确认对话框 */}
      <DeleteConfirmDialog
        open={deleteLessonDialog.open}
        onOpenChange={(open) =>
          setDeleteLessonDialog({ open, lessonId: open ? deleteLessonDialog.lessonId : null })
        }
        title="确认删除"
        description="确定要删除这个经验教训吗？"
        confirmText={saving ? "删除中..." : "确认删除"}
        confirmDisabled={saving}
        onConfirm={handleDeleteLesson}
      />

      {/* 删除最佳实践确认对话框 */}
      <DeleteConfirmDialog
        open={deletePracticeDialog.open}
        onOpenChange={(open) =>
          setDeletePracticeDialog({ open, practiceId: open ? deletePracticeDialog.practiceId : null })
        }
        title="确认删除"
        description="确定要删除这个最佳实践吗？"
        confirmText={saving ? "删除中..." : "确认删除"}
        confirmDisabled={saving}
        onConfirm={handleDeletePractice}
      />
    </motion.div>);

}
