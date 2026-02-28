import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { projectApi } from "../services/api";
import { formatDate } from "../lib/utils";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui";
import {
  Plus,
  Search,
  Filter,
  Grid3X3,
  List,
  ArrowRight,
  Briefcase,
  Calendar,
  Users,
  ChevronDown,
} from "lucide-react";
// Sprint 3: 使用优化的分步骤表单组件
import ProjectFormStepper from "../components/project/ProjectFormStepper";

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

// Project Card Component
function ProjectCard({ project, onClick }) {
  return (
    <motion.div variants={staggerChild}>
      <Card className="group cursor-pointer overflow-hidden" onClick={onClick}>
        {/* Top colored bar based on health */}
        <div
          className={cn("h-1", {
            "bg-emerald-500": project.health === "H1",
            "bg-amber-500": project.health === "H2",
            "bg-red-500": project.health === "H3",
            "bg-slate-500": project.health === "H4",
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
            <HealthBadge health={project.health || "H1"} />
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

export default function ProjectList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("grid"); // grid | list
  const [formOpen, setFormOpen] = useState(false);
  const [recommendedTemplates, setRecommendedTemplates] = useState([]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      // 增加 page_size 以获取更多项目，避免分页导致项目不在列表中
      const response = await projectApi.list({ page_size: 100 });
      // Handle PaginatedResponse format: { items, total, page, page_size, pages }
      const data = response.data || response;
      const projectList = data.items || data || [];
      setProjects(projectList);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // Sprint 3.2: 加载模板推荐
  useEffect(() => {
    if (formOpen) {
      const loadRecommendedTemplates = async () => {
        try {
          const response = await projectApi.recommendTemplates({
            limit: 5,
          });
          setRecommendedTemplates(response.data?.recommendations || []);
        } catch (err) {
          console.error("Failed to load recommended templates:", err);
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
      fetchProjects();
    } catch (err) {
      alert("创建项目失败: " + (err.response?.data?.detail || err.message));
    }
  };

  // Filter projects based on search
  const filteredProjects = (projects || []).filter(
    (p) =>
      p.project_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.project_code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <motion.div variants={staggerChild}>
        <PageHeader
          title="项目列表"
          description={`共 ${projects?.length} 个项目`}
          breadcrumbs={[{ label: "首页", href: "/" }, { label: "项目列表" }]}
          actions={
            <Button onClick={() => setFormOpen(true)}>
              <Plus className="h-4 w-4" />
              新建项目
            </Button>
          }
        />
      </motion.div>

      {/* Toolbar */}
      <motion.div
        variants={staggerChild}
        className="flex items-center gap-4 mb-6"
      >
        {/* Search */}
        <div className="flex-1 max-w-md">
          <Input
            icon={Search}
            placeholder="搜索项目名称、编码或客户..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Filter Button */}
        <Button variant="secondary" className="hidden sm:flex">
          <Filter className="h-4 w-4" />
          筛选
          <ChevronDown className="h-4 w-4" />
        </Button>

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
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => navigate(`/projects/${project.id}`)}
            />
          ))}
        </motion.div>
      ) : (
        <motion.div variants={staggerChild}>
          <Card className="p-12 text-center">
            <div className="text-5xl mb-4">📦</div>
            <h3 className="text-lg font-semibold text-white mb-2">
              {searchQuery ? "未找到匹配的项目" : "暂无项目"}
            </h3>
            <p className="text-slate-400 mb-6">
              {searchQuery
                ? "请尝试其他搜索关键词"
                : "点击右上角按钮创建您的第一个项目"}
            </p>
            {!searchQuery && (
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
    </motion.div>
  );
}
