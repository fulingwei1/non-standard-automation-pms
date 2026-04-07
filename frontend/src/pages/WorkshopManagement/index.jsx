/**
 * Workshop Management Page - 车间管理页面
 * Features: 车间列表、创建、编辑、工位管理
 */
import { useWorkshopManagement } from "./hooks/useWorkshopManagement";

export default function WorkshopManagement() {
  const {
    // Data
    loading,
    filteredWorkshops,
    managers,
    selectedWorkshop,
    // Filters
    searchKeyword,
    setSearchKeyword,
    filterType,
    setFilterType,
    filterActive,
    setFilterActive,
    // Dialogs
    showCreateDialog,
    setShowCreateDialog,
    showEditDialog,
    setShowEditDialog,
    showDetailDialog,
    setShowDetailDialog,
    // Form
    workshopForm,
    setWorkshopForm,
    // Handlers
    handleCreate,
    handleEdit,
    handleViewDetail,
    handleEditClick,
  } = useWorkshopManagement();

  return (
    <div className="space-y-6 p-6">
      <PageHeader title="车间管理" description="车间列表、创建、编辑、工位管理" />

      <WorkshopFilters
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterType={filterType}
        setFilterType={setFilterType}
        filterActive={filterActive}
        setFilterActive={setFilterActive}
      />

      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建车间
        </Button>
      </div>

      <WorkshopTable
        loading={loading}
        filteredWorkshops={filteredWorkshops}
        onViewDetail={handleViewDetail}
        onEditClick={handleEditClick}
      />

      <WorkshopFormDialog
        mode="create"
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        workshopForm={workshopForm}
        setWorkshopForm={setWorkshopForm}
        managers={managers}
        onSubmit={handleCreate}
      />

      <WorkshopFormDialog
        mode="edit"
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        workshopForm={workshopForm}
        setWorkshopForm={setWorkshopForm}
        managers={managers}
        onSubmit={handleEdit}
      />

      <WorkshopDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedWorkshop={selectedWorkshop}
        onEditClick={handleEditClick}
      />
    </div>
  );
}
