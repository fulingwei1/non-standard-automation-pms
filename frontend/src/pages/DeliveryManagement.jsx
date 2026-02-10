/**
 * Delivery Management (Refactored)
 * PMC发货管理页面 (重构版本)
 */

import { useState, useEffect, useCallback as _useCallback, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
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
  Download } from
"lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
  Typography,
  Alert,
  Spin,
  Tabs,
  Progress,
  Badge,
  message } from
"antd";

import { businessSupportApi } from "../services/api";
import { getItemsCompat } from "../utils/apiResponse";

// 导入拆分后的组件
import {
  DeliveryOverview,
  DeliveryPlan,
  DeliveryTracking } from
'../components/delivery-management';

import {
  DELIVERY_STATUS,
  DELIVERY_PRIORITY,
  SHIPPING_METHODS,
  PACKAGE_TYPES } from
'../components/delivery-management/deliveryManagementConstants';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

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
    notes: item.notes || item.remark || item.remarks
  };
};

const DeliveryManagement = () => {
  const [_searchParams] = useSearchParams();
  const navigate = useNavigate();

  // 状态管理
  const [loading, setLoading] = useState(false);
  const [deliveries, setDeliveries] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchText, setSearchText] = useState('');
  const [_filters, _setFilters] = useState({});

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab]);

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
      message.error('加载交付数据失败');
      setDeliveries([]);
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredDeliveries = useMemo(() => {
    return deliveries.filter((delivery) => {
      const searchLower = (searchText || "").toLowerCase();
    const matchesSearch = !searchText ||
      (delivery.orderNumber || "").toLowerCase().includes(searchLower) ||
      (delivery.customerName || "").toLowerCase().includes(searchLower);

      return matchesSearch;
    });
  }, [deliveries, searchText]);

  const tabItems = [
  {
    key: 'overview',
    tab:
    <span>
          <PackageCheck size={16} />
          交付概览
    </span>,

     content: <DeliveryOverview data={deliveries} loading={loading} />
  },
  {
    key: 'plan',
    tab:
    <span>
          <Calendar size={16} />
          交付计划 ({filteredDeliveries.filter((d) => d.status === 'pending' || d.status === 'preparing').length})
    </span>,

    content: <DeliveryPlan deliveries={filteredDeliveries} loading={loading} />
  },
  {
    key: 'tracking',
    tab:
    <span>
          <Truck size={16} />
          物流跟踪 ({filteredDeliveries.filter((d) => d.status === 'shipped' || d.status === 'in_transit').length})
    </span>,

    content: <DeliveryTracking deliveries={filteredDeliveries} loading={loading} />
  }];


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="delivery-management-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <Truck className="inline-block mr-2" />
              交付管理
            </Title>
            <Text type="secondary">
              PMC发货管理 - 发货计划、订单列表、在途跟踪
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<Plus size={16} />}
              onClick={() => navigate('/deliveries/create')}>

              创建发货单
            </Button>
            <Button
              icon={<RefreshCw size={16} />}
              onClick={loadData}>

              刷新
            </Button>
            <Button
              icon={<Download size={16} />}>

              导出报表
            </Button>
          </Space>
        </div>
      </div>

      {/* 搜索栏 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Input
              placeholder="搜索订单号、客户名称..."
              prefix={<Search size={16} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear />

          </Col>
        </Row>
      </Card>

      {/* 主要内容区域 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          size="large">

          {tabItems.map((item) =>
          <TabPane key={item.key} tab={item.tab}>
              {item.content}
          </TabPane>
          )}
        </Tabs>
      </Card>
    </motion.div>);

};

export default DeliveryManagement;
