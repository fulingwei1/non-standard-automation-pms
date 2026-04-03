import { useState, useMemo, useEffect, useCallback } from "react";
import {
  Wrench,
  RefreshCw,
  AlertTriangle,
  Star,
  FileText,
  Users,
} from "lucide-react";
import { serviceApi } from "../../services/api";
import {
  getServiceTypeConfig,
  calculateServiceDuration,
} from "../../components/service-record";
import { toast } from "../../components/ui/toast";
import { INITIAL_FORM_DATA } from "./constants";

/**
 * Transforms raw backend record data into the frontend format.
 */
function transformRecord(record) {
  return {
    id: record.id,
    record_no: record.record_no || "",
    service_type: record.service_type || "",
    project_code: record.project_code || "",
    project_name: record.project_name || "",
    machine_no: record.machine_no || "",
    customer_name: record.customer_name || "",
    service_location: record.service_location || "",
    service_date: record.service_date || "",
    service_start_time: record.service_start_time || "",
    service_end_time: record.service_end_time || "",
    service_duration: record.service_duration || 0,
    service_engineer: record.service_engineer || "",
    service_engineer_phone: record.service_engineer_phone || "",
    customer_contact: record.customer_contact || "",
    customer_phone: record.customer_phone || "",
    service_content: record.service_content || "",
    service_result: record.service_result || "",
    issues_found: record.issues_found || "",
    solutions: record.solutions || "",
    customer_satisfaction: record.customer_satisfaction || null,
    customer_feedback: record.customer_feedback || "",
    customer_signature: record.customer_signature || false,
    signature_time: record.signature_time || "",
    photos: record.photos || [],
    status: record.status || "进行中",
    created_at: record.created_at || "",
  };
}

/**
 * Returns the Lucide icon component for a given service type.
 */
export function getServiceTypeIcon(type) {
  const typeConfig = getServiceTypeConfig(type);
  const iconMap = {
    Wrench: Wrench,
    Users: Users,
    RefreshCw: RefreshCw,
    AlertTriangle: AlertTriangle,
    TrendingUp: Star,
    FileText: FileText,
  };
  return iconMap[typeConfig.icon] || FileText;
}

/**
 * Main page-level hook for ServiceRecord.
 * Owns all state, filtering, data loading, and action handlers.
 */
export function useServiceRecordPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [dateFilter, setDateFilter] = useState({ start: "", end: "" });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    inProgress: 0,
    completed: 0,
    thisMonth: 0,
    totalHours: 0,
  });

  const [formData, setFormData] = useState({ ...INITIAL_FORM_DATA });

  // Filtered records
  const filteredRecords = useMemo(() => {
    let result = records;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = (result || []).filter(
        (record) =>
          (record.record_no || "").toLowerCase().includes(query) ||
          (record.project_name || "").toLowerCase().includes(query) ||
          (record.customer_name || "").toLowerCase().includes(query) ||
          (record.service_location || "").toLowerCase().includes(query) ||
          (record.service_engineer || "").toLowerCase().includes(query)
      );
    }

    if (typeFilter !== "ALL") {
      result = (result || []).filter((record) => record.service_type === typeFilter);
    }

    if (statusFilter !== "ALL") {
      result = (result || []).filter((record) => record.status === statusFilter);
    }

    if (dateFilter.start) {
      const startDate = new Date(dateFilter.start);
      result = (result || []).filter((record) => {
        const recordDate = new Date(record.service_date);
        return recordDate >= startDate;
      });
    }

    if (dateFilter.end) {
      const endDate = new Date(dateFilter.end);
      result = (result || []).filter((record) => {
        const recordDate = new Date(record.service_date);
        return recordDate <= endDate;
      });
    }

    return result;
  }, [records, searchQuery, typeFilter, statusFilter, dateFilter]);

  // Load records
  const loadRecords = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { page: 1, page_size: 1000 };
      const response = await serviceApi.records.list(params);
      const recordsData =
        response.data?.items || response.data?.items || response.data || [];
      const transformedRecords = (recordsData || []).map(transformRecord);
      setRecords(transformedRecords);
    } catch (err) {
      console.error("Failed to load records:", err);
      setError(err.response?.data?.detail || err.message || "加载服务记录失败");
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Compute statistics
  const loadStatistics = useCallback(async () => {
    try {
      const now = new Date();
      const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);

      setStats({
        total: records?.length,
        inProgress: (records || []).filter(
          (r) => r.status === "进行中" || r.status === "IN_PROGRESS"
        ).length,
        completed: (records || []).filter(
          (r) => r.status === "已完成" || r.status === "COMPLETED"
        ).length,
        thisMonth: (records || []).filter((r) => {
          if (!r.service_date) return false;
          const recordDate = new Date(r.service_date);
          return recordDate >= thisMonthStart;
        }).length,
        totalHours: (records || []).reduce(
          (sum, r) => sum + (r.service_duration || 0),
          0
        ),
      });
    } catch (err) {
      console.error("Failed to load statistics:", err);
    }
  }, [records]);

  // Initial load
  useEffect(() => {
    loadRecords();
  }, []);

  useEffect(() => {
    if (records?.length > 0 || !loading) {
      loadStatistics();
    }
  }, [records, loading, loadStatistics]);

  // Create record
  const handleCreateRecord = async () => {
    try {
      const serviceData = {
        ...formData,
        service_duration: calculateServiceDuration(
          formData.service_start_time,
          formData.service_end_time
        ),
      };

      await serviceApi.records.create(serviceData);
      setShowCreateDialog(false);
      resetForm();
      await loadRecords();
      toast.success("服务记录创建成功");
    } catch (error) {
      console.error("Failed to create record:", error);
      toast.error(
        "创建失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const resetForm = () => {
    setFormData({ ...INITIAL_FORM_DATA });
  };

  const handleViewDetail = (record) => {
    setSelectedRecord(record);
    setShowDetailDialog(true);
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case "createService":
        setShowCreateDialog(true);
        break;
      case "todaySchedule": {
        const today = new Date().toISOString().split("T")[0];
        setDateFilter({ start: today, end: today });
        break;
      }
      case "pendingReports":
        setStatusFilter("PENDING_REVIEW");
        break;
      case "customerFeedback":
        setRecords((records || []).filter((r) => r.customer_feedback));
        break;
    }
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    const newPhotos = (files || []).map((file) => ({
      file,
      url: URL.createObjectURL(file),
      name: file.name,
    }));
    setFormData((prev) => ({
      ...prev,
      photos: [...prev.photos, ...newPhotos],
    }));
  };

  const removePhoto = (index) => {
    setFormData((prev) => ({
      ...prev,
      photos: (prev.photos || []).filter((_, i) => i !== index),
    }));
  };

  return {
    records,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    typeFilter,
    setTypeFilter,
    statusFilter,
    setStatusFilter,
    dateFilter,
    setDateFilter,
    showCreateDialog,
    setShowCreateDialog,
    showDetailDialog,
    setShowDetailDialog,
    selectedRecord,
    stats,
    formData,
    setFormData,
    filteredRecords,
    loadRecords,
    handleCreateRecord,
    handleViewDetail,
    handleQuickAction,
    handlePhotoUpload,
    removePhoto,
  };
}
