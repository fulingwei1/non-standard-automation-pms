import { useState, useEffect, useMemo, useCallback } from "react";
import { productionApi, userApi } from "../../../services/api";
import { DEFAULT_WORKSHOP_FORM } from "../constants";

export function useWorkshopManagement() {
  const [loading, setLoading] = useState(true);
  const [workshops, setWorkshops] = useState([]);
  const [managers, setManagers] = useState([]);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterActive, setFilterActive] = useState("");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedWorkshop, setSelectedWorkshop] = useState(null);

  // Form state
  const [workshopForm, setWorkshopForm] = useState({ ...DEFAULT_WORKSHOP_FORM });

  const fetchManagers = useCallback(async () => {
    try {
      const res = await userApi.list({ page_size: 1000 });
      setManagers(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch managers:", error);
    }
  }, []);

  const fetchWorkshops = useCallback(async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 100 };
      if (filterType) params.workshop_type = filterType;
      if (filterActive !== "") params.is_active = filterActive === "true";
      if (searchKeyword) params.search = searchKeyword;
      const res = await productionApi.workshops.list(params);
      setWorkshops(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch workshops:", error);
    } finally {
      setLoading(false);
    }
  }, [filterType, filterActive, searchKeyword]);

  useEffect(() => {
    fetchManagers();
  }, [fetchManagers]);

  useEffect(() => {
    fetchWorkshops();
  }, [fetchWorkshops]);

  const resetForm = useCallback(() => {
    setWorkshopForm({ ...DEFAULT_WORKSHOP_FORM });
    setSelectedWorkshop(null);
  }, []);

  const handleCreate = useCallback(async () => {
    if (!workshopForm.workshop_code || !workshopForm.workshop_name) {
      alert("请填写车间编码和名称");
      return;
    }
    try {
      await productionApi.workshops.create(workshopForm);
      setShowCreateDialog(false);
      resetForm();
      fetchWorkshops();
    } catch (error) {
      console.error("Failed to create workshop:", error);
      alert("创建车间失败: " + (error.response?.data?.detail || error.message));
    }
  }, [workshopForm, resetForm, fetchWorkshops]);

  const handleEdit = useCallback(async () => {
    if (!selectedWorkshop) return;
    try {
      await productionApi.workshops.update(selectedWorkshop.id, workshopForm);
      setShowEditDialog(false);
      resetForm();
      fetchWorkshops();
    } catch (error) {
      console.error("Failed to update workshop:", error);
      alert("更新车间失败: " + (error.response?.data?.detail || error.message));
    }
  }, [selectedWorkshop, workshopForm, resetForm, fetchWorkshops]);

  const handleViewDetail = useCallback(async (workshopId) => {
    try {
      const res = await productionApi.workshops.get(workshopId);
      setSelectedWorkshop(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch workshop detail:", error);
    }
  }, []);

  const handleEditClick = useCallback((workshop) => {
    setSelectedWorkshop(workshop);
    setWorkshopForm({
      workshop_code: workshop.workshop_code,
      workshop_name: workshop.workshop_name,
      workshop_type: workshop.workshop_type,
      manager_id: workshop.manager_id,
      location: workshop.location || "",
      capacity_hours: workshop.capacity_hours || 0,
      description: workshop.description || "",
      is_active: workshop.is_active !== false,
    });
    setShowEditDialog(true);
  }, []);

  const filteredWorkshops = useMemo(() => {
    return (workshops || []).filter((ws) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          ws.workshop_code?.toLowerCase().includes(keyword) ||
          ws.workshop_name?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [workshops, searchKeyword]);

  return {
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
    resetForm,
  };
}
