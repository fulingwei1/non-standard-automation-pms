import { useState, useEffect, useMemo, useCallback } from "react";
import { productionApi, projectApi } from "../../../services/api";
import { INITIAL_NEW_ORDER, INITIAL_ASSIGN_DATA } from "../statusConstants";

/**
 * Hook encapsulating all work-order CRUD, filtering, and dialog state.
 */
export function useWorkOrders() {
  const [loading, setLoading] = useState(true);
  const [workOrders, setWorkOrders] = useState([]);
  const [projects, setProjects] = useState([]);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  // Form states
  const [newOrder, setNewOrder] = useState({ ...INITIAL_NEW_ORDER });
  const [assignData, setAssignData] = useState({ ...INITIAL_ASSIGN_DATA });

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  }, []);

  const fetchWorkOrders = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject) params.project_id = filterProject;
      if (filterStatus) params.status = filterStatus;
      if (filterPriority) params.priority = filterPriority;
      if (searchKeyword) params.search = searchKeyword;
      const res = await productionApi.workOrders.list(params);
      const orderList = res.data?.items || res.data?.items || res.data || [];
      setWorkOrders(orderList);
    } catch (error) {
      console.error("Failed to fetch work orders:", error);
    } finally {
      setLoading(false);
    }
  }, [filterProject, filterStatus, filterPriority, searchKeyword]);

  useEffect(() => {
    fetchProjects();
    fetchWorkOrders();
  }, [fetchProjects, fetchWorkOrders]);

  const handleCreateOrder = useCallback(async () => {
    if (!newOrder.task_name || !newOrder.project_id) {
      alert("请填写任务名称和选择项目");
      return;
    }
    try {
      await productionApi.workOrders.create(newOrder);
      setShowCreateDialog(false);
      setNewOrder({ ...INITIAL_NEW_ORDER });
      fetchWorkOrders();
    } catch (error) {
      console.error("Failed to create work order:", error);
      alert("创建工单失败: " + (error.response?.data?.detail || error.message));
    }
  }, [newOrder, fetchWorkOrders]);

  const handleViewDetail = useCallback(async (orderId) => {
    try {
      const res = await productionApi.workOrders.get(orderId);
      setSelectedOrder(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch work order detail:", error);
    }
  }, []);

  const handleAssign = useCallback(async () => {
    if (!selectedOrder) return;
    try {
      await productionApi.workOrders.assign(selectedOrder.id, assignData);
      setShowAssignDialog(false);
      setAssignData({ ...INITIAL_ASSIGN_DATA });
      fetchWorkOrders();
      if (showDetailDialog) {
        const res = await productionApi.workOrders.get(selectedOrder.id);
        setSelectedOrder(res.data || res);
      }
    } catch (error) {
      console.error("Failed to assign work order:", error);
      alert("派工失败: " + (error.response?.data?.detail || error.message));
    }
  }, [selectedOrder, assignData, showDetailDialog, fetchWorkOrders]);

  const filteredOrders = useMemo(() => {
    return (workOrders || []).filter((order) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          order.work_order_no?.toLowerCase().includes(keyword) ||
          order.task_name?.toLowerCase().includes(keyword) ||
          order.material_name?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [workOrders, searchKeyword]);

  return {
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
    handleViewDetail,
    handleAssign,
  };
}
