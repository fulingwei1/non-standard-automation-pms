import { useState, useCallback } from "react";
import { productionApi, userApi } from "../../../services/api";
import { useDataManagement } from "../../../hooks/useDataManagement";
import { DEFAULT_WORKSHOP_FORM } from "../constants";

/**
 * 车间管理数据 Hook
 *
 * 重构说明：加载 / 过滤 / reload / mutate 的公共逻辑已下沉到
 * `useDataManagement`，本 hook 只保留车间领域特有的状态与操作。
 * 对外暴露的 API 与重构前完全一致。
 */
export function useWorkshopManagement() {
  // ── Filter state ─────────────────────────────────────────────────────────
  // Kept here so the UI can drive them independently before useDataManagement
  // sees them bundled in `filters`.
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterActive, setFilterActive] = useState("");

  // ── Shared data-management core ───────────────────────────────────────────
  const {
    filteredData: filteredWorkshops,
    loading,
    reload: fetchWorkshops,
    mutate,
  } = useDataManagement(
    // fetchFn: called by useDataManagement on mount and whenever filters change.
    // Receives the filters object; we destructure the three fields we care about.
    ({ type, active, search }) => {
      const params = { page: 1, page_size: 100 };
      if (type) params.workshop_type = type;
      if (active !== "") params.is_active = active === "true";
      if (search) params.search = search;
      return productionApi.workshops.list(params);
    },
    {
      // Keep defaultFilters in sync with the three individual useState values
      // above. The setters below update both the local state (for the UI's
      // controlled inputs) AND the shared filters object (to trigger re-fetch).
      defaultFilters: { type: filterType, active: filterActive, search: searchKeyword },

      // Client-side keyword filter mirrors the original useMemo in this hook.
      filterFn: (ws, { search }) => {
        if (!search) return true;
        const keyword = search.toLowerCase();
        return (
          ws.workshop_code?.toLowerCase().includes(keyword) ||
          ws.workshop_name?.toLowerCase().includes(keyword)
        );
      },
    },
  );

  // ── Secondary data: managers list ─────────────────────────────────────────
  const { filteredData: managers, reload: _fetchManagers } = useDataManagement(
    () => userApi.list({ page_size: 1000 }),
    { autoLoad: true },
  );

  // ── Dialog & selection state ──────────────────────────────────────────────
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedWorkshop, setSelectedWorkshop] = useState(null);

  // ── Form state ────────────────────────────────────────────────────────────
  const [workshopForm, setWorkshopForm] = useState({ ...DEFAULT_WORKSHOP_FORM });

  // ── Helpers ───────────────────────────────────────────────────────────────
  const resetForm = useCallback(() => {
    setWorkshopForm({ ...DEFAULT_WORKSHOP_FORM });
    setSelectedWorkshop(null);
  }, []);

  // ── CRUD handlers ─────────────────────────────────────────────────────────
  const handleCreate = useCallback(async () => {
    if (!workshopForm.workshop_code || !workshopForm.workshop_name) {
      alert("请填写车间编码和名称");
      return;
    }
    const result = await mutate(() =>
      productionApi.workshops.create(workshopForm),
    );
    if (result.success) {
      setShowCreateDialog(false);
      resetForm();
    } else {
      console.error("Failed to create workshop:", result.error);
      alert("创建车间失败: " + result.error);
    }
  }, [workshopForm, resetForm, mutate]);

  const handleEdit = useCallback(async () => {
    if (!selectedWorkshop) return;
    const result = await mutate(() =>
      productionApi.workshops.update(selectedWorkshop.id, workshopForm),
    );
    if (result.success) {
      setShowEditDialog(false);
      resetForm();
    } else {
      console.error("Failed to update workshop:", result.error);
      alert("更新车间失败: " + result.error);
    }
  }, [selectedWorkshop, workshopForm, resetForm, mutate]);

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
      workshop_code:  workshop.workshop_code,
      workshop_name:  workshop.workshop_name,
      workshop_type:  workshop.workshop_type,
      manager_id:     workshop.manager_id,
      location:       workshop.location || "",
      capacity_hours: workshop.capacity_hours || 0,
      description:    workshop.description || "",
      is_active:      workshop.is_active !== false,
    });
    setShowEditDialog(true);
  }, []);

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
