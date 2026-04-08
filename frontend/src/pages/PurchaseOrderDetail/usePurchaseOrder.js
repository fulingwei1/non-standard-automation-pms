/**
 * Purchase Order Detail - Custom hook for loading and managing PO state
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { purchaseApi } from "../../services/api";
import { transformOrderData } from "./utils";

const resolveReceiptsApi = () => purchaseApi.goodsReceipts || purchaseApi.receipts;

export function usePurchaseOrder(id) {
  const [po, setPo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadPurchaseOrder = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const orderId = Number(id);
      if (!orderId) {
        throw new Error("订单ID不能为空");
      }

      const response = await purchaseApi.orders.get(orderId);
      const orderData = response?.data ?? response;

      if (!orderData) {
        setPo(null);
        setError(null);
        return;
      }

      let receipts = [];
      const receiptsApi = resolveReceiptsApi();

      if (receiptsApi?.list) {
        try {
          const receiptsResponse = await receiptsApi.list({
            purchase_order_id: orderId,
          });
          receipts =
            receiptsResponse?.data?.items ||
            receiptsResponse?.data ||
            receiptsResponse ||
            [];
        } catch (err) {
          console.error("Failed to load receipts:", err);
        }
      }

      setPo(transformOrderData(orderData, Array.isArray(receipts) ? receipts : []));
    } catch (err) {
      console.error("Failed to load purchase order:", err);
      setError(
        err.response?.data?.detail || err.message || "加载采购订单失败"
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
      (stage) => stage.status === "completed"
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
