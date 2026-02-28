/**
 * 项目阶段视图主页面
 *
 * 提供三种视图切换：
 * - 流水线视图 (Pipeline): 多项目阶段全景
 * - 时间轴视图 (Timeline): 单项目甘特图
 * - 分解树视图 (Tree): 阶段/节点/任务分解
 */
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Calendar,
  GitBranch,
  RefreshCw,
  Filter,
  Search,
  ChevronDown,
  ArrowLeft,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  Button,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Badge,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";

// Hooks
import { useStageViews, useStageActions } from "./hooks";

// Components
import {
  StatisticsCards,
  ProgressOverviewCard,
  CategoryStatsCard,
  CurrentStageDistributionCard,
  PipelineView,
  TimelineView,
  TreeView,
} from "./components";

// Constants
import {
  VIEW_TYPES,
  STAGE_CATEGORIES,
  HEALTH_STATUS,
} from "./constants";

/**
 * 视图选项卡配置
 */
const VIEW_TABS = [
  {
    value: VIEW_TYPES.PIPELINE,
    label: "流水线视图",
    icon: LayoutDashboard,
    description: "多项目阶段全景",
  },
  {
    value: VIEW_TYPES.TIMELINE,
    label: "时间轴视图",
    icon: Calendar,
    description: "单项目甘特图",
  },
  {
    value: VIEW_TYPES.TREE,
    label: "分解树视图",
    icon: GitBranch,
    description: "阶段/节点/任务分解",
  },
];

/**
 * 筛选栏组件
 */
function FilterBar({ filters, updateFilters, availableTemplates = [] }) {
  // 获取当前选中模板的名称
  const selectedTemplate = (availableTemplates || []).find(t => t.id === filters.templateId);

  return (
    <div className="flex items-center gap-4 flex-wrap">
      {/* 搜索框 */}
      <div className="relative flex-1 min-w-[200px] max-w-[300px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="搜索项目..."
          value={filters.search || ""}
          onChange={(e) => updateFilters({ search: e.target.value })}
          className="pl-10 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
        />
      </div>

      {/* 模板筛选 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="bg-gray-800 border-gray-700 text-gray-300">
            <LayoutDashboard className="h-4 w-4 mr-2" />
            {selectedTemplate ? selectedTemplate.name : "全部模板"}
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="bg-gray-800 border-gray-700">
          <DropdownMenuItem
            onClick={() => updateFilters({ templateId: null })}
            className="text-gray-300 hover:bg-gray-700"
          >
            全部模板
          </DropdownMenuItem>
          {(availableTemplates || []).map((template) => (
            <DropdownMenuItem
              key={template.id}
              onClick={() => updateFilters({ templateId: template.id })}
              className="text-gray-300 hover:bg-gray-700"
            >
              <Badge className="mr-2 bg-blue-500/20 text-blue-400">
                {template.code}
              </Badge>
              {template.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 分类筛选 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="bg-gray-800 border-gray-700 text-gray-300">
            <Filter className="h-4 w-4 mr-2" />
            {filters.category
              ? STAGE_CATEGORIES[filters.category]?.label
              : "阶段分类"}
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="bg-gray-800 border-gray-700">
          <DropdownMenuItem
            onClick={() => updateFilters({ category: null })}
            className="text-gray-300 hover:bg-gray-700"
          >
            全部分类
          </DropdownMenuItem>
          {Object.entries(STAGE_CATEGORIES).map(([key, config]) => (
            <DropdownMenuItem
              key={key}
              onClick={() => updateFilters({ category: key })}
              className="text-gray-300 hover:bg-gray-700"
            >
              {config.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 健康状态筛选 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="bg-gray-800 border-gray-700 text-gray-300">
            {filters.healthStatus
              ? HEALTH_STATUS[filters.healthStatus]?.label
              : "健康状态"}
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="bg-gray-800 border-gray-700">
          <DropdownMenuItem
            onClick={() => updateFilters({ healthStatus: null })}
            className="text-gray-300 hover:bg-gray-700"
          >
            全部状态
          </DropdownMenuItem>
          {Object.entries(HEALTH_STATUS).map(([key, config]) => (
            <DropdownMenuItem
              key={key}
              onClick={() => updateFilters({ healthStatus: key })}
              className="text-gray-300 hover:bg-gray-700"
            >
              <Badge
                className="mr-2"
                style={{ backgroundColor: `${config.color}20`, color: config.color }}
              >
                {config.label}
              </Badge>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 分组切换 */}
      <Button
        variant={filters.groupByTemplate ? "default" : "outline"}
        onClick={() => updateFilters({ groupByTemplate: !filters.groupByTemplate })}
        className={cn(
          filters.groupByTemplate
            ? "bg-blue-600 text-white hover:bg-blue-700"
            : "bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700"
        )}
      >
        <GitBranch className="h-4 w-4 mr-2" />
        按模板分组
      </Button>
    </div>
  );
}

/**
 * 项目阶段视图主组件
 */
export default function ProjectStageView() {
  // 数据 Hook
  const {
    currentView,
    selectedProjectId,
    setSelectedProjectId,
    switchView,
    pipelineData,
    timelineData,
    treeData,
    loading,
    error,
    filters,
    updateFilters,
    refresh,
  } = useStageViews();

  // 操作 Hook
  const stageActions = useStageActions(selectedProjectId);

  /**
   * 处理项目选择（从流水线视图进入详情视图）
   */
  const handleSelectProject = (projectId, viewType = VIEW_TYPES.TIMELINE) => {
    setSelectedProjectId(projectId);
    switchView(viewType, projectId);
  };

  /**
   * 返回流水线视图
   */
  const handleBackToPipeline = () => {
    setSelectedProjectId(null);
    switchView(VIEW_TYPES.PIPELINE);
  };

  /**
   * 渲染当前视图
   */
  const renderView = () => {
    switch (currentView) {
      case VIEW_TYPES.PIPELINE:
        return (
          <PipelineView
            data={pipelineData}
            loading={loading}
            onSelectProject={handleSelectProject}
          />
        );
      case VIEW_TYPES.TIMELINE:
        return (
          <TimelineView
            data={timelineData}
            loading={loading}
            stageActions={stageActions}
            onRefresh={refresh}
          />
        );
      case VIEW_TYPES.TREE:
        return (
          <TreeView
            data={treeData}
            loading={loading}
            stageActions={stageActions}
            onRefresh={refresh}
          />
        );
      default:
        return null;
    }
  };

  return (
    <motion.div
      className="min-h-screen bg-gray-900 p-6 space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* 页面头部 */}
      <motion.div variants={fadeIn}>
        <PageHeader
          title="项目阶段视图"
          description="查看和管理项目的阶段进度"
          action={
            <div className="flex items-center gap-2">
              {selectedProjectId && (
                <Button
                  variant="outline"
                  onClick={handleBackToPipeline}
                  className="bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  返回全景
                </Button>
              )}
              <Button
                variant="outline"
                onClick={refresh}
                disabled={loading}
                className="bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700"
              >
                <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                刷新
              </Button>
            </div>
          }
        />
      </motion.div>

      {/* 错误提示 */}
      {error && (
        <motion.div variants={fadeIn}>
          <Card className="bg-red-900/20 border-red-800">
            <CardContent className="p-4 text-red-400">
              {error}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* 统计卡片 - 仅在流水线视图显示 */}
      {currentView === VIEW_TYPES.PIPELINE && pipelineData?.statistics && (
        <motion.div variants={fadeIn}>
          <StatisticsCards statistics={pipelineData.statistics} />
        </motion.div>
      )}

      {/* 进度概览 - 在详情视图显示 */}
      {(currentView === VIEW_TYPES.TIMELINE || currentView === VIEW_TYPES.TREE) && (
        <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ProgressOverviewCard data={currentView === VIEW_TYPES.TREE ? treeData : timelineData} />
          {pipelineData?.statistics && (
            <>
              <CategoryStatsCard byCategory={pipelineData.statistics.by_category} />
              <CurrentStageDistributionCard byCurrentStage={pipelineData.statistics.by_current_stage} />
            </>
          )}
        </motion.div>
      )}

      {/* 视图切换和筛选 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gray-800/50 border-gray-700">
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              {/* 视图切换标签 */}
              <Tabs
                value={currentView}
                onValueChange={(value) => {
                  if (value === VIEW_TYPES.PIPELINE) {
                    handleBackToPipeline();
                  } else if (selectedProjectId) {
                    switchView(value, selectedProjectId);
                  }
                }}
              >
                <TabsList className="bg-gray-900/50">
                  {VIEW_TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isDisabled =
                      tab.value !== VIEW_TYPES.PIPELINE && !selectedProjectId;
                    return (
                      <TabsTrigger
                        key={tab.value}
                        value={tab.value}
                        disabled={isDisabled}
                        className={cn(
                          "data-[state=active]:bg-gray-700",
                          isDisabled && "opacity-50 cursor-not-allowed"
                        )}
                      >
                        <Icon className="h-4 w-4 mr-2" />
                        {tab.label}
                      </TabsTrigger>
                    );
                  })}
                </TabsList>
              </Tabs>

              {/* 筛选栏 - 仅在流水线视图显示 */}
              {currentView === VIEW_TYPES.PIPELINE && (
                <FilterBar
                  filters={filters}
                  updateFilters={updateFilters}
                  availableTemplates={pipelineData?.available_templates || []}
                />
              )}

              {/* 当前项目信息 - 在详情视图显示 */}
              {selectedProjectId && currentView !== VIEW_TYPES.PIPELINE && (
                <div className="flex items-center gap-2 text-gray-400">
                  <span>当前项目:</span>
                  <Badge className="bg-blue-500/20 text-blue-400">
                    {timelineData?.project_code || treeData?.project_code || `#${selectedProjectId}`}
                  </Badge>
                  <span className="text-sm">
                    {timelineData?.project_name || treeData?.project_name}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 主内容区 */}
      <motion.div variants={fadeIn}>
        {renderView()}
      </motion.div>
    </motion.div>
  );
}
