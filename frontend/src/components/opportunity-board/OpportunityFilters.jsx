/**
 * Opportunity Filters Component
 * 商机过滤器组件 - 过选和搜索功能
 */

import { useState, useMemo as _useMemo } from "react";
import {
  Search,
  Filter,
  X,
  Check,
  Calendar,
  DollarSign,
  User,
  Building,
  Tag,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Download,
  Eye,
  EyeOff } from
"lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "../../components/ui/collapsible";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { cn } from "../../lib/utils";
import {
  opportunityStatusConfig,
  opportunityStageConfig,
  opportunityPriorityConfig,
  opportunitySourceConfig,
  opportunityTypeConfig,
  opportunitySizeConfig,
  quickFiltersConfig,
  sortOptionsConfig } from
"@/lib/constants/opportunityBoard";

/**
 * 过滤器组件属性
 */
export const OpportunityFilters = ({
  onFilterChange,
  initialFilters = {},
  showQuickFilters = true,
  showAdvancedFilters = true,
  className
}) => {
  const [filters, setFilters] = useState(initialFilters);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showHiddenFilters, _setShowHiddenFilters] = useState(false);

  // 状态选项
  const statusOptions = Object.entries(opportunityStatusConfig).map(([key, config]) => ({
    value: key,
    label: config.label
  }));

  // 阶段选项
  const stageOptions = Object.entries(opportunityStageConfig).
  sort(([, a], [, b]) => a.order - b.order).
  map(([key, config]) => ({
    value: key,
    label: config.label
  }));

  // 优先级选项
  const priorityOptions = Object.entries(opportunityPriorityConfig).map(([key, config]) => ({
    value: key,
    label: config.label
  }));

  // 来源选项
  const sourceOptions = Object.entries(opportunitySourceConfig).map(([key, config]) => ({
    value: key,
    label: config.label
  }));

  // 类型选项
  const typeOptions = Object.entries(opportunityTypeConfig).map(([key, config]) => ({
    value: key,
    label: config.label
  }));

  // 规模选项
  const sizeOptions = Object.entries(opportunitySizeConfig).map(([key, config]) => ({
    value: key,
    label: config.label
  }));

  // 快速过滤器选项
  const quickFilterOptions = Object.entries(quickFiltersConfig).map(([key, config]) => ({
    value: key,
    label: config.label,
    icon: config.icon
  }));

  // 应用过滤器
  const applyFilters = (newFilters) => {
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  // 清除所有过滤器
  const clearAllFilters = () => {
    const emptyFilters = {};
    setFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };

  // 切换过滤器值
  const toggleFilter = (key, value) => {
    const currentValues = filters[key] || [];
    const newValues = currentValues.includes(value) ?
    currentValues.filter((v) => v !== value) :
    [...currentValues, value];

    const newFilters = {
      ...filters,
      [key]: newValues.length > 0 ? newValues : undefined
    };

    applyFilters(newFilters);
  };

  // 设置范围值
  const setRangeFilter = (key, value) => {
    const newFilters = {
      ...filters,
      [key]: value
    };
    applyFilters(newFilters);
  };

  // 应用快速过滤器
  const applyQuickFilter = (filterKey) => {
    const filterConfig = quickFiltersConfig[filterKey];

    if (filterConfig.condition) {
      // 这里应该从父组件获取商机列表并应用条件
      // 暂时使用简单的过滤器逻辑
      const newFilters = {
        ...filters,
        quick_filter: filterKey
      };
      applyFilters(newFilters);
    }
  };

  // 获取激活的过滤器数量
  const getActiveFilterCount = () => {
    return Object.values(filters).filter((value) => {
      if (Array.isArray(value)) {
        return value.length > 0;
      }
      return value !== undefined && value !== '';
    }).length;
  };

  // 渲染搜索框
  const renderSearchBox = () =>
  <div className="relative">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
      <Input
      placeholder="搜索商机名称、客户公司..."
      value={filters.search || ''}
      onChange={(e) => setRangeFilter('search', e.target.value)}
      className="pl-10" />

  </div>;


  // 渲染快速过滤器
  const renderQuickFilters = () =>
  <div className="flex flex-wrap gap-2">
      {quickFilterOptions.map(({ value, label, icon: Icon }) =>
    <Button
      key={value}
      variant={filters.quick_filter === value ? "default" : "outline"}
      size="sm"
      className="h-8"
      onClick={() => applyQuickFilter(value)}>

          <Icon className="mr-1 h-3 w-3" />
          {label}
    </Button>
    )}
  </div>;


  // 渲染多选过滤器
  const _renderMultiSelectFilter = (title, options, key) => {
    const selectedValues = filters[key] || [];

    return (
      <Collapsible open={showHiddenFilters}>
        <CollapsibleContent className="space-y-3">
          <div className="space-y-2">
            <div className="text-sm font-medium">{title}</div>
            <div className="flex flex-wrap gap-2">
              {options.map(({ value, label }) =>
              <Badge
                key={value}
                variant={selectedValues.includes(value) ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => toggleFilter(key, value)}>

                  {label}
                  {selectedValues.includes(value) &&
                <X className="ml-1 h-3 w-3" />
                }
              </Badge>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>);

  };

  // 渲染范围过滤器
  const renderRangeFilter = (title, key, placeholder = "") =>
  <div className="space-y-2">
      <div className="text-sm font-medium">{title}</div>
      <Input
      type="number"
      placeholder={placeholder}
      value={filters[key] || ''}
      onChange={(e) => setRangeFilter(key, e.target.value ? Number(e.target.value) : undefined)} />

  </div>;


  // 渲染日期范围过滤器
  const renderDateRangeFilter = (title, key) =>
  <div className="space-y-2">
      <div className="text-sm font-medium">{title}</div>
      <Input
      type="date"
      value={filters[key] || ''}
      onChange={(e) => setRangeFilter(key, e.target.value)} />

  </div>;


  // 渲染选择器过滤器
  const renderSelectFilter = (title, options, key) =>
  <div className="space-y-2">
      <div className="text-sm font-medium">{title}</div>
      <Select value={filters[key] || '__all__'} onValueChange={(value) => setRangeFilter(key, value === '__all__' ? undefined : value)}>
        <SelectTrigger>
          <SelectValue placeholder="选择..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部</SelectItem>
          {options.map(({ value, label }) =>
        <SelectItem key={value} value={value}>
              {label}
        </SelectItem>
        )}
        </SelectContent>
      </Select>
  </div>;


  // 渲染排序选项
  const renderSortSelector = () =>
  <div className="space-y-2">
      <div className="text-sm font-medium">排序</div>
      <Select value={filters.sort || ''} onValueChange={(value) => setRangeFilter('sort', value || undefined)}>
        <SelectTrigger>
          <SelectValue placeholder="选择排序方式" />
        </SelectTrigger>
        <SelectContent>
          {sortOptionsConfig.map(({ value, label }) =>
        <SelectItem key={value} value={value}>
              {label}
        </SelectItem>
        )}
        </SelectContent>
      </Select>
  </div>;


  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">筛选商机</CardTitle>
          <div className="flex items-center gap-2">
            {getActiveFilterCount() > 0 &&
            <Badge variant="secondary">
                {getActiveFilterCount()} 个筛选条件
            </Badge>
            }
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}>

              <Filter className="h-4 w-4 mr-1" />
              {isExpanded ? "收起" : "展开"}
            </Button>
            {getActiveFilterCount() > 0 &&
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}>

                <RotateCcw className="h-4 w-4" />
            </Button>
            }
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 搜索框 */}
        {renderSearchBox()}

        {/* 快速过滤器 */}
        {showQuickFilters && renderQuickFilters()}

        {/* 高级过滤器 */}
        {isExpanded && showAdvancedFilters &&
        <div className="space-y-4 pt-4 border-t">
            {/* 状态和阶段 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderSelectFilter("状态", statusOptions, "status")}
              {renderSelectFilter("阶段", stageOptions, "stage")}
            </div>

            {/* 优先级和来源 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderSelectFilter("优先级", priorityOptions, "priority")}
              {renderSelectFilter("来源", sourceOptions, "source")}
            </div>

            {/* 类型和规模 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderSelectFilter("类型", typeOptions, "type")}
              {renderSelectFilter("规模", sizeOptions, "size")}
            </div>

            {/* 金额范围 */}
            <div className="grid grid-cols-2 gap-4">
              {renderRangeFilter("最小金额", "minAmount", "最小金额")}
              {renderRangeFilter("最大金额", "maxAmount", "最大金额")}
            </div>

            {/* 日期范围 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderDateRangeFilter("创建时间", "created_from")}
              {renderDateRangeFilter("至", "created_to")}
            </div>

            {/* 排序 */}
            {renderSortSelector()}
        </div>
        }
      </CardContent>
    </Card>);

};

export default OpportunityFilters;