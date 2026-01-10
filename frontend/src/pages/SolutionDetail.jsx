/**
 * 方案详情页面
 * 展示方案完整信息、技术规格、设备配置、成本估算等
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  FileText,
  ArrowLeft,
  Calendar,
  Clock,
  Users,
  Building2,
  Edit,
  Copy,
  Download,
  Share2,
  Archive,
  Trash2,
  MoreHorizontal,
  Briefcase,
  DollarSign,
  Tag,
  History,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileCheck,
  Eye,
  MessageSquare,
  Paperclip,
  Upload,
  ChevronRight,
  Package,
  Cpu,
  Settings,
  Wrench,
  Box,
  BarChart3,
  TrendingUp,
  User,
  GitBranch,
  Send,
  Target,
  ExternalLink,
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

// Mock 方案详情数据
// Mock data - 已移除，使用真实API
// 获取状态样式
const getStatusStyle = (status) => {
  switch (status) {
    case "draft":
      return { bg: "bg-slate-500", text: "草稿" };
    case "in_progress":
      return { bg: "bg-blue-500", text: "编写中" };
    case "reviewing":
      return { bg: "bg-amber-500", text: "评审中" };
    case "published":
      return { bg: "bg-emerald-500", text: "已发布" };
    case "archived":
      return { bg: "bg-slate-600", text: "已归档" };
    default:
      return { bg: "bg-slate-500", text: status };
  }
};

// 获取交付物状态样式
const getDeliverableStatus = (status) => {
  switch (status) {
    case "completed":
      return { icon: CheckCircle, color: "text-emerald-500", text: "已完成" };
    case "in_progress":
      return { icon: Clock, color: "text-blue-500", text: "进行中" };
    case "pending":
      return { icon: AlertTriangle, color: "text-slate-500", text: "待开始" };
    default:
      return { icon: AlertTriangle, color: "text-slate-500", text: status };
  }
};

// Tab 配置
const tabs = [
  { id: "overview", name: "概览", icon: FileText },
  { id: "specs", name: "技术规格", icon: Cpu },
  { id: "equipment", name: "设备配置", icon: Package },
  { id: "deliverables", name: "交付物", icon: Paperclip },
  { id: "cost", name: "成本估算", icon: DollarSign },
  { id: "history", name: "版本历史", icon: History },
];

export default function SolutionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const [solution, setSolution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [costEstimate, setCostEstimate] = useState(null);

  // Load solution detail
  const loadSolution = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      // Load solution detail
      const solutionResponse = await presaleApi.solutions.get(id);
      const solutionData = solutionResponse.data;

      // Load cost estimate if available
      let costData = null;
      try {
        const costResponse = await presaleApi.solutions.getCost(id);
        costData = costResponse.data;
      } catch (err) {
        // Cost estimate may not exist, ignore error
      }

      // Transform solution data
      const transformedSolution = {
        id: solutionData.id,
        code: solutionData.solution_no || `SOL-${solutionData.id}`,
        name: solutionData.name || "",
        customer: solutionData.customer_name || "",
        customerId: solutionData.customer_id,
        version: solutionData.version || "V1.0",
        status: solutionData.status?.toLowerCase() || "draft",
        deviceType: solutionData.solution_type?.toLowerCase() || "",
        deviceTypeName: solutionData.solution_type || "",
        progress: solutionData.progress || 0,
        amount: solutionData.estimated_cost
          ? solutionData.estimated_cost / 10000
          : solutionData.suggested_price
            ? solutionData.suggested_price / 10000
            : 0,
        deadline: solutionData.deadline || "",
        createdAt: solutionData.created_at || "",
        updatedAt: solutionData.updated_at || solutionData.created_at || "",
        creator: solutionData.creator_name || "",
        opportunity: solutionData.opportunity_name || "",
        opportunityId: solutionData.opportunity_id,
        salesPerson: solutionData.sales_person_name || "",
        tags: solutionData.tags || [],
        description: solutionData.description || "",
        techSpecs: solutionData.tech_specs || {},
        equipment: solutionData.equipment || {},
        deliverables: solutionData.deliverables || [],
        versionHistory: [],
        reviews: [],
        collaborators: [],
      };

      setSolution(transformedSolution);
      setCostEstimate(costData);
    } catch (err) {
      console.error("Failed to load solution:", err);
      setError(err.response?.data?.detail || err.message || "加载方案详情失败");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadSolution();
  }, [loadSolution]);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="方案详情" description="加载中..." />
        <div className="text-center py-16 text-slate-400">
          <FileText className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
        </div>
      </div>
    );
  }

  if (error || !solution) {
    return (
      <div className="space-y-6">
        <PageHeader title="方案详情" description="加载失败" />
        <div className="text-center py-16 text-red-400">
          <div className="text-lg font-medium">加载失败</div>
          <div className="text-sm mt-2">{error || "方案不存在"}</div>
          <Button className="mt-4" onClick={() => navigate("/solutions")}>
            返回方案列表
          </Button>
        </div>
      </div>
    );
  }

  const statusStyle = getStatusStyle(solution.status);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 返回按钮和头部 */}
      <motion.div variants={fadeIn} className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/solutions")}
          className="text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <Badge className={cn("text-xs", statusStyle.bg)}>
              {statusStyle.text}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {solution.version}
            </Badge>
            <span className="text-sm text-slate-500">{solution.code}</span>
          </div>
          <h1 className="text-2xl font-bold text-white">{solution.name}</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="flex items-center gap-2">
            <Share2 className="w-4 h-4" />
            分享
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="w-4 h-4" />
            导出
          </Button>
          <Button className="flex items-center gap-2">
            <Edit className="w-4 h-4" />
            编辑
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Copy className="w-4 h-4 mr-2" />
                复制方案
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Send className="w-4 h-4 mr-2" />
                提交评审
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <Archive className="w-4 h-4 mr-2" />
                归档
              </DropdownMenuItem>
              <DropdownMenuItem className="text-red-400">
                <Trash2 className="w-4 h-4 mr-2" />
                删除
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </motion.div>

      {/* 基本信息卡片 */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Building2 className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">客户</p>
                <p className="text-sm font-medium text-white">
                  {solution.customer}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                <Briefcase className="w-5 h-5 text-violet-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">设备类型</p>
                <p className="text-sm font-medium text-white">
                  {solution.deviceTypeName}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">方案金额</p>
                <p className="text-sm font-medium text-emerald-400">
                  ¥{solution.amount}万
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">截止时间</p>
                <p className="text-sm font-medium text-white">
                  {solution.deadline}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 进度条 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">方案进度</span>
              <span className="text-sm font-medium text-white">
                {solution.progress}%
              </span>
            </div>
            <Progress value={solution.progress} className="h-2" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Tab 导航 */}
      <motion.div variants={fadeIn}>
        <div className="flex overflow-x-auto custom-scrollbar pb-2 gap-1 border-b border-white/5">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "ghost"}
              size="sm"
              onClick={() => setActiveTab(tab.id)}
              className="flex items-center gap-2 whitespace-nowrap"
            >
              <tab.icon className="w-4 h-4" />
              {tab.name}
            </Button>
          ))}
        </div>
      </motion.div>

      {/* Tab 内容 */}
      <motion.div variants={fadeIn}>
        {/* 概览 Tab */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧 - 描述和标签 */}
            <div className="lg:col-span-2 space-y-6">
              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                  <CardTitle className="text-lg">方案描述</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {solution.description}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {solution.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 关联商机 */}
              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Target className="w-5 h-5 text-primary" />
                    关联商机
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Briefcase className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">
                          {solution.opportunity}
                        </p>
                        <p className="text-xs text-slate-500">
                          销售：{solution.salesPerson}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* 评审状态 */}
              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-primary" />
                    评审记录
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {solution.reviews.map((review) => (
                    <div key={review.id} className="flex gap-3">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-primary/20 text-primary text-sm">
                          {review.avatar}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-white">
                            {review.reviewer}
                          </span>
                          <span className="text-xs text-slate-500">
                            {review.date}
                          </span>
                          <Badge
                            className={cn(
                              "text-xs",
                              review.status === "approved"
                                ? "bg-emerald-500"
                                : review.status === "pending"
                                  ? "bg-amber-500"
                                  : "bg-red-500",
                            )}
                          >
                            {review.status === "approved"
                              ? "已通过"
                              : review.status === "pending"
                                ? "待审核"
                                : "需修改"}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-400">
                          {review.comments}
                        </p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* 右侧 - 协作人员和元数据 */}
            <div className="space-y-6">
              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Users className="w-5 h-5 text-primary" />
                    协作人员
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {solution.collaborators.map((person, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-primary/20 text-primary text-sm">
                          {person.avatar}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-sm font-medium text-white">
                          {person.name}
                        </p>
                        <p className="text-xs text-slate-500">{person.role}</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                  <CardTitle className="text-lg">详细信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">创建人</span>
                    <span className="text-white">{solution.creator}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">创建时间</span>
                    <span className="text-white">{solution.createdAt}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">更新时间</span>
                    <span className="text-white">{solution.updatedAt}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">当前版本</span>
                    <span className="text-white">{solution.version}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* 技术规格 Tab */}
        {activeTab === "specs" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
              <CardHeader>
                <CardTitle className="text-lg">产品信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {Object.entries(solution.techSpecs.productInfo).map(
                  ([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-slate-500">
                        {key === "name"
                          ? "产品名称"
                          : key === "model"
                            ? "型号规格"
                            : key === "size"
                              ? "外形尺寸"
                              : key === "weight"
                                ? "重量"
                                : "材质"}
                      </span>
                      <span className="text-white">{value}</span>
                    </div>
                  ),
                )}
              </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
              <CardHeader>
                <CardTitle className="text-lg">产能参数</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">UPH</span>
                  <span className="text-white">
                    {solution.techSpecs.capacity.uph} pcs/h
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">节拍</span>
                  <span className="text-white">
                    {solution.techSpecs.capacity.cycleTime} 秒/件
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">日产能</span>
                  <span className="text-white">
                    {solution.techSpecs.capacity.dailyOutput} pcs
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">测试通道</span>
                  <span className="text-white">
                    {solution.techSpecs.capacity.channels} 通道
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
              <CardHeader>
                <CardTitle className="text-lg">测试项目</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {solution.techSpecs.testItems.map((item, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {item}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
              <CardHeader>
                <CardTitle className="text-lg">执行标准</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {solution.techSpecs.testStandards.map((standard, index) => (
                    <Badge key={index} className="text-xs bg-blue-500">
                      {standard}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 bg-surface-100/50 backdrop-blur-lg border border-white/5">
              <CardHeader>
                <CardTitle className="text-lg">环境要求</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {Object.entries(solution.techSpecs.environment).map(
                    ([key, value]) => (
                      <div
                        key={key}
                        className="text-center p-3 bg-surface-50 rounded-lg"
                      >
                        <p className="text-xs text-slate-500 mb-1">
                          {key === "temperature"
                            ? "温度范围"
                            : key === "humidity"
                              ? "湿度范围"
                              : key === "power"
                                ? "电源"
                                : key === "airPressure"
                                  ? "气压"
                                  : "占地面积"}
                        </p>
                        <p className="text-sm font-medium text-white">
                          {value}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 设备配置 Tab */}
        {activeTab === "equipment" && (
          <div className="space-y-6">
            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Package className="w-5 h-5 text-primary" />
                  主要设备
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-xs text-slate-400 border-b border-white/5">
                      <tr>
                        <th className="text-left py-2">设备名称</th>
                        <th className="text-left py-2">型号规格</th>
                        <th className="text-right py-2">数量</th>
                        <th className="text-right py-2">单价</th>
                        <th className="text-right py-2">总价</th>
                      </tr>
                    </thead>
                    <tbody>
                      {solution.equipment.main.map((item, index) => (
                        <tr key={index} className="border-b border-white/5">
                          <td className="py-3 text-white">{item.name}</td>
                          <td className="py-3 text-slate-400">{item.model}</td>
                          <td className="py-3 text-right text-white">
                            {item.qty}
                          </td>
                          <td className="py-3 text-right text-slate-400">
                            ¥{item.unitPrice.toLocaleString()}
                          </td>
                          <td className="py-3 text-right text-emerald-400">
                            ¥{item.totalPrice.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Settings className="w-5 h-5 text-primary" />
                  配套设备
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-xs text-slate-400 border-b border-white/5">
                      <tr>
                        <th className="text-left py-2">设备名称</th>
                        <th className="text-left py-2">型号规格</th>
                        <th className="text-right py-2">数量</th>
                        <th className="text-right py-2">单价</th>
                        <th className="text-right py-2">总价</th>
                      </tr>
                    </thead>
                    <tbody>
                      {solution.equipment.auxiliary.map((item, index) => (
                        <tr key={index} className="border-b border-white/5">
                          <td className="py-3 text-white">{item.name}</td>
                          <td className="py-3 text-slate-400">{item.model}</td>
                          <td className="py-3 text-right text-white">
                            {item.qty}
                          </td>
                          <td className="py-3 text-right text-slate-400">
                            ¥{item.unitPrice.toLocaleString()}
                          </td>
                          <td className="py-3 text-right text-emerald-400">
                            ¥{item.totalPrice.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-primary" />
                    软件系统
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {solution.equipment.software.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-surface-50 rounded-lg"
                    >
                      <div>
                        <p className="text-sm font-medium text-white">
                          {item.name}
                        </p>
                        <p className="text-xs text-slate-500">{item.version}</p>
                      </div>
                      <span className="text-sm text-emerald-400">
                        ¥{item.price.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Wrench className="w-5 h-5 text-primary" />
                    治具夹具
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {solution.equipment.fixtures.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-surface-50 rounded-lg"
                    >
                      <div>
                        <p className="text-sm font-medium text-white">
                          {item.name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {item.model} × {item.qty}
                        </p>
                      </div>
                      <span className="text-sm text-emerald-400">
                        ¥{item.totalPrice.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* 成本估算 Tab */}
        {activeTab === "cost" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {costEstimate ? (
              <>
                <Card className="lg:col-span-2 bg-surface-100/50 backdrop-blur-lg border border-white/5">
                  <CardHeader>
                    <CardTitle className="text-lg">成本明细</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {[
                        {
                          name: "硬件成本",
                          value: costEstimate.hardware_cost || 0,
                          color: "bg-blue-500",
                        },
                        {
                          name: "软件成本",
                          value: costEstimate.software_cost || 0,
                          color: "bg-violet-500",
                        },
                        {
                          name: "治具成本",
                          value: costEstimate.fixture_cost || 0,
                          color: "bg-amber-500",
                        },
                        {
                          name: "安装调试",
                          value: costEstimate.installation_cost || 0,
                          color: "bg-emerald-500",
                        },
                        {
                          name: "培训费用",
                          value: costEstimate.training_cost || 0,
                          color: "bg-pink-500",
                        },
                        {
                          name: "运输费用",
                          value: costEstimate.shipping_cost || 0,
                          color: "bg-slate-500",
                        },
                      ].map((item, index) => {
                        const total = costEstimate.total_cost || 1;
                        return (
                          <div key={index} className="flex items-center gap-4">
                            <div className="w-24 text-sm text-slate-400">
                              {item.name}
                            </div>
                            <div className="flex-1">
                              <Progress
                                value={(item.value / total) * 100}
                                className="h-2"
                              />
                            </div>
                            <div className="w-28 text-right text-sm text-white">
                              ¥{item.value.toLocaleString()}
                            </div>
                          </div>
                        );
                      })}
                      <div className="flex items-center gap-4 pt-4 border-t border-white/5">
                        <div className="w-24 text-sm font-medium text-white">
                          总成本
                        </div>
                        <div className="flex-1" />
                        <div className="w-28 text-right text-lg font-bold text-white">
                          ¥{(costEstimate.total_cost || 0).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20">
                  <CardHeader>
                    <CardTitle className="text-lg text-emerald-400">
                      利润分析
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="text-center p-4 bg-surface-50/50 rounded-lg">
                      <p className="text-sm text-slate-400 mb-1">报价金额</p>
                      <p className="text-3xl font-bold text-white">
                        ¥{(costEstimate.suggested_price || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-surface-50/50 rounded-lg">
                        <p className="text-xs text-slate-400 mb-1">毛利率</p>
                        <p className="text-xl font-bold text-emerald-400">
                          {(costEstimate.gross_margin || 0).toFixed(0)}%
                        </p>
                      </div>
                      <div className="text-center p-3 bg-surface-50/50 rounded-lg">
                        <p className="text-xs text-slate-400 mb-1">预计利润</p>
                        <p className="text-xl font-bold text-emerald-400">
                          ¥
                          {(
                            (costEstimate.suggested_price || 0) -
                            (costEstimate.total_cost || 0)
                          ).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <div className="col-span-full text-center py-16 text-slate-400">
                <Calculator className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                <p className="text-lg font-medium">暂无成本估算</p>
                <p className="text-sm">请先进行成本核算</p>
              </div>
            )}
          </div>
        )}

        {/* 交付物 Tab */}
        {activeTab === "deliverables" && (
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">交付物清单</CardTitle>
              <Button size="sm" className="flex items-center gap-2">
                <Upload className="w-4 h-4" />
                上传文件
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {solution.deliverables.map((item) => {
                  const statusConfig = getDeliverableStatus(item.status);
                  const StatusIcon = statusConfig.icon;
                  return (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-4 bg-surface-50 rounded-lg hover:bg-white/[0.03] transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">
                            {item.name}
                          </p>
                          {item.file ? (
                            <p className="text-xs text-slate-500">
                              {item.file} ({item.size})
                            </p>
                          ) : (
                            <p className="text-xs text-slate-500">待上传</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <StatusIcon
                            className={cn("w-4 h-4", statusConfig.color)}
                          />
                          <span className={cn("text-xs", statusConfig.color)}>
                            {statusConfig.text}
                          </span>
                        </div>
                        {item.file && (
                          <Button variant="ghost" size="sm">
                            <Download className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 版本历史 Tab */}
        {activeTab === "history" && (
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-primary" />
                版本历史
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {solution.versionHistory.map((version, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div
                        className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center",
                          index === 0 ? "bg-primary" : "bg-slate-600",
                        )}
                      >
                        <History className="w-4 h-4 text-white" />
                      </div>
                      {index < solution.versionHistory.length - 1 && (
                        <div className="w-px h-full bg-slate-700 my-2" />
                      )}
                    </div>
                    <div className="flex-1 pb-6">
                      <div className="flex items-center gap-3 mb-1">
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            index === 0 && "border-primary text-primary",
                          )}
                        >
                          {version.version}
                        </Badge>
                        <span className="text-sm text-slate-400">
                          {version.date}
                        </span>
                        <span className="text-sm text-slate-500">
                          by {version.author}
                        </span>
                      </div>
                      <p className="text-sm text-white">{version.changes}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </motion.div>
    </motion.div>
  );
}
