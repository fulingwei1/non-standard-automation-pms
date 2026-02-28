import { memo } from "react";
import { cn } from "../../lib/utils";
import { HEALTH_CONFIG, PROJECT_STATUS } from "../../lib/constants";
import { Input, Button } from "../ui";
import {
  Search,
  LayoutGrid,
  List,
  Table2,
  Filter,
  X,
  User,
  Users,
  RefreshCw,
  Layers,
  Calendar,
  GitBranch,
  Copy,
} from "lucide-react";
/**
 * 看板筛选器组件
 */
const BoardFilters = memo(function BoardFilters({
  // 视图模式
  viewMode = "kanban",
  onViewModeChange,
  // 筛选模式
  filterMode = "my",
  onFilterModeChange,
  // 状态筛选
  statusFilter = "all",
  onStatusFilterChange,
  // 健康度筛选
  healthFilter = "all",
  onHealthFilterChange,
  // 搜索
  searchQuery = "",
  onSearchChange,
  // 刷新
  onRefresh,
  isLoading = false,
  // 统计信息
  stats = {},
  // 模板筛选（阶段视图专用）
  templateFilter = "all",
  onTemplateFilterChange,
  groupByTemplate = true,
  onGroupByTemplateChange,
  availableTemplates = [],
}) {
  return (
    <div className="flex flex-col gap-4 mb-6">
      {/* 第一行：视图切换 + 智能筛选 + 搜索 */}
      <div className="flex flex-wrap items-center gap-4">
        {/* 视图切换 */}
        <div className="flex items-center bg-surface-1 rounded-lg p-1 border border-white/10">
          <button
            onClick={() => onViewModeChange?.("kanban")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              viewMode === "kanban"
                ? "bg-primary text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <LayoutGrid className="w-4 h-4" />
            <span>看板</span>
          </button>
          <button
            onClick={() => onViewModeChange?.("matrix")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              viewMode === "matrix"
                ? "bg-primary text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <Table2 className="w-4 h-4" />
            <span>矩阵</span>
          </button>
          <button
            onClick={() => onViewModeChange?.("list")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              viewMode === "list"
                ? "bg-primary text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <List className="w-4 h-4" />
            <span>列表</span>
          </button>
          {/* 新增阶段视图模式 */}
          <div className="w-px h-6 bg-white/10 mx-1" />
          <button
            onClick={() => onViewModeChange?.("pipeline")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              viewMode === "pipeline"
                ? "bg-blue-500 text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <Layers className="w-4 h-4" />
            <span>流水线</span>
          </button>
          <button
            onClick={() => onViewModeChange?.("timeline")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              viewMode === "timeline"
                ? "bg-green-500 text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <Calendar className="w-4 h-4" />
            <span>时间轴</span>
          </button>
          <button
            onClick={() => onViewModeChange?.("tree")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              viewMode === "tree"
                ? "bg-purple-500 text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <GitBranch className="w-4 h-4" />
            <span>分解树</span>
          </button>
        </div>
        {/* 智能筛选切换 */}
        <div className="flex items-center bg-surface-1 rounded-lg p-1 border border-white/10">
          <button
            onClick={() => onFilterModeChange?.("my")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              filterMode === "my"
                ? "bg-primary/20 text-primary border border-primary/30"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <User className="w-4 h-4" />
            <span>我相关的</span>
          </button>
          <button
            onClick={() => onFilterModeChange?.("all")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
              filterMode === "all"
                ? "bg-white/10 text-white"
                : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            <Users className="w-4 h-4" />
            <span>全部项目</span>
          </button>
        </div>
        {/* 搜索框 */}
        <div className="flex-1 min-w-[200px] max-w-[400px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索项目编号、名称..."
              value={searchQuery}
              onChange={(e) => onSearchChange?.(e.target.value)}
              className="pl-10 pr-8"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange?.("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
        {/* 刷新按钮 */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={isLoading}
          className="text-slate-400 hover:text-white"
        >
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
        </Button>
      </div>
      {/* 第二行：状态筛选 + 健康度筛选 + 统计 */}
      <div className="flex flex-wrap items-center gap-4">
        {/* 状态筛选 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">状态:</span>
          <div className="flex items-center gap-1">
            {[
              { key: "all", label: "全部" },
              { key: "active", label: "进行中" },
              { key: "paused", label: "暂停" },
              { key: "completed", label: "已完成" },
            ].map((status) => (
              <button
                key={status.key}
                onClick={() => onStatusFilterChange?.(status.key)}
                className={cn(
                  "px-2 py-1 rounded text-xs transition-all",
                  statusFilter === status.key
                    ? "bg-white/10 text-white"
                    : "text-slate-400 hover:text-white hover:bg-white/5",
                )}
              >
                {status.label}
              </button>
            ))}
          </div>
        </div>
        {/* 健康度筛选 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">健康度:</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onHealthFilterChange?.("all")}
              className={cn(
                "px-2 py-1 rounded text-xs transition-all",
                healthFilter === "all"
                  ? "bg-white/10 text-white"
                  : "text-slate-400 hover:text-white hover:bg-white/5",
              )}
            >
              全部
            </button>
            {Object.entries(HEALTH_CONFIG).map(([key, config]) => (
              <button
                key={key}
                onClick={() => onHealthFilterChange?.(key)}
                className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded text-xs transition-all",
                  healthFilter === key
                    ? cn(config.bgClass, config.textClass)
                    : "text-slate-400 hover:text-white hover:bg-white/5",
                )}
              >
                <span className={cn("w-2 h-2 rounded-full", config.dotClass)} />
                <span>{config.label}</span>
                {stats[key] > 0 && (
                  <span className="text-slate-500">({stats[key]})</span>
                )}
              </button>
            ))}
          </div>
        </div>
        {/* 统计信息 */}
        <div className="ml-auto flex items-center gap-4 text-xs text-slate-400">
          <span>
            共{" "}
            <span className="text-white font-medium">{stats.total || 0}</span>{" "}
            个项目
          </span>
          {stats.myCount !== undefined && filterMode === "my" && (
            <span>
              我相关{" "}
              <span className="text-primary font-medium">{stats.myCount}</span>{" "}
              个
            </span>
          )}
        </div>
      </div>
      {/* 第三行：模板筛选（仅阶段视图显示） */}
      {(viewMode === "pipeline" || viewMode === "timeline" || viewMode === "tree") && (
        <div className="flex flex-wrap items-center gap-4">
          {/* 按模板分组切换 */}
          <div className="flex items-center gap-2">
            <Copy className="w-4 h-4 text-slate-500" />
            <button
              onClick={() => onGroupByTemplateChange?.(!groupByTemplate)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-all",
                groupByTemplate
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  : "text-slate-400 hover:text-white hover:bg-white/5",
              )}
            >
              按模板分组
            </button>
          </div>
          {/* 模板筛选 */}
          {availableTemplates && availableTemplates.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">模板:</span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => onTemplateFilterChange?.("all")}
                  className={cn(
                    "px-2 py-1 rounded text-xs transition-all",
                    templateFilter === "all"
                      ? "bg-white/10 text-white"
                      : "text-slate-400 hover:text-white hover:bg-white/5",
                  )}
                >
                  全部
                </button>
                {(availableTemplates || []).map((template) => (
                  <button
                    key={template.id}
                    onClick={() => onTemplateFilterChange?.(template.id)}
                    className={cn(
                      "px-2 py-1 rounded text-xs transition-all",
                      templateFilter === template.id
                        ? "bg-purple-500/20 text-purple-400"
                        : "text-slate-400 hover:text-white hover:bg-white/5",
                    )}
                  >
                    {template.name || template.code}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
});
export default BoardFilters;
