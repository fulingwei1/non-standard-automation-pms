/**
 * Supplier Management Page - Complete supplier lifecycle management
 * Supplier evaluation, performance tracking, and relationship management
 */

import { useState, useMemo, useEffect } from "react";
import {
  Plus,
} from "lucide-react";


import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { supplierApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

import { levelConfig } from "./pageConstants";

export default function SupplierManagement() {
  const [suppliers, setSuppliers] = useState([]);
  const [searchText, setSearchText] = useState("");
  const [filterLevel, setFilterLevel] = useState("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [_loading, setLoading] = useState(true);
  const [_error, setError] = useState(null);

  // Load suppliers from API
  useEffect(() => {
    const fetchSuppliers = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await supplierApi.list();
        const data = response.data?.items || response.data?.items || response.data || [];
        setSuppliers(Array.isArray(data) ? data : []);
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
    return (suppliers || []).filter((s) => {
      const searchLower = searchText.toLowerCase();
      const matchSearch =
      (s.name || "").toLowerCase().includes(searchLower) ||
      (s.category || "").toLowerCase().includes(searchLower) ||
      (s.contactPerson || "").toLowerCase().includes(searchLower);

      const matchLevel = filterLevel === "all" || s.level === filterLevel;

      return matchSearch && matchLevel;
    });
  }, [suppliers, searchText, filterLevel]);

  const stats = useMemo(() => {
    return {
      total: suppliers.length,
      aGrade: (suppliers || []).filter((s) => s.level === "A级").length,
      bGrade: (suppliers || []).filter((s) => s.level === "B级").length,
      active: (suppliers || []).filter((s) => s.status === "active").length,
      avgRating: (
      (suppliers || []).reduce((sum, s) => sum + s.overallRating, 0) /
      suppliers.length).
      toFixed(2),
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
        }} />


      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">供应商总数</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">
                {stats.total}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">A级供应商</p>
              <p className="text-3xl font-bold text-emerald-400 mt-2">
                {stats.aGrade}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">B级供应商</p>
              <p className="text-3xl font-bold text-amber-400 mt-2">
                {stats.bGrade}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">活跃供应商</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">
                {stats.active}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">平均评分</p>
              <div className="flex items-center gap-1 mt-2">
                <p className="text-3xl font-bold text-amber-400">
                  {stats.avgRating}
                </p>
                <Star className="w-6 h-6 fill-amber-400 text-amber-400" />
              </div>
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
                placeholder="搜索供应商名称、分类、联系人..."
                value={searchText || "unknown"}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10" />

            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterLevel === "all" ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterLevel("all")}>

                全部等级
              </Button>
              {Object.entries(levelConfig).map(([key, cfg]) =>
              <Button
                key={key}
                variant={filterLevel === key ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilterLevel(key)}
                className={cn(filterLevel === key && cfg.color)}>

                  {cfg.label}
              </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Suppliers Grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 gap-4">

        <AnimatePresence>
          {filteredSuppliers.length > 0 ?
          (filteredSuppliers || []).map((supplier) =>
          <SupplierCard
            key={supplier.id}
            supplier={supplier}
            onView={(_s) => {

              // Handle view supplier if needed
            }} />
          ) :

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="col-span-full py-12 text-center">

              <Building2 className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">没有符合条件的供应商</p>
          </motion.div>
          }
        </AnimatePresence>
      </motion.div>

      {/* Supplier Risk Summary */}
      {(suppliers || []).some((s) => s.riskLevel !== "low") &&
      <Card className="bg-amber-500/5 border-amber-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
              风险供应商预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {suppliers.
            filter((s) => s.riskLevel === "high").
            map((s) =>
            <div
              key={s.id}
              className="flex items-start gap-3 p-3 rounded-lg bg-red-500/5 border border-red-500/20">

                    <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-100 text-sm">
                        {s.name}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {s.issues?.length > 0 ?
                  `${s.issues[0].issue}` :
                  "存在多项问题需要关注"}
                      </p>
                    </div>
            </div>
            )}
            </div>
          </CardContent>
      </Card>
      }

      {/* Create Supplier Dialog */}
      {showCreateDialog &&
      <CreateSupplierDialog
        onClose={() => setShowCreateDialog(false)}
        onSuccess={() => {
          setShowCreateDialog(false);
          // Reload suppliers if needed
          // loadSuppliers()
          toast.success("供应商创建成功");
        }} />

      }
    </div>);

}
