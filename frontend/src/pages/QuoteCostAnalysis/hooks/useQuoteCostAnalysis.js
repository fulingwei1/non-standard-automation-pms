import { useState, useEffect, useMemo, useCallback } from "react";
import { quoteApi } from "../../../services/api";

const asList = (payload) => {
  const data = payload?.formatted ?? payload?.data?.data ?? payload?.data ?? payload;
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;
  return [];
};

/**
 * Custom hook encapsulating all data-fetching and state logic for
 * the Quote Cost Analysis page.
 */
export function useQuoteCostAnalysis(quoteId) {
  const [loading, setLoading] = useState(false);
  const [quote, setQuote] = useState(null);
  const [versions, setVersions] = useState([]);
  const [selectedVersions, setSelectedVersions] = useState([null, null]);
  const [comparison, setComparison] = useState(null);
  const [costStructure, setCostStructure] = useState(null);
  const [_costTrend, setCostTrend] = useState(null);

  const loadData = useCallback(async () => {
    if (!quoteId) return;
    setLoading(true);
    try {
      // Load quote
      const quoteRes = await quoteApi.get(quoteId);
      setQuote(quoteRes.data?.data || quoteRes.data);

      // Load versions
      const versionsRes = await quoteApi.getVersions(quoteId);
      const versionsList = asList(versionsRes);
      setVersions(versionsList);

      // Set default selected versions (latest two)
      if (versionsList.length >= 2) {
        setSelectedVersions([
          versionsList[versionsList.length - 2],
          versionsList[versionsList.length - 1],
        ]);
      } else if (versionsList.length === 1) {
        setSelectedVersions([versionsList[0], versionsList[0]]);
      }

      // Load cost structure for current version
      if (versionsList.length > 0) {
        const currentVersion = versionsList[versionsList.length - 1];
        try {
          const structureRes = await quoteApi.getCostStructure(
            quoteId,
            currentVersion.id
          );
          setCostStructure(structureRes.data?.data || structureRes.data);
        } catch (_e) {
          console.log("Cost structure not available:", _e);
        }
      }

      // Load cost trend
      try {
        const trendRes = await quoteApi.getCostTrend(quoteId, {});
        setCostTrend(trendRes.data?.data || trendRes.data);
      } catch (_e) {
        console.log("Cost trend not available:", _e);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
    } finally {
      setLoading(false);
    }
  }, [quoteId]);

  const loadComparison = useCallback(async () => {
    if (!selectedVersions[0] || !selectedVersions[1]) return;
    try {
      // Prefer backend version comparison endpoint
      const res = await quoteApi.compareVersions(
        quoteId,
        selectedVersions[0].id,
        selectedVersions[1].id
      );
      const data = res.data?.data || res.data;

      // Adapt to legacy display structure
      if (data?.summary_diff) {
        const v1Price = data?.version_1?.total_price || 0;
        const v1Cost = data?.version_1?.cost_total || 0;
        const v1Margin = data?.version_1?.gross_margin || 0;

        const priceChange = data?.summary_diff?.price_diff || 0;
        const costChange = data?.summary_diff?.cost_diff || 0;
        const marginChange = data?.summary_diff?.margin_diff || 0;

        setComparison({
          comparison: {
            price_change: priceChange,
            price_change_pct: v1Price ? (priceChange / v1Price) * 100 : 0,
            cost_change: costChange,
            cost_change_pct: v1Cost ? (costChange / v1Cost) * 100 : 0,
            margin_change: marginChange,
            margin_change_pct: v1Margin
              ? (marginChange / v1Margin) * 100
              : 0,
          },
          breakdown_comparison: [],
          item_diff: data?.item_diff || null,
        });
        return;
      }

      setComparison(data);
    } catch (error) {
      console.error("加载对比数据失败:", error);
      // Fall back to legacy endpoint to avoid a blank screen
      try {
        const fallbackRes = await quoteApi.compareCosts(quoteId, {
          version_ids: `${selectedVersions[0].id},${selectedVersions[1].id}`,
        });
        setComparison(fallbackRes.data?.data || fallbackRes.data);
      } catch (fallbackError) {
        console.error("旧对比接口也失败:", fallbackError);
      }
    }
  }, [quoteId, selectedVersions]);

  // Derived: cost structure enriched with percentage per category
  const structureByCategory = useMemo(() => {
    if (!costStructure?.by_category) return [];
    return (costStructure.by_category || []).map((cat) => ({
      ...cat,
      percentage:
        costStructure.total_cost > 0
          ? ((cat.amount / costStructure.total_cost) * 100).toFixed(2)
          : 0,
    }));
  }, [costStructure]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (selectedVersions[0] && selectedVersions[1]) {
      loadComparison();
    }
  }, [loadComparison, selectedVersions]);

  return {
    loading,
    quote,
    versions,
    selectedVersions,
    setSelectedVersions,
    comparison,
    costStructure,
    structureByCategory,
  };
}
