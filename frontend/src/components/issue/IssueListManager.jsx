/**
 * Issue List Manager Component
 * 问题列表管理组件 - 支持列表和看板视图
 */

import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay } from
"@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import {
  Search,
  Filter,
  Plus,
  Eye,
  Edit3,
  MoreHorizontal,
  ChevronDown,
  ChevronUp,
  Download,
  Upload,
  List,
  Kanban,
  AlertTriangle,
  User,
  Calendar,
  Tag,
  ArrowRight } from
"lucide-react";
import { DynamicIcon } from "../../utils/iconMap.jsx";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { cn } from "../../lib/utils";
import {
  issueStatusConfig,
  issueSeverityConfig,
  issueCategoryConfig,
  issuePriorityConfig as _issuePriorityConfig,
  getIssueStatusConfig,
  getIssueSeverityConfig,
  getIssueCategoryConfig,
  getIssuePriorityConfig,
  isIssueOverdue,
  isIssueBlocking,
  ISSUE_SORT_OPTIONS,
  ISSUE_VIEW_MODES } from
"./issueConstants";

export const IssueListManager = ({
  issues = [],
  viewMode = "list",
  searchTerm = "",
  onSearchChange = null,
  filters = {},
  onFilterChange = null,
  sortBy = "created_desc",
  onSortChange = null,
  selectedIssues = [],
  onSelectionChange = null,
  onIssueView = null,
  onIssueEdit = null,
  onIssueCreate = null,
  onIssueStatusChange: _onIssueStatusChange = null,
  onExport = null,
  onImport = null,
  loading = false,
  className = ""
}) => {
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [activeId, setActiveId] = useState(null);

  // DnD sensors for kanban view
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates
    })
  );

  // 过滤后的 issues
  const filteredIssues = useMemo(() => {
    return issues.filter((issue) => {
      // 搜索过滤
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch =
        issue.title?.toLowerCase().includes(searchLower) ||
        issue.description?.toLowerCase().includes(searchLower) ||
        issue.id?.toLowerCase().includes(searchLower) ||
        issue.assignee?.toLowerCase().includes(searchLower);
        if (!matchesSearch) {return false;}
      }

      // 状态过滤
      if (filters.status && filters.status !== 'all' && issue.status !== filters.status) {
        return false;
      }

      // 严重程度过滤
      if (filters.severity && filters.severity !== 'all' && issue.severity !== filters.severity) {
        return false;
      }

      // 分类过滤
      if (filters.category && filters.category !== 'all' && issue.category !== filters.category) {
        return false;
      }

      // 优先级过滤
      if (filters.priority && filters.priority !== 'all' && issue.priority !== filters.priority) {
        return false;
      }

      // 指派人过滤
      if (filters.assignee && filters.assignee !== 'all' && issue.assignee !== filters.assignee) {
        return false;
      }

      return true;
    });
  }, [issues, searchTerm, filters]);

  // 排序后的 issues
  const sortedIssues = useMemo(() => {
    const sorted = [...filteredIssues];

    switch (sortBy) {
      case 'created_desc':
        return sorted.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
      case 'created_asc':
        return sorted.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
      case 'updated_desc':
        return sorted.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
      case 'updated_asc':
        return sorted.sort((a, b) => new Date(a.updatedAt) - new Date(b.updatedAt));
      case 'priority_desc':
        return sorted.sort((a, b) => {
          const priorityA = getIssuePriorityConfig(a.priority).level;
          const priorityB = getIssuePriorityConfig(b.priority).level;
          return priorityB - priorityA;
        });
      case 'severity_desc':
        return sorted.sort((a, b) => {
          const severityA = getIssueSeverityConfig(a.severity).level;
          const severityB = getIssueSeverityConfig(b.severity).level;
          return severityB - severityA;
        });
      case 'title_asc':
        return sorted.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
      case 'title_desc':
        return sorted.sort((a, b) => (b.title || '').localeCompare(a.title || ''));
      default:
        return sorted;
    }
  }, [filteredIssues, sortBy]);

  // 按状态分组的 issues (用于看板视图)
  const issuesByStatus = useMemo(() => {
    const grouped = {};
    Object.keys(issueStatusConfig).forEach((status) => {
      grouped[status] = sortedIssues.filter((issue) => issue.status === status);
    });
    return grouped;
  }, [sortedIssues]);

  // 处理行展开/收起
  const toggleRowExpansion = useCallback((issueId) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedRows(newExpanded);
  }, [expandedRows]);

  // 处理选择
  const handleSelectionChange = useCallback((issueId, selected) => {
    if (!onSelectionChange) {return;}

    let newSelection;
    if (selected) {
      newSelection = [...selectedIssues, issueId];
    } else {
      newSelection = selectedIssues.filter((id) => id !== issueId);
    }
    onSelectionChange(newSelection);
  }, [selectedIssues, onSelectionChange]);

  // 处理全选
  const handleSelectAll = useCallback((selected) => {
    if (!onSelectionChange) {return;}
    onSelectionChange(selected ? sortedIssues.map((issue) => issue.id) : []);
  }, [sortedIssues, onSelectionChange]);

  // 渲染状态徽章
  const renderStatusBadge = (status) => {
    const config = getIssueStatusConfig(status);

    return (
      <Badge variant="outline" className={config.color}>
        {config.icon && <DynamicIcon name={config.icon} className="w-3 h-3 mr-1" />}
        {config.label}
      </Badge>);

  };

  // 渲染严重程度徽章
  const renderSeverityBadge = (severity) => {
    const config = getIssueSeverityConfig(severity);
    return (
      <Badge variant="outline" className={config.color}>
        {config.label}
      </Badge>);

  };

  // 渲染优先级徽章
  const renderPriorityBadge = (priority) => {
    const config = getIssuePriorityConfig(priority);
    return (
      <Badge variant="outline" className={config.color}>
        {config.label}
      </Badge>);

  };

  // 渲染问题卡片（看板视图）
  const renderIssueCard = (issue) => {
    const isOverdue = isIssueOverdue(issue);
    const isBlocking = isIssueBlocking(issue);
    const _statusConfig = getIssueStatusConfig(issue.status);

    return (
      <motion.div
        key={issue.id}
        layout
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        whileHover={{ scale: 1.02 }}
        className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-4 cursor-pointer hover:border-slate-600/60 transition-all"
        onClick={() => onIssueView?.(issue)}>

        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="text-sm font-medium text-white mb-1 line-clamp-2">
              {issue.title}
            </h4>
            <p className="text-xs text-slate-400 line-clamp-2">
              {issue.description}
            </p>
          </div>
          <div className="flex items-center gap-1 ml-2">
            {isOverdue && <AlertTriangle className="w-4 h-4 text-red-400" />}
            {isBlocking && <AlertCircle className="w-4 h-4 text-orange-400" />}
          </div>
        </div>
        
        <div className="flex items-center gap-2 mb-3">
          {renderSeverityBadge(issue.severity)}
          {renderPriorityBadge(issue.priority)}
        </div>
        
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <User className="w-3 h-3" />
            <span>{issue.assignee || '未分配'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-3 h-3" />
            <span>{issue.createdAt ? new Date(issue.createdAt).toLocaleDateString() : '-'}</span>
          </div>
        </div>
      </motion.div>);

  };

  // 渲染表格行（列表视图）
  const renderTableRow = (issue, index) => {
    const isExpanded = expandedRows.has(issue.id);
    const isSelected = selectedIssues.includes(issue.id);
    const isOverdue = isIssueOverdue(issue);
    const isBlocking = isIssueBlocking(issue);

    return (
      <motion.tr
        key={issue.id}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.02 }}
        className={cn(
          "border-b border-slate-700/40 hover:bg-slate-800/40 transition-colors",
          isSelected && "bg-slate-800/60"
        )}>

        <td className="px-3 py-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => handleSelectionChange(issue.id, e.target.checked)}
            className="rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500" />

        </td>
        
        <td className="px-3 py-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-white font-mono">#{issue.id}</span>
            {isOverdue && <AlertTriangle className="w-4 h-4 text-red-400" />}
            {isBlocking && <AlertCircle className="w-4 h-4 text-orange-400" />}
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="max-w-xs">
            <p className="text-sm text-white font-medium line-clamp-1">
              {issue.title}
            </p>
            <p className="text-xs text-slate-500 line-clamp-1">
              {issue.description}
            </p>
          </div>
        </td>
        
        <td className="px-3 py-3">
          {renderStatusBadge(issue.status)}
        </td>
        
        <td className="px-3 py-3">
          {renderSeverityBadge(issue.severity)}
        </td>
        
        <td className="px-3 py-3">
          {renderPriorityBadge(issue.priority)}
        </td>
        
        <td className="px-3 py-3">
          <Badge variant="outline" className={getIssueCategoryConfig(issue.category).color}>
            {getIssueCategoryConfig(issue.category).label}
          </Badge>
        </td>
        
        <td className="px-3 py-3">
          <div className="flex items-center gap-2">
            <User className="w-3 h-3 text-slate-400" />
            <span className="text-sm text-white">{issue.assignee || '未分配'}</span>
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-3 h-3 text-slate-400" />
            <span className="text-sm text-white">
              {issue.createdAt ? new Date(issue.createdAt).toLocaleDateString() : '-'}
            </span>
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onIssueView?.(issue);
              }}
              className="h-8 w-8 p-0 text-slate-400 hover:text-white">

              <Eye className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onIssueEdit?.(issue);
              }}
              className="h-8 w-8 p-0 text-slate-400 hover:text-white">

              <Edit3 className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                toggleRowExpansion(issue.id);
              }}
              className="h-8 w-8 p-0 text-slate-400 hover:text-white">

              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          </div>
        </td>
      </motion.tr>);

  };

  // 渲染看板列
  const renderKanbanColumn = (status) => {
    const statusConfig = getIssueStatusConfig(status);
    const columnIssues = issuesByStatus[status] || [];

    return (
      <div key={status} className="flex-1 min-w-0">
        <Card className="h-full border border-slate-700/70 bg-slate-900/40">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold text-white">
              {statusConfig.icon && <DynamicIcon name={statusConfig.icon} className="w-4 h-4" />}
              <span>{statusConfig.label}</span>
              <Badge variant="outline" className="bg-slate-800/80 text-xs border-slate-600 text-slate-200">
                {columnIssues.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-3 min-h-[400px]">
              <AnimatePresence>
                {columnIssues.map((issue) => renderIssueCard(issue))}
              </AnimatePresence>
              {columnIssues.length === 0 &&
              <div className="text-center py-8 text-slate-500 text-sm">
                  暂无问题
              </div>
              }
            </div>
          </CardContent>
        </Card>
      </div>);

  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* 搜索和筛选栏 */}
      <Card className="border border-slate-700/70 bg-slate-900/40">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* 搜索框 */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                placeholder="搜索问题编号、标题、描述..."
                value={searchTerm}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="pl-10 bg-slate-800/60 border-slate-700 text-white" />

            </div>
            
            {/* 筛选选项 */}
            <div className="flex flex-wrap gap-2">
              <Select
                value={filters.status || "all"}
                onValueChange={(value) => onFilterChange?.({ ...filters, status: value })}>

                <SelectTrigger className="w-32 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  {Object.entries(issueStatusConfig).map(([key, config]) =>
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  )}
                </SelectContent>
              </Select>

              <Select
                value={filters.severity || "all"}
                onValueChange={(value) => onFilterChange?.({ ...filters, severity: value })}>

                <SelectTrigger className="w-32 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部严重程度</SelectItem>
                  {Object.entries(issueSeverityConfig).map(([key, config]) =>
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  )}
                </SelectContent>
              </Select>

              <Select
                value={filters.category || "all"}
                onValueChange={(value) => onFilterChange?.({ ...filters, category: value })}>

                <SelectTrigger className="w-32 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部分类</SelectItem>
                  {Object.entries(issueCategoryConfig).map(([key, config]) =>
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  )}
                </SelectContent>
              </Select>

              <Select
                value={sortBy}
                onValueChange={onSortChange}>

                <SelectTrigger className="w-40 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ISSUE_SORT_OPTIONS.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                      {option.label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-2">
              {onImport &&
              <Button variant="outline" size="sm" onClick={onImport}>
                  <Upload className="w-4 h-4 mr-2" />
                  导入
              </Button>
              }
              {onExport &&
              <Button variant="outline" size="sm" onClick={onExport}>
                  <Download className="w-4 h-4 mr-2" />
                  导出
              </Button>
              }
              {onIssueCreate &&
              <Button onClick={onIssueCreate} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  新建问题
              </Button>
              }
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 列表视图 */}
      {viewMode === 'list' &&
      <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardContent className="p-0">
            {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          sortedIssues.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无问题数据</div> :

          <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-slate-700/60">
                      <th className="px-3 py-3 text-left">
                        <input
                      type="checkbox"
                      checked={selectedIssues.length === sortedIssues.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500" />

                      </th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">编号</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">标题</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">状态</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">严重程度</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">优先级</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">分类</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">指派人</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">创建时间</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedIssues.map((issue, index) => renderTableRow(issue, index))}
                  </tbody>
                </table>
          </div>
          }
          </CardContent>
      </Card>
      }

      {/* 看板视图 */}
      {viewMode === 'kanban' &&
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={(event) => setActiveId(event.active.id)}
        onDragEnd={(_event) => {
          setActiveId(null);
          // Handle drag end logic here
        }}>

          <div className="flex gap-4 overflow-x-auto pb-4">
            {Object.keys(issueStatusConfig).map((status) => renderKanbanColumn(status))}
          </div>
          <DragOverlay>
            {activeId ?
          <div className="bg-slate-800 border border-slate-600 rounded-lg p-4 shadow-xl">
                <p className="text-white text-sm">拖拽中...</p>
          </div> :
          null}
          </DragOverlay>
      </DndContext>
      }
    </div>);

};

export default IssueListManager;