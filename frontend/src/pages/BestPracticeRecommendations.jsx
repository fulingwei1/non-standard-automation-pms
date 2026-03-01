/**
 * 最佳实践推荐页面
 * 基于项目信息智能推荐最佳实践
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { projectReviewApi, projectApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  SkeletonCard,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../components/ui";
import {
  Search,
  Sparkles,
  TrendingUp,
  CheckCircle2,
  Star,
  ArrowRight,
  Eye,
  Target,
  Filter,
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

const getValidationBadge = (status) => {
  const badges = {
    PENDING: { label: "待验证", variant: "secondary", color: "text-slate-400" },
    VALIDATED: {
      label: "已验证",
      variant: "success",
      color: "text-emerald-400",
    },
    REJECTED: {
      label: "已拒绝",
      variant: "destructive",
      color: "text-red-400",
    },
  };
  return badges[status] || badges.PENDING;
};

export default function BestPracticeRecommendations() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState([]);
  const [popularPractices, setPopularPractices] = useState([]);
  const [project, setProject] = useState(null);
  const [activeTab, setActiveTab] = useState("recommend");

  // 推荐参数
  const [projectType, setProjectType] = useState("");
  const [currentStage, setCurrentStage] = useState("");
  const [category, setCategory] = useState("");

  useEffect(() => {
    if (projectId) {
      fetchProject();
      fetchRecommendations();
    } else {
      setLoading(false);
    }
    fetchPopularPractices();
  }, [projectId]);

  useEffect(() => {
    if (!projectId && (projectType || currentStage || category)) {
      fetchManualRecommendations();
    }
  }, [projectType, currentStage, category]);

  const fetchProject = async () => {
    try {
      const res = await projectApi.get(projectId);
      const data = res.data || res;
      setProject(data);
      setProjectType(data.project_type || "");
      setCurrentStage(data.stage || "");
    } catch (err) {
      console.error("Failed to fetch project:", err);
    }
  };

  const fetchRecommendations = async () => {
    if (!projectId) {return;}
    try {
      setLoading(true);
      const res = await projectReviewApi.getProjectBestPracticeRecommendations(
        projectId,
        20,
      );
      const data = res.data || res;
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error("Failed to fetch recommendations:", err);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchManualRecommendations = async () => {
    try {
      setLoading(true);
      const res = await projectReviewApi.recommendBestPractices({
        project_type: projectType || undefined,
        current_stage: currentStage || undefined,
        category: category || undefined,
        limit: 20,
      });
      const data = res.data || res;
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error("Failed to fetch recommendations:", err);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchPopularPractices = async () => {
    try {
      const res = await projectReviewApi.getPopularBestPractices({
        page: 1,
        page_size: 10,
      });
      const data = res.data || res;
      setPopularPractices(data.items || data || []);
    } catch (err) {
      console.error("Failed to fetch popular practices:", err);
      setPopularPractices([]);
    }
  };

  const handleApplyPractice = async (practiceId, targetProjectId) => {
    try {
      await projectReviewApi.applyBestPractice(
        practiceId,
        targetProjectId,
        "从推荐页面应用",
      );
      alert("最佳实践应用成功！");
      fetchRecommendations();
      fetchPopularPractices();
    } catch (err) {
      console.error("Failed to apply practice:", err);
      alert("应用失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleViewReview = (reviewId) => {
    navigate(`/projects/reviews/${reviewId}`);
  };

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <PageHeader
        title={
          projectId
            ? `最佳实践推荐 - ${project?.project_name || project?.project_code}`
            : "最佳实践推荐"
        }
        description={
          projectId
            ? "基于项目信息智能推荐最佳实践"
            : "手动配置条件推荐最佳实践"
        }
        action={
          !projectId && (
            <Button onClick={fetchManualRecommendations} variant="outline">
              <Sparkles className="h-4 w-4 mr-2" />
              重新推荐
            </Button>
          )
        }
      />

      <Tabs
        value={activeTab || "unknown"}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="recommend">智能推荐</TabsTrigger>
          <TabsTrigger value="popular">热门实践</TabsTrigger>
        </TabsList>

        <TabsContent value="recommend" className="space-y-6">
          {/* 推荐条件（仅非项目页面显示） */}
          {!projectId && (
            <Card>
              <CardContent className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm text-slate-400 mb-2 block">
                      项目类型
                    </label>
                    <Input
                      placeholder="输入项目类型..."
                      value={projectType || "unknown"}
                      onChange={(e) => setProjectType(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm text-slate-400 mb-2 block">
                      当前阶段
                    </label>
                    <select
                      value={currentStage || "unknown"}
                      onChange={(e) => setCurrentStage(e.target.value)}
                      className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="">全部阶段</option>
                      <option value="S1">S1: 需求进入</option>
                      <option value="S2">S2: 方案设计</option>
                      <option value="S3">S3: 采购备料</option>
                      <option value="S4">S4: 加工制造</option>
                      <option value="S5">S5: 装配调试</option>
                      <option value="S6">S6: 出厂验收</option>
                      <option value="S7">S7: 包装发运</option>
                      <option value="S8">S8: 现场安装</option>
                      <option value="S9">S9: 质保结项</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-slate-400 mb-2 block">
                      分类
                    </label>
                    <Input
                      placeholder="输入分类..."
                      value={category || "unknown"}
                      onChange={(e) => setCategory(e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 推荐结果 */}
          {loading ? (
            <div className="space-y-4">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : recommendations.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Sparkles className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-400">暂无推荐的最佳实践</p>
                <p className="text-sm text-slate-500 mt-2">
                  请调整筛选条件或等待更多最佳实践被添加
                </p>
              </CardContent>
            </Card>
          ) : (
            <motion.div variants={staggerContainer} className="space-y-4">
              {(recommendations || []).map((rec, index) => {
                const practice = rec.practice || rec;
                const matchScore = rec.match_score || 0;
                const matchReasons = rec.match_reasons || [];
                const validationBadge = getValidationBadge(
                  practice.validation_status,
                );

                return (
                  <motion.div
                    key={practice.id || index}
                    variants={staggerChild}
                  >
                    <Card className="hover:border-primary/50 transition-colors">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 space-y-3">
                            <div className="flex items-center gap-3">
                              <div className="flex items-center gap-2">
                                <Star
                                  className={cn(
                                    "h-5 w-5",
                                    matchScore > 0.7
                                      ? "text-yellow-400 fill-yellow-400"
                                      : "text-slate-400",
                                  )}
                                />
                                <h3 className="text-lg font-semibold text-white">
                                  {practice.title}
                                </h3>
                              </div>
                              <Badge variant={validationBadge.variant}>
                                {validationBadge.label}
                              </Badge>
                              {matchScore > 0 && (
                                <Badge variant="info" className="gap-1">
                                  <Target className="h-3 w-3" />
                                  匹配度: {(matchScore * 100).toFixed(0)}%
                                </Badge>
                              )}
                            </div>
                            <p className="text-slate-300 line-clamp-2">
                              {practice.description}
                            </p>
                            {matchReasons.length > 0 && (
                              <div className="flex flex-wrap gap-2">
                                {(matchReasons || []).map((reason, idx) => (
                                  <Badge
                                    key={idx}
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    {reason}
                                  </Badge>
                                ))}
                              </div>
                            )}
                            <div className="flex items-center gap-4 text-sm text-slate-400">
                              {practice.project_code && (
                                <span>
                                  来源: {practice.project_code}{" "}
                                  {practice.project_name}
                                </span>
                              )}
                              {practice.category && (
                                <span>分类: {practice.category}</span>
                              )}
                              {practice.reuse_count > 0 && (
                                <span className="text-emerald-400">
                                  复用 {practice.reuse_count} 次
                                </span>
                              )}
                              {practice.last_reused_at && (
                                <span>
                                  最后复用:{" "}
                                  {formatDate(practice.last_reused_at)}
                                </span>
                              )}
                            </div>
                            {practice.context && (
                              <div className="mt-3 p-3 bg-surface-2 rounded-md">
                                <p className="text-sm text-slate-300">
                                  <span className="font-medium">适用场景:</span>{" "}
                                  {practice.context}
                                </p>
                              </div>
                            )}
                            {practice.benefits && (
                              <div className="mt-2 p-3 bg-surface-2 rounded-md">
                                <p className="text-sm text-slate-300">
                                  <span className="font-medium">
                                    带来的收益:
                                  </span>{" "}
                                  {practice.benefits}
                                </p>
                              </div>
                            )}
                          </div>
                          <div className="ml-4 flex flex-col gap-2">
                            {projectId && (
                              <Button
                                size="sm"
                                onClick={() =>
                                  handleApplyPractice(practice.id, projectId)
                                }
                                className="gap-2"
                              >
                                <ArrowRight className="h-4 w-4" />
                                应用
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                handleViewReview(practice.review_id)
                              }
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              查看复盘
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </TabsContent>

        <TabsContent value="popular" className="space-y-6">
          {popularPractices.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <p className="text-slate-400">暂无热门最佳实践</p>
              </CardContent>
            </Card>
          ) : (
            <motion.div variants={staggerContainer} className="space-y-4">
              {(popularPractices || []).map((practice) => {
                const validationBadge = getValidationBadge(
                  practice.validation_status,
                );

                return (
                  <motion.div key={practice.id} variants={staggerChild}>
                    <Card className="hover:border-primary/50 transition-colors">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 space-y-3">
                            <div className="flex items-center gap-3">
                              <TrendingUp className="h-5 w-5 text-emerald-400" />
                              <h3 className="text-lg font-semibold text-white">
                                {practice.title}
                              </h3>
                              <Badge variant={validationBadge.variant}>
                                {validationBadge.label}
                              </Badge>
                              {practice.reuse_count > 0 && (
                                <Badge variant="success" className="gap-1">
                                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                  热门 ({practice.reuse_count})
                                </Badge>
                              )}
                            </div>
                            <p className="text-slate-300 line-clamp-2">
                              {practice.description}
                            </p>
                            <div className="flex items-center gap-4 text-sm text-slate-400">
                              {practice.project_code && (
                                <span>
                                  来源: {practice.project_code}{" "}
                                  {practice.project_name}
                                </span>
                              )}
                              {practice.category && (
                                <span>分类: {practice.category}</span>
                              )}
                              {practice.reuse_count > 0 && (
                                <span className="text-emerald-400">
                                  复用 {practice.reuse_count} 次
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="ml-4 flex gap-2">
                            {projectId && (
                              <Button
                                size="sm"
                                onClick={() =>
                                  handleApplyPractice(practice.id, projectId)
                                }
                                className="gap-2"
                              >
                                <ArrowRight className="h-4 w-4" />
                                应用
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                handleViewReview(practice.review_id)
                              }
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              查看复盘
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
