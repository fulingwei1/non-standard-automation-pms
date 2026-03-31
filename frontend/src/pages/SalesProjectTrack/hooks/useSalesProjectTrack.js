import { useState, useMemo, useEffect } from "react";
import { projectApi } from "../../../services/api";

/**
 * Custom hook for Sales Project Track page.
 * Handles data fetching, filtering, and derived stats.
 */
export function useSalesProjectTrack() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStage, setSelectedStage] = useState("all");
  const [selectedHealth, setSelectedHealth] = useState("all");

  // Fetch projects from API
  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await projectApi.list();
        const data = res.data?.items || res.data || [];
        setProjects(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to load sales projects:", err);
        setError("加载项目数据失败");
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  // Filtered project list
  const filteredProjects = useMemo(() => {
    return (projects || []).filter((project) => {
      const projectName = project.name || project.project_name || "";
      const projectId = String(project.id || project.project_code || "");
      const customerName =
        project.customerShort ||
        project.customer_name ||
        project.customer?.name ||
        "";

      const matchesSearch =
        !searchTerm ||
        projectName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        projectId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        customerName.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStage =
        selectedStage === "all" || project.stage === selectedStage;
      const matchesHealth =
        selectedHealth === "all" || project.health === selectedHealth;

      return matchesSearch && matchesStage && matchesHealth;
    });
  }, [projects, searchTerm, selectedStage, selectedHealth]);

  // Derived stats
  const stats = useMemo(() => {
    return {
      total: projects?.length ?? 0,
      inProgress: (projects || []).filter(
        (p) => !["warranty", "S9"].includes(p.stage)
      ).length,
      nearDelivery: (projects || []).filter((p) => {
        const deliveryDate =
          p.expectedDelivery || p.expected_delivery || p.plan_delivery_date;
        if (!deliveryDate) return false;
        const delivery = new Date(deliveryDate);
        const now = new Date();
        const diff = (delivery - now) / (1000 * 60 * 60 * 24);
        return diff <= 14 && diff > 0;
      }).length,
      hasIssue: (projects || []).filter(
        (p) => p.health && !["good", "H1"].includes(p.health)
      ).length,
    };
  }, [projects]);

  return {
    projects,
    loading,
    error,
    searchTerm,
    setSearchTerm,
    selectedStage,
    setSelectedStage,
    selectedHealth,
    setSelectedHealth,
    filteredProjects,
    stats,
  };
}
