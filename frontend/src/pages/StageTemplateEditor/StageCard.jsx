

import { cn } from "../../lib/utils";
import { NODE_TYPES, COMPLETION_METHODS } from "./constants";

function NodeRow({ stage, node, onEdit, onDelete }) {
  return (
    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5 hover:border-white/10 transition-colors">
      <div className="flex items-center gap-3">
        <GripVertical className="h-4 w-4 text-slate-600 cursor-grab" />
        <Badge
          variant="outline"
          className={cn(
            "text-xs",
            NODE_TYPES[node.node_type]?.color || NODE_TYPES.TASK.color
          )}
        >
          {NODE_TYPES[node.node_type]?.label || "任务"}
        </Badge>
        <code className="text-xs font-mono text-slate-400 bg-white/5 px-2 py-0.5 rounded">
          {node.node_code}
        </code>
        <span className="text-white">{node.node_name}</span>
        <span className="text-xs text-slate-500">
          {COMPLETION_METHODS[node.completion_method] || "手动完成"}
        </span>
        <span className="text-xs text-slate-500">
          {node.estimated_days} 天
        </span>
        {node.is_required && (
          <Badge variant="secondary" className="text-xs">
            必需
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => onEdit(stage, node)}
        >
          <Edit3 className="h-3 w-3" />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
          onClick={() => onDelete(stage, node)}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}

export default function StageCard({
  stage,
  stageIndex: _stageIndex,
  isExpanded,
  onToggleExpanded,
  onAddNode,
  onEditStage,
  onDeleteStage,
  onEditNode,
  onDeleteNode,
}) {
  return (
    <Card className="bg-surface-100 border-white/5 overflow-hidden">
      {/* 阶段标题 */}
      <CardHeader
        className={cn(
          "border-b border-white/5 cursor-pointer hover:bg-white/[0.02] transition-colors",
          isExpanded ? "bg-white/[0.02]" : ""
        )}
        onClick={() => onToggleExpanded(stage.id)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-slate-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-slate-400" />
            )}
            <GripVertical className="h-4 w-4 text-slate-600 cursor-grab" />
            <Badge variant="outline" className="bg-violet-500/20 text-violet-400 border-violet-500/30">
              {stage.stage_code}
            </Badge>
            <span className="text-white font-medium">{stage.stage_name}</span>
            <span className="text-sm text-slate-400">
              {stage.estimated_days} 天
            </span>
            {stage.is_required && (
              <Badge variant="secondary" className="text-xs">
                必需
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={(e) => {
                e.stopPropagation();
                onAddNode(stage);
              }}
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={(e) => {
                e.stopPropagation();
                onEditStage(stage);
              }}
            >
              <Edit3 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteStage(stage);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {stage.description && (
          <p className="text-sm text-slate-400 mt-2 ml-9">{stage.description}</p>
        )}
      </CardHeader>

      {/* 节点列表 */}
      {isExpanded && (
        <CardContent className="p-4">
          <div className="space-y-2">
            {(stage.node_definitions || []).map((node, nodeIndex) => (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: nodeIndex * 0.03 }}
              >
                <NodeRow
                  stage={stage}
                  node={node}
                  onEdit={onEditNode}
                  onDelete={onDeleteNode}
                />
              </motion.div>
            ))}
            {(stage.node_definitions || []).length === 0 && (
              <div className="text-center py-6 text-slate-500">
                暂无节点，点击上方 "+" 添加节点
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
