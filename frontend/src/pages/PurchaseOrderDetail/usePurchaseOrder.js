/**
 * Purchase Order Detail - Custom hook for loading and managing PO state
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { purchaseApi } from "../../services/api";
import { transformOrderData } from "./utils";

export function usePurchaseOrder(id) {
  const [po, setPo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadPurchaseOrder = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const orderId = id || parseInt(id);
      if (!orderId) {
        throw new Error("\u8ba2\u5355ID\u4e0d\u80fd\u4e3a\u7a7a");
      }

      const response = await purchaseApi.orders.get(orderId);
      const orderData = response.data || response;

      // Load goods receipts for this order
      let receipts = [];
      try {
        const receiptsResponse = await purchaseApi.goodsReceipts.list({
          purchase_order_id: orderId,
        });
        receipts =
          receiptsResponse.data?.items ||
          receiptsResponse.data?.items ||
          receiptsResponse.data ||
          [];
      } catch (err) {
        console.error("Failed to load receipts:", err);
      }

      setPo(transformOrderData(orderData, receipts));
    } catch (err) {
      console.error("Failed to load purchase order:", err);
      setError(
        err.response?.data?.detail || err.message || "\u52a0\u8f7d\u91c7\u8d2d\u8ba2\u5355\u5931\u8d25"
      );
      setPo(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadPurchaseOrder();
  }, [loadPurchaseOrder]);

  const progress = useMemo(() => {
    if (!po) return 0;
    const completedStages = (po.timeline || []).filter(
      (s) => s.status === "completed"
    ).length;
    return po.timeline?.length > 0
      ? (completedStages / po.timeline.length) * 100
      : 0;
  }, [po]);

  const totalItems = useMemo(() => {
    if (!po) return 0;
    return (po.items || []).reduce((sum, item) => sum + item.amount, 0);
  }, [po]);

  return { po, loading, error, progress, totalItems };
}
