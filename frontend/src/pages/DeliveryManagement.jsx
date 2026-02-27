/**
 * Delivery Management (Refactored)
 * PMC发货管理页面 (重构版本)
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
'@/lib/constants/service';

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
      .catch(() => message.error('加载发货单详情失败'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />;
  if (!detail) return <Alert message="发货单不存在" type="warning" />;

  return (
    <Card
      title={`发货单详情 - ${detail.delivery_no || ''}`}
      extra={<Button onClick={onBack}>返回列表</Button>}
    >
      <Row gutter={[24, 16]}>
        <Col span={8}><Text type="secondary">发货单号</Text><br /><Text strong>{detail.delivery_no}</Text></Col>
        <Col span={8}><Text type="secondary">订单号</Text><br /><Text strong>{detail.order_no}</Text></Col>
        <Col span={8}><Text type="secondary">客户名称</Text><br /><Text strong>{detail.customer_name}</Text></Col>
        <Col span={8}><Text type="secondary">发货日期</Text><br /><Text>{detail.delivery_date || '-'}</Text></Col>
        <Col span={8}><Text type="secondary">发货类型</Text><br /><Text>{detail.delivery_type || '-'}</Text></Col>
        <Col span={8}><Text type="secondary">物流公司</Text><br /><Text>{detail.logistics_company || '-'}</Text></Col>
        <Col span={8}><Text type="secondary">物流单号</Text><br /><Text>{detail.tracking_no || '-'}</Text></Col>
        <Col span={8}><Text type="secondary">收货人</Text><br /><Text>{detail.receiver_name || '-'}</Text></Col>
        <Col span={8}><Text type="secondary">联系电话</Text><br /><Text>{detail.receiver_phone || '-'}</Text></Col>
        <Col span={24}><Text type="secondary">收货地址</Text><br /><Text>{detail.receiver_address || '-'}</Text></Col>
        <Col span={8}><Text type="secondary">发货金额</Text><br /><Text>{detail.delivery_amount ?? '-'}</Text></Col>
        <Col span={8}>
          <Text type="secondary">审批状态</Text><br />
          <Tag color={detail.approval_status === 'approved' ? 'green' : detail.approval_status === 'rejected' ? 'red' : 'orange'}>
            {detail.approval_status || '-'}
          </Tag>
        </Col>
        <Col span={8}>
          <Text type="secondary">发货状态</Text><br />
          <Tag color={detail.delivery_status === 'shipped' ? 'blue' : detail.delivery_status === 'received' ? 'green' : 'default'}>
            {detail.delivery_status || '-'}
          </Tag>
        </Col>
        <Col span={24}><Text type="secondary">备注</Text><br /><Text>{detail.remark || '-'}</Text></Col>
      </Row>
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
      .catch(() => message.error('加载发货单数据失败'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async () => {
    if (!formData.order_id) {
      message.warning('请填写销售订单ID');
      return;
    }
    setSubmitting(true);
    try {
      if (isEdit) {
        await businessSupportApi.deliveryOrders.update(id, formData);
        message.success('更新成功');
      } else {
        await businessSupportApi.deliveryOrders.create(formData);
        message.success('创建成功');
      }
      onBack();
    } catch (_err) {
      message.error(isEdit ? '更新失败' : '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  const updateField = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />;

  return (
    <Card
      title={isEdit ? '编辑发货单' : '新建发货单'}
      extra={<Space><Button onClick={onBack}>取消</Button><Button type="primary" loading={submitting} onClick={handleSubmit}>保存</Button></Space>}
    >
      <Row gutter={[24, 16]}>
        <Col span={8}>
          <Text type="secondary">销售订单ID *</Text>
          <Input value={formData.order_id} onChange={e => updateField('order_id', e.target.value)} placeholder="输入销售订单ID" />
        </Col>
        <Col span={8}>
          <Text type="secondary">发货日期</Text>
          <Input type="date" value={formData.delivery_date} onChange={e => updateField('delivery_date', e.target.value)} />
        </Col>
        <Col span={8}>
          <Text type="secondary">发货类型</Text>
          <Select value={formData.delivery_type || undefined} onChange={v => updateField('delivery_type', v)} placeholder="选择类型" style={{ width: '100%' }}>
            <Select.Option value="standard">标准发货</Select.Option>
            <Select.Option value="express">加急发货</Select.Option>
            <Select.Option value="freight">物流发货</Select.Option>
            <Select.Option value="self_pickup">自提</Select.Option>
          </Select>
        </Col>
        <Col span={8}>
          <Text type="secondary">物流公司</Text>
          <Input value={formData.logistics_company} onChange={e => updateField('logistics_company', e.target.value)} placeholder="物流公司名称" />
        </Col>
        <Col span={8}>
          <Text type="secondary">物流单号</Text>
          <Input value={formData.tracking_no} onChange={e => updateField('tracking_no', e.target.value)} placeholder="物流单号" />
        </Col>
        <Col span={8}>
          <Text type="secondary">发货金额</Text>
          <Input type="number" value={formData.delivery_amount} onChange={e => updateField('delivery_amount', e.target.value)} placeholder="金额" />
        </Col>
        <Col span={8}>
          <Text type="secondary">收货人</Text>
          <Input value={formData.receiver_name} onChange={e => updateField('receiver_name', e.target.value)} placeholder="收货人姓名" />
        </Col>
        <Col span={8}>
          <Text type="secondary">联系电话</Text>
          <Input value={formData.receiver_phone} onChange={e => updateField('receiver_phone', e.target.value)} placeholder="联系电话" />
        </Col>
        <Col span={24}>
          <Text type="secondary">收货地址</Text>
          <Input value={formData.receiver_address} onChange={e => updateField('receiver_address', e.target.value)} placeholder="收货地址" />
        </Col>
        <Col span={24}>
          <Text type="secondary">备注</Text>
          <Input.TextArea rows={3} value={formData.remark} onChange={e => updateField('remark', e.target.value)} placeholder="备注信息" />
        </Col>
      </Row>
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


  // 子视图渲染
  const handleBack = () => navigate('/pmc/delivery-orders');

  if (viewMode === 'detail') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: 24, background: '#f5f5f5', minHeight: '100vh' }}>
        <DeliveryDetail id={params.id} onBack={handleBack} />
      </motion.div>
    );
  }

  if (viewMode === 'edit') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: 24, background: '#f5f5f5', minHeight: '100vh' }}>
        <DeliveryForm id={params.id} onBack={handleBack} />
      </motion.div>
    );
  }

  if (viewMode === 'create') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: 24, background: '#f5f5f5', minHeight: '100vh' }}>
        <DeliveryForm onBack={handleBack} />
      </motion.div>
    );
  }

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
              onClick={() => navigate('/pmc/delivery-orders/new')}>

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
