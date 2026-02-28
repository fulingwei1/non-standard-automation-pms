/**
 * 流水线视图组件
 *
 * 显示多项目阶段全景，类似看板/甘特图的横向布局
 */
import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  ChevronRight,
  Eye,
  Calendar,
  GitBranch,
  Star,
  MoreHorizontal,
} from "lucide-react";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
  Skeleton,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import {
  STAGE_STATUS,
  STAGE_CATEGORIES,
  getStatusConfig,
  getHealthConfig,
  getCategoryConfig,
} from "../constants";

/**
 * 加载骨架屏
 */
function PipelineViewSkeleton() {
  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <div className="space-y-4">
          {/* 表头骨架 */}
          <div className="flex gap-2 pb-2 border-b border-gray-700">
            <Skeleton className="h-8 w-32 bg-gray-700" />
            {[...Array(8)].map((_, i) => (
              <Skeleton key={i} className="h-8 w-20 bg-gray-700" />
            ))}
          </div>
          {/* 行骨架 */}
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex gap-2 items-center">
              <Skeleton className="h-12 w-32 bg-gray-700" />
              {[...Array(8)].map((_, j) => (
                <Skeleton key={j} className="h-8 w-20 bg-gray-700" />
              ))}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 阶段单元格组件
 */
function StageCell({ stage, onClick }) {
  const statusConfig = getStatusConfig(stage.status);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <motion.div
            className={cn(
              "min-w-[80px] h-8 rounded-md flex items-center justify-center cursor-pointer transition-all",
              "hover:ring-2 hover:ring-offset-1 hover:ring-offset-gray-900",
              statusConfig.bgColor
            )}
            style={{ borderColor: statusConfig.color }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onClick}
          >
            {/* 进度指示器 */}
            <div className="relative w-full h-full overflow-hidden rounded-md">
              {/* 进度条背景 */}
              <div
                className="absolute inset-0 opacity-30"
                style={{ backgroundColor: statusConfig.color }}
              />
              {/* 进度条 */}
              <motion.div
                className="absolute left-0 top-0 h-full"
                style={{ backgroundColor: statusConfig.color }}
                initial={{ width: 0 }}
                animate={{ width: `${stage.progress_pct}%` }}
                transition={{ duration: 0.3 }}
              />
              {/* 内容 */}
              <div className="relative z-10 flex items-center justify-center h-full px-2">
                {stage.is_milestone && (
                  <Star className="h-3 w-3 text-yellow-400 mr-1" />
                )}
                <span className={cn("text-xs font-medium", statusConfig.textColor)}>
                  {stage.progress_pct.toFixed(0)}%
                </span>
              </div>
            </div>
          </motion.div>
        </TooltipTrigger>
        <TooltipContent className="bg-gray-800 border-gray-700 text-white">
          <div className="space-y-1">
            <p className="font-medium">{stage.stage_name}</p>
            <p className="text-xs text-gray-400">
              状态: {statusConfig.label}
            </p>
            <p className="text-xs text-gray-400">
              进度: {stage.progress_pct.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-400">
              节点: {stage.completed_nodes}/{stage.total_nodes}
            </p>
            {stage.is_milestone && (
              <Badge className="bg-yellow-500/20 text-yellow-400 text-xs">
                里程碑
              </Badge>
            )}
            {stage.is_parallel && (
              <Badge className="bg-purple-500/20 text-purple-400 text-xs">
                可并行
              </Badge>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * 项目行组件
 */
function ProjectRow({ project, stageDefinitions, onSelectProject }) {
  const healthConfig = getHealthConfig(project.health_status);

  // 构建阶段映射，按 stage_code 索引
  const stageMap = useMemo(() => {
    const map = {};
    project.stages?.forEach((stage) => {
      map[stage.stage_code] = stage;
    });
    return map;
  }, [project.stages]);

  return (
    <motion.div
      className="flex items-center gap-2 py-2 border-b border-gray-700/50 hover:bg-gray-800/30 transition-colors"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
    >
      {/* 项目信息 */}
      <div className="min-w-[180px] flex items-center gap-2">
        <div
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: healthConfig.color }}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1">
            <span className="text-sm font-medium text-white truncate">
              {project.project_code}
            </span>
            <Badge className={cn("text-xs shrink-0", healthConfig.bgColor, healthConfig.textColor)}>
              {healthConfig.label}
            </Badge>
          </div>
          <p className="text-xs text-gray-400 truncate">{project.project_name}</p>
        </div>
      </div>

      {/* 阶段单元格 */}
      <div className="flex-1 flex gap-1 overflow-x-auto">
        {stageDefinitions.map((stageDef) => {
          const stage = stageMap[stageDef.stage_code];
          if (!stage) {
            return (
              <div
                key={stageDef.stage_code}
                className="min-w-[80px] h-8 rounded-md bg-gray-700/30 border border-dashed border-gray-600"
              />
            );
          }
          return (
            <StageCell
              key={stage.id}
              stage={stage}
              onClick={() => onSelectProject(project.project_id, "timeline")}
            />
          );
        })}
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-1 shrink-0">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-gray-400 hover:text-white"
                onClick={() => onSelectProject(project.project_id, "timeline")}
              >
                <Calendar className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>时间轴视图</TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-gray-400 hover:text-white"
                onClick={() => onSelectProject(project.project_id, "tree")}
              >
                <GitBranch className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>分解树视图</TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-gray-400 hover:text-white"
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="bg-gray-800 border-gray-700">
            <DropdownMenuItem
              onClick={() => onSelectProject(project.project_id, "timeline")}
              className="text-gray-300 hover:bg-gray-700"
            >
              <Eye className="h-4 w-4 mr-2" />
              查看详情
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </motion.div>
  );
}

/**
 * 阶段表头组件
 */
function StageHeader({ stageDefinitions }) {
  return (
    <div className="flex items-center gap-2 pb-2 border-b border-gray-700 sticky top-0 bg-gray-800/90 backdrop-blur-sm z-10">
      {/* 项目列标题 */}
      <div className="min-w-[180px] text-sm font-medium text-gray-400">
        项目
      </div>

      {/* 阶段列标题 */}
      <div className="flex-1 flex gap-1 overflow-x-auto">
        {stageDefinitions.map((stageDef) => {
          const categoryConfig = getCategoryConfig(stageDef.category);
          return (
            <TooltipProvider key={stageDef.stage_code}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      "min-w-[80px] h-8 rounded-md flex items-center justify-center",
                      "text-xs font-medium border",
                      categoryConfig.bgColor
                    )}
                    style={{ borderColor: categoryConfig.color, color: categoryConfig.color }}
                  >
                    {stageDef.is_milestone && (
                      <Star className="h-3 w-3 text-yellow-400 mr-1" />
                    )}
                    {stageDef.stage_code}
                  </div>
                </TooltipTrigger>
                <TooltipContent className="bg-gray-800 border-gray-700 text-white">
                  <div className="space-y-1">
                    <p className="font-medium">{stageDef.stage_name}</p>
                    <p className="text-xs text-gray-400">
                      分类: {categoryConfig.label}
                    </p>
                    {stageDef.estimated_days && (
                      <p className="text-xs text-gray-400">
                        预计: {stageDef.estimated_days} 天
                      </p>
                    )}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}
      </div>

      {/* 操作列 */}
      <div className="min-w-[100px] text-sm font-medium text-gray-400 text-center">
        操作
      </div>
    </div>
  );
}

/**
 * 分类图例组件
 */
function CategoryLegend() {
  return (
    <div className="flex items-center gap-4 text-xs text-gray-400">
      <span>分类:</span>
      {Object.entries(STAGE_CATEGORIES).map(([key, config]) => (
        <div key={key} className="flex items-center gap-1">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: config.color }}
          />
          <span>{config.label}</span>
        </div>
      ))}
      <span className="ml-4">状态:</span>
      {Object.entries(STAGE_STATUS).slice(0, 4).map(([key, config]) => (
        <div key={key} className="flex items-center gap-1">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: config.color }}
          />
          <span>{config.label}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * 模板分组组件
 */
function TemplateGroupSection({ group, onSelectProject }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        {/* 分组标题 */}
        <div
          className="flex items-center justify-between mb-3 cursor-pointer"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <div className="flex items-center gap-3">
            <ChevronRight
              className={cn(
                "h-5 w-5 text-gray-400 transition-transform",
                !isCollapsed && "rotate-90"
              )}
            />
            <div>
              <h3 className="text-lg font-semibold text-white">
                {group.template_name}
              </h3>
              <p className="text-sm text-gray-400">
                {group.template_code} · {group.project_count} 个项目 · {group.stage_definitions?.length || 0} 个阶段
              </p>
            </div>
          </div>
          <Badge className="bg-primary/20 text-primary">
            {group.project_count} 项目
          </Badge>
        </div>

        {/* 项目列表 */}
        {!isCollapsed && (
          <div className="overflow-x-auto">
            <StageHeader stageDefinitions={group.stage_definitions || []} />
            <div className="space-y-0 mt-2">
              {group.projects?.map((project) => (
                <ProjectRow
                  key={project.project_id}
                  project={project}
                  stageDefinitions={group.stage_definitions || []}
                  onSelectProject={onSelectProject}
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * 流水线视图主组件
 */
export default function PipelineView({ data, loading, onSelectProject }) {
  if (loading || !data) {
    return <PipelineViewSkeleton />;
  }

  const { projects = [], stage_definitions = [], template_groups = [] } = data;

  // 如果有模板分组，按分组显示
  const hasGroups = template_groups && template_groups.length > 0;

  if (!hasGroups && projects.length === 0) {
    return (
      <Card className="bg-gray-800/50 border-gray-700">
        <CardContent className="p-8 text-center">
          <p className="text-gray-400">暂无项目数据</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      className="space-y-4"
      initial="hidden"
      animate="visible"
      variants={fadeIn}
    >
      {/* 图例 */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardContent className="p-3">
          <CategoryLegend />
        </CardContent>
      </Card>

      {/* 按模板分组显示 */}
      {hasGroups ? (
        <div className="space-y-4">
          {template_groups.map((group) => (
            <TemplateGroupSection
              key={group.template_id}
              group={group}
              onSelectProject={onSelectProject}
            />
          ))}
        </div>
      ) : (
        /* 不分组显示（兼容旧模式） */
        <Card className="bg-gray-800/50 border-gray-700">
          <CardContent className="p-4">
            <div className="overflow-x-auto">
              <StageHeader stageDefinitions={stage_definitions} />
              <div className="space-y-0 mt-2">
                {projects.map((project) => (
                  <ProjectRow
                    key={project.project_id}
                    project={project}
                    stageDefinitions={stage_definitions}
                    onSelectProject={onSelectProject}
                  />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}
