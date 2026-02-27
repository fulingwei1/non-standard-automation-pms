import { useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Button, Badge } from '../ui';
import { Switch } from '../ui/switch';
import { 
  Filter, 
  Download, 
  AlertCircle, 
  TrendingUp, 
  TrendingDown,
  DollarSign,
  X
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { Calendar } from "lucide-react";

/**
 * 项目成本筛选器
 */
export default function ProjectCostFilter({ 
  filters, 
  onFilterChange, 
  onExport,
  showCost 
}) {
  const [showFilters, setShowFilters] = useState(false);

  const handleToggleCost = (checked) => {
    onFilterChange({ ...filters, includeCost: checked });
  };

  const handleToggleOverrun = (checked) => {
    onFilterChange({ ...filters, overrunOnly: checked });
  };

  const handleSortChange = (value) => {
    onFilterChange({ ...filters, sort: value });
  };

  const handleClearFilters = () => {
    onFilterChange({
      includeCost: false,
      overrunOnly: false,
      sort: 'created_at_desc',
    });
  };

  const hasActiveFilters = filters.includeCost || filters.overrunOnly || filters.sort !== 'created_at_desc';

  return (
    <div className="space-y-4">
      {/* 主要筛选栏 */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* 显示成本开关 */}
        <div className="flex items-center gap-2 px-4 py-2 bg-white/[0.05] rounded-xl border border-white/10">
          <DollarSign className="h-4 w-4 text-slate-400" />
          <span className="text-sm text-slate-300">显示成本</span>
          <Switch
            checked={filters.includeCost}
            onCheckedChange={handleToggleCost}
          />
        </div>

        {/* 仅显示超支 */}
        {showCost && (
          <div className="flex items-center gap-2 px-4 py-2 bg-white/[0.05] rounded-xl border border-white/10">
            <AlertCircle className="h-4 w-4 text-red-400" />
            <span className="text-sm text-slate-300">仅超支项目</span>
            <Switch
              checked={filters.overrunOnly}
              onCheckedChange={handleToggleOverrun}
              className={filters.overrunOnly ? 'bg-red-500' : ''}
            />
          </div>
        )}

        {/* 排序选择 */}
        {showCost && (
          <Select value={filters.sort} onValueChange={handleSortChange}>
            <SelectTrigger className="w-48 bg-white/[0.05] border-white/10">
              <SelectValue placeholder="选择排序方式" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-white/10">
              <SelectItem value="created_at_desc">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>创建时间（新→旧）</span>
                </div>
              </SelectItem>
              <SelectItem value="cost_desc">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  <span>成本（高→低）</span>
                </div>
              </SelectItem>
              <SelectItem value="cost_asc">
                <div className="flex items-center gap-2">
                  <TrendingDown className="h-4 w-4" />
                  <span>成本（低→高）</span>
                </div>
              </SelectItem>
              <SelectItem value="budget_used_pct">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  <span>预算使用率（高→低）</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        )}

        {/* 更多筛选按钮 */}
        <Button
          variant="secondary"
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            "hidden sm:flex",
            showFilters && "bg-primary text-white"
          )}
        >
          <Filter className="h-4 w-4" />
          筛选
          {showFilters && <X className="h-4 w-4 ml-1" />}
        </Button>

        {/* 导出按钮 */}
        {showCost && onExport && (
          <Button
            variant="secondary"
            onClick={onExport}
            className="ml-auto"
          >
            <Download className="h-4 w-4" />
            导出Excel
          </Button>
        )}

        {/* 清除筛选 */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="text-slate-400 hover:text-white"
          >
            <X className="h-4 w-4" />
            清除筛选
          </Button>
        )}
      </div>

      {/* 活跃筛选标签 */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500">活跃筛选:</span>
          {filters.includeCost && (
            <Badge variant="secondary" className="text-xs">
              显示成本
            </Badge>
          )}
          {filters.overrunOnly && (
            <Badge variant="destructive" className="text-xs">
              仅超支项目
            </Badge>
          )}
          {filters.sort !== 'created_at_desc' && (
            <Badge variant="secondary" className="text-xs">
              {filters.sort === 'cost_desc' && '按成本倒序'}
              {filters.sort === 'cost_asc' && '按成本正序'}
              {filters.sort === 'budget_used_pct' && '按预算使用率'}
            </Badge>
          )}
        </div>
      )}

      {/* 展开的筛选面板 */}
      {showFilters && (
        <div className="bg-white/[0.02] rounded-xl p-4 border border-white/5 space-y-4">
          <h3 className="text-white font-medium mb-3">高级筛选</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* 可以在这里添加更多筛选选项 */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">阶段</label>
              <Select>
                <SelectTrigger className="bg-white/[0.05] border-white/10">
                  <SelectValue placeholder="全部阶段" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-white/10">
                  <SelectItem value="all">全部阶段</SelectItem>
                  <SelectItem value="S1">S1 - 立项</SelectItem>
                  <SelectItem value="S2">S2 - 设计</SelectItem>
                  <SelectItem value="S3">S3 - 执行</SelectItem>
                  <SelectItem value="S4">S4 - 验收</SelectItem>
                  <SelectItem value="S5">S5 - 结算</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-2 block">健康度</label>
              <Select>
                <SelectTrigger className="bg-white/[0.05] border-white/10">
                  <SelectValue placeholder="全部健康度" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-white/10">
                  <SelectItem value="all">全部健康度</SelectItem>
                  <SelectItem value="H1">H1 - 健康</SelectItem>
                  <SelectItem value="H2">H2 - 预警</SelectItem>
                  <SelectItem value="H3">H3 - 风险</SelectItem>
                  <SelectItem value="H4">H4 - 危机</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-2 block">状态</label>
              <Select>
                <SelectTrigger className="bg-white/[0.05] border-white/10">
                  <SelectValue placeholder="全部状态" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-white/10">
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="active">进行中</SelectItem>
                  <SelectItem value="completed">已完成</SelectItem>
                  <SelectItem value="suspended">已暂停</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
