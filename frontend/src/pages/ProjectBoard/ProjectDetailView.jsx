import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { Badge, Card, CardContent, Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui";
import {
  Layers,
  ArrowLeft,
  RefreshCw,
  Calendar,
  GitBranch,
  Target,
} from "lucide-react";

import {
  PipelineView,
  TimelineView,
  TreeView,
} from "../../pages/ProjectStageView/components";

import { VIEW_TYPES } from "../../pages/ProjectStageView/constants";

import MilestonePanel from "./MilestonePanel";

export default function ProjectDetailView({
  selectedProjectId,
  detailViewMode,
  stageViewsHook,
  stageActions,
  milestones,
  milestonesLoading,
  onBack,
  onDetailViewChange,
  onMilestoneRefresh,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4">
      {/* 详情视图头部 */}
      <Card className="bg-surface-1 border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                返回项目列表
              </button>
              <div className="h-6 w-px bg-white/10" />
              <div className="flex items-center gap-2">
                <Badge className="bg-primary/20 text-primary">
                  {selectedProjectId}
                </Badge>
              </div>
            </div>
            <button
              onClick={stageViewsHook.refresh}
              disabled={stageViewsHook.loading}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <RefreshCw className={cn("w-4 h-4", stageViewsHook.loading && "animate-spin")} />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* 视图切换标签 */}
      <Tabs value={detailViewMode || "unknown"} onValueChange={onDetailViewChange}>
        <TabsList className="bg-surface-1 border border-white/10">
          <TabsTrigger value={VIEW_TYPES.PIPELINE} className="data-[state=active]:bg-blue-500">
            <Layers className="w-4 h-4 mr-2" />
            流水线视图
          </TabsTrigger>
          <TabsTrigger value={VIEW_TYPES.TIMELINE} className="data-[state=active]:bg-green-500">
            <Calendar className="w-4 h-4 mr-2" />
            时间轴视图
          </TabsTrigger>
          <TabsTrigger value={VIEW_TYPES.TREE} className="data-[state=active]:bg-purple-500">
            <GitBranch className="w-4 h-4 mr-2" />
            分解树视图
          </TabsTrigger>
          <TabsTrigger value="milestones" className="data-[state=active]:bg-amber-500">
            <Target className="w-4 h-4 mr-2" />
            里程碑
          </TabsTrigger>
        </TabsList>

        <TabsContent value={VIEW_TYPES.PIPELINE} className="mt-4">
          <PipelineView
            data={{
              ...stageViewsHook.pipelineData,
              projects: stageViewsHook.pipelineData?.projects?.filter(p => p.project_id === selectedProjectId) || [],
            }}
            loading={stageViewsHook.loading}
            onSelectProject={() => {}}
          />
        </TabsContent>

        <TabsContent value={VIEW_TYPES.TIMELINE} className="mt-4">
          <TimelineView
            data={stageViewsHook.timelineData}
            loading={stageViewsHook.loading}
            stageActions={stageActions}
            onRefresh={stageViewsHook.refresh}
          />
        </TabsContent>

        <TabsContent value={VIEW_TYPES.TREE} className="mt-4">
          <TreeView
            data={stageViewsHook.treeData}
            loading={stageViewsHook.loading}
            stageActions={stageActions}
            onRefresh={stageViewsHook.refresh}
          />
        </TabsContent>

        <TabsContent value="milestones" className="mt-4">
          <MilestonePanel
            milestones={milestones}
            loading={milestonesLoading}
            onRefresh={onMilestoneRefresh}
          />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
