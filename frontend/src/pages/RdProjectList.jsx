import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { rdProjectApi } from "../services/api";
import { formatDate, formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  SkeletonCard,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
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
  FlaskConical,
  Calendar,
  Users,
  DollarSign,
  CheckCircle2,
  Clock,
  XCircle,
  FileText,
} from "lucide-react";

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

// Status badge mapping
const statusMap = {
  DRAFT: { label: "草稿", color: "secondary" },
  APPROVED: { label: "已审批", color: "success" },
  IN_PROGRESS: { label: "进行中", color: "primary" },
  COMPLETED: { label: "已完成", color: "success" },
  CANCELLED: { label: "已取消", color: "danger" },
};

const approvalStatusMap = {
  PENDING: { label: "待审批", color: "warning" },
  APPROVED: { label: "已通过", color: "success" },
  REJECTED: { label: "已驳回", color: "danger" },
};

const categoryTypeMap = {
  SELF: { label: "自主研发", color: "primary" },
  ENTRUST: { label: "委托研发", color: "info" },
  COOPERATION: { label: "合作研发", color: "success" },
};

// R&D Project Card Component
function RdProjectCard({ project, onClick }) {
  const status = statusMap[project.status] || statusMap.DRAFT;
  const approvalStatus =
    approvalStatusMap[project.approval_status] || approvalStatusMap.PENDING;
  const categoryType =
    categoryTypeMap[project.category_type] || categoryTypeMap.SELF;

  return (
    <motion.div variants={staggerChild}>
      <Card
        className="group cursor-pointer overflow-hidden hover:border-primary/50 transition-colors"
        onClick={onClick}
      >
        <div className="h-1 bg-gradient-to-r from-primary to-indigo-500" />
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-indigo-500/10 ring-1 ring-primary/20 group-hover:scale-105 transition-transform">
                <FlaskConical className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-white line-clamp-1 group-hover:text-primary transition-colors">
                  {project.project_name}
                </h3>
                <p className="text-xs text-slate-500">{project.project_no}</p>
              </div>
            </div>
            <div className="flex flex-col gap-1 items-end">
              <Badge variant={status.color}>{status.label}</Badge>
              {project.approval_status === "PENDING" && (
                <Badge variant={approvalStatus.color} className="text-xs">
                  {approvalStatus.label}
                </Badge>
              )}
            </div>
          </div>

          {/* Meta info */}
          <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
            <div className="flex items-center gap-2 text-slate-400">
              <Users className="h-4 w-4" />
              <span className="truncate">
                {project.project_manager_name || "未指定"}
              </span>
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

          {/* Category and Budget */}
          <div className="flex items-center justify-between mb-4">
            <Badge variant="outline">{categoryType.label}</Badge>
            <div className="flex items-center gap-1 text-sm text-slate-400">
              <DollarSign className="h-4 w-4" />
              <span>{formatCurrency(project.budget_amount || 0)}</span>
            </div>
          </div>

          {/* Stats */}
          {project.total_cost !== undefined && (
            <div className="mb-4 p-3 rounded-lg bg-white/[0.03] border border-white/5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">已归集费用</span>
                <span className="text-white font-medium">
                  {formatCurrency(project.total_cost || 0)}
                </span>
              </div>
              {project.total_hours && (
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-slate-400">总工时</span>
                  <span className="text-white font-medium">
                    {project.total_hours.toFixed(1)} 小时
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-white/5">
            <div className="flex items-center gap-2">
              {project.status === "COMPLETED" && (
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              )}
              {project.status === "IN_PROGRESS" && (
                <Clock className="h-4 w-4 text-primary" />
              )}
              {project.status === "CANCELLED" && (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-xs text-slate-500">
                {project.initiation_date
                  ? formatDate(project.initiation_date)
                  : "未立项"}
              </span>
            </div>
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

// R&D Project Form Component
function RdProjectFormDialog({
  open,
  onOpenChange,
  onSubmit,
  categories = [],
}) {
  const [formData, setFormData] = useState({
    project_name: "",
    category_id: "",
    category_type: "SELF",
    initiation_date: "",
    planned_start_date: "",
    planned_end_date: "",
    project_manager_id: null,
    initiation_reason: "",
    research_goal: "",
    research_content: "",
    expected_result: "",
    budget_amount: "",
    linked_project_id: null,
    remark: "",
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const submitData = {
        ...formData,
        budget_amount: formData.budget_amount
          ? parseFloat(formData.budget_amount)
          : null,
        project_manager_id: formData.project_manager_id || null,
        linked_project_id: formData.linked_project_id || null,
        initiation_date: formData.initiation_date || null,
        planned_start_date: formData.planned_start_date || null,
        planned_end_date: formData.planned_end_date || null,
      };
      await onSubmit(submitData);
      setFormData({
        project_name: "",
        category_id: "",
        category_type: "SELF",
        initiation_date: "",
        planned_start_date: "",
        planned_end_date: "",
        project_manager_id: null,
        initiation_reason: "",
        research_goal: "",
        research_content: "",
        expected_result: "",
        budget_amount: "",
        linked_project_id: null,
        remark: "",
      });
      onOpenChange(false);
    } catch (err) {
      console.error("Failed to create project:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建研发项目</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  项目名称 <span className="text-red-500">*</span>
                </label>
                <Input
                  value={formData.project_name}
                  onChange={(e) =>
                    setFormData({ ...formData, project_name: e.target.value })
                  }
                  placeholder="请输入项目名称"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  项目分类
                </label>
                <Select
                  value={formData.category_id?.toString() || "__none__"}
                  onValueChange={(value) =>
                    setFormData({
                      ...formData,
                      category_id:
                        value && value !== "__none__" ? parseInt(value) : "",
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="请选择分类" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">请选择分类</SelectItem>
                    {categories.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id.toString()}>
                        {cat.category_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  项目类型 <span className="text-red-500">*</span>
                </label>
                <Select
                  value={formData.category_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, category_type: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="请选择类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SELF">自主研发</SelectItem>
                    <SelectItem value="ENTRUST">委托研发</SelectItem>
                    <SelectItem value="COOPERATION">合作研发</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  立项日期
                </label>
                <Input
                  type="date"
                  value={formData.initiation_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      initiation_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  计划开始日期
                </label>
                <Input
                  type="date"
                  value={formData.planned_start_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      planned_start_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  计划结束日期
                </label>
                <Input
                  type="date"
                  value={formData.planned_end_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      planned_end_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  预算金额
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.budget_amount}
                  onChange={(e) =>
                    setFormData({ ...formData, budget_amount: e.target.value })
                  }
                  placeholder="0.00"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                立项原因
              </label>
              <textarea
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
                value={formData.initiation_reason}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    initiation_reason: e.target.value,
                  })
                }
                placeholder="请输入立项原因"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                研究目标
              </label>
              <textarea
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
                value={formData.research_goal}
                onChange={(e) =>
                  setFormData({ ...formData, research_goal: e.target.value })
                }
                placeholder="请输入研究目标"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                研究内容
              </label>
              <textarea
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                rows={3}
                value={formData.research_content}
                onChange={(e) =>
                  setFormData({ ...formData, research_content: e.target.value })
                }
                placeholder="请输入研究内容"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                预期结果
              </label>
              <textarea
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
                value={formData.expected_result}
                onChange={(e) =>
                  setFormData({ ...formData, expected_result: e.target.value })
                }
                placeholder="请输入预期结果"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                备注
              </label>
              <textarea
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
                value={formData.remark}
                onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="请输入备注"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <Button type="submit" loading={loading}>
              创建项目
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function RdProjectList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategoryType, setFilterCategoryType] = useState("all");
  const [viewMode, setViewMode] = useState("grid");
  const [formOpen, setFormOpen] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0,
  });

  const fetchCategories = async () => {
    try {
      const response = await rdProjectApi.getCategories();
      const data = response.data?.data || response.data || [];
      setCategories(data);
    } catch (err) {
      console.error("Failed to fetch categories:", err);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
      };
      if (searchQuery) {params.keyword = searchQuery;}
      if (filterStatus && filterStatus !== "all") {params.status = filterStatus;}
      if (filterCategoryType && filterCategoryType !== "all")
        {params.category_type = filterCategoryType;}

      const response = await rdProjectApi.list(params);
      const data = response.data || response;

      if (data.items) {
        // PaginatedResponse format
        setProjects(data.items || []);
        setPagination({
          page: data.page || 1,
          page_size: data.page_size || 20,
          total: data.total || 0,
          pages: data.pages || 0,
        });
      } else {
        // Array format
        setProjects(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [pagination.page, searchQuery, filterStatus, filterCategoryType]);

  const handleCreateProject = async (data) => {
    try {
      const response = await rdProjectApi.create(data);
      if (response.data?.code === 201 || response.status === 201) {
        setFormOpen(false);
        fetchProjects();
      } else {
        throw new Error(response.data?.message || "创建失败");
      }
    } catch (err) {
      alert("创建研发项目失败: " + (err.response?.data?.detail || err.message));
      throw err;
    }
  };

  const handleProjectClick = (project) => {
    navigate(`/rd-projects/${project.id}`);
  };

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <PageHeader
        title="研发项目管理"
        description="IPO合规、高新技术企业认定、研发费用加计扣除"
        actions={
          <Button onClick={() => setFormOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            创建研发项目
          </Button>
        }
      />

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="搜索项目名称或编号..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="项目状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="DRAFT">草稿</SelectItem>
                <SelectItem value="APPROVED">已审批</SelectItem>
                <SelectItem value="IN_PROGRESS">进行中</SelectItem>
                <SelectItem value="COMPLETED">已完成</SelectItem>
                <SelectItem value="CANCELLED">已取消</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filterCategoryType}
              onValueChange={setFilterCategoryType}
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="项目类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="SELF">自主研发</SelectItem>
                <SelectItem value="ENTRUST">委托研发</SelectItem>
                <SelectItem value="COOPERATION">合作研发</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2">
              <Button
                variant={viewMode === "grid" ? "primary" : "secondary"}
                size="icon"
                onClick={() => setViewMode("grid")}
              >
                <Grid3X3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "primary" : "secondary"}
                size="icon"
                onClick={() => setViewMode("list")}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Projects Grid/List */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="h-12 w-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400">暂无研发项目</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => setFormOpen(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              创建第一个研发项目
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div
            className={cn(
              "grid gap-6",
              viewMode === "grid"
                ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
                : "grid-cols-1",
            )}
          >
            {projects.map((project) => (
              <RdProjectCard
                key={project.id}
                project={project}
                onClick={() => handleProjectClick(project)}
              />
            ))}
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  setPagination({ ...pagination, page: pagination.page - 1 })
                }
                disabled={pagination.page <= 1}
              >
                上一页
              </Button>
              <span className="text-sm text-slate-400">
                第 {pagination.page} / {pagination.pages} 页，共{" "}
                {pagination.total} 条
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  setPagination({ ...pagination, page: pagination.page + 1 })
                }
                disabled={pagination.page >= pagination.pages}
              >
                下一页
              </Button>
            </div>
          )}
        </>
      )}

      {/* Create Form Dialog */}
      <RdProjectFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={handleCreateProject}
        categories={categories}
      />
    </motion.div>
  );
}
