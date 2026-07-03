/**
 * Installation Dispatch Management Page - 安装调试派工管理页面
 * Features: 安装调试派工单管理、批量派工、进度跟踪
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Plus } from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { toast } from "../components/ui/toast";
import {
  installationDispatchApi,
  workLogApi,
  userApi,
  projectApi,
  machineApi,
} from "../services/api";
import {
  InstallationDispatchOverview,
  DispatchList,
  DispatchFilters,
  DispatchBatchActions,
  CreateDispatchDialog,
  AssignDispatchDialog,
  DispatchDetailDialog,
  UpdateProgressDialog,
  CompleteDispatchDialog,
  FieldServiceWorkLogDialog,
  DISPATCH_STATUS,
  DISPATCH_PRIORITY,
  INSTALLATION_TYPE,
  normalizeDispatchOrder,
  validateDispatchData,
} from "../components/installation-dispatch";

const getLocalDateInputValue = (date = new Date()) => {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
};

const getInitialCreateData = () => ({
  project_id: "",
  machine_id: "",
  customer_id: "",
  task_type: INSTALLATION_TYPE.INSTALLATION,
  task_title: "",
  task_description: "",
  location: "",
  scheduled_date: "",
  estimated_hours: "",
  priority: DISPATCH_PRIORITY.NORMAL,
  customer_contact: "",
  customer_phone: "",
  customer_address: "",
  remark: "",
});

const getInitialWorkLogData = () => ({
  today_progress: "",
  issues_found: "",
  next_plan: "",
  work_hours: "",
});

export default function InstallationDispatchManagement() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [machines, setMachines] = useState([]);
  const [_stats, setStats] = useState({
    total: 0,
    pending: 0,
    assigned: 0,
    in_progress: 0,
    completed: 0,
    cancelled: 0,
    urgent: 0,
  });

  // Filters
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterTaskType, setFilterTaskType] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Selection
  const [selectedOrders, setSelectedOrders] = useState(new Set());
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [showWorkLogDialog, setShowWorkLogDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [workLogDate, setWorkLogDate] = useState(getLocalDateInputValue());
  const [workLogContext, setWorkLogContext] = useState(null);
  const [workLogLoading, setWorkLogLoading] = useState(false);
  const [workLogSubmitting, setWorkLogSubmitting] = useState(false);
  const [workLogData, setWorkLogData] = useState(getInitialWorkLogData());
  const [progressData, setProgressData] = useState({
    progress: 0,
    execution_notes: "",
  });
  const [completeData, setCompleteData] = useState({
    actual_hours: "",
    execution_notes: "",
    issues_found: "",
    solution_provided: "",
    photos: [],
  });

  const [assignData, setAssignData] = useState({
    assigned_to_id: null,
    remark: "",
  });

  const [createData, setCreateData] = useState(getInitialCreateData());

  useEffect(() => {
    fetchUsers();
    fetchProjects();
    fetchOrders();
    fetchStatistics();
  }, [
    filterStatus,
    filterPriority,
    filterProject,
    filterTaskType,
    searchQuery,
  ]);

  useEffect(() => {
    if (createData.project_id) {
      fetchMachines(createData.project_id);
    } else {
      setMachines([]);
    }
  }, [createData.project_id]);

  useEffect(() => {
    if (showWorkLogDialog && workLogDate) {
      fetchFieldServiceWorkLogContext(workLogDate);
    }
  }, [showWorkLogDialog, workLogDate]);

  // API Functions
  const fetchUsers = async () => {
    try {
      const res = await userApi.options({ page_size: 1000, is_active: true });
      const data = res.data || res;
      setUsers(data.items || data || []);
    } catch (error) {
      console.error("Failed to fetch users:", error);
      toast.error("获取用户列表失败");
    }
  };

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
      toast.error("获取项目列表失败");
    }
  };

  const fetchMachines = async (projectId) => {
    try {
      const res = await machineApi.list(projectId, {
        page_size: 1000,
      });
      setMachines(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch machines:", error);
      toast.error("获取设备列表失败");
    }
  };

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 1000,
      };
      if (filterStatus) params.status = filterStatus;
      if (filterPriority) params.priority = filterPriority;
      if (filterProject) params.project_id = filterProject;
      if (filterTaskType) params.task_type = filterTaskType;
      if (searchQuery) params.search = searchQuery;

      const res = await installationDispatchApi.orders.list(params);
      setOrders((res.data?.items || res.data || []).map(normalizeDispatchOrder));
    } catch (error) {
      console.error("Failed to fetch orders:", error);
      toast.error("获取派工单列表失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const res = await installationDispatchApi.statistics();
      setStats(res.data || {});
    } catch (error) {
      console.error("Failed to fetch statistics:", error);
    }
  };

  const fetchFieldServiceWorkLogContext = async (dateValue = workLogDate) => {
    setWorkLogLoading(true);
    try {
      const res = await workLogApi.fieldServiceContext({ work_date: dateValue });
      setWorkLogContext(res.data?.data || res.data || null);
    } catch (error) {
      console.error("Failed to fetch field service work log context:", error);
      toast.error("获取外出日志上下文失败");
    } finally {
      setWorkLogLoading(false);
    }
  };

  // CRUD Operations
  const handleCreateOrder = async () => {
    const validation = validateDispatchData(createData);
    if (!validation.isValid) {
      toast.error(validation.errors.join(", "));
      return;
    }

    try {
      const payload = {
        ...createData,
        project_id: Number(createData.project_id),
        customer_id: Number(createData.customer_id),
        machine_id: createData.machine_id ? Number(createData.machine_id) : null,
        estimated_hours: createData.estimated_hours
          ? Number(createData.estimated_hours)
          : null,
      };
      await installationDispatchApi.orders.create(payload);
      toast.success("派工单创建成功");
      setShowCreateDialog(false);
      setCreateData(getInitialCreateData());
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to create order:", error);
      toast.error("创建派工单失败");
    }
  };

  const handleAssignOrder = async (orderId) => {
    try {
      await installationDispatchApi.orders.assign(orderId, {
        assigned_to_id: Number(assignData.assigned_to_id),
        remark: assignData.remark,
      });
      toast.success("派工成功");
      setShowAssignDialog(false);
      setAssignData({ assigned_to_id: null, remark: "" });
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to assign order:", error);
      toast.error("派工失败");
    }
  };

  const handleUpdateProgress = async () => {
    try {
      await installationDispatchApi.orders.progress(
        selectedOrder.id,
        progressData
      );
      toast.success("进度更新成功");
      setShowProgressDialog(false);
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to update progress:", error);
      toast.error("更新进度失败");
    }
  };

  const handleStartOrder = async (orderId) => {
    try {
      await installationDispatchApi.orders.start(orderId, {});
      toast.success("已开始执行");
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to start order:", error);
      toast.error("开始执行失败");
    }
  };

  const handleCompleteOrder = async () => {
    try {
      await installationDispatchApi.orders.complete(selectedOrder.id, completeData);
      toast.success("派工单完成");
      setShowCompleteDialog(false);
      setCompleteData({
        actual_hours: "",
        execution_notes: "",
        issues_found: "",
        solution_provided: "",
        photos: [],
      });
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to complete order:", error);
      toast.error("完成派工单失败");
    }
  };

  const handleBatchAssign = async () => {
    if (selectedOrders.size === 0) {
      toast.error("请选择要派工的订单");
      return;
    }
    if (!assignData.assigned_to_id) {
      toast.error("请选择派工人员");
      return;
    }

    try {
      await installationDispatchApi.orders.batchAssign({
        order_ids: Array.from(selectedOrders),
        assigned_to_id: Number(assignData.assigned_to_id),
        remark: assignData.remark,
      });
      toast.success("批量派工成功");
      setShowAssignDialog(false);
      setSelectedOrders(new Set());
      setAssignData({ assigned_to_id: null, remark: "" });
      fetchOrders();
      fetchStatistics();
    } catch (error) {
      console.error("Failed to batch assign:", error);
      toast.error("批量派工失败");
    }
  };

  const handleOpenWorkLogDialog = () => {
    const today = getLocalDateInputValue();
    setWorkLogDate(today);
    setWorkLogData(getInitialWorkLogData());
    setShowWorkLogDialog(true);
  };

  const handleSubmitFieldServiceWorkLog = async () => {
    const dispatchOrderIds = (workLogContext?.items || []).map((item) => item.dispatch_order_id);
    if (dispatchOrderIds.length === 0) {
      toast.error("当天没有可提交的外出派工单");
      return;
    }

    setWorkLogSubmitting(true);
    try {
      await workLogApi.createFromDispatch({
        work_date: workLogDate,
        dispatch_order_ids: dispatchOrderIds,
        today_progress: workLogData.today_progress,
        issues_found: workLogData.issues_found,
        next_plan: workLogData.next_plan,
        work_hours: workLogData.work_hours ? Number(workLogData.work_hours) : undefined,
      });
      toast.success("工作日志已提交");
      setShowWorkLogDialog(false);
      setWorkLogData(getInitialWorkLogData());
    } catch (error) {
      console.error("Failed to submit field service work log:", error);
      toast.error("提交工作日志失败");
    } finally {
      setWorkLogSubmitting(false);
    }
  };

  // Selection handlers
  const handleSelectOrder = (orderId) => {
    const newSelected = new Set(selectedOrders);
    if (newSelected.has(orderId)) {
      newSelected.delete(orderId);
    } else {
      newSelected.add(orderId);
    }
    setSelectedOrders(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedOrders.size === orders?.length) {
      setSelectedOrders(new Set());
    } else {
      setSelectedOrders(new Set((orders || []).map((order) => order.id)));
    }
  };

  // Quick action handlers for overview component
  const handleQuickAction = (action) => {
    switch (action) {
      case "createDispatch":
        setShowCreateDialog(true);
        break;
      case "viewPending":
        setFilterStatus(DISPATCH_STATUS.PENDING);
        break;
      case "viewOverdue":
        // Filter overdue tasks
        {
          const today = new Date().toISOString().split("T")[0];
          setSearchQuery(today);
        }
        break;
      case "technicianSchedule":
        // Navigate to technician schedule view
        navigate("/technician-schedule");
        break;
      default:
        break;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="安装调试派工管理"
        description="管理安装调试派工单、批量派工、进度跟踪"
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={handleOpenWorkLogDialog}>
              <FileText className="mr-2 h-4 w-4" />
              今日外出日志
            </Button>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              新建派工单
            </Button>
          </div>
        }
      />

      {/* Overview Section */}
      <InstallationDispatchOverview
        dispatches={orders}
        technicians={users}
        onQuickAction={handleQuickAction}
      />

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle>派工单列表</CardTitle>
          <CardDescription>管理所有安装调试派工单</CardDescription>
        </CardHeader>
        <CardContent>
          <DispatchFilters
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            filterStatus={filterStatus}
            setFilterStatus={setFilterStatus}
            filterPriority={filterPriority}
            setFilterPriority={setFilterPriority}
            filterProject={filterProject}
            setFilterProject={setFilterProject}
            filterTaskType={filterTaskType}
            setFilterTaskType={setFilterTaskType}
            projects={projects}
          />

          <DispatchBatchActions
            selectedCount={selectedOrders.size}
            onBatchAssign={() => setShowAssignDialog(true)}
            onCancelSelection={() => setSelectedOrders(new Set())}
          />

          <DispatchList
            orders={orders}
            loading={loading}
            selectedOrders={selectedOrders}
            onSelectOrder={handleSelectOrder}
            onSelectAll={handleSelectAll}
            onViewDetail={(order) => {
              setSelectedOrder(order);
              setShowDetailDialog(true);
            }}
            onAssign={(order) => {
              setSelectedOrder(order);
              setShowAssignDialog(true);
            }}
            onStart={(order) => handleStartOrder(order.id)}
            onUpdateProgress={(order) => {
              setSelectedOrder(order);
              setProgressData({
                progress: order.progress || 0,
                execution_notes: "",
              });
              setShowProgressDialog(true);
            }}
            onComplete={(order) => {
              setSelectedOrder(order);
              setShowCompleteDialog(true);
            }}
          />
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <CreateDispatchDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        createData={createData}
        onDataChange={setCreateData}
        projects={projects}
        machines={machines}
        onCreate={handleCreateOrder}
      />

      {/* Assign Dialog */}
      <AssignDispatchDialog
        open={showAssignDialog}
        onOpenChange={setShowAssignDialog}
        assignData={assignData}
        onDataChange={setAssignData}
        users={users}
        isBatch={selectedOrders.size > 0}
        onAssign={() =>
          selectedOrders.size > 0
            ? handleBatchAssign()
            : handleAssignOrder(selectedOrder.id)
        }
      />

      {/* Detail Dialog */}
      <DispatchDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        order={selectedOrder}
      />

      {/* Progress Dialog */}
      <UpdateProgressDialog
        open={showProgressDialog}
        onOpenChange={setShowProgressDialog}
        progressData={progressData}
        onDataChange={setProgressData}
        onUpdate={handleUpdateProgress}
      />

      {/* Complete Dialog */}
      <CompleteDispatchDialog
        open={showCompleteDialog}
        onOpenChange={setShowCompleteDialog}
        completeData={completeData}
        onDataChange={setCompleteData}
        onComplete={handleCompleteOrder}
      />

      <FieldServiceWorkLogDialog
        open={showWorkLogDialog}
        onOpenChange={setShowWorkLogDialog}
        workLogDate={workLogDate}
        onWorkLogDateChange={setWorkLogDate}
        context={workLogContext}
        contextLoading={workLogLoading}
        logData={workLogData}
        onLogDataChange={setWorkLogData}
        onSubmit={handleSubmitFieldServiceWorkLog}
        submitting={workLogSubmitting}
      />
    </div>
  );
}
