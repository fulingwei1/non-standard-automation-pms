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

const getViewMode = (location, params) => {
  const path = location.pathname;
  if (path.endsWith("/new")) return "create";
  if (path.endsWith("/edit")) return "edit";
  if (params.id && !path.endsWith("/edit")) return "detail";
  return "list";
};

const useDeliveryManagement = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const params = useParams();
  const location = useLocation();

  const viewMode = getViewMode(location, params);
  const projectContextFilters = useMemo(
    () => getProjectContextFilters(searchParams),
    [searchParams],
  );
  const buildDeliveryPath = (path) => {
    const query = searchParams.toString();
    return `${path}${query ? `?${query}` : ""}`;
  };

  // ── state ──────────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [deliveries, setDeliveries] = useState([]);
  const [deliveryStatistics, setDeliveryStatistics] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [searchText, setSearchText] = useState("");
  const [_filters, _setFilters] = useState({});

  // ── data loading ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (viewMode === "list") loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      toast({
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
        (delivery.orderNumber || "").toLowerCase().includes(searchLower) ||
        (delivery.customerName || "").toLowerCase().includes(searchLower);
      return matchesSearch;
    });
  }, [deliveries, searchText]);

  // ── navigation helpers ─────────────────────────────────────────────────────
  const handleBack = () => navigate(buildDeliveryPath("/pmc/delivery-orders"));

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
    buildDeliveryPath,
    navigate,
  };
};

export default useDeliveryManagement;
