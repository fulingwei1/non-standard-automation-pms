/**
 * 需求调研管理
 * 管理客户需求调研记录、现场勘察、问题跟踪
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ClipboardList,
  Search,
  Filter,
  Plus,
  Calendar,
  Clock,
  Users,
  Building2,
  MapPin,
  Phone,
  Video,
  Eye,
  Edit,
  Trash2,
  MoreHorizontal,
  ChevronRight,
  FileText,
  Image,
  CheckCircle,
  XCircle,
  AlertTriangle,
  MessageSquare,
  Paperclip,
  Camera,
  Upload,
  X,
  User,
  Briefcase,
  Target,
  Package,
  Settings,
  Ruler,
  Thermometer,
  Zap,
  DollarSign,
  HelpCircle,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi } from "../services/api";

// 调研方式配置
const surveyMethods = [
  { id: "onsite", name: "现场调研", icon: MapPin, color: "text-emerald-400" },
  { id: "remote", name: "远程调研", icon: Video, color: "text-blue-400" },
  { id: "phone", name: "电话调研", icon: Phone, color: "text-amber-400" },
];

// 调研状态配置
const surveyStatuses = [
  { id: "all", name: "全部", color: "bg-slate-500" },
  { id: "scheduled", name: "已排期", color: "bg-blue-500" },
  { id: "in_progress", name: "进行中", color: "bg-amber-500" },
  { id: "completed", name: "已完成", color: "bg-emerald-500" },
  { id: "cancelled", name: "已取消", color: "bg-red-500" },
];

// Mock 调研数据
// Mock data - 已移除，使用真实API
// 获取状态样式
const getStatusStyle = (status) => {
  const config = surveyStatuses.find((s) => s.id === status);
  return config?.color || "bg-slate-500";
};

// 获取状态名称
const getStatusName = (status) => {
  const config = surveyStatuses.find((s) => s.id === status);
  return config?.name || status;
};

// 获取调研方式图标
const getMethodIcon = (method) => {
  const config = surveyMethods.find((m) => m.id === method);
  return config || surveyMethods[0];
};

// 调研卡片组件
function SurveyCard({ survey, onClick }) {
  const methodConfig = getMethodIcon(survey.method);
  const MethodIcon = methodConfig.icon;

  return (
    <motion.div
      variants={fadeIn}
      className="p-4 rounded-xl bg-surface-100/50 backdrop-blur-lg border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group"
      onClick={() => onClick(survey)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", getStatusStyle(survey.status))}>
              {getStatusName(survey.status)}
            </Badge>
            <span className="text-xs text-slate-500">{survey.code}</span>
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors">
            {survey.customer}
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">{survey.opportunity}</p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem>
              <FileText className="w-4 h-4 mr-2" />
              生成方案
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-400">
              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <p className="text-xs text-slate-500 line-clamp-2 mb-3">
        {survey.summary}
      </p>

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <MethodIcon className={cn("w-3 h-3", methodConfig.color)} />
          {survey.methodName}
        </span>
        <span className="flex items-center gap-1">
          <User className="w-3 h-3" />
          {survey.contactPerson}
        </span>
      </div>

      {survey.pendingQuestions.length > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="w-3 h-3 text-amber-400" />
          <span className="text-xs text-amber-400">
            {survey.pendingQuestions.length} 个待确认问题
          </span>
        </div>
      )}

      <div className="flex items-center justify-between text-xs pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {survey.scheduledDate}
          </span>
          <span className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {survey.engineer}
          </span>
        </div>
        {survey.attachments.length > 0 && (
          <span className="flex items-center gap-1 text-slate-500">
            <Paperclip className="w-3 h-3" />
            {survey.attachments.length}
          </span>
        )}
      </div>
    </motion.div>
  );
}

// 调研详情面板
function SurveyDetailPanel({ survey, onClose }) {
  if (!survey) return null;

  const methodConfig = getMethodIcon(survey.method);
  const MethodIcon = methodConfig.icon;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge className={cn("text-xs", getStatusStyle(survey.status))}>
                {getStatusName(survey.status)}
              </Badge>
              <span className="text-xs text-slate-500">{survey.code}</span>
            </div>
            <h2 className="text-lg font-semibold text-white">
              {survey.customer}
            </h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5 text-slate-400" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
          {/* 基本信息 */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">基本信息</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">调研方式</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <MethodIcon className={cn("w-4 h-4", methodConfig.color)} />
                  {survey.methodName}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">调研日期</p>
                <p className="text-sm text-white">{survey.scheduledDate}</p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">联系人</p>
                <p className="text-sm text-white">{survey.contactPerson}</p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">联系电话</p>
                <p className="text-sm text-white">{survey.contactPhone}</p>
              </div>
            </div>
            {survey.location && (
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">调研地点</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-primary" />
                  {survey.location}
                </p>
              </div>
            )}
          </div>

          {/* 调研摘要 */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">调研摘要</h4>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {survey.summary}
            </p>
          </div>

          {/* 产品信息 */}
          {survey.productInfo && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Package className="w-4 h-4 text-primary" />
                产品信息
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">产品名称</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.name}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">型号规格</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.model}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">外形尺寸</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.size}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">材质</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.material}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 测试需求 */}
          {survey.testRequirements.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Settings className="w-4 h-4 text-primary" />
                测试需求
              </h4>
              <div className="flex flex-wrap gap-2">
                {survey.testRequirements.map((item, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 产能需求 */}
          {survey.capacityRequirements && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Target className="w-4 h-4 text-primary" />
                产能需求
              </h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-surface-50 p-3 rounded-lg text-center">
                  <p className="text-xs text-slate-500 mb-1">年产量</p>
                  <p className="text-lg font-bold text-white">
                    {(survey.capacityRequirements.annual / 10000).toFixed(0)}万
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg text-center">
                  <p className="text-xs text-slate-500 mb-1">日产量</p>
                  <p className="text-lg font-bold text-white">
                    {survey.capacityRequirements.daily}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg text-center">
                  <p className="text-xs text-slate-500 mb-1">UPH</p>
                  <p className="text-lg font-bold text-white">
                    {survey.capacityRequirements.uph}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 场地条件 */}
          {survey.siteConditions && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-primary" />
                场地条件
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <Ruler className="w-3 h-3" />
                    可用面积
                  </p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.area}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    电源
                  </p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.power}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">气源</p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.airPressure}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <Thermometer className="w-3 h-3" />
                    环境
                  </p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.environment}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 预算和时间 */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 p-4 rounded-lg border border-emerald-500/20">
              <p className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                <DollarSign className="w-3 h-3" />
                预算范围
              </p>
              <p className="text-lg font-bold text-emerald-400">
                {survey.budget}
              </p>
            </div>
            <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 p-4 rounded-lg border border-blue-500/20">
              <p className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                交付时间
              </p>
              <p className="text-lg font-bold text-blue-400">
                {survey.timeline}
              </p>
            </div>
          </div>

          {/* 竞争情况 */}
          {survey.competitors.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400">竞争情况</h4>
              <div className="flex flex-wrap gap-2">
                {survey.competitors.map((item, index) => (
                  <Badge key={index} variant="destructive" className="text-xs">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 待确认问题 */}
          {survey.pendingQuestions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-amber-400 flex items-center gap-2">
                <HelpCircle className="w-4 h-4" />
                待确认问题
              </h4>
              <div className="space-y-2">
                {survey.pendingQuestions.map((question, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 bg-amber-500/10 p-3 rounded-lg border border-amber-500/20"
                  >
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span className="text-sm text-white">{question}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 附件 */}
          {survey.attachments.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Paperclip className="w-4 h-4 text-primary" />
                附件 ({survey.attachments.length})
              </h4>
              <div className="space-y-2">
                {survey.attachments.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-surface-50 p-3 rounded-lg"
                  >
                    <div className="flex items-center gap-2">
                      {file.type === "image" ? (
                        <Image className="w-4 h-4 text-slate-400" />
                      ) : (
                        <FileText className="w-4 h-4 text-slate-400" />
                      )}
                      <span className="text-sm text-white">{file.name}</span>
                      <span className="text-xs text-slate-500">
                        {file.size}
                      </span>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/5 flex gap-2">
          <Button variant="outline" className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            编辑
          </Button>
          <Button className="flex-1">
            <FileText className="w-4 h-4 mr-2" />
            生成方案
          </Button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default function RequirementSurvey() {
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedMethod, setSelectedMethod] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [surveys, setSurveys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Map backend ticket type to frontend method
  const mapTicketTypeToMethod = (ticketType) => {
    const typeMap = {
      REQUIREMENT_RESEARCH: "onsite",
      TECHNICAL_EXCHANGE: "remote",
      SITE_VISIT: "onsite",
    };
    return typeMap[ticketType] || "onsite";
  };

  // Map backend status to frontend status
  const mapTicketStatus = (backendStatus) => {
    const statusMap = {
      PENDING: "scheduled",
      ACCEPTED: "scheduled",
      IN_PROGRESS: "in_progress",
      COMPLETED: "completed",
      CANCELLED: "cancelled",
    };
    return statusMap[backendStatus] || "scheduled";
  };

  // Load surveys from API
  const loadSurveys = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100,
        ticket_type: "REQUIREMENT_RESEARCH,TECHNICAL_EXCHANGE,SITE_VISIT",
      };

      if (selectedStatus !== "all") {
        const statusMap = {
          scheduled: "PENDING,ACCEPTED",
          in_progress: "IN_PROGRESS",
          completed: "COMPLETED",
          cancelled: "CANCELLED",
        };
        params.status = statusMap[selectedStatus] || selectedStatus;
      }

      if (searchTerm) {
        params.keyword = searchTerm;
      }

      const response = await presaleApi.tickets.list(params);
      const ticketsData = response.data?.items || response.data || [];

      // Transform tickets to surveys
      const transformedSurveys = ticketsData.map((ticket) => {
        const method = mapTicketTypeToMethod(ticket.ticket_type);
        const methodConfig =
          surveyMethods.find((m) => m.id === method) || surveyMethods[0];
        return {
          id: ticket.id,
          code: ticket.ticket_no || `SUR-${ticket.id}`,
          customer: ticket.customer_name || "",
          customerId: ticket.customer_id,
          contactPerson: ticket.applicant_name || "",
          contactPhone: "",
          method,
          methodName: methodConfig.name,
          status: mapTicketStatus(ticket.status),
          scheduledDate: ticket.expected_date || ticket.apply_time || "",
          completedDate: ticket.complete_time || null,
          location: ticket.description || "",
          engineer: ticket.assignee_name || ticket.owner_name || "",
          salesPerson: ticket.applicant_name || "",
          opportunity: ticket.opportunity_name || "",
          opportunityId: ticket.opportunity_id,
          summary: ticket.description || ticket.requirement || "",
          productInfo: null,
          testRequirements: [],
          capacityRequirements: null,
          siteConditions: null,
          budget: "",
          timeline: ticket.deadline || "",
          competitors: [],
          pendingQuestions: [],
          attachments: [],
          comments: 0,
        };
      });

      setSurveys(transformedSurveys);
    } catch (err) {
      console.error("Failed to load surveys:", err);
      setError(err.response?.data?.detail || err.message || "加载调研记录失败");
      setSurveys([]);
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, searchTerm]);

  useEffect(() => {
    loadSurveys();
  }, [loadSurveys]);

  // 筛选调研记录
  const filteredSurveys = surveys.filter((survey) => {
    const matchesStatus =
      selectedStatus === "all" || survey.status === selectedStatus;
    const matchesMethod =
      selectedMethod === "all" || survey.method === selectedMethod;
    const matchesSearch =
      survey.customer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      survey.opportunity.toLowerCase().includes(searchTerm.toLowerCase()) ||
      survey.code.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesMethod && matchesSearch;
  });

  // 统计数据
  const stats = {
    total: surveys.length,
    scheduled: surveys.filter((s) => s.status === "scheduled").length,
    completed: surveys.filter((s) => s.status === "completed").length,
    pendingQuestions: surveys.reduce(
      (acc, s) => acc + s.pendingQuestions.length,
      0,
    ),
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="需求调研"
        description="管理客户需求调研记录、现场勘察、问题跟踪"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              新建调研
            </Button>
          </motion.div>
        }
      />

      {/* 统计卡片 */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-500/10 flex items-center justify-center">
                <ClipboardList className="w-5 h-5 text-slate-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">全部调研</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">已排期</p>
                <p className="text-2xl font-bold text-blue-400">
                  {stats.scheduled}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">已完成</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {stats.completed}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">待确认问题</p>
                <p className="text-2xl font-bold text-amber-400">
                  {stats.pendingQuestions}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4"
      >
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 搜索 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder="搜索客户、商机、调研编号..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full"
            />
          </div>

          {/* 筛选 */}
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {surveyStatuses.map((status) => (
                <option key={status.id} value={status.id}>
                  {status.name}
                </option>
              ))}
            </select>
            <select
              value={selectedMethod}
              onChange={(e) => setSelectedMethod(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">全部方式</option>
              {surveyMethods.map((method) => (
                <option key={method.id} value={method.id}>
                  {method.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-16 text-slate-400">
          <ClipboardList className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
        </div>
      )}

      {/* 错误提示 */}
      {error && !loading && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* 调研列表 */}
      {!loading && !error && (
        <motion.div
          variants={fadeIn}
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          {filteredSurveys.length > 0 ? (
            filteredSurveys.map((survey) => (
              <SurveyCard
                key={survey.id}
                survey={survey}
                onClick={setSelectedSurvey}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-16 text-slate-400">
              <ClipboardList className="w-12 h-12 mx-auto mb-4 text-slate-600" />
              <p className="text-lg font-medium">暂无调研记录</p>
              <p className="text-sm">请调整筛选条件或创建新调研</p>
            </div>
          )}
        </motion.div>
      )}

      {/* 调研详情面板 */}
      {selectedSurvey && (
        <SurveyDetailPanel
          survey={selectedSurvey}
          onClose={() => setSelectedSurvey(null)}
        />
      )}
    </motion.div>
  );
}
