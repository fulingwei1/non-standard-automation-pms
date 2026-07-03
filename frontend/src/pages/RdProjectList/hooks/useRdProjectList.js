import { useState, useCallback, useEffect } from "react";
import { rdProjectApi } from "../../../services/api";
import { DEFAULT_PAGINATION } from "../constants";

const getErrorMessage = (err) => {
  const detail = err.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || JSON.stringify(item))
      .join("; ");
  }
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return err.response?.data?.message || err.message;
};

export function useRdProjectList() {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategoryType, setFilterCategoryType] = useState("all");
  const [viewMode, setViewMode] = useState("grid");
  const [formOpen, setFormOpen] = useState(false);
  const [pagination, setPagination] = useState(DEFAULT_PAGINATION);

  const fetchCategories = useCallback(async () => {
    try {
      const response = await rdProjectApi.getCategories();
      const data =
        response.data?.data || response.data?.items || response.data || [];
      setCategories(data);
    } catch (err) {
      console.error("Failed to fetch categories:", err);
    }
  }, []);

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
      };
      if (searchQuery) params.keyword = searchQuery;
      if (filterStatus && filterStatus !== "all") params.status = filterStatus;
      if (filterCategoryType && filterCategoryType !== "all")
        params.category_type = filterCategoryType;

      const response = await rdProjectApi.list(params);
      const data = response.data || response;

      if (data.items) {
        setProjects(data.items || []);
        setPagination({
          page: data.page || 1,
          page_size: data.page_size || 20,
          total: data.total || 0,
          pages: data.pages || 0,
        });
      } else {
        setProjects(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, searchQuery, filterStatus, filterCategoryType]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleCreateProject = async (data) => {
    try {
      const response = await rdProjectApi.create(data);
      if (response.data?.code === 201 || response.status === 201) {
        setFormOpen(false);
        fetchProjects();
      } else {
        throw new Error(response.data?.message || "创建失败");
      }
    } catch (err) {
      alert("创建研发项目失败: " + getErrorMessage(err));
      throw err;
    }
  };

  return {
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
  };
}
