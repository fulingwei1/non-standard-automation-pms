/**
 * Delivery Management (Refactored)
 * PMC 发货管理页面 (重构版本) - shadcn/Tailwind Dark Theme
 */

import { useState, useEffect, useCallback as _useCallback, useMemo } from "react";
import { useSearchParams, useNavigate, useParams, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Truck,
  Calendar,
  Package,
  MapPin,
  Clock,
  CheckCircle2,
  AlertCircle,
  Search,
  Filter,
  Plus,
  Edit,
  Eye,
  FileText,
  TrendingUp,
  PackageCheck,
  PackageX,
  RefreshCw,
  Download,
  ChevronRight,
  X
} from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
  Progress,
  toast
} from "../components/ui";
// import { fadeIn, staggerContainer } from "../lib/animations";

import { businessSupportApi } from "../services/api";
import { getItemsCompat } from "../utils/apiResponse";

// 导入拆分后的组件
import {
  DeliveryOverview,
  DeliveryPlan,
  DeliveryTracking
} from '../components/delivery-management';

import {
  DELIVERY_STATUS,
  DELIVERY_PRIORITY,
  SHIPPING_METHODS,
  PACKAGE_TYPES
} from "@/lib/constants/service";

// TabPane removed - using items prop instead

const normalizeEnumValue = (value, fallbackMap = {}) => {
  if (!value) {return value;}
  const normalized = String(value)
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");
  return fallbackMap[normalized] || normalized;
};

const normalizeStatus = (value) =>
normalizeEnumValue(value, {
  intransit: "in_transit",
  in_transit: "in_transit",
  on_the_way: "in_transit",
  delivered: "delivered",
  shipped: "shipped",
  pending: "pending",
  preparing: "preparing",
  cancelled: "cancelled"
});

const normalizePriority = (value) =>
normalizeEnumValue(value, {
  urgent: "urgent",
  high: "high",
  normal: "normal",
  low: "low"
});

const normalizeMethod = (value) =>
normalizeEnumValue(value, {
  standard_delivery: "standard",
  express_delivery: "express",
  freight_delivery: "freight",
  selfpickup: "self_pickup",
  pickup: "self_pickup",
  self_pickup: "self_pickup"
});

const normalizePackageType = (value) =>
normalizeEnumValue(value, {
  standard_package: "standard",
  fragile_package: "fragile",
  liquid_package: "liquid",
  oversize_package: "oversize"
});

const normalizeDelivery = (item = {}) => {
  const orderNumber =
    item.orderNumber ||
    item.order_no ||
    item.order_number ||
    item.delivery_no ||
    item.deliveryNo ||
    item.delivery_code ||
    item.code;

  const customerName =
    item.customerName ||
    item.customer_name ||
    item.customer?.name ||
    item.customer ||
    item.recipient_name ||
    "";

  return {
    id: item.id || item.delivery_id || item.order_id || orderNumber,
    orderNumber: orderNumber || "",
    customerName,
    status: normalizeStatus(item.status || item.delivery_status),
    priority: normalizePriority(item.priority || item.delivery_priority),
    shippingMethod: normalizeMethod(
      item.shippingMethod || item.shipping_method || item.delivery_method
    ),
    packageType: normalizePackageType(item.packageType || item.package_type),
    scheduledDate:
      item.scheduledDate ||
      item.scheduled_date ||
      item.planned_delivery_time ||
      item.planned_delivery_date ||
      item.plan_delivery_date,
    actualDate:
      item.actualDate || item.actual_date || item.actual_delivery_time,
    trackingNumber:
      item.trackingNumber || item.tracking_no || item.tracking_number,
    deliveryAddress:
      item.deliveryAddress || item.delivery_address || item.recipient_address,
    itemCount: item.itemCount ?? item.item_count ?? item.total_items,
    totalWeight: item.totalWeight ?? item.total_weight ?? item.weight,
    notes: item.notes || item.remark || item.remarks,
    deliveryAmount:
      item.delivery_amount != null && item.delivery_amount !== ""
        ? Number(item.delivery_amount)
        : item.deliveryAmount != null
          ? Number(item.deliveryAmount)
          : 0,
    deliveryDate:
      item.delivery_date ||
      item.deliveryDate ||
      item.scheduled_date ||
      item.scheduledDate ||
      item.actual_date ||
      item.actualDate,
  };
};

// 发货单详情子视图
const DeliveryDetail = ({ id, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    businessSupportApi.deliveryOrders.get(id)
      .then(res => {
        const data = res?.data?.data || res?.data || {};
        setDetail(data);
      })
      .catch(() => toast({
        title: "错误",
        description: "加载发货单详情失败",
        variant: "destructive"
      }))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (!detail) {
    return (
      <Card className="bg-surface-100/50">
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-amber-400">
            <AlertCircle className="w-5 h-5" />
            <span>发货单不存在</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusColor = (status) => {
    if (status === 'approved') return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    if (status === 'rejected') return 'bg-red-500/20 text-red-400 border-red-500/30';
    return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
  };

  const getDeliveryStatusColor = (status) => {
    if (status === 'shipped') return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    if (status === 'received') return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <Card className="bg-surface-100/50">
      <CardHeader className="border-b border-white/10">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">
            发货单详情 - {detail.delivery_no || ''}
          </CardTitle>
          <Button variant="outline" onClick={onBack}>返回列表</Button>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货单号</p>
            <p className="text-white font-medium">{detail.delivery_no}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">订单号</p>
            <p className="text-white font-medium">{detail.order_no}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">客户名称</p>
            <p className="text-white font-medium">{detail.customer_name}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货日期</p>
            <p className="text-white">{detail.delivery_date || '-'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货类型</p>
            <p className="text-white">{detail.delivery_type || '-'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">物流公司</p>
            <p className="text-white">{detail.logistics_company || '-'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">物流单号</p>
            <p className="text-white">{detail.tracking_no || '-'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">收货人</p>
            <p className="text-white">{detail.receiver_name || '-'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">联系电话</p>
            <p className="text-white">{detail.receiver_phone || '-'}</p>
          </div>
          <div className="md:col-span-3 space-y-1">
            <p className="text-sm text-slate-400">收货地址</p>
            <p className="text-white">{detail.receiver_address || '-'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货金额</p>
            <p className="text-white">{detail.delivery_amount ?? '-'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">审批状态</p>
            <Badge variant="outline" className={getStatusColor(detail.approval_status)}>
              {detail.approval_status || '-'}
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货状态</p>
            <Badge variant="outline" className={getDeliveryStatusColor(detail.delivery_status)}>
              {detail.delivery_status || '-'}
            </Badge>
          </div>
          <div className="md:col-span-3 space-y-1">
            <p className="text-sm text-slate-400">备注</p>
            <p className="text-white">{detail.remark || '-'}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// 发货单编辑/新建表单
const DeliveryForm = ({ id, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    order_id: '',
    delivery_date: '',
    delivery_type: '',
    logistics_company: '',
    tracking_no: '',
    receiver_name: '',
    receiver_phone: '',
    receiver_address: '',
    delivery_amount: '',
    remark: '',
  });

  const isEdit = Boolean(id);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    businessSupportApi.deliveryOrders.get(id)
      .then(res => {
        const data = res?.data?.data || res?.data || {};
        setFormData({
          order_id: data.order_id || '',
          delivery_date: data.delivery_date || '',
          delivery_type: data.delivery_type || '',
          logistics_company: data.logistics_company || '',
          tracking_no: data.tracking_no || '',
          receiver_name: data.receiver_name || '',
          receiver_phone: data.receiver_phone || '',
          receiver_address: data.receiver_address || '',
          delivery_amount: data.delivery_amount || '',
          remark: data.remark || '',
        });
      })
      .catch(() => toast({
        title: "错误",
        description: "加载发货单数据失败",
        variant: "destructive"
      }))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async () => {
    if (!formData.order_id) {
      toast({
        title: "警告",
        description: "请填写销售订单 ID",
        variant: "destructive"
      });
      return;
    }
    setSubmitting(true);
    try {
      if (isEdit) {
        await businessSupportApi.deliveryOrders.update(id, formData);
        toast({
          title: "成功",
          description: "更新成功"
        });
      } else {
        await businessSupportApi.deliveryOrders.create(formData);
        toast({
          title: "成功",
          description: "创建成功"
        });
      }
      onBack();
    } catch (_err) {
      toast({
        title: "错误",
        description: isEdit ? '更新失败' : '创建失败',
        variant: "destructive"
      });
    } finally {
      setSubmitting(false);
    }
  };

  const updateField = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <Card className="bg-surface-100/50">
      <CardHeader className="border-b border-white/10">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">
            {isEdit ? '编辑发货单' : '新建发货单'}
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onBack}>取消</Button>
            <Button onClick={handleSubmit} disabled={submitting}>保存</Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">销售订单 ID *</label>
            <Input 
              value={formData.order_id} 
              onChange={e => updateField('order_id', e.target.value)} 
              placeholder="输入销售订单 ID" 
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">发货日期</label>
            <Input 
              type="date" 
              value={formData.delivery_date} 
              onChange={e => updateField('delivery_date', e.target.value)}
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">发货类型</label>
            <Select value={formData.delivery_type} onValueChange={v => updateField('delivery_type', v)}>
              <SelectTrigger className="bg-surface-100 border-white/10">
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="standard">标准发货</SelectItem>
                <SelectItem value="express">加急发货</SelectItem>
                <SelectItem value="freight">物流发货</SelectItem>
                <SelectItem value="self_pickup">自提</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">物流公司</label>
            <Input 
              value={formData.logistics_company} 
              onChange={e => updateField('logistics_company', e.target.value)} 
              placeholder="物流公司名称"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">物流单号</label>
            <Input 
              value={formData.tracking_no} 
              onChange={e => updateField('tracking_no', e.target.value)} 
              placeholder="物流单号"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">发货金额</label>
            <Input 
              type="number" 
              value={formData.delivery_amount} 
              onChange={e => updateField('delivery_amount', e.target.value)} 
              placeholder="金额"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">收货人</label>
            <Input 
              value={formData.receiver_name} 
              onChange={e => updateField('receiver_name', e.target.value)} 
              placeholder="收货人姓名"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">联系电话</label>
            <Input 
              value={formData.receiver_phone} 
              onChange={e => updateField('receiver_phone', e.target.value)} 
              placeholder="联系电话"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="md:col-span-3 space-y-2">
            <label className="text-sm text-slate-400">收货地址</label>
            <Input 
              value={formData.receiver_address} 
              onChange={e => updateField('receiver_address', e.target.value)} 
              placeholder="收货地址"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="md:col-span-3 space-y-2">
            <label className="text-sm text-slate-400">备注</label>
            <textarea
              rows={3}
              value={formData.remark}
              onChange={e => updateField('remark', e.target.value)}
              placeholder="备注信息"
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const DeliveryManagement = () => {
  const [_searchParams] = useSearchParams();
  const navigate = useNavigate();
  const params = useParams();
  const location = useLocation();

  // 判断当前视图模式
  const getViewMode = () => {
    const path = location.pathname;
    if (path.endsWith('/new')) return 'create';
    if (path.endsWith('/edit')) return 'edit';
    if (params.id && !path.endsWith('/edit')) return 'detail';
    return 'list';
  };
  const viewMode = getViewMode();

  // 状态管理
  const [loading, setLoading] = useState(false);
  const [deliveries, setDeliveries] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchText, setSearchText] = useState('');
  const [_filters, _setFilters] = useState({});

  // 数据加载
  useEffect(() => {
    if (viewMode === 'list') loadData();
  }, [activeTab, viewMode]);

  const loadData = async () => {
     setLoading(true);
    try {
      const response = await businessSupportApi.deliveryOrders.list({
        page: 1,
        page_size: 200
      });
      const items = getItemsCompat(response);
      setDeliveries(Array.isArray(items) ? items.map(normalizeDelivery) : []);
    } catch (_error) {
      toast({
        title: "错误",
        description: "加载交付数据失败",
        variant: "destructive"
      });
      setDeliveries([]);
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredDeliveries = useMemo(() => {
    return (deliveries || []).filter((delivery) => {
      const searchLower = (searchText || "").toLowerCase();
      const matchesSearch = !searchText ||
        (delivery.orderNumber || "").toLowerCase().includes(searchLower) ||
        (delivery.customerName || "").toLowerCase().includes(searchLower);

      return matchesSearch;
    });
  }, [deliveries, searchText]);



  // 子视图渲染
  const handleBack = () => navigate('/pmc/delivery-orders');

  if (viewMode === 'detail') {
    return (
      <motion.div 
        initial={{ opacity: 0 }} 
        animate={{ opacity: 1 }} 
        className="p-6 bg-slate-900 min-h-screen"
      >
        <DeliveryDetail id={params.id} onBack={handleBack} />
      </motion.div>
    );
  }

  if (viewMode === 'edit') {
    return (
      <motion.div 
        initial={{ opacity: 0 }} 
        animate={{ opacity: 1 }} 
        className="p-6 bg-slate-900 min-h-screen"
      >
        <DeliveryForm id={params.id} onBack={handleBack} />
      </motion.div>
    );
  }

  if (viewMode === 'create') {
    return (
      <motion.div 
        initial={{ opacity: 0 }} 
        animate={{ opacity: 1 }} 
        className="p-6 bg-slate-900 min-h-screen"
      >
        <DeliveryForm onBack={handleBack} />
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="delivery-management-container p-6 bg-slate-900 min-h-screen"
    >
      {/* 页面头部 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-1">
              <Truck className="w-6 h-6" />
              发货管理
            </h1>
            <p className="text-slate-400">
              PMC 发货管理 - 发货计划、订单列表、在途跟踪
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              className="flex items-center gap-2"
              onClick={() => navigate('/pmc/delivery-orders/new')}
            >
              <Plus size={16} />
              创建发货单
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={loadData}
            >
              <RefreshCw size={16} />
              刷新
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
            >
              <Download size={16} />
              导出报表
            </Button>
          </div>
        </div>
      </div>

      {/* 搜索栏 */}
      <Card className="mb-4 bg-surface-100/50">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索订单号、客户名称..."
              value={searchText || "unknown"}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10 bg-surface-100 border-white/10 max-w-md"
            />
          </div>
        </CardContent>
      </Card>

      {/* 主要内容区域 */}
      <Card className="bg-surface-100/50">
        <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-surface-100">
            <TabsTrigger value="overview" className="data-[state=active]:bg-primary data-[state=active]:text-white">
              <PackageCheck size={16} className="mr-2" />
              交付概览
            </TabsTrigger>
            <TabsTrigger value="plan" className="data-[state=active]:bg-primary data-[state=active]:text-white">
              <Calendar size={16} className="mr-2" />
              交付计划
            </TabsTrigger>
            <TabsTrigger value="tracking" className="data-[state=active]:bg-primary data-[state=active]:text-white">
              <Truck size={16} className="mr-2" />
              物流跟踪
            </TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="mt-4">
            <DeliveryOverview data={deliveries} loading={loading} />
          </TabsContent>
          <TabsContent value="plan" className="mt-4">
            <DeliveryPlan deliveries={filteredDeliveries} loading={loading} />
          </TabsContent>
          <TabsContent value="tracking" className="mt-4">
            <DeliveryTracking deliveries={filteredDeliveries} loading={loading} />
          </TabsContent>
        </Tabs>
      </Card>
    </motion.div>
  );
};

export default DeliveryManagement;
