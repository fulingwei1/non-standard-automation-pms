import { useNavigate } from "react-router-dom";
import { useRdProjectList } from "./hooks/useRdProjectList";
import { staggerContainer } from "./constants";

export default function RdProjectList() {
  const navigate = useNavigate();

  const {
    loading,
    projects,
    categories,
    searchQuery,
    setSearchQuery,
    filterStatus,
    setFilterStatus,
    filterCategoryType,
    setFilterCategoryType,
    viewMode,
    setViewMode,
    formOpen,
    setFormOpen,
    pagination,
    setPagination,
    handleCreateProject,
  } = useRdProjectList();

  const handleProjectClick = (project) => {
    navigate(`/rd-projects/${project.id}`);
  };

  const handlePageChange = (newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
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

      <ProjectFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        filterStatus={filterStatus}
        onFilterStatusChange={setFilterStatus}
        filterCategoryType={filterCategoryType}
        onFilterCategoryTypeChange={setFilterCategoryType}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      <ProjectListView
        loading={loading}
        projects={projects}
        viewMode={viewMode}
        pagination={pagination}
        onProjectClick={handleProjectClick}
        onPageChange={handlePageChange}
        onCreateClick={() => setFormOpen(true)}
      />

      <RdProjectFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={handleCreateProject}
        categories={categories}
      />
    </motion.div>
  );
}
