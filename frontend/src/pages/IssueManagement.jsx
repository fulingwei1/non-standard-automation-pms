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
import { cn } from "../lib/utils";

// Import refactored components
import {
  IssueStatsOverview,
  IssueListManager,
  DEFAULT_ISSUE_STATS,
  ISSUE_VIEW_MODES
} from "../components/issue";

// Import services
import { issueApi, issueTemplateApi } from "../services/api";

// Import utilities
import { fadeIn, staggerContainer } from "../lib/animations";

export default function IssueManagement() {
  // 状态管理
  const [issues, setIssues] = useState([]);
  const [filteredIssues, setFilteredIssues] = useState([]);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [selectedIssues, setSelectedIssues] = useState([]);
  const [loading, setLoading] = useState(false);
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

  // 获取问题列表
  const fetchIssues = useCallback(async () => {
    try {
      setLoading(true);
      const response = await issueApi.getIssues({
        ...filters,
        search: searchTerm,
        sort: sortBy,
        timeRange
      });
      const issuesData = response.data || [];
      setIssues(issuesData);
      setFilteredIssues(issuesData);
    } catch (error) {
      console.error('Failed to fetch issues:', error);
      // 使用模拟数据
      const mockIssues = [
        {
          id: "ISS-001",
          title: "系统登录页面无法正常显示",
          description: "用户反馈登录页面在Chrome浏览器中显示异常，部分按钮无法点击",
          status: "OPEN",
          severity: "MAJOR",
          priority: "HIGH",
          category: "TECHNICAL",
          assignee: "张三",
          createdAt: "2024-01-14T10:00:00Z",
          updatedAt: "2024-01-14T10:00:00Z",
          dueDate: "2024-01-17T10:00:00Z"
        },
        {
          id: "ISS-002", 
          title: "数据库连接超时",
          description: "高峰期数据库连接超时，影响用户体验",
          status: "PROCESSING",
          severity: "CRITICAL",
          priority: "URGENT",
          category: "TECHNICAL",
          assignee: "李四",
          createdAt: "2024-01-13T15:30:00Z",
          updatedAt: "2024-01-14T09:15:00Z",
          dueDate: "2024-01-15T15:30:00Z"
        },
        {
          id: "ISS-003",
          title: "报表生成速度缓慢",
          description: "月度报表生成需要超过5分钟时间",
          status: "RESOLVED",
          severity: "MINOR",
          priority: "MEDIUM",
          category: "PERFORMANCE",
          assignee: "王五",
          createdAt: "2024-01-12T08:00:00Z",
          updatedAt: "2024-01-14T11:20:00Z",
          dueDate: "2024-01-19T08:00:00Z"
        }
      ];
      setIssues(mockIssues);
      setFilteredIssues(mockIssues);
    } finally {
      setLoading(false);
    }
  }, [filters, searchTerm, sortBy, timeRange]);

  // 获取统计数据
  const fetchStats = useCallback(async () => {
    try {
      const response = await issueApi.getStats({ timeRange });
      setStats(response.data || DEFAULT_ISSUE_STATS);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // 使用模拟数据
      setStats({
        total: 25,
        open: 8,
        processing: 6,
        resolved: 7,
        closed: 4,
        blocking: 2,
        overdue: 3,
        byStatus: {
          OPEN: 8,
          PROCESSING: 6,
          RESOLVED: 7,
          CLOSED: 4
        },
        bySeverity: {
          CRITICAL: 2,
          MAJOR: 8,
          MINOR: 12,
          TRIVIAL: 3
        },
        byCategory: {
          TECHNICAL: 10,
          PERFORMANCE: 5,
          UI: 6,
          PROCESS: 4
        },
        createdToday: 3,
        resolvedToday: 2,
        avgResolutionTime: 48.5,
        slaCompliance: 85.2
      });
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
    setShowCreateDialog(true);
  }, []);

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
      animate="show"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="问题管理"
        subtitle="问题跟踪、状态管理、优先级分配、分析统计"
        breadcrumbs={[
          { label: "项目管理", href: "/projects" },
          { label: "问题管理", href: "/issues" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => window.location.href = "/issue-analytics"}
            >
              数据分析
            </Button>
            <Button
              onClick={handleIssueCreate}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              新建问题
            </Button>
          </div>
        }
      />

      <motion.div variants={fadeIn} className="space-y-6">
        {/* 统计概览 */}
        <IssueStatsOverview
          stats={stats}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onRefresh={handleRefresh}
          loading={loading}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
        />

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
          loading={loading}
        />
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
          {selectedIssue && (
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
                  onClick={() => setShowDetailDialog(false)}
                >
                  关闭
                </Button>
                <Button
                  onClick={() => {
                    handleIssueEdit(selectedIssue);
                    setShowDetailDialog(false);
                  }}
                >
                  编辑
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* 创建问题对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>新建问题</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-400">创建新问题的表单将在这里显示</p>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
              >
                取消
              </Button>
              <Button>
                创建
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}