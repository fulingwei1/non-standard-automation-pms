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
  Star,
  MessageSquare,
  TrendingUp,
  BarChart3,
  Target,
  RefreshCw,
  Download,
  Edit,
  Plus } from
"lucide-react";

import {
  Card,
  Tabs,
  Button,
  Space,
  Typography,
  Spin,
  DatePicker,
  message } from
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

import { customerApi } from '../services/api/crm';




const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const Customer360 = () => {
  const { customerId, id: routeId } = useParams();
  const resolvedCustomerId = customerId || routeId;
  const navigate = useNavigate();

  // 状态管理
  const [loading, setLoading] = useState(false);
  const [customer, setCustomer] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [_dateRange, _setDateRange] = useState(null);

  // 数据加载
  useEffect(() => {
    if (!resolvedCustomerId) {
      setCustomer(null);
      setLoading(false);
      return;
    }
    loadCustomerData();
  }, [resolvedCustomerId]);

  const loadCustomerData = async () => {
    if (!resolvedCustomerId) {
      setCustomer(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await customerApi.get360(resolvedCustomerId);
      setCustomer(response.data || response);
    } catch (_error) {
      message.error('加载客户数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/sales/customers');
  };

  const handleRefresh = () => {
    if (!resolvedCustomerId) {return;}
    loadCustomerData();
  };

  const _handleExport = (format) => {
    message.success(`正在导出${format}格式客户报告...`);
  };

  const handleCreateQuote = () => {
    if (!resolvedCustomerId) {return;}
    navigate(`/quotes/create?customerId=${resolvedCustomerId}`);
  };

  const handleCreateOrder = () => {
    if (!resolvedCustomerId) {return;}
    navigate(`/orders/create?customerId=${resolvedCustomerId}`);
  };

  if (!resolvedCustomerId) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="customer-360-container"
        style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
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
                <Text type="secondary">请选择客户后查看详情</Text>
              </div>
            </div>
          </div>
        </div>
        <Card>
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <Building2 size={48} style={{ color: '#94a3b8', marginBottom: 16 }} />
            <Title level={4}>暂未选择客户</Title>
            <Text type="secondary">从客户列表进入后，可查看订单、报价、合同、回款和服务记录。</Text>
            <div style={{ marginTop: 24 }}>
              <Button type="primary" onClick={handleBack}>前往客户列表</Button>
            </div>
          </div>
        </Card>
      </motion.div>);
  }

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
          size="large"
          items={(tabItems || []).map((item) => ({
            key: item.key,
            label: item.tab,
            children: item.content,
          }))}
        />
      </Card>
    </motion.div>);

};

export default Customer360;
