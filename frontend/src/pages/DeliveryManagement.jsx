/**
 * Delivery Management (Refactored)
 * PMC发货管理页面 (重构版本)
 */

import { useState, useEffect, useCallback, useMemo } from "react";
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
  Download
} from "lucide-react";

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
  message
} from "antd";

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
} from '../components/delivery-management/deliveryManagementConstants';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

const DeliveryManagement = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [deliveries, setDeliveries] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({});

  // 模拟数据
  const mockData = {
    deliveries: [
      {
        id: 1,
        orderNumber: 'ORD202401001',
        customerName: '智能制造科技有限公司',
        deliveryAddress: '北京市海淀区中关村科技园',
        status: 'preparing',
        priority: 'high',
        shippingMethod: 'express',
        packageType: 'standard',
        scheduledDate: '2024-01-20',
        actualDate: null,
        trackingNumber: null,
        totalWeight: 150,
        totalVolume: 2.5,
        itemCount: 5,
        createdDate: '2024-01-18',
        notes: '包含易碎品，需要小心搬运'
      },
      // 更多模拟数据...
    ]
  };

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      setTimeout(() => {
        setDeliveries(mockData.deliveries);
        setLoading(false);
      }, 1000);
    } catch (error) {
      message.error('加载交付数据失败');
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredDeliveries = useMemo(() => {
    return deliveries.filter(delivery => {
      const matchesSearch = !searchText || 
        delivery.orderNumber.toLowerCase().includes(searchText.toLowerCase()) ||
        delivery.customerName?.toLowerCase().includes(searchText.toLowerCase());
      
      return matchesSearch;
    });
  }, [deliveries, searchText]);

  const tabItems = [
    {
      key: 'overview',
      tab: (
        <span>
          <PackageCheck size={16} />
          交付概览
        </span>
      ),
      content: <DeliveryOverview data={mockData} loading={loading} />
    },
    {
      key: 'plan',
      tab: (
        <span>
          <Calendar size={16} />
          交付计划 ({filteredDeliveries.filter(d => d.status === 'pending' || d.status === 'preparing').length})
        </span>
      ),
      content: <DeliveryPlan deliveries={filteredDeliveries} loading={loading} />
    },
    {
      key: 'tracking',
      tab: (
        <span>
          <Truck size={16} />
          物流跟踪 ({filteredDeliveries.filter(d => d.status === 'shipped' || d.status === 'in_transit').length})
        </span>
      ),
      content: <DeliveryTracking deliveries={filteredDeliveries} loading={loading} />
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="delivery-management-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}
    >
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
              onClick={() => navigate('/deliveries/create')}
            >
              创建发货单
            </Button>
            <Button 
              icon={<RefreshCw size={16} />}
              onClick={loadData}
            >
              刷新
            </Button>
            <Button 
              icon={<Download size={16} />}
            >
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
              allowClear
            />
          </Col>
        </Row>
      </Card>

      {/* 主要内容区域 */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          type="card"
          size="large"
        >
          {tabItems.map(item => (
            <TabPane key={item.key} tab={item.tab}>
              {item.content}
            </TabPane>
          ))}
        </Tabs>
      </Card>
    </motion.div>
  );
};

export default DeliveryManagement;
