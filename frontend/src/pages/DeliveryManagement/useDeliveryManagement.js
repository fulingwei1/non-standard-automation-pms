/**
 * DeliveryManagement — primary data hook
 * Owns list/statistics fetching, search text, and derived filtered list.
 */

import { useState, useEffect, useMemo } from "react";
import { useSearchParams, useNavigate, useParams, useLocation } from "react-router-dom";

import { toast } from "../../components/ui";
import { businessSupportApi } from "../../services/api";
import { getProjectContextFilters } from "../../lib/projectContext";
import { getItemsCompat } from "../../utils/apiResponse";
import { normalizeDelivery } from "./constants";
import { notifyDelivery } from "./notify";

const getViewMode = (location, params) => {
  const path = location.pathname;
  if (path.endsWith("/new")) return "create";
  if (path.endsWith("/edit")) return "edit";
  if (params.id && !path.endsWith("/edit")) return "detail";
  return "list";
};

const getDefaultTab = (location, searchParams) => {
  if (location.pathname === "/pmc/delivery-plan") return "plan";
  if (searchParams.get("status") === "in_transit") return "tracking";
  return "overview";
};

const matchesRouteStatus = (delivery, routeStatus) => {
  if (!routeStatus) return true;
  if (routeStatus === "pending") {
    return ["pending", "preparing"].includes(delivery.status);
  }
  if (routeStatus === "in_transit") {
    return ["shipped", "in_transit"].includes(delivery.status);
  }
  return delivery.status === routeStatus;
};

const csvEscape = (value) => {
  const text = value == null ? "" : String(value);
  return `"${text.replace(/"/g, '""')}"`;
};

const useDeliveryManagement = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const params = useParams();
  const location = useLocation();

  const viewMode = getViewMode(location, params);
  const routeStatus = searchParams.get("status") || "";
  const defaultTab = useMemo(
    () => getDefaultTab(location, searchParams),
    [location, searchParams],
  );
  const projectContextFilters = useMemo(
    () => getProjectContextFilters(searchParams),
    [searchParams],
  );
  const orderContextId = searchParams.get("order_id") || searchParams.get("orderId");
  const canCreateDeliveryPlan = Boolean(projectContextFilters.project_id || orderContextId);
  const buildDeliveryPath = (path) => {
    const query = searchParams.toString();
    return `${path}${query ? `?${query}` : ""}`;
  };

  // ── state ──────────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [deliveries, setDeliveries] = useState([]);
  const [deliveryStatistics, setDeliveryStatistics] = useState(null);
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [searchText, setSearchText] = useState("");
  const [_filters, _setFilters] = useState({});
  const notify = (options) => notifyDelivery(toast, options);

  // ── data loading ───────────────────────────────────────────────────────────
  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  useEffect(() => {
    if (viewMode === "list") loadData();
     
  }, [activeTab, viewMode]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [listRes, statsRes] = await Promise.all([
        businessSupportApi.deliveryOrders.list({
          page: 1,
          page_size: 200,
          ...projectContextFilters,
        }),
        businessSupportApi.deliveryOrders
          .statistics(projectContextFilters)
          .catch(() => ({ data: null })),
      ]);
      const items = getItemsCompat(listRes);
      setDeliveries(Array.isArray(items) ? items.map(normalizeDelivery) : []);
      const statsData = statsRes?.data?.data ?? statsRes?.data ?? null;
      setDeliveryStatistics(statsData);
    } catch (_error) {
      notify({
        title: "错误",
        description: "加载交付数据失败",
        variant: "destructive",
      });
      setDeliveries([]);
    } finally {
      setLoading(false);
    }
  };

  // ── derived data ───────────────────────────────────────────────────────────
  const filteredDeliveries = useMemo(() => {
    return (deliveries || []).filter((delivery) => {
      const searchLower = (searchText || "").toLowerCase();
      const matchesSearch =
        !searchText ||
        (delivery.deliveryNo || "").toLowerCase().includes(searchLower) ||
        (delivery.orderNumber || "").toLowerCase().includes(searchLower) ||
        (delivery.customerName || "").toLowerCase().includes(searchLower) ||
        (delivery.trackingNumber || "").toLowerCase().includes(searchLower);
      return matchesSearch && matchesRouteStatus(delivery, routeStatus);
    });
  }, [deliveries, routeStatus, searchText]);

  const handleExport = () => {
    const rows = filteredDeliveries || [];
    if (rows.length === 0) {
      notify({
        title: "提示",
        description: "当前没有可导出的发货单",
      });
      return;
    }

    const header = [
      "发货单号",
      "销售订单号",
      "客户名称",
      "审批状态",
      "发货状态",
      "计划发货日期",
      "实际发货日期",
      "物流公司",
      "物流单号",
      "发货金额",
      "收货人",
      "收货地址",
    ];
    const body = rows.map((item) =>
      [
        item.deliveryNo,
        item.orderNumber,
        item.customerName,
        item.approvalStatus,
        item.deliveryStatusRaw,
        item.scheduledDate,
        item.actualDate || item.shipDate,
        item.logisticsCompany,
        item.trackingNumber,
        item.deliveryAmount,
        item.receiverName,
        item.deliveryAddress,
      ].map(csvEscape).join(",")
    );
    const csv = `\ufeff${header.map(csvEscape).join(",")}\n${body.join("\n")}`;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `发货报表_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    notify({ title: "成功", description: "发货报表已导出" });
  };

  // ── navigation helpers ─────────────────────────────────────────────────────
  const handleBack = () => navigate(buildDeliveryPath("/pmc/delivery-orders"));
  const handleView = (id) => navigate(buildDeliveryPath(`/pmc/delivery-orders/${id}`));
  const handleEdit = (id) => navigate(buildDeliveryPath(`/pmc/delivery-orders/${id}/edit`));

  return {
    viewMode,
    params,
    loading,
    deliveries,
    deliveryStatistics,
    filteredDeliveries,
    activeTab,
    setActiveTab,
    searchText,
    setSearchText,
    loadData,
    handleBack,
    handleView,
    handleEdit,
    handleExport,
    buildDeliveryPath,
    canCreateDeliveryPlan,
    navigate,
  };
};

export default useDeliveryManagement;
