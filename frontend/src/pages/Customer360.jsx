/**
 * Customer 360 View (Refactored)
 * 客户360度视图 - 展示客户的全面信息 (重构版本)
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Building2,
  FileText,
  DollarSign,
  Receipt,
  Package,
  CheckCircle2,
  Star,
  MessageSquare,
  TrendingUp,
  Calendar,
  User,
  Phone,
  Mail,
  MapPin,
  BarChart3,
  Target,
  Award,
  Activity,
  RefreshCw,
  Download,
  Edit,
  Plus } from
"lucide-react";

import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
  Typography,
  Alert,
  Spin,
  DatePicker,
  Select,
  Input,
  message,
  Badge } from
"antd";

// 导入拆分后的组件
import {
  CustomerBasicInfo,
  CustomerOrderHistory,
  CustomerQuoteHistory,
  CustomerContractHistory,
  CustomerPaymentRecords,
  CustomerProjectDelivery,
  CustomerSatisfaction,
  CustomerServiceRecords,
  CustomerAnalytics } from
'../components/customer-360';

import {
  CUSTOMER_TYPES,
  CUSTOMER_STATUS,
  CUSTOMER_LEVELS,
  ORDER_STATUS,
  PAYMENT_STATUS,
  PROJECT_PHASES,
  BUSINESS_METRICS,
  TABLE_CONFIG,
  CHART_COLORS } from
'@/lib/constants/customer360';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

const Customer360 = () => {
  const { customerId } = useParams();
  const navigate = useNavigate();

  // 状态管理
  const [loading, setLoading] = useState(false);
  const [customer, setCustomer] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [_dateRange, _setDateRange] = useState(null);

  // 模拟数据
  const mockCustomerData = {
    id: customerId,
    name: '智能制造科技有限公司',
    type: 'enterprise',
    status: 'active',
    level: 'gold',
    contactPerson: '张总',
    phone: '13800138000',
    email: 'zhang@smarttech.com',
    address: '北京市海淀区中关村科技园A座1201室',
    industry: '智能制造',
    sinceDate: '2022-03-15',
    serviceLevel: 'premium',
    satisfactionScore: 4.6,
    lifetimeValue: 2500000,
    orderCount: 15,
    avgOrderValue: 166667,
    projectSuccessRate: 93,
    growthTrend: 65,
    loyaltyIndex: 78,
    notes: '重点客户，合作稳定，有较大增长潜力，建议加强服务和关系维护',

    // 历史订单
    orders: [
    {
      id: 'ORD202401001',
      date: '2024-01-15',
      product: '智能生产线解决方案',
      amount: 500000,
      status: 'delivered',
      deliveryDate: '2024-01-20'
    }
    // 更多订单数据...
    ],

    // 历史报价
    quotes: [
    {
      id: 'Q202401001',
      date: '2024-01-10',
      title: '自动化改造项目',
      amount: 300000,
      status: 'accepted',
      validUntil: '2024-02-10'
    }
    // 更多报价数据...
    ],

    // 历史合同
    contracts: [
    {
      id: 'CT202401001',
      title: '年度服务协议',
      type: 'service',
      amount: 800000,
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      status: 'active'
    }
    // 更多合同数据...
    ],

    // 支付记录
    payments: [
    {
      id: 'PAY202401001',
      date: '2024-01-18',
      amount: 150000,
      method: 'bank_transfer',
      status: 'paid',
      orderId: 'ORD202401001'
    }
    // 更多支付数据...
    ],

    // 项目交付
    projects: [
    {
      id: 'PRJ202401001',
      name: '车间自动化改造',
      phase: 'deployment',
      startDate: '2024-01-05',
      expectedDate: '2024-02-15',
      progress: 85,
      satisfaction: null
    }
    // 更多项目数据...
    ],

    // 满意度调查
    satisfactions: [
    {
      id: 'SAT202401001',
      date: '2024-01-16',
      type: 'project_completion',
      score: 4.8,
      feedback: '项目实施专业，团队服务态度好，效果超出预期',
      improvements: '希望加强后续技术支持响应速度'
    }
    // 更多满意度数据...
    ],

    // 服务记录
    services: [
    {
      id: 'SRV202401001',
      date: '2024-01-14',
      type: 'technical_support',
      issue: '设备故障排查',
      resolution: '远程协助解决软件配置问题',
      satisfaction: 4.5,
      responseTime: 2.5
    }
    // 更多服务数据...
    ]
  };

  // 数据加载
  useEffect(() => {
    loadCustomerData();
  }, [customerId]);

  const loadCustomerData = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      setTimeout(() => {
        setCustomer(mockCustomerData);
        setLoading(false);
      }, 1000);
    } catch (_error) {
      message.error('加载客户数据失败');
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/customers');
  };

  const handleRefresh = () => {
    loadCustomerData();
  };

  const _handleExport = (format) => {
    message.success(`正在导出${format}格式客户报告...`);
  };

  const handleCreateQuote = () => {
    navigate(`/quotes/create?customerId=${customerId}`);
  };

  const handleCreateOrder = () => {
    navigate(`/orders/create?customerId=${customerId}`);
  };

  const tabItems = [
  {
    key: 'overview',
    tab:
    <span>
          <BarChart3 size={16} />
          基本信息
    </span>,

    content: <CustomerBasicInfo customer={customer} loading={loading} />
  },
  {
    key: 'orders',
    tab:
    <span>
          <Package size={16} />
          订单历史 ({customer?.orders?.length || 0})
    </span>,

    content: <CustomerOrderHistory orders={customer?.orders || []} loading={loading} />
  },
  {
    key: 'quotes',
    tab:
    <span>
          <FileText size={16} />
          报价历史 ({customer?.quotes?.length || 0})
    </span>,

    content: <CustomerQuoteHistory quotes={customer?.quotes || []} loading={loading} />
  },
  {
    key: 'contracts',
    tab:
    <span>
          <Receipt size={16} />
          合同管理 ({customer?.contracts?.length || 0})
    </span>,

    content: <CustomerContractHistory contracts={customer?.contracts || []} loading={loading} />
  },
  {
    key: 'payments',
    tab:
    <span>
          <DollarSign size={16} />
          支付记录 ({customer?.payments?.length || 0})
    </span>,

    content: <CustomerPaymentRecords payments={customer?.payments || []} loading={loading} />
  },
  {
    key: 'projects',
    tab:
    <span>
          <Target size={16} />
          项目交付 ({customer?.projects?.length || 0})
    </span>,

    content: <CustomerProjectDelivery projects={customer?.projects || []} loading={loading} />
  },
  {
    key: 'satisfaction',
    tab:
    <span>
          <Star size={16} />
          满意度调查 ({customer?.satisfactions?.length || 0})
    </span>,

    content: <CustomerSatisfaction satisfactions={customer?.satisfactions || []} loading={loading} />
  },
  {
    key: 'services',
    tab:
    <span>
          <MessageSquare size={16} />
          服务记录 ({customer?.services?.length || 0})
    </span>,

    content: <CustomerServiceRecords services={customer?.services || []} loading={loading} />
  },
  {
    key: 'analytics',
    tab:
    <span>
          <TrendingUp size={16} />
          数据分析
    </span>,

    content: <CustomerAnalytics customer={customer} loading={loading} />
  }];


  if (loading && !customer) {
    return (
      <div style={{ padding: '100px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>);

  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="customer-360-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              icon={<ArrowLeft size={16} />}
              onClick={handleBack}
              style={{ marginRight: 16 }}>

              返回客户列表
            </Button>
            <div>
              <Title level={2} style={{ margin: 0 }}>
                <Building2 className="inline-block mr-2" />
                客户360度视图
              </Title>
              {customer &&
              <Text type="secondary">
                  {customer.name} - {customer.contactPerson}
              </Text>
              }
            </div>
          </div>
          
          <Space>
            <Button
              icon={<Plus size={16} />}
              type="primary"
              onClick={handleCreateQuote}>

              创建报价
            </Button>
            <Button
              icon={<Plus size={16} />}
              onClick={handleCreateOrder}>

              创建订单
            </Button>
            <Button
              icon={<RefreshCw size={16} />}
              onClick={handleRefresh}>

              刷新数据
            </Button>
            <Button
              icon={<Edit size={16} />}>

              编辑客户
            </Button>
            <Button
              icon={<Download size={16} />}>

              导出报告
            </Button>
          </Space>
        </div>
      </div>

      {/* 客户基本信息卡片 */}
      {customer && <CustomerBasicInfo customer={customer} loading={loading} />}

      {/* 主要内容区域 */}
      <Card style={{ marginTop: '24px' }}>
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

export default Customer360;