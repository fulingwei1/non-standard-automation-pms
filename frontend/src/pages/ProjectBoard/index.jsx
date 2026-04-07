import { useState, useEffect, useMemo, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { PROJECT_STAGES } from "../../lib/constants";
import { useRoleFilter } from "../../hooks/useRoleFilter";
import { projectApi, milestoneApi } from "../../services/api";



// 导入阶段视图组件



// 导入阶段视图常量和hooks
import {
  VIEW_TYPES,
} from "../../pages/ProjectStageView/constants";
import { useStageViews, useStageActions } from "../../pages/ProjectStageView/hooks";

// 导入拆分出的子组件和常量
import { getStoredUser } from "./constants";

export default function ProjectBoard() {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [projects, setProjects] = useState([]);
  const [user] = useState(getStoredUser);

  // 从 URL 参数获取初始视图模式
  const getInitialViewMode = () => {
    const viewParam = searchParams.get("view");
    const validViews = ["card", "kanban", "matrix", "list", "pipeline", "timeline", "tree"];
    return validViews.includes(viewParam) ? viewParam : "kanban";
  };

  // 筛选状态
  const [viewMode, setViewMode] = useState(getInitialViewMode);
  const [filterMode, setFilterMode] = useState("my");
  const [statusFilter, setStatusFilter] = useState("all");
  const [healthFilter, setHealthFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedStages, setCollapsedStages] = useState({});

  // 阶段视图筛选状态
  const [templateFilter, setTemplateFilter] = useState("all");
  const [groupByTemplate, setGroupByTemplate] = useState(true);

  // 新增：阶段视图相关状态
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [detailViewMode, setDetailViewMode] = useState(VIEW_TYPES.PIPELINE);

  // 新建项目对话框状态
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [recommendedTemplates, setRecommendedTemplates] = useState([]);

  // 里程碑数据状态
  const [milestones, setMilestones] = useState([]);
  const [milestonesLoading, setMilestonesLoading] = useState(false);

  // 使用阶段视图Hook
  const stageViewsHook = useStageViews(VIEW_TYPES.PIPELINE);
  const stageActions = useStageActions(selectedProjectId);

  // 使用角色筛选 Hook
  const {
    relevantStages: _relevantStages,
    isProjectRelevant,
    isStageRelevant,
    filterProjects,
    groupByStage,
    stageStats: _stageStats
  } = useRoleFilter(user, projects);

  // 加载数据
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await projectApi.list();
      // API返回分页格式：{ items: [], total: 0, page: 1, page_size: 20, pages: 0 }
      const items = response.data?.items || response.data?.items || response.data || [];
      setProjects(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setError(err);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 加载模板推荐
  useEffect(() => {
    if (showCreateDialog) {
      const loadRecommendedTemplates = async () => {
        try {
          const response = await projectApi.recommendTemplates({ limit: 5 });
          setRecommendedTemplates(response.data?.recommendations || []);
        } catch (err) {
          console.error("Failed to load recommended templates:", err);
          setRecommendedTemplates([]);
        }
      };
      loadRecommendedTemplates();
    }
  }, [showCreateDialog]);

  // 加载里程碑数据
  const loadMilestones = useCallback(async (projectId) => {
    if (!projectId) return;
    setMilestonesLoading(true);
    try {
      const res = await milestoneApi.list({ project_id: projectId });
      const list = res?.data?.items ?? res?.data ?? res ?? [];
      setMilestones(Array.isArray(list) ? list : []);
    } catch (err) {
      console.error("Failed to load milestones:", err);
      setMilestones([]);
    } finally {
      setMilestonesLoading(false);
    }
  }, []);

  // 创建项目处理
  const handleCreateProject = async (data) => {
    try {
      await projectApi.create(data);
      setShowCreateDialog(false);
      fetchData();
    } catch (err) {
      alert("创建项目失败: " + (err.response?.data?.detail || err.message));
    }
  };

  // 当切换到阶段视图模式时，加载对应的数据
  useEffect(() => {
    if (viewMode === "pipeline") {
      // 应用当前筛选条件
      stageViewsHook.updateFilters({
        category: null, // 可以根据需要映射statusFilter
        healthStatus: healthFilter !== "all" ? healthFilter : null,
        templateId: templateFilter !== "all" ? templateFilter : null,
        groupByTemplate: groupByTemplate,
        search: searchQuery,
      });
      stageViewsHook.loadPipelineData();
    }
    // timeline和tree视图在选择项目后才加载数据
  }, [viewMode, healthFilter, searchQuery, templateFilter, groupByTemplate]);

  // 筛选后的项目
  const filteredProjects = useMemo(() => {
    let result = projects;

    // 智能筛选模式
    if (filterMode === "my") {
      result = filterProjects(result, "my");
    }

    // 状态筛选
    if (statusFilter !== "all") {
      result = (result || []).filter((p) => p.status === statusFilter);
    }

    // 健康度筛选
    if (healthFilter !== "all") {
      result = (result || []).filter((p) => p.health === healthFilter);
    }

    // 搜索
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = (result || []).filter(
        (p) =>
        p.project_code?.toLowerCase().includes(query) ||
        p.name?.toLowerCase().includes(query) ||
        p.customer_name?.toLowerCase().includes(query)
      );
    }

    return result;
  }, [
  projects,
  filterMode,
  statusFilter,
  healthFilter,
  searchQuery,
  filterProjects]
  );

  // 按阶段分组的项目
  const projectsByStage = useMemo(() => {
    return groupByStage(filteredProjects);
  }, [filteredProjects, groupByStage]);

  // 统计信息
  const stats = useMemo(() => {
    const healthCounts = { H1: 0, H2: 0, H3: 0, H4: 0 };
    (filteredProjects || []).forEach((p) => {
      const h = p.health || "H1";
      healthCounts[h]++;
    });

    return {
      total: projects?.length,
      filtered: filteredProjects.length,
      myCount: filterProjects(projects, "my").length,
      ...healthCounts
    };
  }, [projects, filteredProjects, filterProjects]);

  // 处理阶段折叠
  const handleToggleCollapse = (stageKey, collapsed) => {
    setCollapsedStages((prev) => ({
      ...prev,
      [stageKey]: collapsed
    }));
  };

  // 处理项目点击
  const handleProjectClick = (project) => {
    // 选中项目并显示详情视图（带三个标签页）
    setSelectedProjectId(project.id);
    setDetailViewMode(VIEW_TYPES.PIPELINE); // 默认显示流水线视图

    // 加载时间轴和分解树数据
    stageViewsHook.loadTimelineData(project.id);
    stageViewsHook.loadTreeData(project.id);
  };

  // 处理返回项目列表
  const handleBackToProjects = () => {
    setSelectedProjectId(null);
  };

  // 处理详情视图切换
  const handleDetailViewChange = (viewType) => {
    setDetailViewMode(viewType);
    if (selectedProjectId) {
      if (viewType === VIEW_TYPES.TIMELINE) {
        stageViewsHook.loadTimelineData(selectedProjectId);
      } else if (viewType === VIEW_TYPES.TREE) {
        stageViewsHook.loadTreeData(selectedProjectId);
      } else if (viewType === "milestones") {
        loadMilestones(selectedProjectId);
      }
    }
  };

  // 滚动看板
  const scrollBoard = (direction) => {
    const container = document.getElementById("board-container");
    if (container) {
      const scrollAmount = 320;
      container.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth"
      });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen">

      {/* 页面头部 */}
      <PageHeader
        title="项目中心"
        description="多维度可视化项目状态，快速定位关注项目"
        breadcrumb={[{ label: "首页", href: "/" }, { label: "项目中心" }]}
        actions={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-1" />
            新建项目
          </Button>
        }
      />


      {/* 筛选器 */}
      <BoardFilters
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        filterMode={filterMode}
        onFilterModeChange={setFilterMode}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        healthFilter={healthFilter}
        onHealthFilterChange={setHealthFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onRefresh={fetchData}
        isLoading={loading}
        stats={stats}
        templateFilter={templateFilter}
        onTemplateFilterChange={setTemplateFilter}
        groupByTemplate={groupByTemplate}
        onGroupByTemplateChange={setGroupByTemplate}
        availableTemplates={stageViewsHook.data?.available_templates || []} />


      {/* 错误状态 */}
      {error && !loading &&
      <ApiIntegrationError
        error={error}
        apiEndpoint="/api/v1/projects"
        onRetry={fetchData} />

      }

      {/* 加载状态 */}
      {loading &&
      <div className="flex gap-4 overflow-hidden">
          {[1, 2, 3, 4, 5].map((i) =>
        <div key={i} className="min-w-[280px]">
              <Skeleton className="h-16 mb-2" />
              <Skeleton className="h-32 mb-2" />
              <Skeleton className="h-32 mb-2" />
              <Skeleton className="h-32" />
        </div>
        )}
      </div>
      }

      {/* 卡片视图 */}
      {!loading && !error && viewMode === "card" &&
      <motion.div
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
      >
        {(filteredProjects || []).map((project) => (
          <ProjectCard
            key={project.id}
            project={project}
            onClick={() => handleProjectClick(project)}
          />
        ))}
      </motion.div>
      }

      {/* 看板视图 */}
      {!loading && !error && viewMode === "kanban" &&
      <div className="relative">
          {/* 左滚动按钮 */}
          <button
          onClick={() => scrollBoard("left")}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full bg-surface-2/90 border border-white/10 flex items-center justify-center text-white hover:bg-surface-1 transition-colors shadow-lg">

            <ChevronLeft className="w-5 h-5" />
          </button>

          {/* 看板容器 */}
          <div
          id="board-container"
          className="flex gap-4 overflow-x-auto pb-4 px-12 scroll-smooth custom-scrollbar"
          style={{ scrollbarWidth: "thin" }}>

            {PROJECT_STAGES.map((stage) =>
          <BoardColumn
            key={stage.key}
            stage={stage}
            projects={projectsByStage[stage.key] || []}
            isRelevant={isStageRelevant(stage.key)}
            onProjectClick={handleProjectClick}
            isProjectRelevant={isProjectRelevant}
            collapsed={collapsedStages[stage.key]}
            onToggleCollapse={handleToggleCollapse} />

          )}
          </div>

          {/* 右滚动按钮 */}
          <button
          onClick={() => scrollBoard("right")}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full bg-surface-2/90 border border-white/10 flex items-center justify-center text-white hover:bg-surface-1 transition-colors shadow-lg">

            <ChevronRight className="w-5 h-5" />
          </button>
      </div>
      }

      {/* 矩阵视图 */}
      {!loading && !error && viewMode === "matrix" &&
      <MatrixView
        projects={filteredProjects}
        stages={PROJECT_STAGES}
        onProjectClick={handleProjectClick} />

      }

      {/* 列表视图 */}
      {!loading && !error && viewMode === "list" &&
      <ListView
        projects={filteredProjects}
        onProjectClick={handleProjectClick}
        isProjectRelevant={isProjectRelevant} />
      }

      {/* ========== 新增：阶段视图模式 ========== */}

      {/* 流水线视图 - 多项目阶段全景 */}
      {!loading && !error && viewMode === "pipeline" && !selectedProjectId &&
      <PipelineView
        data={stageViewsHook.pipelineData}
        loading={stageViewsHook.loading}
        onSelectProject={(projectId, viewType) => {
          setSelectedProjectId(projectId);
          setDetailViewMode(VIEW_TYPES[viewType.toUpperCase()] || VIEW_TYPES.TIMELINE);
        }}
      />
      }

      {/* 时间轴视图 - 单项目甘特图 */}
      {!loading && !error && viewMode === "timeline" && !selectedProjectId &&
      <div className="bg-surface-1 rounded-lg border border-white/10 p-6 text-center">
        <Layers className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">请选择项目查看时间轴</h3>
        <p className="text-slate-400">时间轴视图用于查看单个项目的详细阶段进度</p>
      </div>
      }

      {/* 分解树视图 - 阶段/节点/任务分解 */}
      {!loading && !error && viewMode === "tree" && !selectedProjectId &&
      <div className="bg-surface-1 rounded-lg border border-white/10 p-6 text-center">
        <GitBranch className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">请选择项目查看分解树</h3>
        <p className="text-slate-400">分解树视图用于查看项目的完整阶段和任务结构</p>
      </div>
      }

      {/* ========== 选中项目后的详情视图 ========== */}

      {/* 项目详情视图 - 带三视图切换标签 */}
      {selectedProjectId &&
      <ProjectDetailView
        selectedProjectId={selectedProjectId}
        detailViewMode={detailViewMode}
        stageViewsHook={stageViewsHook}
        stageActions={stageActions}
        milestones={milestones}
        milestonesLoading={milestonesLoading}
        onBack={handleBackToProjects}
        onDetailViewChange={handleDetailViewChange}
        onMilestoneRefresh={() => loadMilestones(selectedProjectId)}
      />
      }

      {/* 空状态 */}
      {!loading && filteredProjects.length === 0 &&
      <div className="flex flex-col items-center justify-center py-20">
          <Layers className="w-16 h-16 text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">暂无项目</h3>
          <p className="text-slate-400">
            {searchQuery ? "没有找到匹配的项目" : "当前筛选条件下没有项目"}
          </p>
          <Button className="mt-4" onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-1" />
            新建项目
          </Button>
      </div>
      }

      {/* 新建项目对话框 */}
      <ProjectFormStepper
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSubmit={handleCreateProject}
        recommendedTemplates={recommendedTemplates}
      />
    </motion.div>);
}
