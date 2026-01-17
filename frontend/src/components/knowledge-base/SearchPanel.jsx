/**
 * Search Panel Component - Advanced search functionality for knowledge base
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { fadeIn as _fadeIn } from "../../lib/animations";
import {
  Search,
  Filter,
  X,
  Calendar,
  Eye,
  User,
  Bookmark,
  Star,
  TrendingUp,
  Clock,
  Tag,
  FileText,
  Settings,
  SlidersHorizontal,
  RotateCcw,
  CheckCircle,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Filter as FilterIcon,
  Grid3X3,
  List,
  SortAsc,
  SortDesc,
  Calendar as CalendarIcon,
  Tag as TagIcon,
  User as UserIcon } from
"lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  searchConfigs,
  articleStatusConfigs as _articleStatusConfigs,
  articlePriorityConfigs as _articlePriorityConfigs,
  articleTypeConfigs as _articleTypeConfigs,
  viewConfigs,
  isValidCategory as _isValidCategory,
  isValidStatus as _isValidStatus,
  isValidPriority as _isValidPriority,
  isValidType as _isValidType } from
"./knowledgeBaseConstants";

export default function SearchPanel({
  onSearch,
  onFilterChange,
  onSortChange,
  onViewChange,
  initialFilters = {},
  initialSort = 'relevance',
  initialView = 'list',
  showAdvanced: _showAdvanced = true,
  showSort = true,
  showView = true,
  showFilters: _showFilters = true,
  placeholder = "搜索知识库...",
  className
}) {
  const [searchTerm, setSearchTerm] = useState(initialFilters.search || "");
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [localFilters, setLocalFilters] = useState({
    ...initialFilters,
    category: initialFilters.category || "all",
    status: initialFilters.status || "all",
    priority: initialFilters.priority || "all",
    type: initialFilters.type || "all",
    author: initialFilters.author || "",
    dateRange: initialFilters.dateRange || null,
    tags: initialFilters.tags || []
  });
  const [sortBy, setSortBy] = useState(initialSort);
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState(initialView);
  const [searchHistory, setSearchHistory] = useState([]);
  const [popularTags, setPopularTags] = useState([]);

  // Initialize popular tags
  useEffect(() => {
    // Mock popular tags - in real app, fetch from API
    setPopularTags(['项目管理', '技术规范', '质量控制', '安全生产', '最佳实践', '故障排查', '操作指南']);
  }, []);

  // Handle search
  const handleSearch = () => {
    const searchParams = {
      search: searchTerm,
      ...localFilters,
      sortBy,
      sortOrder
    };

    // Add to search history
    if (searchTerm.trim()) {
      setSearchHistory((prev) => [searchTerm, ...prev.filter((h) => h !== searchTerm)].slice(0, 10));
    }

    onSearch?.(searchParams);
    onFilterChange?.(localFilters);
    onSortChange?.({ sortBy, sortOrder });
  };

  // Handle filter change
  const handleFilterChange = (key, value) => {
    setLocalFilters((prev) => ({
      ...prev,
      [key]: value
    }));
    onFilterChange?.({ ...localFilters, [key]: value });
  };

  // Clear filters
  const clearFilters = () => {
    const newFilters = {
      category: "all",
      status: "all",
      priority: "all",
      type: "all",
      author: "",
      dateRange: null,
      tags: []
    };
    setLocalFilters(newFilters);
    onFilterChange?.(newFilters);
  };

  // Clear search
  const clearSearch = () => {
    setSearchTerm("");
    setLocalFilters((prev) => ({
      ...prev,
      search: ""
    }));
    onSearch?.("");
  };

  // Toggle view mode
  const toggleViewMode = (mode) => {
    setViewMode(mode);
    onViewChange?.(mode);
  };

  // Toggle sort order
  const toggleSortOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    setSortOrder(newOrder);
    onSortChange?.({ sortBy, sortOrder: newOrder });
  };

  // Apply sort
  const applySort = (newSortBy) => {
    setSortBy(newSortBy);
    onSortChange?.({ sortBy: newSortBy, sortOrder });
  };

  // Check if any filters are active
  const hasActiveFilters = Object.entries(localFilters).some(([key, value]) =>
  value !== "all" && value !== "" && value !== null && key !== 'search' && key !== 'tags' ||
  Array.isArray(value) && value.length > 0
  );

  return (
    <div className={cn("w-full space-y-4", className)}>
      {/* Main Search Bar */}
      <div className="relative">
        <div className="relative flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder={placeholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-10"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()} />

            {searchTerm &&
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6"
              onClick={clearSearch}>

                <X className="w-3 h-3" />
              </Button>
            }
          </div>

          <Button onClick={handleSearch}>
            搜索
          </Button>

          <Button
            variant="outline"
            size="icon"
            onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            className={isAdvancedOpen && "bg-primary/10"}>

            <Filter className="w-4 h-4" />
          </Button>
        </div>

        {/* Search History */}
        {searchHistory.length > 0 &&
        <div className="absolute top-full left-0 right-0 mt-1 bg-surface-100 border border-white/10 rounded-lg shadow-lg z-50">
            <div className="p-2">
              <div className="text-xs text-slate-400 mb-2">搜索历史</div>
              {searchHistory.map((term, index) =>
            <div
              key={index}
              className="px-3 py-1.5 hover:bg-surface-50/50 cursor-pointer rounded text-sm text-slate-300"
              onClick={() => {
                setSearchTerm(term);
                handleSearch();
              }}>

                  {term}
                </div>
            )}
            </div>
          </div>
        }
      </div>

      {/* Advanced Search Panel */}
      <AnimatePresence>
        {isAdvancedOpen &&
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="bg-surface-50/50 rounded-lg p-4 space-y-4">

            {/* Filter Rows */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Category Filter */}
              <div>
                <label className="text-xs text-slate-400 mb-2 block">文章分类</label>
                <select
                value={localFilters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                className="w-full bg-surface-50 border border-white/10 rounded px-3 py-2 text-sm text-white">

                  {searchConfigs.FILTER_OPTIONS.category.map((option) =>
                <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                )}
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label className="text-xs text-slate-400 mb-2 block">发布状态</label>
                <select
                value={localFilters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full bg-surface-50 border border-white/10 rounded px-3 py-2 text-sm text-white">

                  {searchConfigs.FILTER_OPTIONS.status.map((option) =>
                <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                )}
                </select>
              </div>

              {/* Priority Filter */}
              <div>
                <label className="text-xs text-slate-400 mb-2 block">优先级</label>
                <select
                value={localFilters.priority}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
                className="w-full bg-surface-50 border border-white/10 rounded px-3 py-2 text-sm text-white">

                  {searchConfigs.FILTER_OPTIONS.priority.map((option) =>
                <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                )}
                </select>
              </div>

              {/* Type Filter */}
              <div>
                <label className="text-xs text-slate-400 mb-2 block">文章类型</label>
                <select
                value={localFilters.type}
                onChange={(e) => handleFilterChange('type', e.target.value)}
                className="w-full bg-surface-50 border border-white/10 rounded px-3 py-2 text-sm text-white">

                  {searchConfigs.FILTER_OPTIONS.type.map((option) =>
                <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                )}
                </select>
              </div>
            </div>

            {/* Date Range Filter */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-400 mb-2 block">开始日期</label>
                <Input
                type="date"
                value={localFilters.dateRange?.startDate || ""}
                onChange={(e) => handleFilterChange('dateRange', {
                  ...localFilters.dateRange,
                  startDate: e.target.value
                })}
                className="bg-surface-50 border border-white/10" />

              </div>
              <div>
                <label className="text-xs text-slate-400 mb-2 block">结束日期</label>
                <Input
                type="date"
                value={localFilters.dateRange?.endDate || ""}
                onChange={(e) => handleFilterChange('dateRange', {
                  ...localFilters.dateRange,
                  endDate: e.target.value
                })}
                className="bg-surface-50 border border-white/10" />

              </div>
            </div>

            {/* Author Filter */}
            <div>
              <label className="text-xs text-slate-400 mb-2 block">作者</label>
              <Input
              placeholder="输入作者名称"
              value={localFilters.author}
              onChange={(e) => handleFilterChange('author', e.target.value)}
              className="bg-surface-50 border border-white/10" />

            </div>

            {/* Tags Filter */}
            <div>
              <label className="text-xs text-slate-400 mb-2 block">标签</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {popularTags.map((tag, index) =>
              <Badge
                key={index}
                variant={localFilters.tags.includes(tag) ? "default" : "secondary"}
                className="cursor-pointer"
                onClick={() => {
                  const newTags = localFilters.tags.includes(tag) ?
                  localFilters.tags.filter((t) => t !== tag) :
                  [...localFilters.tags, tag];
                  handleFilterChange('tags', newTags);
                }}>

                    {tag}
                  </Badge>
              )}
              </div>
              <Input
              placeholder="自定义标签..."
              value={localFilters.tags.join(', ')}
              onChange={(e) => handleFilterChange('tags', e.target.value.split(',').map((t) => t.trim()).filter((t) => t))}
              className="bg-surface-50 border border-white/10" />

            </div>

            {/* Filter Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-white/10">
              <Button variant="outline" size="sm" onClick={clearFilters}>
                <RotateCcw className="w-4 h-4 mr-2" />
                清除筛选
              </Button>

              <div className="flex items-center gap-2">
                <Button size="sm" onClick={handleSearch}>
                  应用筛选
                </Button>
              </div>
            </div>
          </motion.div>
        }
      </AnimatePresence>

      {/* Active Filters Display */}
      {hasActiveFilters &&
      <div className="flex flex-wrap items-center gap-2 p-3 bg-surface-50/50 rounded-lg">
          <span className="text-xs text-slate-400">当前筛选:</span>

          {localFilters.category !== "all" &&
        <Badge variant="secondary" className="text-xs">
              分类: {searchConfigs.FILTER_OPTIONS.category.find((c) => c.value === localFilters.category)?.label}
            </Badge>
        }

          {localFilters.status !== "all" &&
        <Badge variant="secondary" className="text-xs">
              状态: {searchConfigs.FILTER_OPTIONS.status.find((s) => s.value === localFilters.status)?.label}
            </Badge>
        }

          {localFilters.priority !== "all" &&
        <Badge variant="secondary" className="text-xs">
              优先级: {searchConfigs.FILTER_OPTIONS.priority.find((p) => p.value === localFilters.priority)?.label}
            </Badge>
        }

          {localFilters.type !== "all" &&
        <Badge variant="secondary" className="text-xs">
              类型: {searchConfigs.FILTER_OPTIONS.type.find((t) => t.value === localFilters.type)?.label}
            </Badge>
        }

          {localFilters.author &&
        <Badge variant="secondary" className="text-xs">
              作者: {localFilters.author}
            </Badge>
        }

          {localFilters.dateRange &&
        <Badge variant="secondary" className="text-xs">
              日期: {localFilters.dateRange.startDate} ~ {localFilters.dateRange.endDate}
            </Badge>
        }

          {localFilters.tags.length > 0 &&
        <Badge variant="secondary" className="text-xs">
              标签: {localFilters.tags.join(', ')}
            </Badge>
        }

          <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={clearFilters}>

            <X className="w-3 h-3 mr-1" />
            清除全部
          </Button>
        </div>
      }

      {/* Sort and View Controls */}
      <div className="flex items-center justify-between">
        {/* Sort Controls */}
        {showSort &&
        <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">排序:</span>
            <div className="flex items-center gap-1 bg-surface-50/50 rounded-lg p-1">
              {searchConfigs.SORT_OPTIONS.map((option) =>
            <Button
              key={option.value}
              variant={sortBy === option.value ? "default" : "ghost"}
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => applySort(option.value)}>

                  {option.label}
                </Button>
            )}
              <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0"
              onClick={toggleSortOrder}>

                {sortOrder === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />}
              </Button>
            </div>
          </div>
        }

        {/* View Controls */}
        {showView &&
        <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">视图:</span>
            <div className="flex items-center gap-1 bg-surface-50/50 rounded-lg p-1">
              {Object.values(viewConfigs).map((view) =>
            <Button
              key={view.value}
              variant={viewMode === view.value ? "default" : "ghost"}
              size="sm"
              className="h-7 w-7 p-0"
              onClick={() => toggleViewMode(view.value)}
              title={view.label}>

                  {view.icon}
                </Button>
            )}
            </div>
          </div>
        }
      </div>
    </div>);

}

// Quick Search Suggestions Component
export function SearchSuggestions({
  searchTerm,
  suggestions = [],
  onSelect,
  maxResults = 5
}) {
  if (!searchTerm) return null;

  const filteredSuggestions = suggestions.
  filter((suggestion) =>
  suggestion.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
  suggestion.content.toLowerCase().includes(searchTerm.toLowerCase())
  ).
  slice(0, maxResults);

  if (filteredSuggestions.length === 0) return null;

  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-surface-100 border border-white/10 rounded-lg shadow-lg z-50">
      {filteredSuggestions.map((suggestion, index) =>
      <div
        key={index}
        className="px-4 py-3 hover:bg-surface-50/50 cursor-pointer border-b border-white/10 last:border-b-0"
        onClick={() => onSelect?.(suggestion)}>

          <div className="font-medium text-sm text-white mb-1">
            {highlightText(suggestion.title, searchTerm)}
          </div>
          <div className="text-xs text-slate-400">
            {highlightText(suggestion.summary || suggestion.content.substring(0, 100) + '...', searchTerm)}
          </div>
        </div>
      )}
    </div>);

}

// Search Results Summary Component
export function SearchResultsSummary({
  totalResults,
  searchTime,
  filters: _filters = {},
  sortBy,
  sortOrder
}) {
  return (
    <div className="flex items-center justify-between text-sm">
      <div className="text-slate-400">
        找到 <span className="text-white font-medium">{totalResults}</span> 个结果
        {searchTime && ` (耗时 ${searchTime}ms)`}
      </div>

      <div className="text-xs text-slate-400">
        已按 {searchConfigs.SORT_OPTIONS.find((s) => s.value === sortBy)?.label}
        {sortOrder === 'asc' ? '升序' : '降序'} 排序
      </div>
    </div>);

}

// Highlight matching text helper
function highlightText(text, searchTerm) {
  if (!searchTerm) return text;

  const regex = new RegExp(`(${searchTerm})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) =>
  regex.test(part) ?
  <span key={index} className="bg-amber-500/20 text-amber-400">{part}</span> :
  part
  );
}