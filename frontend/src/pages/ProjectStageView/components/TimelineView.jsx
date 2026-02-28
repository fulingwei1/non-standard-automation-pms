/**
 * 时间轴视图组件
 *
 * 显示单项目的阶段和节点时间线（甘特图样式）
 */
import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronRight,
  Play,
  CheckCircle2,
  SkipForward,
  AlertTriangle,
  Clock,
  User,
  Calendar,
  Star,
  Zap,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Skeleton,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import {
  STAGE_STATUS,
  NODE_TYPES,
  getStatusConfig,
  getCategoryConfig,
} from "../constants";

/**
 * 加载骨架屏
 */
function TimelineViewSkeleton() {
  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-12 w-full bg-gray-700" />
              <div className="pl-8 space-y-2">
                {[...Array(3)].map((_, j) => (
                  <Skeleton key={j} className="h-8 w-full bg-gray-700/50" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 节点组件
 */
function NodeItem({ node, onAction }) {
  const statusConfig = getStatusConfig(node.status);
  const nodeTypeConfig = NODE_TYPES[node.node_type] || NODE_TYPES.TASK;

  return (
    <motion.div
      className={cn(
        "flex items-center gap-3 p-2 rounded-lg transition-colors",
        "hover:bg-gray-700/30 group"
      )}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
    >
      {/* 状态指示器 */}
      <div
        className={cn("w-2 h-2 rounded-full shrink-0")}
        style={{ backgroundColor: statusConfig.color }}
      />

      {/* 节点信息 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm text-white truncate">{node.node_name}</span>
          <Badge className="text-xs bg-gray-700 text-gray-400 shrink-0">
            {nodeTypeConfig.label}
          </Badge>
          <Badge className={cn("text-xs shrink-0", statusConfig.bgColor, statusConfig.textColor)}>
            {statusConfig.label}
          </Badge>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-400 mt-1">
          {node.assignee_name && (
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              {node.assignee_name}
            </span>
          )}
          {node.planned_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {node.planned_date}
            </span>
          )}
          {node.progress > 0 && (
            <span className="flex items-center gap-1">
              进度: {node.progress}%
            </span>
          )}
        </div>
      </div>

      {/* 进度条 */}
      <div className="w-24 hidden md:block">
        <Progress value={node.progress} className="h-1.5 bg-gray-700" />
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {node.status === "PENDING" && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-blue-400 hover:text-blue-300"
                  onClick={() => onAction?.("start", node.id)}
                >
                  <Play className="h-3 w-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>开始节点</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        {node.status === "IN_PROGRESS" && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-green-400 hover:text-green-300"
                  onClick={() => onAction?.("complete", node.id)}
                >
                  <CheckCircle2 className="h-3 w-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>完成节点</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        {(node.status === "PENDING" || node.status === "IN_PROGRESS") && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-gray-400 hover:text-gray-300"
                  onClick={() => onAction?.("skip", node.id)}
                >
                  <SkipForward className="h-3 w-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>跳过节点</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    </motion.div>
  );
}

/**
 * 阶段组件
 */
function StageItem({ stage, index, onNodeAction, onStageAction }) {
  const [isOpen, setIsOpen] = useState(stage.status === "IN_PROGRESS");
  const statusConfig = getStatusConfig(stage.status);
  const categoryConfig = getCategoryConfig(stage.category);

  // 计算阶段内节点统计
  const nodeStats = useMemo(() => {
    const nodes = stage.nodes || [];
    return {
      total: nodes.length,
      completed: (nodes || []).filter((n) => n.status === "COMPLETED").length,
      inProgress: (nodes || []).filter((n) => n.status === "IN_PROGRESS").length,
    };
  }, [stage.nodes]);

  return (
    <motion.div
      className="border-l-2 ml-3"
      style={{ borderColor: statusConfig.color }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <div>
        <div
          className={cn(
            "flex items-center gap-3 p-3 rounded-r-lg cursor-pointer transition-colors",
            "hover:bg-gray-700/30",
            stage.status === "IN_PROGRESS" && "bg-gray-700/20"
          )}
          onClick={() => setIsOpen(!isOpen)}
          >
            {/* 展开/收起图标 */}
            <motion.div
              animate={{ rotate: isOpen ? 90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </motion.div>

            {/* 阶段状态圆点 */}
            <div
              className={cn(
                "w-4 h-4 rounded-full flex items-center justify-center",
                statusConfig.bgColor
              )}
              style={{ border: `2px solid ${statusConfig.color}` }}
            >
              {stage.status === "COMPLETED" && (
                <CheckCircle2 className="h-3 w-3" style={{ color: statusConfig.color }} />
              )}
              {stage.status === "IN_PROGRESS" && (
                <Clock className="h-2 w-2" style={{ color: statusConfig.color }} />
              )}
            </div>

            {/* 阶段信息 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">
                  {stage.stage_code}
                </span>
                <span className="text-sm text-gray-300">
                  {stage.stage_name}
                </span>
                {stage.is_milestone && (
                  <Star className="h-4 w-4 text-yellow-400" />
                )}
                {stage.is_parallel && (
                  <Zap className="h-4 w-4 text-purple-400" />
                )}
                <Badge
                  className={cn("text-xs", statusConfig.bgColor, statusConfig.textColor)}
                >
                  {statusConfig.label}
                </Badge>
                <Badge
                  className="text-xs"
                  style={{ backgroundColor: `${categoryConfig.color}20`, color: categoryConfig.color }}
                >
                  {categoryConfig.label}
                </Badge>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-400 mt-1">
                <span>
                  节点: {nodeStats.completed}/{nodeStats.total}
                </span>
                <span>进度: {stage.progress}%</span>
                {stage.planned_start_date && (
                  <span>
                    计划: {stage.planned_start_date} - {stage.planned_end_date}
                  </span>
                )}
              </div>
            </div>

            {/* 进度条 */}
            <div className="w-32 hidden md:block">
              <Progress value={stage.progress} className="h-2 bg-gray-700" />
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center gap-1">
              {stage.status === "PENDING" && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-blue-400 hover:text-blue-300"
                        onClick={(e) => {
                          e.stopPropagation();
                          onStageAction?.("start", stage.id);
                        }}
                      >
                        <Play className="h-4 w-4 mr-1" />
                        开始
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>开始此阶段</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              {stage.status === "IN_PROGRESS" && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-green-400 hover:text-green-300"
                        onClick={(e) => {
                          e.stopPropagation();
                          onStageAction?.("complete", stage.id);
                        }}
                      >
                        <CheckCircle2 className="h-4 w-4 mr-1" />
                        完成
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>完成此阶段</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              {(stage.status === "IN_PROGRESS" || stage.status === "DELAYED") && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-orange-400 hover:text-orange-300"
                        onClick={(e) => {
                          e.stopPropagation();
                          onStageAction?.("block", stage.id);
                        }}
                      >
                        <AlertTriangle className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>标记受阻</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </div>

        <AnimatePresence>
          {isOpen && stage.nodes && stage.nodes?.length > 0 && (
            <motion.div
              className="ml-8 pl-4 border-l border-gray-700 space-y-1 pb-2"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              {(stage.nodes || []).map((node) => (
                <NodeItem
                  key={node.id}
                  node={node}
                  onAction={onNodeAction}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

/**
 * 时间轴视图主组件
 */
export default function TimelineView({ data, loading, stageActions, onRefresh }) {
  if (loading || !data) {
    return <TimelineViewSkeleton />;
  }

  const { stages = [], project_code, project_name, overall_progress } = data;

  const handleNodeAction = async (action, nodeId) => {
    let success = false;
    try {
      switch (action) {
        case "start":
          success = await stageActions?.startNode(nodeId);
          break;
        case "complete":
          success = await stageActions?.completeNode(nodeId);
          break;
        case "skip":
          success = await stageActions?.skipNode(nodeId);
          break;
        default:
          console.warn("未知节点操作:", action);
          break;
      }
    } catch (err) {
      console.error("节点操作失败:", err);
    }
    if (success) {
      onRefresh?.();
    }
  };

  const handleStageAction = async (action, stageId) => {
    let success = false;
    switch (action) {
      case "start":
        success = await stageActions?.startStage(stageId);
        break;
      case "complete":
        success = await stageActions?.completeStage(stageId);
        break;
      case "block":
        success = await stageActions?.updateStageStatus(stageId, "BLOCKED");
        break;
      default:
        break;
    }
    if (success) {
      onRefresh?.();
    }
  };

  if (stages.length === 0) {
    return (
      <Card className="bg-gray-800/50 border-gray-700">
        <CardContent className="p-8 text-center">
          <p className="text-gray-400">该项目暂无阶段数据</p>
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
      {/* 项目总览卡片 */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg text-white">
              {project_code} - {project_name}
            </CardTitle>
            <Badge className="text-lg bg-blue-500/20 text-blue-400">
              {overall_progress?.toFixed(1)}%
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <Progress value={overall_progress} className="h-2 bg-gray-700" />
        </CardContent>
      </Card>

      {/* 阶段列表 */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardContent className="p-4">
          <div className="space-y-1">
            {(stages || []).map((stage, index) => (
              <StageItem
                key={stage.id}
                stage={stage}
                index={index}
                onNodeAction={handleNodeAction}
                onStageAction={handleStageAction}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
