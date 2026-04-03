/**
 * Work Order Management Page - 工单管理页面
 * Features: 工单列表、详情、创建、派工、进度跟踪
 */
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { useWorkOrders } from "./hooks/useWorkOrders";
import WorkOrderFilters from "./WorkOrderFilters";
import WorkOrderTable from "./WorkOrderTable";
import CreateOrderDialog from "./CreateOrderDialog";
import OrderDetailDialog from "./OrderDetailDialog";
import AssignDialog from "./AssignDialog";

export default function WorkOrderManagement() {
  const {
    loading,
    projects,
    filteredOrders,
    // Filters
    searchKeyword,
    setSearchKeyword,
    filterProject,
    setFilterProject,
    filterStatus,
    setFilterStatus,
    filterPriority,
    setFilterPriority,
    // Dialogs
    showCreateDialog,
    setShowCreateDialog,
    showDetailDialog,
    setShowDetailDialog,
    showAssignDialog,
    setShowAssignDialog,
    selectedOrder,
    setSelectedOrder,
    // Form states
    newOrder,
    setNewOrder,
    assignData,
    setAssignData,
    // Actions
    handleCreateOrder,
    handleAssign,
  } = useWorkOrders();

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="工单管理"
        description="生产工单管理，支持创建、派工、进度跟踪"
      />

      {/* Filters */}
      <WorkOrderFilters
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterProject={filterProject}
        setFilterProject={setFilterProject}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
        filterPriority={filterPriority}
        setFilterPriority={setFilterPriority}
        projects={projects}
      />

      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建工单
        </Button>
      </div>

      {/* Work Order List */}
      <WorkOrderTable
        loading={loading}
        filteredOrders={filteredOrders}
        setSelectedOrder={setSelectedOrder}
        setShowAssignDialog={setShowAssignDialog}
      />

      {/* Create Work Order Dialog */}
      <CreateOrderDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        newOrder={newOrder}
        setNewOrder={setNewOrder}
        projects={projects}
        onSubmit={handleCreateOrder}
      />

      {/* Work Order Detail Dialog */}
      <OrderDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedOrder={selectedOrder}
        onAssign={() => {
          setShowDetailDialog(false);
          setShowAssignDialog(true);
        }}
      />

      {/* Assign Dialog */}
      <AssignDialog
        open={showAssignDialog}
        onOpenChange={setShowAssignDialog}
        selectedOrder={selectedOrder}
        assignData={assignData}
        setAssignData={setAssignData}
        onSubmit={handleAssign}
      />
    </div>
  );
}
