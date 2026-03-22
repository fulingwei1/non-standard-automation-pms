import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { projectApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { 
  formatCurrencyWan, 
  formatPercent, 
  getCostStatus,
  getCostProgressColor 
} from "../lib/utils/cost";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  HealthBadge,
  Progress,
  Input,
  SkeletonCard,
} from "../components/ui";
import {
  Plus,
  Search,
  Grid3X3,
  List,
  ArrowRight,
  Briefcase,
  Calendar,
  Users,
  Eye,
} from "lucide-react";
import ProjectFormStepper from "../components/project/ProjectFormStepper";
import ProjectCostFilter from "../components/project/ProjectCostFilter";
import ProjectCostDetailDialog from "../components/project/ProjectCostDetailDialog";
import { toast } from "sonner";
import * as XLSX from 'xlsx';

// Stagger animation
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
};

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

// Project Card Component with Cost
function ProjectCardWithCost({ project, onClick, onViewCostDetail, showCost }) {
  const costSummary = project?.cost_summary;
  const _costStatus = getCostStatus(costSummary);

  return (
    <motion.div variants={staggerChild}>
      <Card 
        className={cn(
          "group cursor-pointer overflow-hidden transition-all",
          showCost && costSummary?.overrun && "ring-2 ring-red-500/50"
        )} 
        onClick={onClick}
      >
        {/* Top colored bar based on health or cost status */}
        <div
          className={cn("h-1", {
            "bg-red-500": showCost && costSummary?.overrun,
            "bg-yellow-500": showCost && !costSummary?.overrun && costSummary?.budget_used_pct >= 90,
            "bg-emerald-500": showCost && costSummary && !costSummary.overrun && costSummary.budget_used_pct < 90,
            "bg-slate-500": !showCost || !costSummary,
          })}
        />

        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "p-2.5 rounded-xl",
                  "bg-gradient-to-br from-primary/20 to-indigo-500/10",
                  "ring-1 ring-primary/20",
                  "group-hover:scale-105 transition-transform",
                )}
              >
                <Briefcase className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-white line-clamp-1 group-hover:text-primary transition-colors">
                  {project.project_name}
                </h3>
                <p className="text-xs text-slate-500">{project.project_code}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <HealthBadge health={project.health || "H1"} />
              {showCost && costSummary?.overrun && (
                <Badge variant="destructive" className="text-xs">
                  超支
                </Badge>
              )}
            </div>
          </div>

          {/* Meta info */}
          <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
            <div className="flex items-center gap-2 text-slate-400">
              <Users className="h-4 w-4" />
              <span className="truncate">{project.customer_name}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <Calendar className="h-4 w-4" />
              <span>
                {project.planned_end_date
                  ? formatDate(project.planned_end_date)
                  : "未设置"}
              </span>
            </div>
          </div>

          {/* Progress */}
          <div className="mb-4">
            <div className="flex justify-between text-xs mb-2">
              <span className="text-slate-400">整体进度</span>
              <span className="text-white font-medium">
                {project.progress_pct || 0}%
              </span>
            </div>
            <Progress
              value={project.progress_pct || 0}
              color={
                project.health === "H3"
                  ? "danger"
                  : project.health === "H2"
                    ? "warning"
                    : "primary"
              }
            />
          </div>

          {/* Cost Section */}
          {showCost && costSummary && (
            <div className="mb-4 p-3 bg-white/[0.02] rounded-lg border border-white/5">
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-xs text-slate-500 mb-1">总成本</p>
                  <p className="text-sm font-semibold text-white">
                    {formatCurrencyWan(costSummary.total_cost)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">预算</p>
                  <p className="text-sm font-semibold text-white">
                    {formatCurrencyWan(costSummary.budget)}
                  </p>
                </div>
              </div>

              {/* Budget usage bar */}
              <div className="mb-2">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500">预算使用率</span>
                  <span className={cn(
                    "font-medium",
                    costSummary.overrun ? "text-red-400" : 
                    costSummary.budget_used_pct >= 90 ? "text-yellow-400" : 
                    "text-emerald-400"
                  )}>
                    {formatPercent(costSummary.budget_used_pct, 1)}
                  </span>
                </div>
                <div className="relative w-full h-2 bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full transition-all duration-500",
                      getCostProgressColor(costSummary.budget_used_pct, costSummary.overrun)
                    )}
                    style={{ width: `${Math.min(costSummary.budget_used_pct, 100)}%` }}
                  />
                </div>
              </div>

              {/* View detail button */}
              <Button
                variant="ghost"
                size="sm"
                className="w-full mt-2 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewCostDetail(project);
                }}
              >
                <Eye className="h-3 w-3 mr-1" />
                查看成本明细
              </Button>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-white/5">
            <Badge variant="secondary">{project.stage || "S1"}</Badge>
            <div className="flex items-center gap-1 text-sm text-slate-500 group-hover:text-primary transition-colors">
              查看详情
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function ProjectListWithCost() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("grid"); // grid | list
  const [formOpen, setFormOpen] = useState(false);
  const [recommendedTemplates, setRecommendedTemplates] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [costDetailOpen, setCostDetailOpen] = useState(false);

  // Cost filters
  const [filters, setFilters] = useState({
    includeCost: true,
    overrunOnly: false,
    sort: 'created_at_desc',
  });

  const fetchProjects = async () => {
    try {
      setLoading(true);
      
      const params = {
        page_size: 100,
        include_cost: filters.includeCost,
        overrun_only: filters.overrunOnly,
        sort: filters.sort,
      };

      const response = await projectApi.list(params);
      const data = response.data || response;
      const projectList = data.items || data || [];
      setProjects(projectList);
    } catch (err) {
      toast.error("获取项目列表失败: " + (err.response?.data?.detail || err.message));
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [filters]);

  useEffect(() => {
    if (formOpen) {
      const loadRecommendedTemplates = async () => {
        try {
          const response = await projectApi.recommendTemplates({
            limit: 5,
          });
          setRecommendedTemplates(response.data?.recommendations || []);
        } catch (err) {
          setRecommendedTemplates([]);
        }
      };
      loadRecommendedTemplates();
    }
  }, [formOpen]);

  const handleCreateProject = async (data) => {
    try {
      await projectApi.create(data);
      setFormOpen(false);
      toast.success("项目创建成功！");
      fetchProjects();
    } catch (err) {
      toast.error("创建项目失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleViewCostDetail = (project) => {
    setSelectedProject(project);
    setCostDetailOpen(true);
  };

  const handleExport = () => {
    try {
      if (projects?.length === 0) {
        toast.warning("没有可导出的项目数据");
        return;
      }

      // 准备导出数据
      const exportData = (projects || []).map(project => {
        const row = {
          '项目编号': project.project_code,
          '项目名称': project.project_name,
          '客户': project.customer_name,
          '项目经理': project.pm_name || '--',
          '阶段': project.stage || '--',
          '健康度': project.health || '--',
          '进度': `${project.progress_pct || 0}%`,
        };

        if (filters.includeCost && project.cost_summary) {
          const cost = project.cost_summary;
          row['总成本'] = cost.total_cost || 0;
          row['预算'] = cost.budget || 0;
          row['预算使用率'] = `${cost.budget_used_pct?.toFixed(2) || 0}%`;
          row['是否超支'] = cost.overrun ? '是' : '否';
          row['差异'] = cost.variance || 0;
          row['人工成本'] = cost.cost_breakdown?.labor || 0;
          row['材料成本'] = cost.cost_breakdown?.material || 0;
          row['设备成本'] = cost.cost_breakdown?.equipment || 0;
          row['差旅成本'] = cost.cost_breakdown?.travel || 0;
          row['其他成本'] = cost.cost_breakdown?.other || 0;
        }

        return row;
      });

      // 创建工作簿
      const worksheet = XLSX.utils.json_to_sheet(exportData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "项目列表");

      // 下载
      const fileName = `项目列表_${filters.includeCost ? '含成本_' : ''}${new Date().toISOString().split('T')[0]}.xlsx`;
      XLSX.writeFile(workbook, fileName);

      toast.success("导出成功！");
    } catch (err) {
      toast.error("导出失败: " + err.message);
    }
  };

  // Filter projects based on search
  const filteredProjects = (projects || []).filter(
    (p) =>
      p.project_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.project_code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // Calculate statistics
  const stats = {
    total: filteredProjects.length,
    overrun: (filteredProjects || []).filter(p => p.cost_summary?.overrun).length,
    warning: (filteredProjects || []).filter(p => !p.cost_summary?.overrun && p.cost_summary?.budget_used_pct >= 90).length,
    safe: (filteredProjects || []).filter(p => p.cost_summary && !p.cost_summary.overrun && p.cost_summary.budget_used_pct < 90).length,
  };

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <motion.div variants={staggerChild}>
        <PageHeader
          title="项目列表"
          description={
            filters.includeCost 
              ? `共 ${stats.total} 个项目 · 超支 ${stats.overrun} · 预警 ${stats.warning} · 正常 ${stats.safe}`
              : `共 ${stats.total} 个项目`
          }
          breadcrumbs={[{ label: "首页", href: "/" }, { label: "项目列表" }]}
          actions={
            <Button onClick={() => setFormOpen(true)}>
              <Plus className="h-4 w-4" />
              新建项目
            </Button>
          }
        />
      </motion.div>

      {/* Cost Filter */}
      <motion.div variants={staggerChild}>
        <ProjectCostFilter
          filters={filters}
          onFilterChange={setFilters}
          onExport={handleExport}
          showCost={filters.includeCost}
        />
      </motion.div>

      {/* Search and View Mode */}
      <motion.div
        variants={staggerChild}
        className="flex items-center gap-4 my-6"
      >
        {/* Search */}
        <div className="flex-1 max-w-md">
          <Input
            icon={Search}
            placeholder="搜索项目名称、编码或客户..."
            value={searchQuery || "unknown"}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center rounded-xl bg-white/[0.05] p-1">
          <button
            onClick={() => setViewMode("grid")}
            className={cn(
              "p-2 rounded-lg transition-colors",
              viewMode === "grid"
                ? "bg-primary text-white"
                : "text-slate-400 hover:text-white",
            )}
          >
            <Grid3X3 className="h-4 w-4" />
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={cn(
              "p-2 rounded-lg transition-colors",
              viewMode === "list"
                ? "bg-primary text-white"
                : "text-slate-400 hover:text-white",
            )}
          >
            <List className="h-4 w-4" />
          </button>
        </div>
      </motion.div>

      {/* Content */}
      {loading ? (
        <div
          className={cn(
            viewMode === "grid"
              ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
              : "space-y-4",
          )}
        >
          {Array(6)
            .fill(null)
            .map((_, i) => (
              <SkeletonCard key={i} />
            ))}
        </div>
      ) : filteredProjects.length > 0 ? (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className={cn(
            viewMode === "grid"
              ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
              : "space-y-4",
          )}
        >
          {(filteredProjects || []).map((project) => (
            <ProjectCardWithCost
              key={project.id}
              project={project}
              onClick={() => navigate(`/projects/${project.id}`)}
              onViewCostDetail={handleViewCostDetail}
              showCost={filters.includeCost}
            />
          ))}
        </motion.div>
      ) : (
        <motion.div variants={staggerChild}>
          <Card className="p-12 text-center">
            <div className="text-5xl mb-4">
              {filters.overrunOnly ? "💰" : "📦"}
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              {searchQuery 
                ? "未找到匹配的项目" 
                : filters.overrunOnly 
                ? "暂无超支项目" 
                : "暂无项目"}
            </h3>
            <p className="text-slate-400 mb-6">
              {searchQuery
                ? "请尝试其他搜索关键词"
                : filters.overrunOnly
                ? "所有项目成本都在预算范围内"
                : "点击右上角按钮创建您的第一个项目"}
            </p>
            {!searchQuery && !filters.overrunOnly && (
              <Button onClick={() => setFormOpen(true)}>
                <Plus className="h-4 w-4" />
                新建项目
              </Button>
            )}
          </Card>
        </motion.div>
      )}

      {/* Create Project Dialog */}
      <ProjectFormStepper
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={handleCreateProject}
        recommendedTemplates={recommendedTemplates}
      />

      {/* Cost Detail Dialog */}
      <ProjectCostDetailDialog
        open={costDetailOpen}
        onOpenChange={setCostDetailOpen}
        project={selectedProject}
      />
    </motion.div>
  );
}
