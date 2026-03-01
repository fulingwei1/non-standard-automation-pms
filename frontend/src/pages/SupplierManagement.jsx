/**
 * Supplier Management Page - Complete supplier lifecycle management
 * Supplier evaluation, performance tracking, and relationship management
 */

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  Phone,
  Mail,
  MapPin,
  Star,
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  Plus,
  Eye,
  Edit,
  Award,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
  Users,
  FileText,
  Zap } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Label,
  Textarea } from
"../components/ui";
import { cn, formatCurrency, formatDate as _formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { supplierApi } from "../services/api";
import { toast } from "../components/ui/toast";

// Mock supplier data
// Mock data - 已移除，使用真实API
const levelConfig = {
  A级: {
    label: "A级",
    color: "bg-emerald-500/20 text-emerald-400",
    description: "优秀供应商"
  },
  B级: {
    label: "B级",
    color: "bg-amber-500/20 text-amber-400",
    description: "合格供应商"
  },
  C级: {
    label: "C级",
    color: "bg-orange-500/20 text-orange-400",
    description: "待改进"
  },
  D级: {
    label: "D级",
    color: "bg-red-500/20 text-red-400",
    description: "需淘汰"
  }
};

const statusConfig = {
  active: { label: "活跃", color: "bg-blue-500/20 text-blue-400" },
  inactive: { label: "停用", color: "bg-slate-500/20 text-slate-400" },
  review: { label: "评审中", color: "bg-amber-500/20 text-amber-400" }
};

const SupplierCard = ({ supplier, onView }) => {
  const levelCfg = levelConfig[supplier.level];
  const statusCfg = statusConfig[supplier.status];

  return (
    <motion.div
      variants={fadeIn}
      className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden hover:bg-slate-800/70 transition-all">

      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-semibold text-slate-100 text-lg">
              {supplier.name}
            </h3>
            <p className="text-sm text-slate-400 mt-1">{supplier.category}</p>
          </div>
          <div className="flex flex-col gap-1">
            <Badge className={cn("text-xs", levelCfg.color)}>
              <Award className="w-3 h-3 mr-1" />
              {levelCfg.label}
            </Badge>
            <Badge className={cn("text-xs", statusCfg.color)}>
              {statusCfg.label}
            </Badge>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Contact Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2 text-slate-300">
            <Users className="w-4 h-4 text-slate-500" />
            <span>{supplier.contactPerson}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Phone className="w-4 h-4 text-slate-500" />
            <span>{supplier.phone}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Mail className="w-4 h-4 text-slate-500" />
            <span className="truncate">{supplier.email}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <MapPin className="w-4 h-4 text-slate-500" />
            <span>{supplier.address}</span>
          </div>
        </div>

        {/* Rating Section */}
        <div className="border-t border-slate-700/50 pt-4">
          <div className="flex items-center justify-between mb-3">
            <p className="font-medium text-slate-100">综合评分</p>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) =>
              <Star
                key={i}
                className={cn(
                  "w-4 h-4",
                  i < Math.floor(supplier.overallRating) ?
                  "fill-amber-400 text-amber-400" :
                  "text-slate-600"
                )} />

              )}
              <span className="ml-2 text-sm font-semibold text-amber-400">
                {supplier.overallRating.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div>
              <p className="text-slate-500 mb-1">质量</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.quality * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.quality}
                </span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">交期</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.delivery * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.delivery}
                </span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">服务</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.service * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.service}
                </span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">价格</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.price * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.price}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm border-t border-slate-700/50 pt-4">
          <div>
            <p className="text-slate-500 text-xs mb-1">交期准时率</p>
            <p className="font-semibold text-slate-100 flex items-center gap-1">
              {supplier.onTimeDeliveryRate}%
              {supplier.onTimeDeliveryRate >= 95 ?
              <TrendingUp className="w-4 h-4 text-emerald-400" /> :

              <TrendingDown className="w-4 h-4 text-red-400" />
              }
            </p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">质量合格率</p>
            <p className="font-semibold text-slate-100">
              {supplier.qualityPassRate}%
            </p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">总订单</p>
            <p className="font-semibold text-slate-100">
              {supplier.completedOrders}/{supplier.totalOrders}
            </p>
          </div>
        </div>

        {/* Financial Info */}
        <div className="grid grid-cols-2 gap-3 text-sm border-t border-slate-700/50 pt-4">
          <div>
            <p className="text-slate-500 text-xs mb-1">年度采购额</p>
            <p className="font-semibold text-amber-400">
              {formatCurrency(supplier.annualSpend)}
            </p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">年增长率</p>
            <p
              className={cn(
                "font-semibold",
                supplier.growthRate > 0 ? "text-emerald-400" : "text-red-400"
              )}>

              {supplier.growthRate > 0 ? "+" : ""}
              {supplier.growthRate}%
            </p>
          </div>
        </div>

        {/* Issues or Risk Alert */}
        {(supplier.issues?.length > 0 || supplier.riskLevel !== "low") &&
        <div
          className={cn(
            "rounded-lg p-3 border text-sm",
            supplier.riskLevel === "high" ?
            "bg-red-500/10 border-red-500/30" :
            "bg-amber-500/10 border-amber-500/30"
          )}>

            {supplier.issues?.length > 0 &&
          <div>
                <p
              className={cn(
                "text-xs font-medium mb-2",
                supplier.riskLevel === "high" ?
                "text-red-400" :
                "text-amber-400"
              )}>

                  <AlertTriangle className="w-3 h-3 mr-1 inline" />
                  最近问题
                </p>
                <ul className="space-y-1 text-xs text-slate-300">
                  {supplier.issues.slice(0, 2).map((issue, idx) =>
              <li key={idx} className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                      {issue.issue}
              </li>
              )}
                </ul>
          </div>
          }
        </div>
        }

        {/* Action Bar */}
        <div className="flex gap-2 pt-2 border-t border-slate-700/50">
          <Button size="sm" className="flex-1" onClick={() => onView(supplier)}>
            <Eye className="w-4 h-4 mr-1" />
            查看详情
          </Button>
          <Button size="sm" variant="outline">
            <Edit className="w-4 h-4 mr-1" />
            编辑
          </Button>
        </div>
      </div>
    </motion.div>);

};

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
      toFixed(2)
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
          }
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

// Create Supplier Dialog Component
function CreateSupplierDialog({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    supplier_code: "",
    supplier_name: "",
    supplier_short_name: "",
    supplier_type: "",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    address: "",
    business_license: "",
    bank_name: "",
    bank_account: "",
    tax_number: "",
    payment_terms: "",
    remark: ""
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    // Validation
    const newErrors = {};
    if (!formData.supplier_code.trim()) {
      newErrors.supplier_code = "请输入供应商编码";
    }
    if (!formData.supplier_name.trim()) {
      newErrors.supplier_name = "请输入供应商名称";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setLoading(true);
      await supplierApi.create(formData);
      onSuccess();
    } catch (error) {
      console.error("Failed to create supplier:", error);
      toast.error(
        "创建失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle>新建供应商</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="required">
                供应商编码 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.supplier_code}
                onChange={(e) =>
                setFormData({ ...formData, supplier_code: e.target.value })
                }
                placeholder="请输入供应商编码"
                className={errors.supplier_code ? "border-red-400" : ""} />

              {errors.supplier_code &&
              <div className="text-sm text-red-400 mt-1">
                  {errors.supplier_code}
              </div>
              }
            </div>
            <div>
              <Label className="required">
                供应商名称 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.supplier_name}
                onChange={(e) =>
                setFormData({ ...formData, supplier_name: e.target.value })
                }
                placeholder="请输入供应商名称"
                className={errors.supplier_name ? "border-red-400" : ""} />

              {errors.supplier_name &&
              <div className="text-sm text-red-400 mt-1">
                  {errors.supplier_name}
              </div>
              }
            </div>
            <div>
              <Label>供应商简称</Label>
              <Input
                value={formData.supplier_short_name}
                onChange={(e) =>
                setFormData({
                  ...formData,
                  supplier_short_name: e.target.value
                })
                }
                placeholder="请输入供应商简称" />

            </div>
            <div>
              <Label>供应商类型</Label>
              <Input
                value={formData.supplier_type}
                onChange={(e) =>
                setFormData({ ...formData, supplier_type: e.target.value })
                }
                placeholder="如：电子元器件、机械件等" />

            </div>
            <div>
              <Label>联系人</Label>
              <Input
                value={formData.contact_person}
                onChange={(e) =>
                setFormData({ ...formData, contact_person: e.target.value })
                }
                placeholder="请输入联系人姓名" />

            </div>
            <div>
              <Label>联系电话</Label>
              <Input
                value={formData.contact_phone}
                onChange={(e) =>
                setFormData({ ...formData, contact_phone: e.target.value })
                }
                placeholder="请输入联系电话" />

            </div>
            <div>
              <Label>联系邮箱</Label>
              <Input
                type="email"
                value={formData.contact_email}
                onChange={(e) =>
                setFormData({ ...formData, contact_email: e.target.value })
                }
                placeholder="请输入联系邮箱" />

            </div>
            <div>
              <Label>地址</Label>
              <Input
                value={formData.address}
                onChange={(e) =>
                setFormData({ ...formData, address: e.target.value })
                }
                placeholder="请输入供应商地址" />

            </div>
            <div>
              <Label>营业执照号</Label>
              <Input
                value={formData.business_license}
                onChange={(e) =>
                setFormData({ ...formData, business_license: e.target.value })
                }
                placeholder="请输入营业执照号" />

            </div>
            <div>
              <Label>开户银行</Label>
              <Input
                value={formData.bank_name}
                onChange={(e) =>
                setFormData({ ...formData, bank_name: e.target.value })
                }
                placeholder="请输入开户银行" />

            </div>
            <div>
              <Label>银行账号</Label>
              <Input
                value={formData.bank_account}
                onChange={(e) =>
                setFormData({ ...formData, bank_account: e.target.value })
                }
                placeholder="请输入银行账号" />

            </div>
            <div>
              <Label>税号</Label>
              <Input
                value={formData.tax_number}
                onChange={(e) =>
                setFormData({ ...formData, tax_number: e.target.value })
                }
                placeholder="请输入税号" />

            </div>
            <div>
              <Label>付款条件</Label>
              <Input
                value={formData.payment_terms}
                onChange={(e) =>
                setFormData({ ...formData, payment_terms: e.target.value })
                }
                placeholder="如：2/10 N30" />

            </div>
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={formData.remark}
              onChange={(e) =>
              setFormData({ ...formData, remark: e.target.value })
              }
              placeholder="请输入备注信息"
              rows={3}
              className="bg-slate-800/50 border-slate-700" />

          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? "创建中..." : "创建供应商"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}