/**
 * 方案管理中心
 * 技术方案列表、筛选、搜索
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import {
  FileText,
  Search,
  Filter,
  Plus,
  Calendar,
  Clock,
  Users,
  Building2,
  Target,
  Eye,
  Edit,
  Copy,
  Archive,
  Trash2,
  MoreHorizontal,
  ChevronRight,
  LayoutGrid,
  List,
  Briefcase,
  DollarSign,
  Tag,
  History,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileCheck,
  Download,
  Share2 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger } from
"../components/ui/dropdown-menu";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi } from "../services/api";

// 方案状态配置
const solutionStatuses = [
{ id: "all", name: "全部", color: "bg-slate-500" },
{ id: "draft", name: "草稿", color: "bg-slate-500" },
{ id: "in_progress", name: "编写中", color: "bg-blue-500" },
{ id: "reviewing", name: "评审中", color: "bg-amber-500" },
{ id: "published", name: "已发布", color: "bg-emerald-500" },
{ id: "archived", name: "已归档", color: "bg-slate-600" }];


// 设备类型配置
const deviceTypes = [
{ id: "all", name: "全部类型" },
{ id: "ict", name: "ICT测试设备" },
{ id: "fct", name: "FCT功能测试" },
{ id: "eol", name: "EOL测试设备" },
{ id: "aging", name: "老化设备" },
{ id: "burning", name: "烧录设备" },
{ id: "vision", name: "视觉检测" },
{ id: "assembly", name: "组装线" },
{ id: "hybrid", name: "综合测试线" }];


// Mock 方案数据
// Mock data - 已移除，使用真实API
// 获取状态样式
const getStatusStyle = (status) => {
  const config = (solutionStatuses || []).find((s) => s.id === status);
  return config?.color || "bg-slate-500";
};

// 获取状态名称
const getStatusName = (status) => {
  const config = (solutionStatuses || []).find((s) => s.id === status);
  return config?.name || status;
};

// 方案卡片组件
function SolutionCard({ solution, onView }) {
  const _navigate = useNavigate();

  return (
    <motion.div
      variants={fadeIn}
      className="p-4 rounded-xl bg-surface-100/50 backdrop-blur-lg border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group"
      onClick={() => onView(solution)}>

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", getStatusStyle(solution.status))}>
              {getStatusName(solution.status)}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {solution.version}
            </Badge>
            <span className="text-xs text-slate-500">{solution.code}</span>
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors line-clamp-2">
            {solution.name}
          </h4>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}>

              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onView(solution)}>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Copy className="w-4 h-4 mr-2" />
              复制
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Download className="w-4 h-4 mr-2" />
              导出
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

      <p className="text-xs text-slate-500 line-clamp-2 mb-3">
        {solution.description}
      </p>

      <div className="flex items-center gap-2 flex-wrap mb-3">
        {solution.tags.slice(0, 3).map((tag, index) =>
        <span
          key={index}
          className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">

            {tag}
        </span>
        )}
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <Building2 className="w-3 h-3" />
          {solution.customer}
        </span>
        <span className="flex items-center gap-1">
          <Briefcase className="w-3 h-3" />
          {solution.deviceTypeName}
        </span>
      </div>

      {solution.status !== "published" && solution.status !== "archived" &&
      <div className="space-y-1 mb-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">进度</span>
            <span className="text-white">{solution.progress}%</span>
          </div>
          <Progress value={solution.progress} className="h-1.5" />
      </div>
      }

      <div className="flex items-center justify-between text-xs pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {solution.updatedAt}
          </span>
          <span className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {solution.creator}
          </span>
        </div>
        <span className="text-emerald-400 font-medium">
          ¥{solution.amount}万
        </span>
      </div>
    </motion.div>);

}

// 方案表格行组件
function SolutionTableRow({ solution, onView }) {
  return (
    <motion.tr
      variants={fadeIn}
      className="border-b border-white/5 hover:bg-white/[0.03] cursor-pointer group"
      onClick={() => onView(solution)}>

      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <FileText className="w-5 h-5 text-primary" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate group-hover:text-primary transition-colors">
              {solution.name}
            </p>
            <p className="text-xs text-slate-500">{solution.code}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-white">{solution.customer}</span>
        </div>
      </td>
      <td className="px-4 py-3">
        <Badge variant="outline" className="text-xs">
          {solution.deviceTypeName}
        </Badge>
      </td>
      <td className="px-4 py-3">
        <Badge variant="outline" className="text-xs">
          {solution.version}
        </Badge>
      </td>
      <td className="px-4 py-3">
        <Badge className={cn("text-xs", getStatusStyle(solution.status))}>
          {getStatusName(solution.status)}
        </Badge>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Progress value={solution.progress} className="w-16 h-1.5" />
          <span className="text-xs text-slate-400">{solution.progress}%</span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-emerald-400 font-medium">
        ¥{solution.amount}万
      </td>
      <td className="px-4 py-3 text-sm text-slate-400">{solution.updatedAt}</td>
      <td className="px-4 py-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => e.stopPropagation()}>

              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onView(solution)}>
              <Eye className="w-4 h-4 mr-2" />
              查看
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Copy className="w-4 h-4 mr-2" />
              复制
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </td>
    </motion.tr>);

}

export default function SolutionList({ embedded = false } = {}) {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState("grid"); // 'grid', 'list'
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedDeviceType, setSelectedDeviceType] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [solutions, setSolutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    draft: 0,
    inProgress: 0,
    reviewing: 0,
    published: 0
  });

  // Map backend status to frontend status
  const mapSolutionStatus = (backendStatus) => {
    const statusMap = {
      DRAFT: "draft",
      IN_PROGRESS: "in_progress",
      REVIEWING: "reviewing",
      APPROVED: "published",
      SUBMITTED: "published",
      ARCHIVED: "archived"
    };
    return statusMap[backendStatus] || "draft";
  };

  // Load solutions from API
  const loadSolutions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100
      };

      if (selectedStatus !== "all") {
        const statusMap = {
          draft: "DRAFT",
          in_progress: "IN_PROGRESS",
          reviewing: "REVIEWING",
          published: "APPROVED,SUBMITTED",
          archived: "ARCHIVED"
        };
        params.status = statusMap[selectedStatus] || selectedStatus;
      }

      if (searchTerm) {
        params.keyword = searchTerm;
      }

      if (selectedDeviceType !== "all") {
        params.solution_type = selectedDeviceType.toUpperCase();
      }

      const response = await presaleApi.solutions.list(params);
      const solutionsData = response.data?.items || response.data?.items || response.data || [];

      // Transform solutions
      const transformedSolutions = (solutionsData || []).map((solution) => ({
        id: solution.id,
        code: solution.solution_no || `SOL-${solution.id}`,
        name: solution.name || "",
        customer: solution.customer_name || "",
        customerId: solution.customer_id,
        version: solution.version || "V1.0",
        status: mapSolutionStatus(solution.status),
        deviceType: solution.solution_type?.toLowerCase() || "",
        deviceTypeName: solution.solution_type || "",
        progress: solution.progress || 0,
        amount: solution.estimated_cost ?
        solution.estimated_cost / 10000 :
        solution.suggested_price ?
        solution.suggested_price / 10000 :
        0,
        deadline: solution.deadline || "",
        createdAt: solution.created_at || "",
        updatedAt: solution.updated_at || solution.created_at || "",
        creator: solution.creator_name || "",
        opportunity: solution.opportunity_name || "",
        opportunityId: solution.opportunity_id,
        salesPerson: solution.sales_person_name || "",
        tags: solution.tags || [],
        description: solution.description || "",
        deliverables: [],
        reviews: 0,
        comments: 0
      }));

      setSolutions(transformedSolutions);

      // Calculate stats
      const allSolutions = transformedSolutions;
      setStats({
        total: allSolutions.length,
        draft: (allSolutions || []).filter((s) => s.status === "draft").length,
        inProgress: (allSolutions || []).filter((s) => s.status === "in_progress").
        length,
        reviewing: (allSolutions || []).filter((s) => s.status === "reviewing").length,
        published: (allSolutions || []).filter((s) => s.status === "published").length
      });
    } catch (err) {
      console.error("Failed to load solutions:", err);
      setError(err.response?.data?.detail || err.message || "加载方案失败");
      setSolutions([]);
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, searchTerm, selectedDeviceType]);

  useEffect(() => {
    loadSolutions();
  }, [loadSolutions]);

  // 筛选方案
  const filteredSolutions = (solutions || []).filter((solution) => {
    const searchLower = searchTerm.toLowerCase();
    const name = (solution.name || "").toLowerCase();
    const customer = (solution.customer || "").toLowerCase();
    const code = (solution.code || "").toLowerCase();
    const tags = solution.tags || [];

    const matchesSearch =
    name.includes(searchLower) ||
    customer.includes(searchLower) ||
    code.includes(searchLower) ||
    (tags || []).some((tag) => (tag || "").toLowerCase().includes(searchLower));

    return matchesSearch;
  });

  const handleViewSolution = (solution) => {
    navigate(`/solutions/${solution.id}`);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 页面头部 */}
      {!embedded && (
        <PageHeader
          title="方案中心"
          description="管理技术方案、版本控制、协作评审"
          actions={
          <motion.div variants={fadeIn} className="flex gap-2">
              <Button variant="outline" className="flex items-center gap-2">
                <History className="w-4 h-4" />
                历史方案
              </Button>
              <Button className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                新建方案
              </Button>
          </motion.div>
          } />
      )}


      {/* 统计卡片 */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 sm:grid-cols-5 gap-4">

        {[
        {
          label: "全部方案",
          value: stats.total,
          color: "text-white",
          bg: "bg-slate-500/10"
        },
        {
          label: "草稿",
          value: stats.draft,
          color: "text-slate-400",
          bg: "bg-slate-500/10"
        },
        {
          label: "编写中",
          value: stats.inProgress,
          color: "text-blue-400",
          bg: "bg-blue-500/10"
        },
        {
          label: "评审中",
          value: stats.reviewing,
          color: "text-amber-400",
          bg: "bg-amber-500/10"
        },
        {
          label: "已发布",
          value: stats.published,
          color: "text-emerald-400",
          bg: "bg-emerald-500/10"
        }].
        map((stat, index) =>
        <Card
          key={index}
          className="bg-surface-100/50 backdrop-blur-lg border border-white/5 cursor-pointer hover:bg-white/[0.03] transition-colors"
          onClick={() =>
          setSelectedStatus(
            index === 0 ? "all" : solutionStatuses[index].id
          )
          }>

            <CardContent className="p-4">
              <p className="text-xs text-slate-400 mb-1">{stat.label}</p>
              <p className={cn("text-2xl font-bold", stat.color)}>
                {stat.value}
              </p>
            </CardContent>
        </Card>
        )}
      </motion.div>

      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4">

        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 搜索 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder="搜索方案名称、客户、编号、标签..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full" />

          </div>

          {/* 筛选和视图切换 */}
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">

              {(solutionStatuses || []).map((status) =>
              <option key={status.id} value={status.id}>
                  {status.name}
              </option>
              )}
            </select>
            <select
              value={selectedDeviceType}
              onChange={(e) => setSelectedDeviceType(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">

              {(deviceTypes || []).map((type) =>
              <option key={type.id} value={type.id}>
                  {type.name}
              </option>
              )}
            </select>
            <div className="flex bg-surface-50 rounded-lg p-1">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="icon"
                onClick={() => setViewMode("grid")}>

                <LayoutGrid className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "ghost"}
                size="icon"
                onClick={() => setViewMode("list")}>

                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* 加载状态 */}
      {loading &&
      <div className="text-center py-16 text-slate-400">
          <FileText className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
      </div>
      }

      {/* 错误提示 */}
      {error && !loading &&
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
      </div>
      }

      {/* 方案列表 */}
      {!loading &&
      !error && (
      viewMode === "grid" ?
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">

            {filteredSolutions.length > 0 ?
        (filteredSolutions || []).map((solution) =>
        <SolutionCard
          key={solution.id}
          solution={solution}
          onView={handleViewSolution} />

        ) :

        <div className="col-span-full text-center py-16 text-slate-400">
                <FileText className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                <p className="text-lg font-medium">暂无方案</p>
                <p className="text-sm">请调整筛选条件或创建新方案</p>
        </div>
        }
      </motion.div> :

      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg overflow-hidden">

            <div className="overflow-x-auto custom-scrollbar">
              <table className="w-full text-left">
                <thead className="text-xs text-slate-400 uppercase bg-surface-50/50">
                  <tr>
                    <th className="px-4 py-3">方案名称</th>
                    <th className="px-4 py-3">客户</th>
                    <th className="px-4 py-3">设备类型</th>
                    <th className="px-4 py-3">版本</th>
                    <th className="px-4 py-3">状态</th>
                    <th className="px-4 py-3">进度</th>
                    <th className="px-4 py-3">金额</th>
                    <th className="px-4 py-3">更新时间</th>
                    <th className="px-4 py-3">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSolutions.length > 0 ?
              (filteredSolutions || []).map((solution) =>
              <SolutionTableRow
                key={solution.id}
                solution={solution}
                onView={handleViewSolution} />

              ) :

              <tr>
                      <td
                  colSpan="9"
                  className="text-center py-16 text-slate-400">

                        <FileText className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                        <p className="text-lg font-medium">暂无方案</p>
                        <p className="text-sm">请调整筛选条件或创建新方案</p>
                      </td>
              </tr>
              }
                </tbody>
              </table>
            </div>
      </motion.div>)
      }
    </motion.div>);

}
