/**
 * Issue Management Page - Refactored Version
 * 问题管理页面 - 重构版本
 * Features: Issue tracking, Status management, Priority assignment, Analytics
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { cn as _cn } from "../lib/utils";

// Import refactored components
import {
  IssueStatsOverview,
  IssueListManager,
  DEFAULT_ISSUE_STATS,
  ISSUE_VIEW_MODES } from
"../components/issue";

// Import services
import { issueApi, issueTemplateApi as _issueTemplateApi } from "../services/api";

// Import utilities
import { fadeIn, staggerContainer } from "../lib/animations";

export default function IssueManagement() {
  // 状态管理
  const [_issues, setIssues] = useState([]);
  const [filteredIssues, setFilteredIssues] = useState([]);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [selectedIssues, setSelectedIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statsError, setStatsError] = useState(null);
  const [emptyHint, setEmptyHint] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // 统计数据
  const [stats, setStats] = useState(DEFAULT_ISSUE_STATS);

  // 视图和筛选
  const [viewMode, setViewMode] = useState("list");
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    status: "all",
    severity: "all",
    category: "all",
    priority: "all",
    assignee: "all"
  });
  const [sortBy, setSortBy] = useState("created_desc");
  const [timeRange, setTimeRange] = useState("week");

  // 新建问题表单数据
  const [newIssue, setNewIssue] = useState({
    title: "",
    description: "",
    category: "PROJECT",
    issue_type: "DEFECT",
    severity: "MAJOR",
    priority: "MEDIUM"
  });
  const [creating, setCreating] = useState(false);

  // 获取问题列表
  const fetchIssues = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setEmptyHint(null);
      // 过滤掉值为 "all" 的参数，后端不接受 "all" 作为筛选值
      const apiParams = {};
      if (filters.status && filters.status !== "all") {apiParams.status = filters.status;}
      if (filters.severity && filters.severity !== "all") {apiParams.severity = filters.severity;}
      if (filters.category && filters.category !== "all") {apiParams.category = filters.category;}
      if (filters.priority && filters.priority !== "all") {apiParams.priority = filters.priority;}
      if (searchTerm) {apiParams.keyword = searchTerm;}

      const response = await issueApi.getIssues(apiParams);
      // API 返回 {items: [...], total, page, page_size, pages}
      const rawData = response.data?.items || response.data || [];
      const dataItems = Array.isArray(rawData) ? rawData : [];
      const hasActiveFilters = Object.values(filters).some(
        (value) => value && value !== "all"
      );
      if (dataItems.length === 0 && !searchTerm && !hasActiveFilters) {
        setEmptyHint("数据库暂无问题数据");
      }
      // 映射 API 字段名到前端期望的字段名
      const issuesData = dataItems.map((issue) => ({
        ...issue,
        // 兼容字段映射
        id: issue.issue_no || issue.id,
        assignee: issue.assignee_name || issue.assignee,
        reporter: issue.reporter_name || issue.reporter,
        createdAt: issue.created_at || issue.createdAt,
        updatedAt: issue.updated_at || issue.updatedAt,
        dueDate: issue.due_date || issue.dueDate,
        resolvedAt: issue.resolved_at || issue.resolvedAt,
        projectName: issue.project_name || issue.projectName,
        machineName: issue.machine_name || issue.machineName
      }));
      setIssues(issuesData);
      setFilteredIssues(issuesData);
    } catch (error) {
      console.error('Failed to fetch issues:', error);
      const status = error.response?.status;
      const detail = error.response?.data?.detail;
      const message = error.response?.data?.message;
      const apiMessage =
        typeof detail === "string"
          ? detail
          : detail?.message || message || error.message;
      setError(status ? `API错误 (${status}): ${apiMessage}` : `API错误: ${apiMessage}`);
      setIssues([]);
      setFilteredIssues([]);
      setEmptyHint(null);
    } finally {
      setLoading(false);
    }
  }, [filters, searchTerm, sortBy, timeRange]);

  // 获取统计数据
  const fetchStats = useCallback(async () => {
    try {
      setStatsError(null);
      const response = await issueApi.getStats({ timeRange });
      const apiStats = response.data || {};
      // 映射 snake_case 到 camelCase
      setStats({
        total: apiStats.total || 0,
        open: apiStats.open || 0,
        processing: apiStats.processing || 0,
        resolved: apiStats.resolved || 0,
        closed: apiStats.closed || 0,
        blocking: apiStats.blocking || 0,
        overdue: apiStats.overdue || 0,
        byStatus: apiStats.by_status || apiStats.byStatus || {},
        bySeverity: apiStats.by_severity || apiStats.bySeverity || {},
        byCategory: apiStats.by_category || apiStats.byCategory || {},
        byType: apiStats.by_type || apiStats.byType || {},
        createdToday: apiStats.created_today || apiStats.createdToday || 0,
        resolvedToday: apiStats.resolved_today || apiStats.resolvedToday || 0,
        avgResolutionTime: apiStats.avg_resolution_time || apiStats.avgResolutionTime || 0,
        slaCompliance: apiStats.sla_compliance || apiStats.slaCompliance || 0
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      const status = error.response?.status;
      const detail = error.response?.data?.detail;
      const message = error.response?.data?.message;
      const apiMessage =
        typeof detail === "string"
          ? detail
          : detail?.message || message || error.message;
      setStatsError(status ? `API错误 (${status}): ${apiMessage}` : `API错误: ${apiMessage}`);
      setStats(DEFAULT_ISSUE_STATS);
    }
  }, [timeRange]);

  // 处理刷新
  const handleRefresh = useCallback(() => {
    fetchIssues();
    fetchStats();
  }, [fetchIssues, fetchStats]);

  // 处理查看问题详情
  const handleIssueView = useCallback((issue) => {
    setSelectedIssue(issue);
    setShowDetailDialog(true);
  }, []);

  // 处理编辑问题
  const handleIssueEdit = useCallback((issue) => {
    setSelectedIssue(issue);
    // 这里可以打开编辑对话框
  }, []);

  // 处理创建问题
  const handleIssueCreate = useCallback(() => {
    setSelectedIssue(null);
    setNewIssue({
      title: "",
      description: "",
      category: "PROJECT",
      issue_type: "DEFECT",
      severity: "MAJOR",
      priority: "MEDIUM"
    });
    setShowCreateDialog(true);
  }, []);

  // 提交新问题
  const handleSubmitIssue = useCallback(async () => {
    if (!newIssue.title || !newIssue.description) {
      alert("请填写标题和描述");
      return;
    }
    try {
      setCreating(true);
      await issueApi.create(newIssue);
      setShowCreateDialog(false);
      fetchIssues();
      fetchStats();
    } catch (error) {
      console.error("Failed to create issue:", error);
      alert("创建问题失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setCreating(false);
    }
  }, [newIssue, fetchIssues, fetchStats]);

  // 处理筛选变化
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  // 处理选择变化
  const handleSelectionChange = useCallback((newSelection) => {
    setSelectedIssues(newSelection);
  }, []);

  // 处理导出
  const handleExport = useCallback(() => {
    // 导出逻辑
    console.log('Exporting issues:', selectedIssues.length);
  }, [selectedIssues]);

  // 处理导入
  const handleImport = useCallback(() => {
    // 导入逻辑
    console.log('Import dialog opened');
  }, []);

  // 初始化数据
  useEffect(() => {
    handleRefresh();
  }, []);

  // 当筛选条件变化时重新获取数据
  useEffect(() => {
    fetchIssues();
  }, [filters, searchTerm, sortBy]);

  // 当时间范围变化时重新获取统计数据
  useEffect(() => {
    fetchStats();
  }, [timeRange]);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6">

      <PageHeader
        title="问题管理"
        subtitle="问题跟踪、状态管理、优先级分配、分析统计"
        breadcrumbs={[
        { label: "项目管理", href: "/projects" },
        { label: "问题管理", href: "/issues" }]
        }
        actions={
        <div className="flex items-center gap-3">
            <Button
            variant="outline"
            onClick={() => window.location.href = "/issue-statistics-snapshot"}>

              数据分析
            </Button>
            <Button
            onClick={handleIssueCreate}
            className="bg-blue-600 hover:bg-blue-700 text-white">

              新建问题
            </Button>
        </div>
        } />


      <motion.div variants={fadeIn} className="space-y-6">
        {(error || statsError) && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
            {error && <div>问题列表加载失败：{error}</div>}
            {statsError && <div>统计数据加载失败：{statsError}</div>}
          </div>
        )}
        {emptyHint && !error && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
            {emptyHint}
          </div>
        )}
        {/* 统计概览 */}
        <IssueStatsOverview
          stats={stats}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onRefresh={handleRefresh}
          loading={loading}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange} />


        {/* 问题列表管理 */}
        <IssueListManager
          issues={filteredIssues}
          viewMode={viewMode}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          filters={filters}
          onFilterChange={handleFilterChange}
          sortBy={sortBy}
          onSortChange={setSortBy}
          selectedIssues={selectedIssues}
          onSelectionChange={handleSelectionChange}
          onIssueView={handleIssueView}
          onIssueEdit={handleIssueEdit}
          onIssueCreate={handleIssueCreate}
          onExport={handleExport}
          onImport={handleImport}
          loading={loading} />

      </motion.div>

      {/* 问题详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 text-white max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              问题详情
              <span className="text-sm text-slate-400">#{selectedIssue?.id}</span>
            </DialogTitle>
          </DialogHeader>
          {selectedIssue &&
          <div className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">标题</label>
                  <p className="text-white font-medium">{selectedIssue.title}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">状态</label>
                  <div className="mt-1">
                    {/* 这里应该渲染状态徽章 */}
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-sm">
                      {selectedIssue.status}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-slate-400">严重程度</label>
                  <p className="text-white">{selectedIssue.severity}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">优先级</label>
                  <p className="text-white">{selectedIssue.priority}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">指派人</label>
                  <p className="text-white">{selectedIssue.assignee || '未分配'}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">截止时间</label>
                  <p className="text-white">
                    {selectedIssue.dueDate ? new Date(selectedIssue.dueDate).toLocaleDateString() : '未设置'}
                  </p>
                </div>
              </div>
              
              {/* 描述 */}
              <div>
                <label className="text-sm text-slate-400">问题描述</label>
                <div className="mt-2 p-4 bg-slate-800/60 rounded-lg">
                  <p className="text-white">{selectedIssue.description}</p>
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                <Button
                variant="outline"
                onClick={() => setShowDetailDialog(false)}>

                  关闭
                </Button>
                <Button
                onClick={() => {
                  handleIssueEdit(selectedIssue);
                  setShowDetailDialog(false);
                }}>

                  编辑
                </Button>
              </div>
          </div>
          }
        </DialogContent>
      </Dialog>

      {/* 创建问题对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>新建问题</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* 标题 */}
            <div className="space-y-2">
              <Label htmlFor="title">问题标题 *</Label>
              <Input
                id="title"
                placeholder="请输入问题标题"
                value={newIssue.title}
                onChange={(e) => setNewIssue({ ...newIssue, title: e.target.value })}
                className="bg-slate-800 border-slate-700" />

            </div>

            {/* 描述 */}
            <div className="space-y-2">
              <Label htmlFor="description">问题描述 *</Label>
              <Textarea
                id="description"
                placeholder="请详细描述问题"
                value={newIssue.description}
                onChange={(e) => setNewIssue({ ...newIssue, description: e.target.value })}
                className="bg-slate-800 border-slate-700 min-h-[100px]" />

            </div>

            {/* 分类和类型 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>问题分类</Label>
                <Select
                  value={newIssue.category}
                  onValueChange={(value) => setNewIssue({ ...newIssue, category: value })}>

                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PROJECT">项目问题</SelectItem>
                    <SelectItem value="TECHNICAL">技术问题</SelectItem>
                    <SelectItem value="QUALITY">质量问题</SelectItem>
                    <SelectItem value="PROCUREMENT">采购问题</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>问题类型</Label>
                <Select
                  value={newIssue.issue_type}
                  onValueChange={(value) => setNewIssue({ ...newIssue, issue_type: value })}>

                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DEFECT">缺陷</SelectItem>
                    <SelectItem value="RISK">风险</SelectItem>
                    <SelectItem value="IMPROVEMENT">改进</SelectItem>
                    <SelectItem value="TECHNICAL">技术问题</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* 严重程度和优先级 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>严重程度</Label>
                <Select
                  value={newIssue.severity}
                  onValueChange={(value) => setNewIssue({ ...newIssue, severity: value })}>

                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CRITICAL">严重</SelectItem>
                    <SelectItem value="MAJOR">主要</SelectItem>
                    <SelectItem value="MINOR">次要</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>优先级</Label>
                <Select
                  value={newIssue.priority}
                  onValueChange={(value) => setNewIssue({ ...newIssue, priority: value })}>

                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="URGENT">紧急</SelectItem>
                    <SelectItem value="HIGH">高</SelectItem>
                    <SelectItem value="MEDIUM">中</SelectItem>
                    <SelectItem value="LOW">低</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                disabled={creating}>

                取消
              </Button>
              <Button
                onClick={handleSubmitIssue}
                disabled={creating}
                className="bg-blue-600 hover:bg-blue-700">

                {creating ? "创建中..." : "创建问题"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </motion.div>);

}
