/**
 * Material Tracking Page - Real-time material inventory and arrival tracking
 * Monitors material status from purchase to receipt and usage
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Package,
  Search,
  Plus,
  AlertCircle
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input
} from "../../components/ui";
import { cn, formatCurrency, formatDate } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { materialApi, purchaseApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

import { statusConfig } from "./constants";
import MaterialRow from "./MaterialRow";
import CreateMaterialDialog from "./CreateMaterialDialog";

const PURCHASE_ORDER_ITEM_LOOKUP_LIMIT = 8;

const toFiniteNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

const getReceivedQuantity = (item) =>
  toFiniteNumber(item.received_quantity ?? item.received_qty);

export default function MaterialTracking() {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchText, setSearchText] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [categories, setCategories] = useState([]);

  // Map backend status to frontend status
  const mapMaterialStatus = (material, purchaseItems) => {
    // Find related purchase order items
    const relatedItems = (purchaseItems || []).filter(
      (item) => item.material_code === material.material_code
    );

    if (relatedItems.length === 0) {
      return "not-arrived";
    }

    const totalQty = (relatedItems || []).reduce(
      (sum, item) => sum + toFiniteNumber(item.quantity),
      0
    );
    const receivedQty = (relatedItems || []).reduce(
      (sum, item) => sum + getReceivedQuantity(item),
      0
    );

    if (receivedQty === 0) {
      return "not-arrived";
    } else if (receivedQty < totalQty) {
      return "partial-arrived";
    } else {
      return "fully-arrived";
    }
  };

  // Load materials from API
  const loadMaterials = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load materials
      const materialsResponse = await materialApi.list({
        page: 1,
        page_size: 100,
        keyword: searchText || undefined,
        is_active: true
      });
      const materialsData =
      materialsResponse.data?.items || materialsResponse.data?.items || materialsResponse.data || [];

      // Load purchase order items to get arrival status
      const purchaseResponse = await purchaseApi.orders.list({
        page: 1,
        page_size: PURCHASE_ORDER_ITEM_LOOKUP_LIMIT
      });
      const purchaseOrders =
      purchaseResponse.data?.items || purchaseResponse.data?.items || purchaseResponse.data || [];

      // Get a bounded set of recent purchase order items. Loading every order
      // detail on page open can trip API rate limits in live smoke runs.
      const allPurchaseItems = [];
      for (const order of (purchaseOrders || []).slice(0, PURCHASE_ORDER_ITEM_LOOKUP_LIMIT)) {
        try {
          const itemsResponse = await purchaseApi.orders.getItems(order.id);
          const items = itemsResponse.data?.items || itemsResponse.data || [];
          allPurchaseItems.push(
            ...(items || []).map((item) => ({
              ...item,
              order_no: item.order_no || order.order_no || ""
            }))
          );
        } catch (_err) {
          // Arrival status is advisory; keep the page usable if one detail call fails.
        }
      }

      // Transform materials data
      const transformedMaterials = (materialsData || []).map((material) => {
        const status = mapMaterialStatus(material, allPurchaseItems);
        const relatedItems = (allPurchaseItems || []).filter(
          (item) => item.material_code === material.material_code
        );

        const totalQuantity = (relatedItems || []).reduce(
          (sum, item) => sum + toFiniteNumber(item.quantity),
          0
        );
        const arrivedQuantity = (relatedItems || []).reduce(
          (sum, item) => sum + getReceivedQuantity(item),
          0
        );
        const unitPrice = toFiniteNumber(material.last_price || material.standard_price);

        return {
          id: material.id?.toString(),
          code: material.material_code || "",
          name: material.material_name || "",
          category: material.category_name || "",
          supplier: "", // Will be filled from purchase order
          poNumber: relatedItems.length > 0 ? relatedItems[0].order_no : "",
          totalQuantity,
          arrivedQuantity,
          usedQuantity: 0, // Not available from current API
          remainingQuantity: arrivedQuantity,
          status,
          poDate: "",
          expectedDate: "",
          actualArrivalDate: "",
          location: "",
          batch: "",
          qualityStatus: "qualified",
          storageCondition: "normal",
          unitPrice,
          totalValue: totalQuantity * unitPrice,
          arrivedValue: arrivedQuantity * unitPrice,
          usedValue: 0,
          project: "",
          nextAction:
          status === "not-arrived" ?
          "等待到货" :
          status === "partial-arrived" ?
          "继续到货" :
          "按需领取",
          daysUntilExpiry: 365
        };
      });

      setMaterials(transformedMaterials);
    } catch (err) {
      console.error("Failed to load materials:", err);
      setError(err.response?.data?.detail || err.message || "加载物料列表失败");
      setMaterials([]); // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false);
    }
  }, [searchText]);

  // Load materials when component mounts or search changes
  useEffect(() => {
    loadMaterials();
  }, [loadMaterials]);

  // Load material categories
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const res = await materialApi.categories.list();
        setCategories(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load categories:", err);
      }
    };
    loadCategories();
  }, []);

  const filteredMaterials = useMemo(() => {
    return (materials || []).filter((m) => {
      const searchLower = (searchText || "").toLowerCase();
    const matchSearch =
      (m.name || "").toLowerCase().includes(searchLower) ||
      (m.code || "").toLowerCase().includes(searchLower) ||
      (m.supplier || "").toLowerCase().includes(searchLower);

      const matchStatus = filterStatus === "all" || m.status === filterStatus;

      return matchSearch && matchStatus;
    });
  }, [materials, searchText, filterStatus]);

  const stats = useMemo(() => {
    const total = materials?.length || 0;
    const fullArrived = (materials || []).filter((m) => m.status === "fully-arrived").length;
    const notArrived = (materials || []).filter((m) => m.status === "not-arrived").length;
    const totalValue = (materials || []).reduce((sum, m) => sum + toFiniteNumber(m.totalValue), 0);
    const arrivedValue = (materials || []).reduce((sum, m) => sum + toFiniteNumber(m.arrivedValue), 0);
    const usedValue = (materials || []).reduce((sum, m) => sum + toFiniteNumber(m.usedValue), 0);

    return {
      total,
      fullArrived,
      notArrived,
      totalValue,
      arrivedValue,
      usedValue,
      fullArrivedRate: total > 0 ? fullArrived / total * 100 : 0,
      arrivedValueRate: totalValue > 0 ? arrivedValue / totalValue * 100 : 0
    };
  }, [materials]);

  if (loading) {
    return (
      <div className="space-y-6 pb-8">
        <PageHeader
          title="物料跟踪"
          description="实时监控物料采购、到货和使用状态" />

        <div className="text-center py-16">
          <div className="text-slate-400">加载中...</div>
        </div>
      </div>);

  }

  if (error && materials?.length === 0) {
    return (
      <div className="space-y-6 pb-8">
        <PageHeader
          title="物料跟踪"
          description="实时监控物料采购、到货和使用状态" />

        <div className="text-center py-16">
          <div className="text-red-400">{error}</div>
        </div>
      </div>);

  }

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="物料跟踪"
        description="实时监控物料采购、到货和使用状态"
        action={{
          label: "新建物料",
          icon: Plus,
          onClick: () => {
            setShowCreateDialog(true);
          }
        }} />

      {error &&
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
      </div>
      }

      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">物料总数</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">
                {stats.total}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">全部到货</p>
              <p className="text-3xl font-bold text-emerald-400 mt-2">
                {stats.fullArrived}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {stats.fullArrivedRate.toFixed(0)}%
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">未到货</p>
              <p className="text-3xl font-bold text-red-400 mt-2">
                {stats.notArrived}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">合同金额</p>
              <p className="text-2xl font-bold text-amber-400 mt-2">
                {formatCurrency(stats.totalValue)}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">已到金额</p>
              <p className="text-2xl font-bold text-emerald-400 mt-2">
                {formatCurrency(stats.arrivedValue)}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {stats.arrivedValueRate.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder="搜索物料名、物料码、供应商..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10" />

            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterStatus === "all" ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterStatus("all")}>

                全部状态
              </Button>
              {Object.entries(statusConfig).map(([key, cfg]) =>
              <Button
                key={key}
                variant={filterStatus === key ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterStatus(key)}
                className={cn(filterStatus === key && cfg.color)}>

                  {cfg.label}
              </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Materials Grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4">

        <AnimatePresence>
          {filteredMaterials.length > 0 ?
          (filteredMaterials || []).map((material) =>
          <MaterialRow
            key={material.id}
            material={material}
            onView={(_m) => {

              // Handle view material if needed
            }} />
          ) :

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="py-12 text-center">

              <Package className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">没有符合条件的物料</p>
          </motion.div>
          }
        </AnimatePresence>
      </motion.div>

      {/* Alert Summary */}
      {(materials || []).some(
        (m) => m.status === "not-arrived" && m.daysUntilExpiry
      ) &&
      <Card className="bg-red-500/5 border-red-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5" />
              待处理提醒
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {materials.
            filter((m) => m.status === "not-arrived").
            map((m) =>
            <li
              key={m.id}
              className="text-sm text-slate-300 flex items-center gap-2">

                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    {m.name} - 预期到货: {formatDate(m.expectedDate)}
            </li>
            )}
            </ul>
          </CardContent>
      </Card>
      }

      {/* Create Material Dialog */}
      {showCreateDialog &&
      <CreateMaterialDialog
        categories={categories}
        onClose={() => setShowCreateDialog(false)}
        onSuccess={() => {
          setShowCreateDialog(false);
          loadMaterials();
          toast.success("物料创建成功");
        }} />

      }
    </div>);

}
