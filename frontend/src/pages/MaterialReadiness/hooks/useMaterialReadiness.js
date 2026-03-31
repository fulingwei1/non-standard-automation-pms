import { useState, useEffect, useMemo, useCallback } from "react";
import { materialApi, projectApi, supplierApi } from "../../../services/api";
import { toast } from "../../../components/ui/toast";
import {
  MATERIAL_STATUS,
  PRIORITY_LEVEL,
  calculateReadinessRate,
  getMaterialStatusStats,
  getCriticalShortages,
  calculateReadinessStatus,
} from "../../../components/material-readiness";

export function useMaterialReadiness() {
  const [loading, setLoading] = useState(true);
  const [materials, setMaterials] = useState([]);
  const [projects, setProjects] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [selectedProject, setSelectedProject] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterPriority, setFilterPriority] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        project_id:
          selectedProject && selectedProject !== "all"
            ? selectedProject
            : undefined,
        search: searchQuery,
        status: filterStatus || undefined,
        type: filterType || undefined,
        priority: filterPriority || undefined,
      };

      const [materialsRes, projectsRes, suppliersRes] = await Promise.all([
        materialApi.list(params),
        projectApi.list({ page_size: 1000 }),
        supplierApi.list({ page_size: 1000 }),
      ]);

      setMaterials(materialsRes.data?.items || materialsRes.data || []);
      setProjects(projectsRes.data?.items || projectsRes.data || []);
      setSuppliers(suppliersRes.data?.items || suppliersRes.data || []);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  }, [selectedProject, searchQuery, filterStatus, filterType, filterPriority]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const stats = useMemo(() => {
    const statusStats = getMaterialStatusStats(materials);
    const readinessRate = calculateReadinessRate(materials);
    const criticalShortages = getCriticalShortages(materials);
    const readinessStatus = calculateReadinessStatus(materials);

    return {
      total: statusStats.total,
      available: statusStats.available,
      outOfStock: statusStats.outOfStock,
      onOrder: statusStats.onOrder,
      readinessRate,
      criticalShortages: criticalShortages.length,
      readinessStatus,
    };
  }, [materials]);

  const urgentMaterials = useMemo(() => {
    return (materials || []).filter(
      (material) =>
        material.priority === PRIORITY_LEVEL.URGENT &&
        material.status !== MATERIAL_STATUS.AVAILABLE
    );
  }, [materials]);

  const arrivingMaterials = useMemo(() => {
    const today = new Date();
    const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

    return (materials || []).filter(
      (material) =>
        material.status === MATERIAL_STATUS.ON_ORDER &&
        material.expected_date &&
        new Date(material.expected_date) <= nextWeek
    );
  }, [materials]);

  return {
    loading,
    materials,
    projects,
    suppliers,
    selectedProject,
    setSelectedProject,
    searchQuery,
    setSearchQuery,
    filterStatus,
    setFilterStatus,
    filterType,
    setFilterType,
    filterPriority,
    setFilterPriority,
    fetchData,
    stats,
    urgentMaterials,
    arrivingMaterials,
  };
}
