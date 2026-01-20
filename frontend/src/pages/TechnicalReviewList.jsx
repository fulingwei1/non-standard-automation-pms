/**
 * 技术评审列表页面
 * 展示所有技术评审，支持筛选和搜索
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { technicalReviewApi, projectApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  Select,
  SkeletonCard,
} from "../components/ui";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui";
import {
  Search,
  Plus,
  Eye,
  Edit,
  Trash2,
  FileCheck,
  Calendar,
  Users,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
} from "lucide-react";

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
};

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const getStatusBadge = (status) => {
  const badges = {
    DRAFT: { label: "草稿", variant: "secondary", color: "text-slate-400" },
    PENDING: { label: "待评审", variant: "info", color: "text-blue-400" },
    IN_PROGRESS: {
      label: "评审中",
      variant: "warning",
      color: "text-amber-400",
    },
    COMPLETED: {
      label: "已完成",
      variant: "success",
      color: "text-emerald-400",
    },
    CANCELLED: { label: "已取消", variant: "danger", color: "text-red-400" },
  };
  return badges[status] || badges.DRAFT;
};

const getReviewTypeLabel = (type) => {
  const types = {
    PDR: "方案设计评审",
    DDR: "详细设计评审",
    PRR: "生产准备评审",
    FRR: "出厂评审",
    ARR: "现场评审",
  };
  return types[type] || type;
};

const getReviewTypeColor = (type) => {
  const colors = {
    PDR: "bg-blue-500/20 text-blue-400",
    DDR: "bg-purple-500/20 text-purple-400",
    PRR: "bg-amber-500/20 text-amber-400",
    FRR: "bg-green-500/20 text-green-400",
    ARR: "bg-orange-500/20 text-orange-400",
  };
  return colors[type] || "bg-slate-500/20 text-slate-400";
};

const getConclusionBadge = (conclusion) => {
  if (!conclusion) {return null;}
  const badges = {
    PASS: { label: "通过", color: "bg-emerald-500/20 text-emerald-400" },
    PASS_WITH_CONDITION: {
      label: "有条件通过",
      color: "bg-amber-500/20 text-amber-400",
    },
    REJECT: { label: "不通过", color: "bg-red-500/20 text-red-400" },
    ABORT: { label: "中止", color: "bg-slate-500/20 text-slate-400" },
  };
  return badges[conclusion] || null;
};

export default function TechnicalReviewList() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [reviews, setReviews] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 筛选条件
  const [searchKeyword, setSearchKeyword] = useState("");
  const [projectId, setProjectId] = useState(null);
  const [status, setStatus] = useState(null);
  const [reviewType, setReviewType] = useState(null);

  // 项目列表（用于筛选）
  const [projectList, setProjectList] = useState([]);

  // 对话框
  const [deleteDialog, setDeleteDialog] = useState({
    open: false,
    review: null,
  });

  useEffect(() => {
    fetchReviews();
    fetchProjectList();
  }, [page, projectId, status, reviewType]);

  const fetchProjectList = async () => {
    try {
      const response = await projectApi.list({ page: 1, page_size: 100 });
      const projects = response.data?.items || response.items || [];
      setProjectList(projects);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchKeyword) {params.keyword = searchKeyword;}
      if (projectId) {params.project_id = projectId;}
      if (status) {params.status = status;}
      if (reviewType) {params.review_type = reviewType;}

      const response = await technicalReviewApi.list(params);
      const data = response.data || response;
      setReviews(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error("Failed to fetch reviews:", error);
      // 使用模拟数据
      setReviews([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteDialog.review) {return;}
    try {
      await technicalReviewApi.delete(deleteDialog.review.id);
      setDeleteDialog({ open: false, review: null });
      fetchReviews();
    } catch (error) {
      console.error("Failed to delete review:", error);
      alert("删除失败：" + (error.response?.data?.detail || error.message));
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchReviews();
  };

  const handleReset = () => {
    setSearchKeyword("");
    setProjectId(null);
    setStatus(null);
    setReviewType(null);
    setPage(1);
    setTimeout(fetchReviews, 100);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <PageHeader
        title="技术评审管理"
        description="管理项目各阶段的技术评审（PDR/DDR/PRR/FRR/ARR）"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 筛选栏 */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索评审编号、名称..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                    className="pl-10 bg-slate-800/50 border-slate-700 text-slate-100"
                  />
                </div>
              </div>
              <Select
                value={projectId || ""}
                onValueChange={(value) => setProjectId(value || null)}
                className="bg-slate-800/50 border-slate-700"
              >
                <option value="">全部项目</option>
                {projectList.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.project_code} - {p.project_name}
                  </option>
                ))}
              </Select>
              <Select
                value={reviewType || ""}
                onValueChange={(value) => setReviewType(value || null)}
                className="bg-slate-800/50 border-slate-700"
              >
                <option value="">全部类型</option>
                <option value="PDR">方案设计评审</option>
                <option value="DDR">详细设计评审</option>
                <option value="PRR">生产准备评审</option>
                <option value="FRR">出厂评审</option>
                <option value="ARR">现场评审</option>
              </Select>
              <Select
                value={status || ""}
                onValueChange={(value) => setStatus(value || null)}
                className="bg-slate-800/50 border-slate-700"
              >
                <option value="">全部状态</option>
                <option value="DRAFT">草稿</option>
                <option value="PENDING">待评审</option>
                <option value="IN_PROGRESS">评审中</option>
                <option value="COMPLETED">已完成</option>
                <option value="CANCELLED">已取消</option>
              </Select>
            </div>
            <div className="flex gap-2 mt-4">
              <Button
                onClick={handleSearch}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Search className="w-4 h-4 mr-2" />
                搜索
              </Button>
              <Button
                onClick={handleReset}
                variant="outline"
                className="border-slate-700"
              >
                重置
              </Button>
              <Button
                onClick={() => navigate("/technical-reviews/new")}
                className="bg-emerald-600 hover:bg-emerald-700 ml-auto"
              >
                <Plus className="w-4 h-4 mr-2" />
                创建技术评审
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 列表 */}
        {loading ? (
          <div className="grid grid-cols-1 gap-4">
            {[1, 2, 3].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : reviews.length === 0 ? (
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="p-12 text-center">
              <FileCheck className="w-16 h-16 mx-auto text-slate-600 mb-4" />
              <p className="text-slate-400">暂无技术评审记录</p>
              <Button
                onClick={() => navigate("/technical-reviews/new")}
                className="mt-4 bg-emerald-600 hover:bg-emerald-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                创建第一个技术评审
              </Button>
            </CardContent>
          </Card>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 gap-4"
          >
            {reviews.map((review) => {
              const statusBadge = getStatusBadge(review.status);
              const conclusionBadge = getConclusionBadge(review.conclusion);
              const totalIssues =
                (review.issue_count_a || 0) +
                (review.issue_count_b || 0) +
                (review.issue_count_c || 0) +
                (review.issue_count_d || 0);

              return (
                <motion.div key={review.id} variants={staggerChild}>
                  <Card className="bg-slate-900/50 border-slate-800 hover:border-slate-700 transition-colors">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <h3 className="text-lg font-semibold text-slate-100">
                              {review.review_name}
                            </h3>
                            <Badge
                              className={cn(
                                "px-2 py-0.5 text-xs",
                                getReviewTypeColor(review.review_type),
                              )}
                            >
                              {getReviewTypeLabel(review.review_type)}
                            </Badge>
                            <Badge
                              className={cn(
                                "px-2 py-0.5 text-xs",
                                statusBadge.color,
                              )}
                            >
                              {statusBadge.label}
                            </Badge>
                            {conclusionBadge && (
                              <Badge
                                className={cn(
                                  "px-2 py-0.5 text-xs",
                                  conclusionBadge.color,
                                )}
                              >
                                {conclusionBadge.label}
                              </Badge>
                            )}
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-400 mb-4">
                            <div className="flex items-center gap-2">
                              <span className="text-slate-500">评审编号:</span>
                              <span className="text-slate-300">
                                {review.review_no}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-slate-500">项目:</span>
                              <span className="text-slate-300">
                                {review.project_no}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4" />
                              <span>
                                {formatDate(
                                  review.scheduled_date,
                                  "YYYY-MM-DD HH:mm",
                                )}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <AlertCircle className="w-4 h-4" />
                              <span>
                                问题: {totalIssues}个 (A:
                                {review.issue_count_a || 0} B:
                                {review.issue_count_b || 0} C:
                                {review.issue_count_c || 0} D:
                                {review.issue_count_d || 0})
                              </span>
                            </div>
                          </div>

                          {review.conclusion_summary && (
                            <p className="text-sm text-slate-400 line-clamp-2">
                              {review.conclusion_summary}
                            </p>
                          )}
                        </div>

                        <div className="flex gap-2 ml-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              navigate(`/technical-reviews/${review.id}`)
                            }
                            className="text-slate-400 hover:text-slate-100"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {review.status === "DRAFT" && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  navigate(
                                    `/technical-reviews/${review.id}/edit`,
                                  )
                                }
                                className="text-slate-400 hover:text-slate-100"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  setDeleteDialog({ open: true, review })
                                }
                                className="text-slate-400 hover:text-red-400"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {/* 分页 */}
        {total > pageSize && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">
              共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="border-slate-700"
              >
                上一页
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
                }
                disabled={page >= Math.ceil(total / pageSize)}
                className="border-slate-700"
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* 删除确认对话框 */}
      <Dialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, review: null })}
      >
        <DialogContent className="bg-slate-900 border-slate-800">
          <DialogHeader>
            <DialogTitle className="text-slate-100">确认删除</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-400">
              确定要删除评审 "{deleteDialog.review?.review_name}"
              吗？此操作不可恢复。
            </p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialog({ open: false, review: null })}
              className="border-slate-700"
            >
              取消
            </Button>
            <Button
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
