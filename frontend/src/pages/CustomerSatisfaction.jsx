/**
 * Customer Satisfaction Survey (Refactored to shadcn/Tailwind)
 * 客户满意度调查 - 客服工程师高级功能 (重构版本)
 */

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Filter,
  Eye,
  Send,
  Star,
  TrendingUp,
  TrendingDown,
  Calendar,
  User,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Download,
  BarChart3,
  PieChart,
  FileText,
  Settings,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  MoreHorizontal,
  ChevronDown,
} from "lucide-react";

import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";

// 导入拆分后的组件
import {
  CustomerSatisfactionOverview,
  SurveyManager,
  SatisfactionAnalytics,
  FeedbackManager,
  SurveyTemplates,
} from "../components/customer-satisfaction";

import {
  SATISFACTION_LEVELS,
  SURVEY_STATUS,
  SURVEY_TYPES,
  QUESTION_TYPES,
  ANALYSIS_PERIODS,
  FEEDBACK_CATEGORIES,
  CHART_COLORS,
  EXPORT_FORMATS,
  DEFAULT_FILTERS,
  TABLE_CONFIG,
} from "@/lib/constants/customer";

import { serviceApi } from "@/services/api/service";

const CustomerSatisfaction = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [surveys, setSurveys] = useState([]);
  const [responses, setResponses] = useState([]);
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [filters, _setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, _setSearchText] = useState("");
  const [_showCreateModal, setShowCreateModal] = useState(false);
  const [_showTemplateModal, _setShowTemplateModal] = useState(false);
  const [_editingSurvey, setEditingSurvey] = useState(null);
  const [notification, setNotification] = useState(null);

  // 满意度趋势数据
  const [trendData, setTrendData] = useState({ direction: "up", percentage: 0 });

  // 显示通知
  const showNotification = (type, message) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
  };

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [satisfactionRes, statsRes] = await Promise.all([
        serviceApi.satisfaction.list(),
        serviceApi.satisfaction.statistics().catch(() => ({ data: {} })),
      ]);
      const satisfactionList =
        satisfactionRes.data?.items ||
        satisfactionRes.data?.items ||
        satisfactionRes.data ||
        [];
      // 将满意度记录映射为 surveys 和 responses 格式
      const surveyItems = (satisfactionList || []).map((item) => ({
        id: item.id,
        title:
          item.title ||
          item.survey_title ||
          `满意度调查 #${item.id}`,
        type: item.type || item.survey_type || "service",
        status: item.status || "active",
        createdDate: item.created_at || item.createdDate || "",
        completedDate: item.completed_at || item.completedDate || "",
        avgScore: item.avg_score ?? item.avgScore ?? 0,
        responseCount: item.response_count ?? item.responseCount ?? 0,
        targetCount: item.target_count ?? item.targetCount ?? 100,
      }));
      const responseItems = satisfactionList
        .filter((item) => item.feedback || item.satisfaction_level != null)
        .map((item) => ({
          id: item.id,
          surveyId: item.survey_id ?? item.id,
          customerName: item.customer_name || item.customerName || "",
          satisfactionLevel:
            item.satisfaction_level ??
            item.satisfactionLevel ??
            item.score ??
            0,
          feedback: item.feedback || item.comment || "",
          category: item.category || "service",
          createdDate: item.created_at || item.createdDate || "",
        }));
      setSurveys(surveyItems);
      setResponses(responseItems);
      const stats = statsRes.data || {};
      setTrendData({
        direction: stats.trend_direction || "up",
        percentage: stats.trend_percentage ?? 0,
      });
    } catch (_error) {
      showNotification("error", "加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredSurveys = useMemo(() => {
    return (surveys || []).filter((survey) => {
      const searchLower = (searchText || "").toLowerCase();
      const matchesSearch = (survey.title || "")
        .toLowerCase()
        .includes(searchLower);
      const matchesType =
        !filters.surveyType || survey.type === filters.surveyType;
      const matchesStatus =
        !filters.status || survey.status === filters.status;

      return matchesSearch && matchesType && matchesStatus;
    });
  }, [surveys, searchText, filters]);

  const filteredResponses = useMemo(() => {
    return (responses || []).filter((response) => {
      const matchesLevel =
        !filters.satisfactionLevel ||
        response.satisfactionLevel === filters.satisfactionLevel;
      const matchesCategory =
        !filters.category || response.category === filters.category;

      return matchesLevel && matchesCategory;
    });
  }, [responses, filters]);

  // 事件处理
  const handleCreateSurvey = () => {
    setShowCreateModal(true);
  };

  const handleEditSurvey = (survey) => {
    setEditingSurvey(survey);
    setShowCreateModal(true);
  };

  const handleDeleteSurvey = async (surveyId) => {
    try {
      setLoading(true);
      // Note: satisfaction API may not have delete; remove locally for now
      setSurveys((surveys || []).filter((s) => s.id !== surveyId));
      showNotification("success", "删除成功");
    } catch (_error) {
      showNotification("error", "删除失败");
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = (format) => {
    showNotification("success", `正在导出${format.label}格式数据...`);
  };

  // 自定义星级评分组件
  const StarRating = ({ value, onChange, disabled = false, size = "default" }) => {
    const [hover, setHover] = useState(0);
    const starSize = size === "small" ? "w-4 h-4" : "w-5 h-5";

    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            disabled={disabled}
            className={cn(
              "transition-colors",
              disabled ? "cursor-default" : "cursor-pointer hover:scale-110"
            )}
            onMouseEnter={() => !disabled && setHover(star)}
            onMouseLeave={() => !disabled && setHover(0)}
            onClick={() => !disabled && onChange && onChange(star)}
          >
            <Star
              className={cn(
                starSize,
                star <= (hover || value)
                  ? "fill-amber-400 text-amber-400"
                  : "text-slate-600"
              )}
            />
          </button>
        ))}
      </div>
    );
  };

  // 自定义统计卡片组件
  const StatCard = ({ title, value, suffix, icon: Icon, trend }) => (
    <Card className="bg-slate-900/50 border-white/10">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 mb-1">{title}</p>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-white">{value}</span>
              {suffix && <span className="text-sm text-slate-400">{suffix}</span>}
            </div>
            {trend && (
              <div
                className={cn(
                  "flex items-center gap-1 text-xs mt-1",
                  trend.direction === "up"
                    ? "text-emerald-400"
                    : "text-red-400"
                )}
              >
                {trend.direction === "up" ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                <span>{trend.percentage}%</span>
              </div>
            )}
          </div>
          {Icon && (
            <div className="p-2 bg-primary/20 rounded-lg">
              <Icon className="w-5 h-5 text-primary" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  // 状态标签配置
  const getStatusConfig = (status) => {
    const config = SURVEY_STATUS[status?.toUpperCase()];
    if (!config) return { label: "未知", color: "bg-slate-500" };

    const colorMap = {
      "#d9d9d9": "bg-slate-500/20 text-slate-400 border-slate-500/30",
      "#52c41a": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      "#1890ff": "bg-blue-500/20 text-blue-400 border-blue-500/30",
      "#ff4d4f": "bg-red-500/20 text-red-400 border-red-500/30",
    };

    return {
      label: config.label,
      className: colorMap[config.color] || "bg-slate-500/20 text-slate-400",
    };
  };

  const getTypeLabel = (type) => {
    const config = SURVEY_TYPES[type?.toUpperCase()];
    return config?.label || type;
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      {/* 通知提示 */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={cn(
              "fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg",
              notification.type === "success"
                ? "bg-emerald-500/20 border border-emerald-500/30 text-emerald-400"
                : "bg-red-500/20 border border-red-500/30 text-red-400"
            )}
          >
            {notification.message}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 页面头部 */}
      <PageHeader
        title="客户满意度管理"
        description="创建、管理和分析客户满意度调查，提升服务质量"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button onClick={handleCreateSurvey}>
              <Plus className="w-4 h-4 mr-2" />
              创建调查
            </Button>
            <Button variant="outline" onClick={loadData}>
              <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
              刷新
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  导出数据
                  <ChevronDown className="w-4 h-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {Object.values(EXPORT_FORMATS).map((format) => (
                  <DropdownMenuItem
                    key={format.value}
                    onClick={() => handleExportData(format)}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    导出{format.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </motion.div>
        }
      />

      {/* 主要内容区域 - Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 bg-slate-800/50">
          <TabsTrigger value="overview" className="data-[state=active]:bg-slate-700">
            <BarChart3 className="w-4 h-4 mr-2" />
            概览分析
          </TabsTrigger>
          <TabsTrigger value="surveys" className="data-[state=active]:bg-slate-700">
            <FileText className="w-4 h-4 mr-2" />
            调查管理
          </TabsTrigger>
          <TabsTrigger value="analytics" className="data-[state=active]:bg-slate-700">
            <PieChart className="w-4 h-4 mr-2" />
            满意度分析
          </TabsTrigger>
          <TabsTrigger value="feedback" className="data-[state=active]:bg-slate-700">
            <MessageSquare className="w-4 h-4 mr-2" />
            反馈管理
          </TabsTrigger>
          <TabsTrigger value="templates" className="data-[state=active]:bg-slate-700">
            <Settings className="w-4 h-4 mr-2" />
            问卷模板
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <CustomerSatisfactionOverview
            data={{ surveys, responses, trend: trendData }}
            loading={loading}
            onRefresh={loadData}
          />
        </TabsContent>

        <TabsContent value="surveys" className="mt-4">
          <SurveyManager
            surveys={filteredSurveys}
            loading={loading}
            onCreate={handleCreateSurvey}
            onEdit={handleEditSurvey}
            onDelete={handleDeleteSurvey}
          />
        </TabsContent>

        <TabsContent value="analytics" className="mt-4">
          <SatisfactionAnalytics
            surveys={surveys}
            responses={filteredResponses}
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="feedback" className="mt-4">
          <FeedbackManager
            responses={filteredResponses}
            loading={loading}
            onRefresh={loadData}
          />
        </TabsContent>

        <TabsContent value="templates" className="mt-4">
          <SurveyTemplates
            loading={loading}
            onUseTemplate={handleCreateSurvey}
          />
        </TabsContent>
      </Tabs>

      {/* 调查详情模态框 */}
      <Dialog open={!!selectedSurvey} onOpenChange={() => setSelectedSurvey(null)}>
        <DialogContent className="max-w-4xl bg-slate-900 border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white">
              {selectedSurvey?.title}
            </DialogTitle>
            <DialogDescription>
              调查详情和统计分析
            </DialogDescription>
          </DialogHeader>
          {selectedSurvey && (
            <div className="space-y-6 py-4">
              {/* 统计卡片 */}
              <div className="grid grid-cols-3 gap-4">
                <StatCard
                  title="平均评分"
                  value={selectedSurvey.avgScore.toFixed(1)}
                  suffix="/5.0"
                  icon={Star}
                />
                <StatCard
                  title="响应人数"
                  value={selectedSurvey.responseCount}
                  icon={User}
                />
                <StatCard
                  title="完成率"
                  value={(
                    (selectedSurvey.responseCount / selectedSurvey.targetCount) *
                    100
                  ).toFixed(1)}
                  suffix="%"
                  icon={CheckCircle2}
                />
              </div>

              {/* 详细信息 */}
              <Card className="bg-slate-800/50 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white text-lg">调查信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-slate-400 mb-1">调查类型</p>
                      <p className="text-white">
                        {getTypeLabel(selectedSurvey.type)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1">状态</p>
                      <Badge
                        variant="outline"
                        className={getStatusConfig(selectedSurvey.status).className}
                      >
                        {getStatusConfig(selectedSurvey.status).label}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1">创建日期</p>
                      <p className="text-white">{selectedSurvey.createdDate || "-"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1">完成日期</p>
                      <p className="text-white">{selectedSurvey.completedDate || "-"}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 响应进度 */}
              <Card className="bg-slate-800/50 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white text-lg">响应进度</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">已响应 / 目标</span>
                    <span className="text-white">
                      {selectedSurvey.responseCount} / {selectedSurvey.targetCount}
                    </span>
                  </div>
                  <Progress
                    value={
                      (selectedSurvey.responseCount / selectedSurvey.targetCount) * 100
                    }
                    className="h-2"
                  />
                </CardContent>
              </Card>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedSurvey(null)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
};

export default CustomerSatisfaction;
