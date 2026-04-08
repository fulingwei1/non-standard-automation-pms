/**
 * Supplier Management Page - Complete supplier lifecycle management
 * Supplier evaluation, performance tracking, and relationship management
 */

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  Star,
  Search,
  Plus,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { supplierApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

import { levelConfig } from "./pageConstants";
import SupplierCard from "./SupplierCard";
import CreateSupplierDialog from "./CreateSupplierDialog";

const toNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const normalizeSupplier = (supplier = {}) => {
  const performance = supplier.performance || supplier.ratingDetails || {};
  const rawLevel = supplier.level || (supplier.rating ? `${supplier.rating}级` : "B级");
  const level = levelConfig[rawLevel] ? rawLevel : "B级";
  const purchaseOrders = Array.isArray(supplier.purchaseOrders)
    ? supplier.purchaseOrders
    : [];

  return {
    ...supplier,
    code: supplier.code || supplier.supplierCode || "",
    level,
    contactPerson: supplier.contactPerson || supplier.contact || "",
    overallRating: toNumber(
      supplier.overallRating ?? performance.overall ?? performance.score,
      0
    ),
    ratingDetails: {
      quality: toNumber(performance.quality, 0),
      delivery: toNumber(performance.delivery, 0),
      service: toNumber(performance.service, 0),
      price: toNumber(
        performance.price ?? performance.cost ?? performance.overall,
        0
      ),
    },
    onTimeDeliveryRate: toNumber(
      supplier.onTimeDeliveryRate ?? performance.delivery,
      0
    ),
    qualityPassRate: toNumber(
      supplier.qualityPassRate ?? performance.quality,
      0
    ),
    completedOrders: toNumber(
      supplier.completedOrders ??
        purchaseOrders.filter((order) => order.status === "completed").length,
      0
    ),
    totalOrders: toNumber(supplier.totalOrders ?? purchaseOrders.length, 0),
    annualSpend: toNumber(
      supplier.annualSpend ??
        purchaseOrders.reduce(
          (sum, order) => sum + toNumber(order.amount ?? order.totalAmount, 0),
          0
        ),
      0
    ),
    growthRate: toNumber(supplier.growthRate, 0),
    riskLevel: supplier.riskLevel || "low",
    issues: Array.isArray(supplier.issues) ? supplier.issues : [],
    certifications: Array.isArray(supplier.certifications)
      ? supplier.certifications
      : [],
    purchaseOrders,
  };
};

export default function SupplierManagement() {
  const [suppliers, setSuppliers] = useState([]);
  const [searchText, setSearchText] = useState("");
  const [filterLevel, setFilterLevel] = useState("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSuppliers = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await supplierApi.list();
        const items = response?.data?.items ?? response?.data ?? response ?? [];
        const normalized = Array.isArray(items)
          ? items.map((item) => normalizeSupplier(item))
          : [];
        setSuppliers(normalized);
      } catch (err) {
        console.error("Failed to load suppliers:", err);
        setError("加载供应商数据失败");
        setSuppliers([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSuppliers();
  }, []);

  const filteredSuppliers = useMemo(() => {
    const searchLower = searchText.trim().toLowerCase();

    return (suppliers || []).filter((supplier) => {
      const matchSearch =
        !searchLower ||
        (supplier.name || "").toLowerCase().includes(searchLower) ||
        (supplier.code || "").toLowerCase().includes(searchLower) ||
        (supplier.category || "").toLowerCase().includes(searchLower) ||
        (supplier.contactPerson || "").toLowerCase().includes(searchLower);

      const matchLevel = filterLevel === "all" || supplier.level === filterLevel;

      return matchSearch && matchLevel;
    });
  }, [suppliers, searchText, filterLevel]);

  const stats = useMemo(() => {
    const total = suppliers.length;
    const average =
      total > 0
        ? suppliers.reduce((sum, supplier) => sum + supplier.overallRating, 0) / total
        : 0;

    return {
      total,
      aGrade: suppliers.filter((supplier) => supplier.level === "A级").length,
      bGrade: suppliers.filter((supplier) => supplier.level === "B级").length,
      active: suppliers.filter((supplier) => supplier.status === "active").length,
      avgRating: average.toFixed(2),
    };
  }, [suppliers]);

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="供应商管理"
        description="供应商评估、性能跟踪和关系管理"
        action={{
          label: "新增供应商",
          icon: Plus,
          onClick: () => {
            setShowCreateDialog(true);
          },
        }}
      />

      {error && (
        <Card className="border-red-500/30 bg-red-500/10">
          <CardContent className="pt-6 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      {loading && (
        <Card>
          <CardContent className="pt-6 text-sm text-slate-400">加载中...</CardContent>
        </Card>
      )}

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5"
      >
        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">供应商总数</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">{stats.total}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">A级供应商</p>
              <p className="text-3xl font-bold text-emerald-400 mt-2">{stats.aGrade}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">B级供应商</p>
              <p className="text-3xl font-bold text-amber-400 mt-2">{stats.bGrade}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">活跃供应商</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">{stats.active}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">平均评分</p>
              <div className="flex items-center gap-1 mt-2">
                <p className="text-3xl font-bold text-amber-400">{stats.avgRating}</p>
                <Star className="w-6 h-6 fill-amber-400 text-amber-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder="搜索供应商名称、分类、联系人..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterLevel === "all" ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterLevel("all")}
              >
                全部等级
              </Button>
              {Object.entries(levelConfig).map(([key, cfg]) => (
                <Button
                  key={key}
                  variant={filterLevel === key ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setFilterLevel(key)}
                  className={cn(filterLevel === key && cfg.color)}
                >
                  {cfg.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        <AnimatePresence>
          {filteredSuppliers.length > 0 ? (
            filteredSuppliers.map((supplier) => (
              <SupplierCard
                key={supplier.id}
                supplier={supplier}
                onView={() => {
                  // Handle view supplier if needed
                }}
              />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="col-span-full py-12 text-center"
            >
              <Building2 className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">没有符合条件的供应商</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {(suppliers || []).some((supplier) => supplier.riskLevel !== "low") && (
        <Card className="bg-amber-500/5 border-amber-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
              风险供应商预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {suppliers
                .filter((supplier) => supplier.riskLevel === "high")
                .map((supplier) => (
                  <div
                    key={supplier.id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-red-500/5 border border-red-500/20"
                  >
                    <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-100 text-sm">{supplier.name}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        {supplier.issues?.length > 0
                          ? `${supplier.issues[0].issue}`
                          : "存在多项问题需要关注"}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {showCreateDialog && (
        <CreateSupplierDialog
          onClose={() => setShowCreateDialog(false)}
          onSuccess={() => {
            setShowCreateDialog(false);
            toast.success("供应商创建成功");
          }}
        />
      )}
    </div>
  );
}
