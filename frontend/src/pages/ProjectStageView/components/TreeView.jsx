/**
 * 分解树视图组件
 *
 * 显示阶段/节点/任务的三级分解结构
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  FileText,
  CheckSquare,
  Square,
  User,
  Clock,
  Star,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Progress,
  Skeleton,
} from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import {
  TASK_PRIORITIES,
  getStatusConfig,
  getCategoryConfig,
} from "../constants";

/**
 * 加载骨架屏
 */
function TreeViewSkeleton() {
  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-10 w-full bg-gray-700" />
              <div className="pl-6 space-y-2">
                {[...Array(2)].map((_, j) => (
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
 * 任务节点组件
 */
function TaskItem({ task }) {
  const priorityConfig = TASK_PRIORITIES[task.priority] || TASK_PRIORITIES.NORMAL;

  return (
    <motion.div
      className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-gray-700/20 transition-colors"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
    >
      {/* 复选框图标 */}
      {task.status === "COMPLETED" ? (
        <CheckSquare className="h-4 w-4 text-green-400 shrink-0" />
      ) : (
        <Square className="h-4 w-4 text-gray-500 shrink-0" />
      )}

      {/* 任务信息 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "text-sm truncate",
              task.status === "COMPLETED" ? "text-gray-500 line-through" : "text-gray-300"
            )}
          >
            {task.task_name}
          </span>
          {task.priority !== "NORMAL" && (
            <Badge
              className="text-xs"
              style={{ backgroundColor: `${priorityConfig.color}20`, color: priorityConfig.color }}
            >
              {priorityConfig.label}
            </Badge>
          )}
        </div>
      </div>

      {/* 执行人 */}
      {task.assignee_name && (
        <span className="text-xs text-gray-500 flex items-center gap-1 shrink-0">
          <User className="h-3 w-3" />
          {task.assignee_name}
        </span>
      )}

      {/* 工时 */}
      {(task.estimated_hours || task.actual_hours) && (
        <span className="text-xs text-gray-500 flex items-center gap-1 shrink-0">
          <Clock className="h-3 w-3" />
          {task.actual_hours || 0}/{task.estimated_hours || 0}h
        </span>
      )}
    </motion.div>
  );
}

/**
 * 节点组件
 */
function NodeItem({ node, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen || node.status === "IN_PROGRESS");
  const statusConfig = getStatusConfig(node.status);
  const hasTasks = node.tasks && node.tasks?.length > 0;

  return (
    <div className="pl-4 border-l border-gray-700/50">
      {/* 节点头部 */}
      <div
        className={cn(
          "flex items-center gap-2 py-2 px-2 rounded cursor-pointer transition-colors",
          "hover:bg-gray-700/20",
          node.status === "IN_PROGRESS" && "bg-gray-700/10"
        )}
        onClick={() => hasTasks && setIsOpen(!isOpen)}
      >
        {/* 展开/收起图标 */}
        {hasTasks ? (
          <motion.div animate={{ rotate: isOpen ? 90 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronRight className="h-4 w-4 text-gray-500" />
          </motion.div>
        ) : (
          <div className="w-4" />
        )}

        {/* 文件夹图标 */}
        {hasTasks ? (
          isOpen ? (
            <FolderOpen className="h-4 w-4 text-blue-400" />
          ) : (
            <Folder className="h-4 w-4 text-blue-400" />
          )
        ) : (
          <FileText className="h-4 w-4 text-gray-400" />
        )}

        {/* 节点信息 */}
        <div className="flex-1 min-w-0 flex items-center gap-2">
          <span className="text-sm text-gray-200 truncate">{node.node_name}</span>
          <Badge className={cn("text-xs", statusConfig.bgColor, statusConfig.textColor)}>
            {statusConfig.label}
          </Badge>
        </div>

        {/* 任务统计 */}
        {hasTasks && (
          <span className="text-xs text-gray-500">
            {node.completed_tasks}/{node.total_tasks}
          </span>
        )}

        {/* 负责人 */}
        {node.assignee_name && (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <User className="h-3 w-3" />
            {node.assignee_name}
          </span>
        )}

        {/* 进度 */}
        <div className="w-20">
          <Progress value={node.progress} className="h-1.5 bg-gray-700" />
        </div>
      </div>

      {/* 子任务列表 */}
      <AnimatePresence>
        {isOpen && hasTasks && (
          <motion.div
            className="pl-6 space-y-0.5 pb-2"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            {(node.tasks || []).map((task) => (
              <TaskItem key={task.id} task={task} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * 阶段组件
 */
function StageItem({ stage, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen || stage.status === "IN_PROGRESS");
  const statusConfig = getStatusConfig(stage.status);
  const categoryConfig = getCategoryConfig(stage.category);
  const hasNodes = stage.nodes && stage.nodes?.length > 0;

  return (
    <motion.div
      className="border border-gray-700/50 rounded-lg overflow-hidden"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* 阶段头部 */}
      <div
        className={cn(
          "flex items-center gap-3 p-3 cursor-pointer transition-colors",
          "bg-gray-800/50 hover:bg-gray-700/50",
          stage.status === "IN_PROGRESS" && "bg-gray-700/30"
        )}
        onClick={() => hasNodes && setIsOpen(!isOpen)}
      >
        {/* 展开/收起图标 */}
        {hasNodes ? (
          <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronDown className="h-5 w-5 text-gray-400" />
          </motion.div>
        ) : (
          <div className="w-5" />
        )}

        {/* 阶段状态指示器 */}
        <div
          className="w-3 h-3 rounded-full shrink-0"
          style={{ backgroundColor: statusConfig.color }}
        />

        {/* 阶段信息 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white">{stage.stage_code}</span>
            <span className="text-sm text-gray-300 truncate">{stage.stage_name}</span>
            {stage.is_milestone && <Star className="h-4 w-4 text-yellow-400" />}
          </div>
        </div>

        {/* 状态和分类标签 */}
        <Badge className={cn("text-xs", statusConfig.bgColor, statusConfig.textColor)}>
          {statusConfig.label}
        </Badge>
        <Badge
          className="text-xs"
          style={{ backgroundColor: `${categoryConfig.color}20`, color: categoryConfig.color }}
        >
          {categoryConfig.label}
        </Badge>

        {/* 节点统计 */}
        <span className="text-xs text-gray-500">
          {stage.completed_nodes}/{stage.total_nodes} 节点
        </span>

        {/* 进度 */}
        <div className="w-24">
          <Progress value={stage.progress} className="h-2 bg-gray-700" />
        </div>
        <span className="text-xs text-gray-400 w-10 text-right">
          {stage.progress}%
        </span>
      </div>

      {/* 节点列表 */}
      <AnimatePresence>
        {isOpen && hasNodes && (
          <motion.div
            className="bg-gray-900/30 p-2 space-y-1"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            {(stage.nodes || []).map((node) => (
              <NodeItem key={node.id} node={node} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/**
 * 统计摘要组件
 */
function StatsSummary({ data }) {
  const {
    total_stages = 0,
    completed_stages = 0,
    total_nodes = 0,
    completed_nodes = 0,
    total_tasks = 0,
    completed_tasks = 0,
  } = data;

  const items = [
    { label: "阶段", completed: completed_stages, total: total_stages, color: "#3B82F6" },
    { label: "节点", completed: completed_nodes, total: total_nodes, color: "#8B5CF6" },
    { label: "任务", completed: completed_tasks, total: total_tasks, color: "#22C55E" },
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {(items || []).map((item) => (
        <div
          key={item.label}
          className="bg-gray-800/50 rounded-lg p-3 border border-gray-700"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">{item.label}</span>
            <span className="text-sm font-medium text-white">
              {item.completed}/{item.total}
            </span>
          </div>
          <Progress
            value={item.total > 0 ? (item.completed / item.total) * 100 : 0}
            className="h-1.5 bg-gray-700"
          />
        </div>
      ))}
    </div>
  );
}

/**
 * 分解树视图主组件
 */
export default function TreeView({ data, loading, stageActions: _stageActions, onRefresh: _onRefresh }) {
  if (loading || !data) {
    return <TreeViewSkeleton />;
  }

  const { stages = [], project_code, project_name, overall_progress } = data;

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
      {/* 项目摘要 */}
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
          <Progress value={overall_progress} className="h-2 bg-gray-700 mb-4" />
          <StatsSummary data={data} />
        </CardContent>
      </Card>

      {/* 分解树 */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardContent className="p-4">
          <div className="space-y-2">
            {(stages || []).map((stage) => (
              <StageItem key={stage.id} stage={stage} />
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
