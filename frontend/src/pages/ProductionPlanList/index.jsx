/**
 * Production Plan List Page - 生产计划列表页面
 * Features: 生产计划列表、创建、审批、发布
 */
import { useProductionPlanList } from "./hooks";

export default function ProductionPlanList() {
  const {
    // data
    loading,
    filteredPlans,
    projects,
    workshops,
    // filters
    searchKeyword, setSearchKeyword,
    filterType,    setFilterType,
    filterProject, setFilterProject,
    filterWorkshop, setFilterWorkshop,
    filterStatus,  setFilterStatus,
    // dialogs
    showCreateDialog, setShowCreateDialog,
    showDetailDialog, setShowDetailDialog,
    selectedPlan,
    // form
    newPlan, setNewPlan,
    // actions
    handleCreatePlan,
    handleViewDetail,
    handlePublish,
  } = useProductionPlanList();

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="生产计划管理"
        description="生产计划列表、创建、审批、发布"
      />

      <PlanFilters
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterType={filterType}
        setFilterType={setFilterType}
        filterProject={filterProject}
        setFilterProject={setFilterProject}
        filterWorkshop={filterWorkshop}
        setFilterWorkshop={setFilterWorkshop}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
        projects={projects}
        workshops={workshops}
      />

      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建计划
        </Button>
      </div>

      <PlanTable
        loading={loading}
        filteredPlans={filteredPlans}
        onViewDetail={handleViewDetail}
        onPublish={handlePublish}
      />

      <CreatePlanDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        newPlan={newPlan}
        setNewPlan={setNewPlan}
        onSubmit={handleCreatePlan}
        projects={projects}
        workshops={workshops}
      />

      <PlanDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedPlan={selectedPlan}
        onPublish={handlePublish}
      />
    </div>
  );
}
