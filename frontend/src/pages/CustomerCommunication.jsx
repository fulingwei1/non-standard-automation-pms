/**
 * Customer Communication Management
 * 客户沟通历史管理 - 客服工程师高级功能
 *
 * 功能：
 * 1. 客户沟通记录创建、查看、编辑
 * 2. 沟通方式管理（电话、邮件、现场、微信、会议等）
 * 3. 沟通主题分类
 * 4. 沟通内容详细记录
 * 5. 后续跟进任务
 * 6. 沟通记录搜索和筛选
 * 7. 沟通统计分析
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  Phone,
  Mail,
  MessageSquare,
  Calendar,
  User,
  Clock,
  FileText,
  CheckCircle2,
  XCircle,
  RefreshCw,
  MapPin,
  Video,
  TrendingUp,
  Download,
  Star,
  AlertCircle,
  ChevronRight,
  Send,
  Tag,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
  DialogBody,
} from "../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { LoadingCard, ErrorMessage, EmptyState } from "../components/common";
import { toast } from "../components/ui/toast";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { serviceApi } from "../services/api";

export default function CustomerCommunication() {
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [topicFilter, setTopicFilter] = useState("ALL");
  const [importanceFilter, setImportanceFilter] = useState("ALL");
  const [followUpFilter, setFollowUpFilter] = useState("ALL");
  const [dateFilter, setDateFilter] = useState({ start: "", end: "" });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedCommunication, setSelectedCommunication] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    thisWeek: 0,
    thisMonth: 0,
    pendingFollowUp: 0,
    byType: {},
  });

  useEffect(() => {
    loadCommunications();
  }, []);

  useEffect(() => {
    if (communications.length > 0 || !loading) {
      loadStatistics();
    }
  }, [communications, loading]);

  const loadCommunications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page: 1,
        page_size: 1000,
      };
      const response = await serviceApi.communications.list(params);
      const communicationsData = response.data?.items || response.data || [];

      // Transform backend data to frontend format
      const transformedCommunications = communicationsData.map((comm) => ({
        id: comm.id,
        communication_no: comm.communication_no || "",
        communication_type: comm.communication_type || "",
        customer_name: comm.customer_name || "",
        customer_contact: comm.customer_contact || "",
        customer_phone: comm.customer_phone || "",
        customer_email: comm.customer_email || "",
        project_code: comm.project_code || "",
        project_name: comm.project_name || "",
        communication_date: comm.communication_date || "",
        communication_time: comm.communication_time || "",
        duration: comm.duration || 0,
        location: comm.location || "",
        topic: comm.topic || "",
        subject: comm.subject || "",
        content: comm.content || "",
        follow_up_required: comm.follow_up_required || false,
        follow_up_task: comm.follow_up_task || "",
        follow_up_due_date: comm.follow_up_due_date || "",
        follow_up_status: comm.follow_up_status || "",
        tags: comm.tags || [],
        importance: comm.importance || "中",
        created_by: comm.created_by || "",
        created_at: comm.created_at || "",
      }));

      setCommunications(transformedCommunications);
    } catch (err) {
      console.error("Failed to load communications:", err);
      setError(err.response?.data?.detail || err.message || "加载沟通记录失败");
      setCommunications([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStatistics = useCallback(async () => {
    try {
      // Calculate statistics from loaded communications
      const now = new Date();
      const thisWeekStart = new Date(now);
      thisWeekStart.setDate(now.getDate() - now.getDay());
      const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);

      setStats({
        total: communications.length,
        thisWeek: communications.filter((c) => {
          if (!c.communication_date) return false;
          const commDate = new Date(c.communication_date);
          return commDate >= thisWeekStart;
        }).length,
        thisMonth: communications.filter((c) => {
          if (!c.communication_date) return false;
          const commDate = new Date(c.communication_date);
          return commDate >= thisMonthStart;
        }).length,
        pendingFollowUp: communications.filter(
          (c) =>
            c.follow_up_required &&
            (c.follow_up_status === "待处理" ||
              c.follow_up_status === "PENDING"),
        ).length,
        byType: communications.reduce((acc, c) => {
          acc[c.communication_type] = (acc[c.communication_type] || 0) + 1;
          return acc;
        }, {}),
      });
    } catch (err) {
      console.error("Failed to load statistics:", err);
    }
  }, [communications]);

  const filteredCommunications = useMemo(() => {
    let result = communications;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (comm) =>
          comm.communication_no.toLowerCase().includes(query) ||
          comm.customer_name.toLowerCase().includes(query) ||
          comm.project_name.toLowerCase().includes(query) ||
          comm.subject.toLowerCase().includes(query) ||
          comm.content.toLowerCase().includes(query),
      );
    }

    // Type filter
    if (typeFilter !== "ALL") {
      result = result.filter((comm) => comm.communication_type === typeFilter);
    }

    // Topic filter
    if (topicFilter !== "ALL") {
      result = result.filter((comm) => comm.topic === topicFilter);
    }

    // Importance filter
    if (importanceFilter !== "ALL") {
      result = result.filter((comm) => comm.importance === importanceFilter);
    }

    // Follow-up filter
    if (followUpFilter === "REQUIRED") {
      result = result.filter((comm) => comm.follow_up_required);
    } else if (followUpFilter === "PENDING") {
      result = result.filter(
        (comm) => comm.follow_up_required && comm.follow_up_status === "待处理",
      );
    }

    // Date filter
    if (dateFilter.start) {
      result = result.filter(
        (comm) => comm.communication_date >= dateFilter.start,
      );
    }
    if (dateFilter.end) {
      result = result.filter(
        (comm) => comm.communication_date <= dateFilter.end,
      );
    }

    return result.sort((a, b) => {
      return (
        new Date(
          b.communication_date + " " + (b.communication_time || "00:00"),
        ) -
        new Date(a.communication_date + " " + (a.communication_time || "00:00"))
      );
    });
  }, [
    communications,
    searchQuery,
    typeFilter,
    topicFilter,
    importanceFilter,
    followUpFilter,
    dateFilter,
  ]);

  const handleViewDetail = (communication) => {
    setSelectedCommunication(communication);
    setShowDetailDialog(true);
  };

  const handleCreateCommunication = async (commData) => {
    try {
      // Transform frontend data to backend format
      const backendData = {
        communication_type: commData.communication_type,
        customer_id: commData.customer_id,
        project_id: commData.project_id,
        communication_date: commData.communication_date,
        communication_time: commData.communication_time,
        duration: commData.duration,
        location: commData.location,
        topic: commData.topic,
        subject: commData.subject,
        content: commData.content,
        follow_up_required: commData.follow_up_required || false,
        follow_up_task: commData.follow_up_task || "",
        follow_up_due_date: commData.follow_up_due_date || "",
        follow_up_status: commData.follow_up_status || "PENDING",
        tags: commData.tags || [],
        importance: commData.importance || "MEDIUM",
      };

      await serviceApi.communications.create(backendData);
      toast.success("沟通记录创建成功");
      setShowCreateDialog(false);
      await loadCommunications();
      await loadStatistics();
    } catch (error) {
      console.error("Failed to create communication:", error);
      toast.error(
        "创建失败: " +
          (error.response?.data?.detail || error.message || "请稍后重试"),
      );
    }
  };

  const handleUpdateCommunication = async (commId, commData) => {
    try {
      // Transform frontend data to backend format
      const backendData = {
        communication_type: commData.communication_type,
        customer_id: commData.customer_id,
        project_id: commData.project_id,
        communication_date: commData.communication_date,
        communication_time: commData.communication_time,
        duration: commData.duration,
        location: commData.location,
        topic: commData.topic,
        subject: commData.subject,
        content: commData.content,
        follow_up_required: commData.follow_up_required || false,
        follow_up_task: commData.follow_up_task || "",
        follow_up_due_date: commData.follow_up_due_date || "",
        follow_up_status: commData.follow_up_status || "PENDING",
        tags: commData.tags || [],
        importance: commData.importance || "MEDIUM",
      };

      await serviceApi.communications.update(commId, backendData);
      toast.success("沟通记录更新成功");
      setShowDetailDialog(false);
      await loadCommunications();
      await loadStatistics();
    } catch (error) {
      console.error("Failed to update communication:", error);
      toast.error(
        "更新失败: " +
          (error.response?.data?.detail || error.message || "请稍后重试"),
      );
    }
  };

  const handleExportCommunications = () => {
    try {
      const commsToExport = filteredCommunications;
      if (commsToExport.length === 0) {
        toast.warning("没有可导出的数据");
        return;
      }

      const headers = [
        "沟通号",
        "沟通方式",
        "客户名称",
        "客户联系人",
        "客户电话",
        "客户邮箱",
        "项目编号",
        "项目名称",
        "沟通日期",
        "沟通时间",
        "沟通时长(分钟)",
        "沟通地点",
        "沟通主题",
        "沟通内容",
        "是否需要跟进",
        "跟进任务",
        "跟进截止日期",
        "跟进状态",
        "重要性",
        "标签",
        "创建人",
        "创建时间",
      ];

      const csvRows = [
        headers.join(","),
        ...commsToExport.map((comm) =>
          [
            comm.communication_no || "",
            comm.communication_type || "",
            comm.customer_name || "",
            comm.customer_contact || "",
            comm.customer_phone || "",
            comm.customer_email || "",
            comm.project_code || "",
            comm.project_name || "",
            comm.communication_date || "",
            comm.communication_time || "",
            comm.duration || "",
            comm.location || "",
            comm.topic || "",
            `"${(comm.subject || "").replace(/"/g, '""')}"`,
            `"${(comm.content || "").replace(/"/g, '""')}"`,
            comm.follow_up_required ? "是" : "否",
            `"${(comm.follow_up_task || "").replace(/"/g, '""')}"`,
            comm.follow_up_due_date || "",
            comm.follow_up_status || "",
            comm.importance || "",
            Array.isArray(comm.tags) ? comm.tags.join(";") : comm.tags || "",
            comm.created_by || "",
            comm.created_at || "",
          ].join(","),
        ),
      ];

      const csvContent = csvRows.join("\n");
      const blob = new Blob(["\ufeff" + csvContent], {
        type: "text/csv;charset=utf-8;",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `客户沟通记录_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success(`成功导出 ${commsToExport.length} 条沟通记录`);
    } catch (error) {
      console.error("Failed to export communications:", error);
      toast.error("导出失败: " + (error.message || "请稍后重试"));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="客户沟通历史"
        description="记录和管理与客户的所有沟通记录，跟踪后续任务"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {
                loadCommunications();
                loadStatistics();
                toast.success("数据已刷新");
              }}
              disabled={loading}
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              刷新
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleExportCommunications}
              disabled={loading}
            >
              <Download className={cn("w-4 h-4", loading && "animate-spin")} />
              导出数据
            </Button>
            <Button
              size="sm"
              className="gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              创建记录
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Statistics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总记录数</div>
                <div className="text-2xl font-bold text-white">
                  {stats.total}
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/10 border-blue-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">本周沟通</div>
                <div className="text-2xl font-bold text-blue-400">
                  {stats.thisWeek}
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-purple-500/10 border-purple-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">本月沟通</div>
                <div className="text-2xl font-bold text-purple-400">
                  {stats.thisMonth}
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-amber-500/10 border-amber-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">待跟进</div>
                <div className="text-2xl font-bold text-amber-400">
                  {stats.pendingFollowUp}
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-emerald-500/10 border-emerald-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">电话沟通</div>
                <div className="text-2xl font-bold text-emerald-400">
                  {stats.byType["电话"] || 0}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Filters */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索记录号、客户名称、项目名称、主题..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700"
                    />
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部方式</option>
                    <option value="电话">电话</option>
                    <option value="邮件">邮件</option>
                    <option value="现场">现场</option>
                    <option value="微信">微信</option>
                    <option value="会议">会议</option>
                  </select>
                  <select
                    value={topicFilter}
                    onChange={(e) => setTopicFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部主题</option>
                    <option value="设备运行问题">设备运行问题</option>
                    <option value="操作培训">操作培训</option>
                    <option value="定期回访">定期回访</option>
                    <option value="技术支持">技术支持</option>
                    <option value="满意度调查">满意度调查</option>
                  </select>
                  <select
                    value={importanceFilter}
                    onChange={(e) => setImportanceFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部重要性</option>
                    <option value="高">高</option>
                    <option value="中">中</option>
                    <option value="低">低</option>
                  </select>
                  <select
                    value={followUpFilter}
                    onChange={(e) => setFollowUpFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部</option>
                    <option value="REQUIRED">需跟进</option>
                    <option value="PENDING">待跟进</option>
                  </select>
                  <Input
                    type="date"
                    value={dateFilter.start}
                    onChange={(e) =>
                      setDateFilter({ ...dateFilter, start: e.target.value })
                    }
                    placeholder="开始日期"
                    className="w-40 bg-slate-800/50 border-slate-700 text-sm"
                  />
                  <Input
                    type="date"
                    value={dateFilter.end}
                    onChange={(e) =>
                      setDateFilter({ ...dateFilter, end: e.target.value })
                    }
                    placeholder="结束日期"
                    className="w-40 bg-slate-800/50 border-slate-700 text-sm"
                  />
                  {(searchQuery ||
                    typeFilter !== "ALL" ||
                    topicFilter !== "ALL" ||
                    importanceFilter !== "ALL" ||
                    followUpFilter !== "ALL" ||
                    dateFilter.start ||
                    dateFilter.end) && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setSearchQuery("");
                        setTypeFilter("ALL");
                        setTopicFilter("ALL");
                        setImportanceFilter("ALL");
                        setFollowUpFilter("ALL");
                        setDateFilter({ start: "", end: "" });
                      }}
                      className="gap-2"
                    >
                      <XCircle className="w-4 h-4" />
                      清除
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Communication List */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-3"
        >
          {loading ? (
            <LoadingCard rows={5} />
          ) : error && communications.length === 0 ? (
            <ErrorMessage error={error} onRetry={loadCommunications} />
          ) : filteredCommunications.length === 0 ? (
            <EmptyState
              icon={MessageSquare}
              title="暂无沟通记录"
              description={
                searchQuery ||
                typeFilter !== "ALL" ||
                topicFilter !== "ALL" ||
                importanceFilter !== "ALL" ||
                followUpFilter !== "ALL" ||
                dateFilter.start ||
                dateFilter.end
                  ? "当前筛选条件下没有匹配的记录，请尝试调整筛选条件"
                  : "当前没有沟通记录数据"
              }
            />
          ) : (
            filteredCommunications.map((comm) => {
              const typeConfig =
                communicationTypeConfig[comm.communication_type] ||
                communicationTypeConfig["其他"];
              const TypeIcon = typeConfig.icon;
              const importance =
                importanceConfig[comm.importance] || importanceConfig["中"];
              const topic = topicConfig[comm.topic] || topicConfig["其他"];

              return (
                <motion.div key={comm.id} variants={fadeIn}>
                  <Card className="hover:bg-slate-800/50 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          {/* Header */}
                          <div className="flex items-center gap-3 flex-wrap">
                            <span className="font-mono text-sm text-slate-300">
                              {comm.communication_no}
                            </span>
                            <Badge
                              className={cn(
                                typeConfig.bg,
                                typeConfig.color,
                                "text-xs",
                              )}
                            >
                              <TypeIcon className="w-3 h-3 mr-1" />
                              {typeConfig.label}
                            </Badge>
                            <Badge
                              className={cn(
                                importance.bg,
                                importance.color,
                                "text-xs",
                              )}
                            >
                              {importance.label}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={cn("text-xs", topic.color)}
                            >
                              {topic.label}
                            </Badge>
                            {comm.follow_up_required && (
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs",
                                  comm.follow_up_status === "待处理"
                                    ? "text-amber-400 border-amber-500/30"
                                    : "text-emerald-400 border-emerald-500/30",
                                )}
                              >
                                {comm.follow_up_status === "待处理" ? (
                                  <AlertCircle className="w-3 h-3 mr-1" />
                                ) : (
                                  <CheckCircle2 className="w-3 h-3 mr-1" />
                                )}
                                {comm.follow_up_status || "需跟进"}
                              </Badge>
                            )}
                          </div>

                          {/* Content */}
                          <div>
                            <h3 className="text-white font-medium mb-1">
                              {comm.subject}
                            </h3>
                            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mb-2">
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {comm.customer_name}
                                {comm.customer_contact &&
                                  ` - ${comm.customer_contact}`}
                              </span>
                              {comm.project_name && (
                                <span className="flex items-center gap-1">
                                  <FileText className="w-3 h-3" />
                                  {comm.project_name}
                                </span>
                              )}
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {comm.communication_date}{" "}
                                {comm.communication_time &&
                                  comm.communication_time}
                              </span>
                              {comm.duration && (
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  时长: {comm.duration}分钟
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-slate-300 line-clamp-2">
                              {comm.content}
                            </p>
                          </div>

                          {/* Tags and Footer */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 flex-wrap">
                              {comm.tags &&
                                comm.tags.map((tag, index) => (
                                  <Badge
                                    key={index}
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    <Tag className="w-3 h-3 mr-1" />
                                    {tag}
                                  </Badge>
                                ))}
                            </div>
                            <div className="text-xs text-slate-500">
                              创建: {comm.created_by} | {comm.created_at}
                            </div>
                          </div>

                          {/* Follow-up Task */}
                          {comm.follow_up_required && comm.follow_up_task && (
                            <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                              <div className="flex items-center gap-2 text-xs">
                                <AlertCircle className="w-3 h-3 text-amber-400" />
                                <span className="text-amber-400 font-medium">
                                  跟进任务:
                                </span>
                                <span className="text-slate-300">
                                  {comm.follow_up_task}
                                </span>
                                {comm.follow_up_due_date && (
                                  <span className="text-slate-500 ml-auto">
                                    截止: {comm.follow_up_due_date}
                                  </span>
                                )}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDetail(comm)}
                            className="gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            查看
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })
          )}
        </motion.div>
      </div>

      {/* Create Communication Dialog */}
      <AnimatePresence>
        {showCreateDialog && (
          <CreateCommunicationDialog
            onClose={() => setShowCreateDialog(false)}
            onSubmit={handleCreateCommunication}
          />
        )}
      </AnimatePresence>

      {/* Detail Dialog */}
      <AnimatePresence>
        {showDetailDialog && selectedCommunication && (
          <CommunicationDetailDialog
            communication={selectedCommunication}
            onClose={() => {
              setShowDetailDialog(false);
              setSelectedCommunication(null);
            }}
            onUpdate={handleUpdateCommunication}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// Create Communication Dialog Component
function CreateCommunicationDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    communication_type: "电话",
    customer_name: "",
    customer_contact: "",
    customer_phone: "",
    customer_email: "",
    project_code: "",
    project_name: "",
    communication_date: new Date().toISOString().split("T")[0],
    communication_time: new Date().toTimeString().slice(0, 5),
    duration: "",
    location: "",
    topic: "技术支持",
    subject: "",
    content: "",
    follow_up_required: false,
    follow_up_task: "",
    follow_up_due_date: "",
    tags: [],
    importance: "中",
  });

  const [tagInput, setTagInput] = useState("");

  const handleSubmit = () => {
    if (!formData.subject || !formData.content || !formData.customer_name) {
      toast.error("请填写主题、内容和客户名称");
      return;
    }
    onSubmit(formData);
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      setTagInput("");
    }
  };

  const handleRemoveTag = (tag) => {
    setFormData({ ...formData, tags: formData.tags.filter((t) => t !== tag) });
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建沟通记录</DialogTitle>
          <DialogDescription>
            记录与客户的沟通内容，系统将自动生成记录号
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  沟通方式 *
                </label>
                <select
                  value={formData.communication_type}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      communication_type: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="电话">电话</option>
                  <option value="邮件">邮件</option>
                  <option value="现场">现场</option>
                  <option value="微信">微信</option>
                  <option value="会议">会议</option>
                  <option value="其他">其他</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  沟通主题 *
                </label>
                <select
                  value={formData.topic}
                  onChange={(e) =>
                    setFormData({ ...formData, topic: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="设备运行问题">设备运行问题</option>
                  <option value="操作培训">操作培训</option>
                  <option value="定期回访">定期回访</option>
                  <option value="技术支持">技术支持</option>
                  <option value="满意度调查">满意度调查</option>
                  <option value="其他">其他</option>
                </select>
              </div>
            </div>

            {/* Customer Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  客户名称 *
                </label>
                <Input
                  value={formData.customer_name}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_name: e.target.value })
                  }
                  placeholder="输入客户名称"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  客户联系人
                </label>
                <Input
                  value={formData.customer_contact}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      customer_contact: e.target.value,
                    })
                  }
                  placeholder="输入客户联系人"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  客户电话
                </label>
                <Input
                  value={formData.customer_phone}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_phone: e.target.value })
                  }
                  placeholder="输入客户电话"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  客户邮箱
                </label>
                <Input
                  type="email"
                  value={formData.customer_email}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_email: e.target.value })
                  }
                  placeholder="输入客户邮箱"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Project Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  项目编号
                </label>
                <Input
                  value={formData.project_code}
                  onChange={(e) =>
                    setFormData({ ...formData, project_code: e.target.value })
                  }
                  placeholder="输入项目编号"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  项目名称
                </label>
                <Input
                  value={formData.project_name}
                  onChange={(e) =>
                    setFormData({ ...formData, project_name: e.target.value })
                  }
                  placeholder="输入项目名称"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Time and Location */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  沟通日期 *
                </label>
                <Input
                  type="date"
                  value={formData.communication_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      communication_date: e.target.value,
                    })
                  }
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  沟通时间
                </label>
                <Input
                  type="time"
                  value={formData.communication_time}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      communication_time: e.target.value,
                    })
                  }
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  沟通时长（分钟）
                </label>
                <Input
                  type="number"
                  value={formData.duration}
                  onChange={(e) =>
                    setFormData({ ...formData, duration: e.target.value })
                  }
                  placeholder="输入时长"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {formData.communication_type === "现场" && (
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  服务地点
                </label>
                <Input
                  value={formData.location}
                  onChange={(e) =>
                    setFormData({ ...formData, location: e.target.value })
                  }
                  placeholder="输入详细地址"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            )}

            {/* Content */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                沟通主题 *
              </label>
              <Input
                value={formData.subject}
                onChange={(e) =>
                  setFormData({ ...formData, subject: e.target.value })
                }
                placeholder="输入沟通主题"
                className="bg-slate-800/50 border-slate-700"
              />
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                沟通内容 *
              </label>
              <Textarea
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                placeholder="详细记录沟通内容..."
                rows={6}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>

            {/* Follow-up */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.follow_up_required}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      follow_up_required: e.target.checked,
                    })
                  }
                  className="w-4 h-4"
                />
                <label className="text-sm text-slate-400">需要后续跟进</label>
              </div>
              {formData.follow_up_required && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">
                      跟进任务
                    </label>
                    <Input
                      value={formData.follow_up_task}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          follow_up_task: e.target.value,
                        })
                      }
                      placeholder="输入跟进任务描述"
                      className="bg-slate-800/50 border-slate-700"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">
                      截止日期
                    </label>
                    <Input
                      type="date"
                      value={formData.follow_up_due_date}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          follow_up_due_date: e.target.value,
                        })
                      }
                      className="bg-slate-800/50 border-slate-700"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Tags and Importance */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  标签
                </label>
                <div className="flex gap-2">
                  <Input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleAddTag()}
                    placeholder="输入标签后按回车"
                    className="bg-slate-800/50 border-slate-700"
                  />
                  <Button variant="outline" size="sm" onClick={handleAddTag}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.tags.map((tag, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="text-xs"
                      >
                        {tag}
                        <XCircle
                          className="w-3 h-3 ml-1 cursor-pointer"
                          onClick={() => handleRemoveTag(tag)}
                        />
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  重要性
                </label>
                <select
                  value={formData.importance}
                  onChange={(e) =>
                    setFormData({ ...formData, importance: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="低">低</option>
                  <option value="中">中</option>
                  <option value="高">高</option>
                </select>
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit}>
            <Send className="w-4 h-4 mr-2" />
            创建记录
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Communication Detail Dialog Component
function CommunicationDetailDialog({ communication, onClose, onUpdate }) {
  const typeConfig =
    communicationTypeConfig[communication.communication_type] ||
    communicationTypeConfig["其他"];
  const TypeIcon = typeConfig.icon;
  const importance =
    importanceConfig[communication.importance] || importanceConfig["中"];
  const topic = topicConfig[communication.topic] || topicConfig["其他"];

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="font-mono">{communication.communication_no}</span>
            <Badge className={cn(typeConfig.bg, typeConfig.color, "text-xs")}>
              <TypeIcon className="w-3 h-3 mr-1" />
              {typeConfig.label}
            </Badge>
            <Badge className={cn(importance.bg, importance.color, "text-xs")}>
              {importance.label}
            </Badge>
          </DialogTitle>
          <DialogDescription>客户沟通记录详情</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">客户名称</p>
                <p className="text-white">{communication.customer_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">客户联系人</p>
                <p className="text-white">
                  {communication.customer_contact || "-"}
                </p>
              </div>
              {communication.customer_phone && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户电话</p>
                  <p className="text-white">{communication.customer_phone}</p>
                </div>
              )}
              {communication.customer_email && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户邮箱</p>
                  <p className="text-white">{communication.customer_email}</p>
                </div>
              )}
            </div>

            {/* Project Info */}
            {communication.project_name && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">项目编号</p>
                  <p className="text-white">
                    {communication.project_code || "-"}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">项目名称</p>
                  <p className="text-white">{communication.project_name}</p>
                </div>
              </div>
            )}

            {/* Communication Info */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">沟通日期</p>
                <p className="text-white">{communication.communication_date}</p>
              </div>
              {communication.communication_time && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">沟通时间</p>
                  <p className="text-white">
                    {communication.communication_time}
                  </p>
                </div>
              )}
              {communication.duration && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">沟通时长</p>
                  <p className="text-white">{communication.duration}分钟</p>
                </div>
              )}
            </div>

            {communication.location && (
              <div>
                <p className="text-sm text-slate-400 mb-1">服务地点</p>
                <p className="text-white">{communication.location}</p>
              </div>
            )}

            {/* Content */}
            <div>
              <p className="text-sm text-slate-400 mb-1">沟通主题</p>
              <p className="text-white font-medium">{communication.subject}</p>
            </div>

            <div>
              <p className="text-sm text-slate-400 mb-1">沟通内容</p>
              <p className="text-white bg-slate-800/50 p-3 rounded-lg whitespace-pre-wrap">
                {communication.content}
              </p>
            </div>

            {/* Tags */}
            {communication.tags && communication.tags.length > 0 && (
              <div>
                <p className="text-sm text-slate-400 mb-2">标签</p>
                <div className="flex flex-wrap gap-2">
                  {communication.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      <Tag className="w-3 h-3 mr-1" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Follow-up */}
            {communication.follow_up_required && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-sm text-amber-400 font-medium mb-2">
                  后续跟进
                </p>
                {communication.follow_up_task && (
                  <p className="text-white mb-1">
                    跟进任务: {communication.follow_up_task}
                  </p>
                )}
                {communication.follow_up_due_date && (
                  <p className="text-slate-400 text-sm">
                    截止日期: {communication.follow_up_due_date}
                  </p>
                )}
                {communication.follow_up_status && (
                  <Badge
                    className={cn(
                      "text-xs mt-2",
                      communication.follow_up_status === "待处理"
                        ? "bg-amber-500/20 text-amber-400"
                        : "bg-emerald-500/20 text-emerald-400",
                    )}
                  >
                    {communication.follow_up_status}
                  </Badge>
                )}
              </div>
            )}

            {/* Metadata */}
            <div className="pt-4 border-t border-slate-700">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>创建人: {communication.created_by}</span>
                <span>创建时间: {communication.created_at}</span>
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
